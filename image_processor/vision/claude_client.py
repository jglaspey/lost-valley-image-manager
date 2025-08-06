"""Claude 3.5 Haiku vision client for image analysis."""

import json
import logging
import base64
import os
from io import BytesIO
from typing import Dict, Any, Optional
import anthropic
from PIL import Image
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

from ..core.config import VisionModelConfig
from ..core.exceptions import VisionAnalysisError

logger = logging.getLogger(__name__)


class ClaudeVisionClient:
    """Client for communicating with Claude 3.5 Haiku via Anthropic API."""
    
    def __init__(self, config: VisionModelConfig):
        """Initialize the Claude vision client."""
        self.config = config
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise VisionAnalysisError("ANTHROPIC_API_KEY environment variable not set")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-5-haiku-20241022"
    
    def analyze_image(self, image_data: bytes, filename: str, file_path: str = None) -> Dict[str, Any]:
        """
        Analyze an image using 2-pass approach: visual analysis then critical scoring.
        
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
            image_b64, media_type = self._prepare_image(image_data)
            
            # Pass 1: Visual Analysis
            logger.debug(f"Starting Pass 1 (visual analysis) for {filename}")
            visual_data = self._pass1_visual_analysis(image_b64, media_type, filename, file_path)
            
            # Pass 2: Critical Scoring
            logger.debug(f"Starting Pass 2 (critical scoring) for {filename}")
            scoring_data = self._pass2_critical_scoring(image_b64, media_type, filename, visual_data)
            
            # Combine results
            final_metadata = {**visual_data, **scoring_data}
            return final_metadata
            
        except Exception as e:
            logger.error(f"Claude 2-pass analysis failed for {filename}: {e}")
            raise VisionAnalysisError(f"Failed to analyze image {filename}: {e}")
    
    def _prepare_image(self, image_data: bytes) -> tuple[str, str]:
        """
        Prepare image data for API request.
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Tuple of (base64 encoded image string, media_type)
        """
        try:
            # Open and potentially resize image
            with Image.open(BytesIO(image_data)) as img:
                # Determine original format for media type
                original_format = img.format
                media_type = self._get_media_type(original_format)
                
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if too large (Claude handles up to 1568px on long edge well)
                max_size = 1568
                if max(img.size) > max_size:
                    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                
                # Convert to appropriate format
                buffer = BytesIO()
                if original_format in ['PNG']:
                    img.save(buffer, format='PNG', optimize=True)
                    media_type = "image/png"
                else:
                    img.save(buffer, format='JPEG', quality=85, optimize=True)
                    media_type = "image/jpeg"
                
                image_bytes = buffer.getvalue()
                
                # Encode to base64
                return base64.b64encode(image_bytes).decode('utf-8'), media_type
                
        except Exception as e:
            raise VisionAnalysisError(f"Failed to prepare image: {e}")
    
    def _get_media_type(self, format_name: str) -> str:
        """Get media type from PIL format name."""
        format_map = {
            'JPEG': 'image/jpeg',
            'PNG': 'image/png',
            'GIF': 'image/gif',
            'WEBP': 'image/webp',
            'BMP': 'image/jpeg',  # Convert BMP to JPEG
            'TIFF': 'image/jpeg',  # Convert TIFF to JPEG
        }
        return format_map.get(format_name, 'image/jpeg')
    
    def _pass1_visual_analysis(self, image_b64: str, media_type: str, filename: str, file_path: str = None) -> Dict[str, Any]:
        """
        Pass 1: Visual analysis only - what do you see?
        """
        prompt = f"""Analyze this image and provide a JSON response with ONLY visual observations:

{{
  "primary_subject": "Brief description of the main focus (1-2 sentences)",
  "has_people": false,
  "people_count": "none",
  "is_indoor": false,
  "activity_tags": ["landscape"],
  "season": "unclear",
  "time_of_day": "unclear",
  "mood_energy": "overall feeling or energy of the image",
  "color_palette": "dominant colors and color mood",
  "notes": "Additional insights from filename and file path context"
}}

