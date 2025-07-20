# Permaculture Community Metadata Schema

## Model Configuration

- **Model**: Gemma-3-4b-it-qat (quantized instruction-tuned, 4B parameters)
- **Access**: LM Studio local API at http://127.0.0.1:1234
- **Temperature**: 0.3-0.5 for consistent factual outputs
- **Max Tokens**: 500 (keep prompts focused and concise)
- **Format**: JSON structured outputs

## Core Metadata Fields

### Required Fields (Always Extract)

1. **Primary Subject** (text, 1-2 sentences)
   - Main focus of the image
   - Examples: "Group planting seedlings in raised beds", "Close-up of ripe tomatoes"

2. **Visual Quality** (1-5 scale)
   - 1: Blurry/poorly composed/unusable
   - 2: Mediocre quality, limited use
   - 3: Decent, usable for some purposes
   - 4: Good quality, clear and well-composed
   - 5: Excellent, professional quality

3. **People Present** (boolean + count)
   - Has people: yes/no
   - Count: none/1-2/3-5/6-10/10+

4. **Activity Tags** (multiple selection)
   - gardening, harvesting, education, construction
   - maintenance, cooking, celebration, children
   - animals, landscape, tools, produce

5. **Social Media Score** (1-5 scale + reason)
   - 1: Not suitable → 5: Highly shareable
   - Include one sentence explaining the rating

6. **Marketing/Professional Use** (1-5 scale + use case)
   - 1: Not suitable → 5: Hero image quality
   - Best use: website banner/newsletter/social media/print materials

### Optional Fields (Include if Model Capacity Allows)

7. **Season/Time** (if discernible)
   - Season: spring/summer/fall/winter/unclear
   - Time: morning/midday/evening/unclear

8. **Mood/Energy**: peaceful, energetic, joyful, focused, contemplative

9. **Color Palette**: Dominant colors (max 3)

## Structured Prompt Template

```json
{
  "primary_subject": "Brief description of the main focus (1-2 sentences)",
  "visual_quality": "[1-5 scale: 1=blurry/poor, 3=decent, 5=excellent]",
  "has_people": "true/false",
  "people_count": "none/1-2/3-5/6-10/10+",
  "activity_tags": ["select all that apply: gardening, harvesting, education, construction, maintenance, cooking, celebration, children, animals, landscape, tools, produce"],
  "social_media_score": "[1-5 scale]",
  "social_media_reason": "One sentence explaining score",
  "marketing_score": "[1-5 scale]",
  "marketing_use": "best use case for this image"
}
```

## Implementation Guidelines

### For Gemma-3-4b Model
- Keep prompts under 500 tokens
- Use structured JSON format requests
- Low temperature (0.3-0.5) for consistency
- Add JSON validation layer with retry logic
- Batch similar images for context retention

### Search Scenarios Enabled
- "5-star marketing photos with produce but no people" (hero images)
- "4+ social media score with children and gardening" (engagement content)
- "education tag with 6-10 people" (workshop documentation)
- "high quality landscape shots from summer" (seasonal banners)
- "celebration photos with 10+ people rated 4+" (community showcase)

### Avoid Asking For
- Detailed facial recognition or demographics
- Complex multi-activity scene analysis
- Subjective artistic critique
- Long-form descriptions (keep to 1-2 sentences max)