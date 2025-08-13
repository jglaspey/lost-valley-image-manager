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
                
                # Resize if too large (use smaller long edge to cut latency/cost)
                max_size = 512
                if max(img.size) > max_size:
                    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                
                # Re-encode to compact JPEG for transmission
                buffer = BytesIO()
                img.save(buffer, format='JPEG', quality=80, optimize=True, progressive=True)
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
        prompt = (
            "Return EXACTLY one JSON object and nothing else. No prose, no markdown.\n\n"
            "{\n"
            "  \"primary_subject\": \"1–3 sentence description\",\n"
            "  \"has_people\": false,\n"
            "  \"people_count\": \"none|1-2|3-5|6-10|10+\",\n"
            "  \"is_indoor\": false,\n"
            "  \"activity_tags\": [\"gardening\",\"harvesting\",\"education\",\"construction\",\"maintenance\",\"cooking\",\"celebration\",\"children\",\"animals\",\"landscape\",\"tools\",\"produce\"],\n"
            "  \"season\": \"spring|summer|fall|winter|unclear\",\n"
            "  \"time_of_day\": \"morning|midday|evening|unclear\",\n"
            "  \"mood_energy\": \"short phrase\",\n"
            "  \"color_palette\": \"short phrase\",\n"
            "  \"file_path_notes\": \"≤320 chars. Focus only on the file path - Extract helpful context you can infer with high confidence from the filename and folder names (e.g., people and names, events, location, date, project, camera, series). Prefer concise phrases; include multiple clues if present. Avoid speculation beyond the path.\"\n"
            "}\n\n"
            "Rules:\n"
            "- Choose only from the allowed values.\n"
            "- If uncertain, use \"unclear\" or a conservative false/none.\n"
            "- Do NOT include any extra keys or text.\n\n"
            f"File context:\n- Filename: {filename}\n- Path: {file_path or filename}"
        )

        response = self._make_request(image_b64, media_type, prompt)
        data = self._parse_visual_response(response, filename)
        # Ensure types are valid to reduce downstream warnings
        data = self._normalize_metadata(data)
        data = self._validate_metadata(data, filename, pass_type="visual")
        return data

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

        prompt = (
            "Return EXACTLY one JSON object and nothing else. No prose, no markdown.\n\n"
            f"Context:\n{visual_summary}\n\n"
            "Return:\n"
            "{\n"
            "  \"visual_quality\": 1|2|3|4|5,\n"
            "  \"social_media_score\": 1|2|3|4|5,\n"
            "  \"marketing_score\": 1|2|3|4|5,\n"
            "  \"social_media_reason\": \"≤140 chars\",\n"
            "  \"marketing_use\": \"≤140 chars\"\n"
            "}\n\n"
            "Guidelines (be harsh; 4–5 are rare):\n"
            "- Visual quality: technical/composition quality only.\n"
            "- Social media: engagement potential.\n"
            "- Marketing: professional usage value.\n"
            "No extra keys or text."
        )

        response = self._make_request(image_b64, media_type, prompt)
        data = self._parse_scoring_response(response, filename)
        data = self._normalize_metadata(data)
        data = self._validate_metadata(data, filename, pass_type="scoring")
        return data

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
                        'is_indoor', 'activity_tags', 'file_path_notes'
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
                
                # Normalize then validate values
                metadata = self._normalize_metadata(metadata)
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

    def _normalize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Coerce common type/format mistakes from the model into our schema."""
        def to_bool(v):
            if isinstance(v, bool):
                return v
            if isinstance(v, (int, float)):
                return bool(v)
            if isinstance(v, str):
                s = v.strip().lower()
                if s in {"true", "yes", "y", "1"}:
                    return True
                if s in {"false", "no", "n", "0"}:
                    return False
            return False

        def to_int_1_5(v):
            try:
                if isinstance(v, str):
                    v = v.replace(" ", "")
                    if "." in v:
                        v = int(round(float(v)))
                    else:
                        v = int(v)
                v = int(v)
            except Exception:
                return None
            return max(1, min(5, v))

        # Booleans
        if 'has_people' in metadata:
            metadata['has_people'] = to_bool(metadata.get('has_people'))
        if 'is_indoor' in metadata:
            metadata['is_indoor'] = to_bool(metadata.get('is_indoor'))

        # Integer scores
        for k in ['visual_quality', 'social_media_score', 'marketing_score']:
            if k in metadata:
                val = to_int_1_5(metadata.get(k))
                if val is not None:
                    metadata[k] = val

        # People count normalization
        if 'people_count' in metadata:
            raw = str(metadata.get('people_count', '')).strip().lower()
            s = raw.replace('–', '-').replace('—', '-').replace('to', '-').replace('people', '').replace('person', '').replace('persons', '').replace(' ', '')
            mapping = {
                '0': 'none', 'zero': 'none', 'none': 'none', 'noone': 'none', 'n/a': 'none', 'na': 'none',
                '1': '1-2', '2': '1-2', '1-2': '1-2', '1or2': '1-2', 'oneortwo': '1-2',
                '3': '3-5', '4': '3-5', '5': '3-5', '3-5': '3-5', '3or5': '3-5',
                '6': '6-10', '7': '6-10', '8': '6-10', '9': '6-10', '10': '6-10', '6-10': '6-10',
            }
            metadata['people_count'] = mapping.get(s, '10+')

        # Activity tags normalization
        valid_tags = {
            'gardening', 'harvesting', 'education', 'construction', 'maintenance', 'cooking',
            'celebration', 'children', 'animals', 'landscape', 'tools', 'produce'
        }
        tags = metadata.get('activity_tags')
        if isinstance(tags, str):
            tags = [t.strip().lower() for t in tags.split(',') if t.strip()]
        if isinstance(tags, list):
            metadata['activity_tags'] = sorted({t for t in [str(x).lower() for x in tags] if t in valid_tags})

        # Season normalization
        if 'season' in metadata and isinstance(metadata['season'], str):
            s = metadata['season'].strip().lower()
            season_map = {
                'spring': 'spring', 'summer': 'summer', 'fall': 'fall', 'autumn': 'fall',
                'winter': 'winter', 'unclear': 'unclear', 'unknown': 'unclear'
            }
            metadata['season'] = season_map.get(s, 'unclear')

        # Time of day normalization
        if 'time_of_day' in metadata and isinstance(metadata['time_of_day'], str):
            t = metadata['time_of_day'].strip().lower()
            time_map = {
                'morning': 'morning', 'sunrise': 'morning', 'dawn': 'morning',
                'midday': 'midday', 'noon': 'midday', 'afternoon': 'midday',
                'evening': 'evening', 'sunset': 'evening', 'dusk': 'evening', 'twilight': 'evening',
                'unclear': 'unclear', 'unknown': 'unclear'
            }
            metadata['time_of_day'] = time_map.get(t, 'unclear')

        # Rename notes->file_path_notes for backward compatibility
        if 'file_path_notes' not in metadata and 'notes' in metadata:
            metadata['file_path_notes'] = metadata['notes']
        return metadata
    
    def _validate_metadata(self, metadata: Dict[str, Any], filename: str, pass_type: str = "combined") -> Dict[str, Any]:
        """Validate and clean metadata values (scoped to pass_type to avoid cross-pass defaults)."""
        check_visual = pass_type in ("visual", "combined")
        check_scoring = pass_type in ("scoring", "combined")

        if check_scoring:
            # Validate visual_quality (1-5)
            if not isinstance(metadata.get('visual_quality'), int) or not 1 <= metadata['visual_quality'] <= 5:
                logger.warning(f"Invalid visual_quality for {filename}, using default")
                metadata['visual_quality'] = 3

            # Validate scores (1-5)
            for score_field in ['social_media_score', 'marketing_score']:
                if not isinstance(metadata.get(score_field), int) or not 1 <= metadata[score_field] <= 5:
                    logger.warning(f"Invalid {score_field} for {filename}, using default")
                    metadata[score_field] = 3

        if check_visual:
            # Validate people_count bucket
            valid_people_counts = ['none', '1-2', '3-5', '6-10', '10+']
            if metadata.get('people_count') not in valid_people_counts:
                logger.warning(f"Invalid people_count for {filename}, using default")
                metadata['people_count'] = 'none' if not metadata.get('has_people') else '1-2'

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
                metadata['activity_tags'] = [tag for tag in metadata['activity_tags'] if tag in valid_tags]

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