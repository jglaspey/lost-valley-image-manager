"""Unit tests for configuration management."""

import os
import tempfile
import pytest
from pathlib import Path

from image_processor.core.config import (
    Config, GoogleDriveConfig, VisionModelConfig, DatabaseConfig,
    ProcessingConfig, LoggingConfig
)
from image_processor.core.exceptions import ConfigurationError


class TestConfigClasses:
    """Test configuration dataclasses."""
    
    def test_google_drive_config_defaults(self):
        """Test GoogleDriveConfig with defaults."""
        config = GoogleDriveConfig(credentials_path="test.json")
        assert config.credentials_path == "test.json"
        assert config.root_folder_id is None
        assert config.batch_size == 100
        assert config.rate_limit_delay == 1.0
    
    def test_vision_model_config_defaults(self):
        """Test VisionModelConfig with defaults."""
        config = VisionModelConfig()
        assert config.model_type == "gemma-3-4b-it-qat"
        assert config.api_endpoint == "http://127.0.0.1:1234"
        assert config.temperature == 0.4
        assert config.max_tokens == 500
        assert config.max_retries == 3
        assert config.timeout_seconds == 30
        assert "JSON response" in config.prompt_template
    
    def test_processing_config_defaults(self):
        """Test ProcessingConfig with defaults."""
        config = ProcessingConfig()
        assert config.thumbnail_size == [200, 200]
        assert "jpg" in config.supported_formats
        assert "png" in config.supported_formats
        assert config.max_file_size_mb == 50
        assert config.concurrent_workers == 4


class TestConfigFromFile:
    """Test loading configuration from YAML files."""
    
    def test_config_from_valid_file(self):
        """Test loading configuration from a valid YAML file."""
        config_content = """
google_drive:
  credentials_path: "test_credentials.json"
  batch_size: 50
  rate_limit_delay: 2.0

vision_model:
  temperature: 0.3
  max_tokens: 400

database:
  path: "test.db"

processing:
  max_file_size_mb: 25
  concurrent_workers: 2

logging:
  level: "DEBUG"
  file_path: "test.log"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            temp_path = f.name
        
        try:
            # Create a dummy credentials file for validation
            with open("test_credentials.json", "w") as cred_file:
                cred_file.write('{"test": "credentials"}')
            
            config = Config.from_file(temp_path)
            
            assert config.google_drive.credentials_path == "test_credentials.json"
            assert config.google_drive.batch_size == 50
            assert config.google_drive.rate_limit_delay == 2.0
            assert config.vision_model.temperature == 0.3
            assert config.vision_model.max_tokens == 400
            assert config.database.path == "test.db"
            assert config.processing.max_file_size_mb == 25
            assert config.processing.concurrent_workers == 2
            assert config.logging.level == "DEBUG"
            assert config.logging.file_path == "test.log"
            
        finally:
            os.unlink(temp_path)
            if os.path.exists("test_credentials.json"):
                os.unlink("test_credentials.json")
    
    def test_config_from_nonexistent_file(self):
        """Test loading configuration from nonexistent file."""
        with pytest.raises(ConfigurationError, match="Configuration file not found"):
            Config.from_file("nonexistent.yaml")
    
    def test_config_from_invalid_yaml(self):
        """Test loading configuration from invalid YAML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = f.name
        
        try:
            with pytest.raises(ConfigurationError, match="Invalid YAML"):
                Config.from_file(temp_path)
        finally:
            os.unlink(temp_path)


class TestConfigFromEnv:
    """Test loading configuration from environment variables."""
    
    def test_config_from_env_defaults(self):
        """Test loading configuration from environment with defaults."""
        # Create a dummy credentials file
        with open("credentials.json", "w") as f:
            f.write('{"test": "credentials"}')
        
        try:
            config = Config.from_env()
            
            assert config.google_drive.credentials_path == "credentials.json"
            assert config.google_drive.batch_size == 100
            assert config.vision_model.api_endpoint == "http://127.0.0.1:1234"
            assert config.vision_model.temperature == 0.4
            assert config.database.path == "image_metadata.db"
            assert config.processing.max_file_size_mb == 50
            assert config.logging.level == "INFO"
            
        finally:
            if os.path.exists("credentials.json"):
                os.unlink("credentials.json")
    
    def test_config_from_env_with_overrides(self):
        """Test loading configuration from environment with overrides."""
        # Set environment variables
        env_vars = {
            'GDRIVE_BATCH_SIZE': '200',
            'VISION_TEMPERATURE': '0.2',
            'DATABASE_PATH': 'custom.db',
            'LOG_LEVEL': 'DEBUG'
        }
        
        # Create a dummy credentials file
        with open("credentials.json", "w") as f:
            f.write('{"test": "credentials"}')
        
        try:
            for key, value in env_vars.items():
                os.environ[key] = value
            
            config = Config.from_env()
            
            assert config.google_drive.batch_size == 200
            assert config.vision_model.temperature == 0.2
            assert config.database.path == "custom.db"
            assert config.logging.level == "DEBUG"
            
        finally:
            # Clean up environment variables
            for key in env_vars:
                if key in os.environ:
                    del os.environ[key]
            if os.path.exists("credentials.json"):
                os.unlink("credentials.json")


class TestConfigValidation:
    """Test configuration validation."""
    
    def test_validate_missing_credentials(self):
        """Test validation with missing credentials file."""
        config = Config.from_env()
        config.google_drive.credentials_path = "nonexistent.json"
        
        with pytest.raises(ConfigurationError, match="credentials file not found"):
            config.validate()
    
    def test_validate_invalid_temperature(self):
        """Test validation with invalid temperature."""
        # Create a dummy credentials file
        with open("credentials.json", "w") as f:
            f.write('{"test": "credentials"}')
        
        try:
            config = Config.from_env()
            config.vision_model.temperature = 1.5
            
            with pytest.raises(ConfigurationError, match="temperature must be between 0 and 1"):
                config.validate()
                
        finally:
            if os.path.exists("credentials.json"):
                os.unlink("credentials.json")
    
    def test_validate_invalid_max_tokens(self):
        """Test validation with invalid max_tokens."""
        # Create a dummy credentials file
        with open("credentials.json", "w") as f:
            f.write('{"test": "credentials"}')
        
        try:
            config = Config.from_env()
            config.vision_model.max_tokens = -1
            
            with pytest.raises(ConfigurationError, match="max_tokens must be positive"):
                config.validate()
                
        finally:
            if os.path.exists("credentials.json"):
                os.unlink("credentials.json")
    
    def test_validate_invalid_thumbnail_size(self):
        """Test validation with invalid thumbnail size."""
        # Create a dummy credentials file
        with open("credentials.json", "w") as f:
            f.write('{"test": "credentials"}')
        
        try:
            config = Config.from_env()
            config.processing.thumbnail_size = [200]  # Should be [width, height]
            
            with pytest.raises(ConfigurationError, match="thumbnail_size must be"):
                config.validate()
                
        finally:
            if os.path.exists("credentials.json"):
                os.unlink("credentials.json")