"""Logging configuration and utilities."""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional, Union

from ..core.config import LoggingConfig


def setup_logging(config: Union[LoggingConfig, int], correlation_id: Optional[str] = None) -> logging.Logger:
    """Set up structured logging with correlation IDs."""
    
    # Create logger
    logger = logging.getLogger("image_processor")
    
    # Handle both LoggingConfig and log level int
    if isinstance(config, int):
        logger.setLevel(config)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Simple console handler for int input
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    # Original LoggingConfig handling
    logger.setLevel(getattr(logging, config.level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    if config.file_path:
        log_file = Path(config.file_path)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=config.max_file_size_mb * 1024 * 1024,
            backupCount=config.backup_count
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


class CorrelationFilter(logging.Filter):
    """Add correlation ID to log records."""
    
    def __init__(self, correlation_id: str):
        super().__init__()
        self.correlation_id = correlation_id
    
    def filter(self, record):
        record.correlation_id = self.correlation_id
        return True


def get_logger(name: str = "image_processor") -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)