# Google Drive Image Processor

An automated batch processing system that discovers, analyzes, and catalogs media files from Google Drive using local AI vision models. Built specifically for permaculture communities to transform poorly organized collections of thousands of images and videos into a searchable, well-categorized asset library.

## Features

- **Automated Discovery**: Recursively traverses entire Google Drive structure to find all media files
- **AI-Powered Analysis**: Uses Gemma-3-4b-it-qat local LLM for detailed metadata extraction
- **Permaculture-Focused**: Specialized metadata schema for gardening, harvesting, education, and community activities
- **Resumable Processing**: Tracks processing state to handle interruptions and avoid duplicate work
- **Local Control**: Runs entirely on local macOS machine with local AI models for privacy
- **Searchable Database**: SQLite database with complex filtering and search capabilities
- **Thumbnail Generation**: Creates thumbnails for quick visual identification

## Metadata Extracted

- Primary subject description (1-2 sentences)
- Visual quality rating (1-5 scale)
- People detection and count
- Activity tags (gardening, harvesting, education, construction, maintenance, cooking, celebration, children, animals, landscape, tools, produce)
- Social media suitability score with reasoning
- Marketing/professional use score with recommended use case
- Optional: Season, time of day, mood/energy, color palette

## Requirements

- Python 3.9+
- macOS (darwin platform)
- LM Studio with Gemma-3-4b-it-qat model running on http://127.0.0.1:1234
- Google Drive API credentials
- SQLite (included with Python)

## Project Structure

This project follows a spec-driven development approach. See `.kiro/specs/google-drive-image-processor/` for:

- `requirements.md` - Detailed feature requirements
- `design.md` - Technical architecture and design decisions
- `tasks.md` - Implementation plan with actionable coding tasks

## Getting Started

1. Set up your local environment with Python 3.9+
2. Install and configure LM Studio with Gemma-3-4b-it-qat model
3. Obtain Google Drive API credentials
4. Follow the implementation tasks in `.kiro/specs/google-drive-image-processor/tasks.md`

## Development Approach

This project uses a "crawl, walk, run" implementation strategy:

1. **Crawl**: Basic proof of concept with core pipeline
2. **Walk**: Robust local system with full feature set
3. **Run**: Optimized system with advanced search and management features

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]