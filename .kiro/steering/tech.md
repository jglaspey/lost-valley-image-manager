# Technology Stack

## Core Technologies

- **Python 3.9+**: Primary development language
- **SQLite**: Local database for metadata storage
- **Google Drive API v3**: File discovery and access
- **Gemma-3-4b-it-qat**: Quantized instruction-tuned vision model via LM Studio (http://127.0.0.1:1234)

## Key Libraries & Frameworks

- `google-api-python-client`: Google Drive API integration
- `Pillow`: Image processing and thumbnail generation
- `click`: Command-line interface framework
- `tqdm`: Progress bars for batch operations
- `python-dotenv`: Environment variable management
- `requests`: HTTP client for API calls
- `sqlite3`: Database operations (built-in)

## Development Environment

- **Platform**: macOS (darwin)
- **Shell**: zsh
- **Package Management**: pip with virtual environments
- **Configuration**: YAML-based configuration files

## Common Commands

### Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up Google Drive credentials
# Place credentials.json in project root
```

### Development
```bash
# Run batch processing
python -m image_processor process --config config.yaml

# Search processed images
python -m image_processor search --query "outdoor" --has-people

# Check processing status
python -m image_processor status

# Run tests
python -m pytest tests/

# Run with coverage
python -m pytest --cov=image_processor tests/
```

### Database Management
```bash
# Initialize database
python -m image_processor init-db

# Backup database
python -m image_processor backup-db

# View processing statistics
python -m image_processor stats
```

## Architecture Patterns

- **Pipeline Architecture**: Discovery → Processing → Storage → Access
- **Repository Pattern**: Data access abstraction layer
- **Command Pattern**: CLI interface design
- **State Machine**: Processing status management
- **Batch Processing**: Queue-based file processing with resumability