File context:
- Filename: {filename}
- File path: {file_path or filename}

INSTRUCTIONS:
- has_people: boolean true or false
- people_count: must be one of: "none", "1-2", "3-5", "6-10", "10+"
- is_indoor: boolean true or false  
- activity_tags: array of strings, select all that apply from: gardening, harvesting, education, construction, maintenance, cooking, celebration, children, animals, landscape, tools, produce
- season: must be one of: "spring", "summer", "fall", "winter", "unclear"
- time_of_day: must be one of: "morning", "midday", "evening", "unclear"
- mood_energy: describe the feeling (e.g., "peaceful and serene", "vibrant and energetic")
- color_palette: describe dominant colors (e.g., "warm earth tones", "cool blues and greens")
- notes: extract insights about source, context, dates from filename/folder structure

Focus only on what you can clearly observe. No quality judgments or scoring."""

        response = self._make_request(image_b64, media_type, prompt)
        return self._parse_visual_response(response, filename)

    def _pass2_critical_scoring(self, image_b64: str, media_type: str, filename: str, visual_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pass 2: Critical scoring based on visual analysis
        """
        visual_summary = f"""Previous analysis of this image:
Subject: {visual_data.get('primary_subject', 'Unknown')}
People: {visual_data.get('people_count', 'none')} people
Setting: {'Indoor' if visual_data.get('is_indoor') else 'Outdoor'}
Activities: {', '.join(visual_data.get('activity_tags', []))}
Season: {visual_data.get('season', 'unclear')}
Time: {visual_data.get('time_of_day', 'unclear')}
Mood: {visual_data.get('mood_energy', 'Unknown')}
Colors: {visual_data.get('color_palette', 'Unknown')}"""

        prompt = f"""You are a CRITICAL evaluator for a permaculture education center's image library. Looking at this image and the analysis below, provide STRICT scoring:

{visual_summary}

Return JSON with these 3 scores:
{{
  "visual_quality": 3,
  "social_media_score": 3,
  "marketing_score": 3,
  "social_media_reason": "One sentence explaining social media score",
  "marketing_use": "Best professional use case for this image"
}}

CRITICAL SCORING GUIDELINES:

**Visual Quality (technical assessment):**
- 5: Portfolio-worthy (perfect focus, lighting, composition) - RARE, maybe 2-3% of photos
- 4: Very good (minor flaws, professional looking) - Maybe 10-15% of photos  
- 3: Good/decent (usable, some issues) - Common, 40-50% of photos
- 2: Below average (noticeable problems) - 30-40% of photos
- 1: Poor (out of focus, bad lighting, unusable) - 5-10% of photos

**Social Media Score (engagement potential):**
- 5: Viral potential (stunning, inspiring, highly shareable)
- 4: Very engaging (clear story, emotional connection)
- 3: Good content (decent engagement, clear message)
- 2: Limited appeal (niche audience only)
- 1: Poor engagement (confusing, boring, low quality)

**Marketing Score (professional use value):**
- 5: Premium marketing (could be in brochures, website headers)
- 4: Professional use (good for newsletters, social posts)
- 3: General use (fine for documentation, basic marketing)
- 2: Limited use (internal only, low-key applications)
- 1: Not recommended (quality/content issues)

BE HARSH. Most permaculture photos are everyday documentation, not professional marketing material. Reserve 4s and 5s for truly exceptional images."""

        response = self._make_request(image_b64, media_type, prompt)
        return self._parse_scoring_response(response, filename)

    def _make_request(self, image_b64: str, media_type: str, prompt: str) -> anthropic.types.Message:
        """
        Make API request with retries.
        
        Args:
            image_b64: Base64 encoded image
            media_type: Image media type
            prompt: Analysis prompt
            
        Returns:
            Anthropic API response
        """
        last_exception = None
        
        for attempt in range(self.config.max_retries):
            try:
                logger.debug(f"Making Claude API request (attempt {attempt + 1}/{self.config.max_retries})")
                
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.config.max_tokens,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": media_type,
                                        "data": image_b64,
                                    },
                                },
                                {
                                    "type": "text",
                                    "text": prompt
                                }
                            ],
                        }
                    ],
                )
                
                return response
                    
            except Exception as e:
                last_exception = e
                logger.warning(f"Claude API request attempt {attempt + 1} failed: {e}")
                
                if attempt < self.config.max_retries - 1:
                    # Wait before retry (exponential backoff)
                    import time
                    time.sleep(2 ** attempt)
        
        raise VisionAnalysisError(f"All {self.config.max_retries} API requests failed. Last error: {last_exception}")
    
    def _parse_visual_response(self, response: anthropic.types.Message, filename: str) -> Dict[str, Any]:
        """Parse Pass 1 visual analysis response."""
        return self._parse_json_response(response, filename, pass_type="visual")

    def _parse_scoring_response(self, response: anthropic.types.Message, filename: str) -> Dict[str, Any]:
        """Parse Pass 2 scoring response."""
        return self._parse_json_response(response, filename, pass_type="scoring")

    def _parse_json_response(self, response: anthropic.types.Message, filename: str, pass_type: str) -> Dict[str, Any]:
        """
        Parse API response and extract structured metadata.
        
        Args:
            response: Anthropic API response
            filename: Original filename for context
            pass_type: "visual" or "scoring"
            
        Returns:
            Parsed metadata dictionary
        """
        try:
            # Extract content from Claude response
            if not response.content or len(response.content) == 0:
                raise VisionAnalysisError("No content in API response")
            
            # Get the text content (Claude returns TextBlock objects)
            content = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    content += block.text
            
            if not content:
                raise VisionAnalysisError("No text content in API response")
            
            # Try to parse JSON from the content
            try:
                # Look for JSON block in the response
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                
                if json_start == -1 or json_end <= json_start:
                    raise ValueError("No JSON block found in response")
                
                json_content = content[json_start:json_end]
                metadata = json.loads(json_content)
                
                # Validate based on pass type
                if pass_type == "visual":
                    required_fields = [
                        'primary_subject', 'has_people', 'people_count', 
                        'is_indoor', 'activity_tags', 'notes'
                    ]
                else:  # scoring
                    required_fields = [
                        'visual_quality', 'social_media_score', 'social_media_reason',
                        'marketing_score', 'marketing_use'
                    ]
                
                for field in required_fields:
                    if field not in metadata:
                        logger.warning(f"Missing required field '{field}' in {pass_type} response for {filename}")
                        metadata[field] = self._get_default_value(field)
                
                # Validate and clean values
                metadata = self._validate_metadata(metadata, filename, pass_type)
                
                return metadata
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse JSON from Claude {pass_type} response for {filename}: {e}")
                logger.debug(f"Raw response content: {content}")
                
                # Return fallback metadata
                return self._get_fallback_metadata(filename, pass_type)
                
        except Exception as e:
            logger.error(f"Failed to parse Claude {pass_type} response for {filename}: {e}")
            return self._get_fallback_metadata(filename, pass_type)
    
    def _validate_metadata(self, metadata: Dict[str, Any], filename: str, pass_type: str = "combined") -> Dict[str, Any]:
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
    
    def _get_fallback_metadata(self, filename: str, pass_type: str = "combined") -> Dict[str, Any]:
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
        Test connection to the Claude API.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Make a simple request to test the connection
            test_response = self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[
                    {
                        "role": "user",
                        "content": "Hello"
                    }
                ]
            )
            
            if test_response and test_response.content:
                logger.info("Claude API connection successful")
                return True
            else:
                logger.error("Claude API returned empty response")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to Claude API: {e}")
            return False