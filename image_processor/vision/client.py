"""Vision model client for communicating with local LLM."""

import json
import logging
import base64
from io import BytesIO
from typing import Dict, Any, Optional
import requests
from PIL import Image
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

from ..core.config import VisionModelConfig
from ..core.exceptions import VisionAnalysisError

logger = logging.getLogger(__name__)


class VisionClient:
    """Client for communicating with local Gemma-3-4b-it-qat vision model."""
    
    def __init__(self, config: VisionModelConfig):
        """Initialize the vision client."""
        self.config = config
        self.session = requests.Session()
        self.session.timeout = config.timeout_seconds
    
    def analyze_image(self, image_data: bytes, filename: str, file_path: str = None) -> Dict[str, Any]:
        """
        Analyze an image and return structured metadata.
        
        Args:
            image_data: Raw image bytes
            filename: Original filename for context
            file_path: Full file path for context
            
        Returns:
            Dict containing extracted metadata
            
        Raises:
            VisionAnalysisError: If analysis fails
        """
        try:
            # Convert image to base64
            image_b64 = self._prepare_image(image_data)
            
            # Format the prompt with filename and path context
            formatted_prompt = self.config.prompt_template.format(
                filename=filename,
                file_path=file_path or filename
            )
            
            # Prepare the request payload
            payload = {
                "model": self.config.model_type,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": formatted_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_b64}"
                                }
                            }
                        ]
                    }
                ],
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "stream": False
            }
            
            # Make the API request
            response = self._make_request(payload)
            
            # Parse the response
            return self._parse_response(response, filename)
            
        except Exception as e:
            logger.error(f"Vision analysis failed for {filename}: {e}")
            raise VisionAnalysisError(f"Failed to analyze image {filename}: {e}")
    
    def _prepare_image(self, image_data: bytes) -> str:
        """
        Prepare image data for API request.
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Base64 encoded image string
        """
        try:
            # Open and potentially resize image
            with Image.open(BytesIO(image_data)) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if too large (max 1024x1024 for efficiency)
                max_size = 1024
                if max(img.size) > max_size:
                    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                
                # Convert to JPEG bytes
                buffer = BytesIO()
                img.save(buffer, format='JPEG', quality=85)
                jpeg_data = buffer.getvalue()
                
                # Encode to base64
                return base64.b64encode(jpeg_data).decode('utf-8')
                
        except Exception as e:
            raise VisionAnalysisError(f"Failed to prepare image: {e}")
    
    def _make_request(self, payload: Dict[str, Any]) -> requests.Response:
        """
        Make API request with retries.
        
        Args:
            payload: Request payload
            
        Returns:
            API response
        """
        url = f"{self.config.api_endpoint}/v1/chat/completions"
        headers = {
            "Content-Type": "application/json"
        }
        
        last_exception = None
        
        for attempt in range(self.config.max_retries):
            try:
                logger.debug(f"Making vision API request (attempt {attempt + 1}/{self.config.max_retries})")
                
                response = self.session.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self.config.timeout_seconds
                )
                
                if response.status_code == 200:
                    return response
                else:
                    raise requests.HTTPError(f"API returned status {response.status_code}: {response.text}")
                    
            except Exception as e:
                last_exception = e
                logger.warning(f"Vision API request attempt {attempt + 1} failed: {e}")
                
                if attempt < self.config.max_retries - 1:
                    # Wait before retry (exponential backoff)
                    import time
                    time.sleep(2 ** attempt)
        
        raise VisionAnalysisError(f"All {self.config.max_retries} API requests failed. Last error: {last_exception}")
    
    def _parse_response(self, response: requests.Response, filename: str) -> Dict[str, Any]:
        """
        Parse API response and extract structured metadata.
        
        Args:
            response: API response
            filename: Original filename for context
            
        Returns:
            Parsed metadata dictionary
        """
        try:
            response_data = response.json()
            
            # Extract content from OpenAI-compatible response
            if 'choices' not in response_data or not response_data['choices']:
                raise VisionAnalysisError("No choices in API response")
            
            content = response_data['choices'][0]['message']['content']
            
            # Try to parse JSON from the content
            # The model should return JSON, but may include additional text
            try:
                # Look for JSON block in the response
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                
                if json_start == -1 or json_end <= json_start:
                    raise ValueError("No JSON block found in response")
                
                json_content = content[json_start:json_end]
                metadata = json.loads(json_content)
                
                # Validate required fields
                required_fields = [
                    'primary_subject', 'visual_quality', 'has_people', 
                    'people_count', 'is_indoor', 'activity_tags',
                    'social_media_score', 'social_media_reason',
                    'marketing_score', 'marketing_use', 'notes'
                ]
                
                for field in required_fields:
                    if field not in metadata:
                        logger.warning(f"Missing required field '{field}' in response for {filename}")
                        metadata[field] = self._get_default_value(field)
                
                # Validate and clean values
                metadata = self._validate_metadata(metadata, filename)
                
                return metadata
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse JSON from API response for {filename}: {e}")
                logger.debug(f"Raw response content: {content}")
                
                # Return fallback metadata
                return self._get_fallback_metadata(filename)
                
        except Exception as e:
            logger.error(f"Failed to parse API response for {filename}: {e}")
            return self._get_fallback_metadata(filename)
    
    def _validate_metadata(self, metadata: Dict[str, Any], filename: str) -> Dict[str, Any]:
        """
        Validate and clean metadata values.
        
        Args:
            metadata: Raw metadata dictionary
            filename: Original filename for logging
            
        Returns:
            Cleaned metadata dictionary
        """
        # Validate visual_quality (1-5)
        if not isinstance(metadata.get('visual_quality'), int) or not 1 <= metadata['visual_quality'] <= 5:
            logger.warning(f"Invalid visual_quality for {filename}, using default")
            metadata['visual_quality'] = 3
        
        # Validate people_count
        valid_people_counts = ['none', '1-2', '3-5', '6-10', '10+']
        if metadata.get('people_count') not in valid_people_counts:
            logger.warning(f"Invalid people_count for {filename}, using default")
            metadata['people_count'] = 'none' if not metadata.get('has_people') else '1-2'
        
        # Validate scores (1-5)
        for score_field in ['social_media_score', 'marketing_score']:
            if not isinstance(metadata.get(score_field), int) or not 1 <= metadata[score_field] <= 5:
                logger.warning(f"Invalid {score_field} for {filename}, using default")
                metadata[score_field] = 3
        
        # Validate boolean fields
        for bool_field in ['has_people', 'is_indoor']:
            if not isinstance(metadata.get(bool_field), bool):
                logger.warning(f"Invalid {bool_field} for {filename}, using default")
                metadata[bool_field] = False
        
        # Validate activity_tags
        valid_tags = [
            'gardening', 'harvesting', 'education', 'construction',
            'maintenance', 'cooking', 'celebration', 'children',
            'animals', 'landscape', 'tools', 'produce'
        ]
        
        if not isinstance(metadata.get('activity_tags'), list):
            metadata['activity_tags'] = []
        else:
            # Filter to valid tags only
            metadata['activity_tags'] = [
                tag for tag in metadata['activity_tags'] 
                if tag in valid_tags
            ]
        
        # Validate season if present
        if metadata.get('season'):
            valid_seasons = ['spring', 'summer', 'fall', 'winter', 'unclear']
            if metadata['season'] not in valid_seasons:
                metadata['season'] = 'unclear'
        
        return metadata
    
    def _get_default_value(self, field: str) -> Any:
        """Get default value for a missing field."""
        defaults = {
            'primary_subject': 'Image content could not be analyzed',
            'visual_quality': 3,
            'has_people': False,
            'people_count': 'none',
            'is_indoor': False,
            'activity_tags': [],
            'social_media_score': 3,
            'social_media_reason': 'Unable to analyze',
            'marketing_score': 3,
            'marketing_use': 'General use',
            'season': 'unclear',
            'notes': 'No additional context available'
        }
        return defaults.get(field, None)
    
    def _get_fallback_metadata(self, filename: str) -> Dict[str, Any]:
        """Return fallback metadata when parsing fails."""
        return {
            'primary_subject': f'Failed to analyze {filename}',
            'visual_quality': 1,
            'has_people': False,
            'people_count': 'none',
            'is_indoor': False,
            'activity_tags': [],
            'social_media_score': 1,
            'social_media_reason': 'Analysis failed',
            'marketing_score': 1,
            'marketing_use': 'Not recommended',
            'season': 'unclear',
            'notes': f'Analysis failed for {filename}'
        }
    
    def test_connection(self) -> bool:
        """
        Test connection to the vision model API.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            url = f"{self.config.api_endpoint}/v1/models"
            response = self.session.get(url, timeout=5)
            
            if response.status_code == 200:
                logger.info("Vision model API connection successful")
                return True
            else:
                logger.error(f"Vision model API returned status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to vision model API: {e}")
            return False