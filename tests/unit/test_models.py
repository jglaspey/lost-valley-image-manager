"""Unit tests for core data models."""

import pytest
from datetime import datetime
from image_processor.core.models import (
    MediaFile, ExtractedMetadata, ProcessingStatus,
    ACTIVITY_TAGS, PEOPLE_COUNT_OPTIONS, SEASON_OPTIONS, TIME_OF_DAY_OPTIONS
)


class TestProcessingStatus:
    """Test ProcessingStatus enum."""
    
    def test_status_values(self):
        """Test that all expected status values exist."""
        assert ProcessingStatus.PENDING.value == "pending"
        assert ProcessingStatus.IN_PROGRESS.value == "in_progress"
        assert ProcessingStatus.COMPLETED.value == "completed"
        assert ProcessingStatus.FAILED.value == "failed"


class TestMediaFile:
    """Test MediaFile data model."""
    
    def test_media_file_creation(self):
        """Test creating a MediaFile instance."""
        now = datetime.now()
        media_file = MediaFile(
            drive_file_id="test_id_123",
            filename="test_image.jpg",
            file_path="/folder/test_image.jpg",
            file_size=1024000,
            mime_type="image/jpeg",
            created_date=now,
            modified_date=now
        )
        
        assert media_file.drive_file_id == "test_id_123"
        assert media_file.filename == "test_image.jpg"
        assert media_file.file_path == "/folder/test_image.jpg"
        assert media_file.file_size == 1024000
        assert media_file.mime_type == "image/jpeg"
        assert media_file.processing_status == ProcessingStatus.PENDING
        assert media_file.processed_at is None
        assert media_file.thumbnail_path is None
        assert media_file.id is None
    
    def test_media_file_with_optional_fields(self):
        """Test MediaFile with optional fields set."""
        now = datetime.now()
        media_file = MediaFile(
            drive_file_id="test_id_123",
            filename="test_image.jpg",
            file_path="/folder/test_image.jpg",
            file_size=1024000,
            mime_type="image/jpeg",
            created_date=now,
            modified_date=now,
            processing_status=ProcessingStatus.COMPLETED,
            processed_at=now,
            thumbnail_path="/thumbnails/test_image_thumb.jpg",
            id=1
        )
        
        assert media_file.processing_status == ProcessingStatus.COMPLETED
        assert media_file.processed_at == now
        assert media_file.thumbnail_path == "/thumbnails/test_image_thumb.jpg"
        assert media_file.id == 1


class TestExtractedMetadata:
    """Test ExtractedMetadata data model."""
    
    def test_extracted_metadata_creation(self):
        """Test creating an ExtractedMetadata instance."""
        now = datetime.now()
        metadata = ExtractedMetadata(
            primary_subject="Group of people planting seedlings in raised garden beds",
            visual_quality=4,
            has_people=True,
            people_count="3-5",
            social_media_score=4,
            social_media_reason="Engaging community activity with good composition",
            marketing_score=5,
            marketing_use="website banner",
            activity_tags=["gardening", "education", "children"]
        )
        
        assert metadata.primary_subject == "Group of people planting seedlings in raised garden beds"
        assert metadata.visual_quality == 4
        assert metadata.has_people is True
        assert metadata.people_count == "3-5"
        assert metadata.social_media_score == 4
        assert metadata.social_media_reason == "Engaging community activity with good composition"
        assert metadata.marketing_score == 5
        assert metadata.marketing_use == "website banner"
        assert metadata.activity_tags == ["gardening", "education", "children"]
        assert metadata.season is None
        assert metadata.time_of_day is None
        assert metadata.mood_energy is None
        assert metadata.color_palette is None
        assert metadata.extracted_at is None
        assert metadata.file_id is None
    
    def test_extracted_metadata_with_optional_fields(self):
        """Test ExtractedMetadata with optional fields set."""
        now = datetime.now()
        metadata = ExtractedMetadata(
            primary_subject="Close-up of ripe tomatoes on the vine",
            visual_quality=5,
            has_people=False,
            people_count="none",
            social_media_score=3,
            social_media_reason="Nice produce shot but common subject",
            marketing_score=4,
            marketing_use="newsletter",
            activity_tags=["produce", "gardening"],
            season="summer",
            time_of_day="midday",
            mood_energy="peaceful",
            color_palette="red, green, brown",
            extracted_at=now,
            file_id=1
        )
        
        assert metadata.season == "summer"
        assert metadata.time_of_day == "midday"
        assert metadata.mood_energy == "peaceful"
        assert metadata.color_palette == "red, green, brown"
        assert metadata.extracted_at == now
        assert metadata.file_id == 1


class TestConstants:
    """Test predefined constants."""
    
    def test_activity_tags(self):
        """Test that all expected activity tags are present."""
        expected_tags = [
            'gardening', 'harvesting', 'education', 'construction',
            'maintenance', 'cooking', 'celebration', 'children',
            'animals', 'landscape', 'tools', 'produce'
        ]
        assert ACTIVITY_TAGS == expected_tags
        assert len(ACTIVITY_TAGS) == 12
    
    def test_people_count_options(self):
        """Test people count options."""
        expected_options = ['none', '1-2', '3-5', '6-10', '10+']
        assert PEOPLE_COUNT_OPTIONS == expected_options
    
    def test_season_options(self):
        """Test season options."""
        expected_seasons = ['spring', 'summer', 'fall', 'winter', 'unclear']
        assert SEASON_OPTIONS == expected_seasons
    
    def test_time_of_day_options(self):
        """Test time of day options."""
        expected_times = ['morning', 'midday', 'evening', 'unclear']
        assert TIME_OF_DAY_OPTIONS == expected_times