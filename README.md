# Lost Valley Image Manager

Full-stack app that discovers, analyzes, and catalogs media files from Google Drive with AI metadata, and serves a searchable gallery. Production runs on Railway.

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

- Node 18+/22 (Railway provides runtime)
- Google Drive credentials (service account recommended) or OAuth client+token
- SQLite DB file (`web-app/image_metadata.db` checked in for convenience)

## Project Structure (high level)

- `web-app/client` – React + Tailwind frontend
- `web-app/server` – Express API, thumbnails, downloads
- `image_processor` – Python pipeline (offline processing)
- `databases/` – DB snapshots (local); production uses `web-app/image_metadata.db`

## Getting Started (Railway)

1. Set Railway variables: `GOOGLE_SERVICE_ACCOUNT_JSON` (or OAuth vars)
2. Deploy: `railway up`
3. Visit your `*.up.railway.app` URL

## Development

- Frontend dev: `cd web-app/client && npm start`
- API dev: `cd web-app && npm run server`
- Combined dev: `cd web-app && npm run dev`

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]