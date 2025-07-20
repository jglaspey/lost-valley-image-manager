"""Configuration management for the Google Drive Image Processor."""

import os
import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .exceptions import ConfigurationError


@dataclass
class GoogleDriveConfig:
    """Google Drive API configuration."""
    credentials_path: str
    root_folder_id: Optional[str] = None
    batch_size: int = 100
    rate_limit_delay: float = 1.0


@dataclass
class VisionModelConfig:
    """Vision model configuration."""
    model_type: str = "gemma-3-4b-it-qat"
    api_endpoint: str = "http://127.0.0.1:1234"
    temperature: float = 0.4
    max_tokens: int = 500
    max_retries: int = 3
    timeout_seconds: int = 30
    prompt_template: str = ""


@dataclass
class DatabaseConfig:
    """Database configuration."""
    type: str = "sqlite"
    path: str = "image_metadata.db"
    backup_enabled: bool = True
    backup_interval_hours: int = 24


@dataclass
class ProcessingConfig:
    """Processing configuration."""
    thumbnail_size: List[int] = None
    supported_formats: List[str] = None
    max_file_size_mb: int = 50
    concurrent_workers: int = 4

    def __post_init__(self):
        if self.thumbnail_size is None:
            self.thumbnail_size = [200, 200]
        if self.supported_formats is None:
            self.supported_formats = ["jpg", "jpeg", "png", "gif", "bmp", "tiff"]


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    file_path: str = "processing.log"
    max_file_size_mb: int = 10
    backup_count: int = 5


@dataclass
class Config:
    """Main configuration class."""
    google_drive: GoogleDriveConfig
    vision_model: VisionModelConfig
    database: DatabaseConfig
    processing: ProcessingConfig
    logging: LoggingConfig

    @classmethod
    def from_file(cls, config_path: str) -> "Config":
        """Load configuration from YAML file."""
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in configuration file: {e}")
        
        try:
            return cls(
                google_drive=GoogleDriveConfig(**config_data.get('google_drive', {})),
                vision_model=VisionModelConfig(**config_data.get('vision_model', {})),
                database=DatabaseConfig(**config_data.get('database', {})),
                processing=ProcessingConfig(**config_data.get('processing', {})),
                logging=LoggingConfig(**config_data.get('logging', {}))
            )
        except TypeError as e:
            raise ConfigurationError(f"Invalid configuration structure: {e}")

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables with defaults."""
        return cls(
            google_drive=GoogleDriveConfig(
                credentials_path=os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json'),
                root_folder_id=os.getenv('GOOGLE_ROOT_FOLDER_ID'),
                batch_size=int(os.getenv('GOOGLE_BATCH_SIZE', '100')),
                rate_limit_delay=float(os.getenv('GOOGLE_RATE_LIMIT_DELAY', '1.0'))
            ),
            vision_model=VisionModelConfig(
                model_type=os.getenv('VISION_MODEL_TYPE', 'gemma-3-4b-it-qat'),
                api_endpoint=os.getenv('VISION_API_ENDPOINT', 'http://127.0.0.1:1234'),
                temperature=float(os.getenv('VISION_TEMPERATURE', '0.4')),
                max_tokens=int(os.getenv('VISION_MAX_TOKENS', '500')),
                max_retries=int(os.getenv('VISION_MAX_RETRIES', '3')),
                timeout_seconds=int(os.getenv('VISION_TIMEOUT_SECONDS', '30'))
            ),
            database=DatabaseConfig(
                type=os.getenv('DATABASE_TYPE', 'sqlite'),
                path=os.getenv('DATABASE_PATH', 'image_metadata.db'),
                backup_enabled=os.getenv('DATABASE_BACKUP_ENABLED', 'true').lower() == 'true',
                backup_interval_hours=int(os.getenv('DATABASE_BACKUP_INTERVAL_HOURS', '24'))
            ),
            processing=ProcessingConfig(
                max_file_size_mb=int(os.getenv('PROCESSING_MAX_FILE_SIZE_MB', '50')),
                concurrent_workers=int(os.getenv('PROCESSING_CONCURRENT_WORKERS', '4'))
            ),
            logging=LoggingConfig(
                level=os.getenv('LOGGING_LEVEL', 'INFO'),
                file_path=os.getenv('LOGGING_FILE_PATH', 'processing.log'),
                max_file_size_mb=int(os.getenv('LOGGING_MAX_FILE_SIZE_MB', '10')),
                backup_count=int(os.getenv('LOGGING_BACKUP_COUNT', '5'))
            )
        )

    def validate(self) -> None:
        """Validate configuration values."""
        # Validate Google Drive credentials
        if not Path(self.google_drive.credentials_path).exists():
            raise ConfigurationError(
                f"Google Drive credentials file not found: {self.google_drive.credentials_path}"
            )
        
        # Validate vision model configuration
        if self.vision_model.temperature < 0 or self.vision_model.temperature > 1:
            raise ConfigurationError("Vision model temperature must be between 0 and 1")
        
        if self.vision_model.max_tokens <= 0:
            raise ConfigurationError("Vision model max_tokens must be positive")
        
        # Validate processing configuration
        if self.processing.max_file_size_mb <= 0:
            raise ConfigurationError("Processing max_file_size_mb must be positive")
        
        if self.processing.concurrent_workers <= 0:
            raise ConfigurationError("Processing concurrent_workers must be positive")
        
        # Validate thumbnail size
        if len(self.processing.thumbnail_size) != 2:
            raise ConfigurationError("Processing thumbnail_size must be [width, height]")
        
        if any(size <= 0 for size in self.processing.thumbnail_size):
            raise ConfigurationError("Processing thumbnail_size values must be positive")