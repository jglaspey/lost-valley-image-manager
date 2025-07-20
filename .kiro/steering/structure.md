# Project Structure

## Directory Organization

```
image_processor/
├── image_processor/           # Main package
│   ├── __init__.py
│   ├── cli/                   # Command-line interface
│   │   ├── __init__.py
│   │   ├── main.py           # CLI entry point
│   │   ├── process.py        # Processing commands
│   │   └── search.py         # Search commands
│   ├── core/                 # Core business logic
│   │   ├── __init__.py
│   │   ├── models.py         # Data models (MediaFile, ExtractedMetadata)
│   │   ├── config.py         # Configuration management
│   │   └── exceptions.py     # Custom exceptions
│   ├── services/             # Business services
│   │   ├── __init__.py
│   │   ├── discovery.py      # File Discovery Service
│   │   ├── processing.py     # Processing Queue
│   │   ├── vision.py         # Vision Analysis Engine
│   │   ├── thumbnails.py     # Thumbnail Generator
│   │   └── search.py         # Search Service
│   ├── data/                 # Data access layer
│   │   ├── __init__.py
│   │   ├── database.py       # Database connection management
│   │   ├── repositories.py   # Repository classes
│   │   └── migrations.py     # Database schema migrations
│   └── utils/                # Utility functions
│       ├── __init__.py
│       ├── logging.py        # Logging configuration
│       └── helpers.py        # Common helper functions
├── tests/                    # Test suite
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   ├── fixtures/             # Test data and fixtures
│   └── conftest.py          # Pytest configuration
├── config/                   # Configuration files
│   ├── config.yaml          # Main configuration
│   └── logging.yaml         # Logging configuration
├── docs/                     # Documentation
├── scripts/                  # Utility scripts
├── requirements.txt          # Python dependencies
├── requirements-dev.txt      # Development dependencies
├── setup.py                 # Package setup
├── README.md                # Project documentation
└── .env.example             # Environment variables template
```

## Key Conventions

### Package Structure
- **Core**: Contains data models, configuration, and fundamental types
- **Services**: Business logic organized by domain (discovery, processing, vision, etc.)
- **Data**: Database operations and data access patterns
- **CLI**: Command-line interface organized by command groups
- **Utils**: Shared utilities and helper functions

### File Naming
- Use snake_case for Python files and directories
- Service classes end with "Service" (e.g., `DiscoveryService`)
- Repository classes end with "Repository" (e.g., `FileRepository`)
- Model classes use PascalCase (e.g., `MediaFile`, `ExtractedMetadata`)

### Import Organization
- Standard library imports first
- Third-party imports second
- Local imports last
- Use absolute imports from package root

### Configuration Management
- YAML files for configuration
- Environment variables for sensitive data
- Configuration validation on startup
- Separate configs for development/production

### Testing Structure
- Mirror source structure in tests/
- Use fixtures for common test data
- Separate unit and integration tests
- Mock external dependencies in unit tests

### Database Files
- SQLite database stored in project root as `image_metadata.db`
- Thumbnails stored in `thumbnails/` directory
- Logs stored in `logs/` directory
- Backup files in `backups/` directory