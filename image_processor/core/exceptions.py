"""Custom exceptions for the Google Drive Image Processor."""


class ImageProcessorError(Exception):
    """Base exception for all image processor errors."""
    pass


class ConfigurationError(ImageProcessorError):
    """Raised when there's a configuration issue."""
    pass


class GoogleDriveError(ImageProcessorError):
    """Raised when there's an issue with Google Drive API."""
    pass


class VisionModelError(ImageProcessorError):
    """Raised when there's an issue with the vision model."""
    pass


class DatabaseError(ImageProcessorError):
    """Raised when there's a database operation error."""
    pass


class ProcessingError(ImageProcessorError):
    """Raised when there's an error during file processing."""
    pass


class ThumbnailError(ImageProcessorError):
    """Raised when there's an error generating thumbnails."""
    pass