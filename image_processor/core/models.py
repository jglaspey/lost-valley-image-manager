"""Data models for the Google Drive Image Processor."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional


class ProcessingStatus(Enum):
    """Processing status for media files."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class MediaFile:
    """Represents a media file from Google Drive."""
    drive_file_id: str
    filename: str
    file_path: str
    file_size: int
    mime_type: str
    created_date: datetime
    modified_date: datetime
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    processed_at: Optional[datetime] = None
    thumbnail_path: Optional[str] = None
    id: Optional[int] = None  # Database ID


@dataclass
class ExtractedMetadata:
    """AI-extracted metadata for permaculture community images."""
    primary_subject: str
    visual_quality: int  # 1-5 scale
    has_people: bool
    people_count: str  # 'none', '1-2', '3-5', '6-10', '10+'
    social_media_score: int  # 1-5 scale
    social_media_reason: str
    marketing_score: int  # 1-5 scale
    marketing_use: str
    activity_tags: List[str]  # From predefined permaculture categories
    season: Optional[str] = None  # 'spring', 'summer', 'fall', 'winter', 'unclear'
    time_of_day: Optional[str] = None  # 'morning', 'midday', 'evening', 'unclear'
    mood_energy: Optional[str] = None
    color_palette: Optional[str] = None
    extracted_at: Optional[datetime] = None
    file_id: Optional[int] = None  # Foreign key to files table


# Predefined activity tags for permaculture community
ACTIVITY_TAGS = [
    'gardening', 'harvesting', 'education', 'construction',
    'maintenance', 'cooking', 'celebration', 'children',
    'animals', 'landscape', 'tools', 'produce'
]

# Valid people count options
PEOPLE_COUNT_OPTIONS = ['none', '1-2', '3-5', '6-10', '10+']

# Valid season options
SEASON_OPTIONS = ['spring', 'summer', 'fall', 'winter', 'unclear']

# Valid time of day options
TIME_OF_DAY_OPTIONS = ['morning', 'midday', 'evening', 'unclear']