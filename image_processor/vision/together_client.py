"""Together AI vision client for image analysis (two 1-shot phases)."""

import os
import json
import base64
import logging
from io import BytesIO
from typing import Dict, Any

import requests
from PIL import Image

from ..core.exceptions import VisionAnalysisError

logger = logging.getLogger(__name__)


class TogetherVisionClient:
    """Client for communicating with Together AI multi-modal chat completion API."""

    API_URL = "https://api.together.xyz/v1/chat/completions"

    def __init__(self, max_tokens: int = 800, max_retries: int = 2):
        self.api_key = os.getenv("TOGETHER_API_KEY")
        if not self.api_key:
            raise VisionAnalysisError("TOGETHER_API_KEY environment variable not set")
        self.max_tokens = max_tokens
        self.max_retries = max_retries

    def analyze_image(self, image_data: bytes, filename: str, file_path: str, model: str) -> Dict[str, Any]:
        """Analyze an image using two 1-shot prompts on the specified Together model."""
        try:
            image_b64, media_type = self._prepare_image(image_data)
            visual = self._pass1_visual(model, image_b64, media_type, filename, file_path)
            scoring = self._pass2_scoring(model, image_b64, media_type, filename, visual)
            return {**visual, **scoring}
        except Exception as e:
            raise VisionAnalysisError(f"Together analysis failed for {filename}: {e}")

    def _prepare_image(self, image_data: bytes) -> tuple[str, str]:
        with Image.open(BytesIO(image_data)) as img:
            original_format = img.format
            if img.mode != 'RGB':
                img = img.convert('RGB')
            max_size = 1568
            if max(img.size) > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            buf = BytesIO()
            if original_format == 'PNG':
                img.save(buf, format='PNG', optimize=True)
                media_type = 'image/png'
            else:
                img.save(buf, format='JPEG', quality=85, optimize=True)
                media_type = 'image/jpeg'
            return base64.b64encode(buf.getvalue()).decode('utf-8'), media_type

    def _post(self, model: str, image_b64: str, media_type: str, prompt: str) -> Dict[str, Any]:
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
        body = {
            'model': model,
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        { 'type': 'image', 'image_url': f'data:{media_type};base64,{image_b64}' },
                        { 'type': 'text', 'text': prompt },
                    ]
                }
            ],
            'max_tokens': self.max_tokens,
        }

        last = None
        for attempt in range(self.max_retries):
            try:
                resp = requests.post(self.API_URL, headers=headers, data=json.dumps(body), timeout=60)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                last = e
                logger.warning(f"Together request failed (attempt {attempt+1}/{self.max_retries}): {e}")
        raise VisionAnalysisError(f"Together API error: {last}")

    def _extract_text(self, response_json: Dict[str, Any]) -> str:
        try:
            return response_json['choices'][0]['message']['content']
        except Exception as e:
            raise VisionAnalysisError(f"Invalid Together response structure: {e}")

    def _parse_json_block(self, text: str) -> Dict[str, Any]:
        start = text.find('{')
        end = text.rfind('}') + 1
        if start == -1 or end <= start:
            raise VisionAnalysisError("No JSON object in model output")
        return json.loads(text[start:end])

    def _pass1_visual(self, model: str, image_b64: str, media_type: str, filename: str, file_path: str) -> Dict[str, Any]:
        prompt = f"""Return EXACTLY one JSON object and nothing else. No prose, no markdown.

{{
  "primary_subject": "1–2 sentence description",
  "has_people": false,
  "people_count": "none|1-2|3-5|6-10|10+",
  "is_indoor": false,
  "activity_tags": ["gardening","harvesting","education","construction","maintenance","cooking","celebration","children","animals","landscape","tools","produce"],
  "season": "spring|summer|fall|winter|unclear",
  "time_of_day": "morning|midday|evening|unclear",
  "mood_energy": "short phrase",
  "color_palette": "short phrase",
  "notes": "≤140 chars of useful context from filename/folders; no speculation"
}}

Rules:
- Choose only from the allowed values.
- If uncertain, use "unclear" or a conservative false/none.
- Do NOT include any extra keys or text.

File context:
- Filename: {filename}
- Path: {file_path}"""

        resp = self._post(model, image_b64, media_type, prompt)
        text = self._extract_text(resp)
        return self._parse_json_block(text)

    def _pass2_scoring(self, model: str, image_b64: str, media_type: str, filename: str, visual: Dict[str, Any]) -> Dict[str, Any]:
        visual_summary = (
            f"Subject: {visual.get('primary_subject','Unknown')}\n"
            f"People: {visual.get('people_count','none')}\n"
            f"Setting: {'Indoor' if visual.get('is_indoor') else 'Outdoor'}\n"
            f"Activities: {', '.join(visual.get('activity_tags', []))}\n"
            f"Season: {visual.get('season','unclear')}\n"
            f"Time: {visual.get('time_of_day','unclear')}\n"
            f"Mood: {visual.get('mood_energy','Unknown')}\n"
            f"Colors: {visual.get('color_palette','Unknown')}"
        )
        prompt = f"""Return EXACTLY one JSON object and nothing else. No prose, no markdown.

Context:
{visual_summary}

Return:
{{
  "visual_quality": 1|2|3|4|5,
  "social_media_score": 1|2|3|4|5,
  "marketing_score": 1|2|3|4|5,
  "social_media_reason": "≤140 chars",
  "marketing_use": "≤140 chars"
}}

Guidelines (be harsh; 4–5 are rare):
- Visual quality: technical/composition quality only.
- Social media: engagement potential.
- Marketing: professional usage value.
No extra keys or text."""

        resp = self._post(model, image_b64, media_type, prompt)
        text = self._extract_text(resp)
        return self._parse_json_block(text)


