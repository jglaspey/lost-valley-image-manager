"""Tests for repository classes."""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile

from image_processor.core.config import DatabaseConfig
from image_processor.core.models import (
    MediaFile, ExtractedMetadata, ProcessingStatus,
    ACTIVITY_TAGS
)
from image_processor.database.connection import DatabaseConnection
from image_processor.database.repositories import (
    FileRepository, MetadataRepository, ActivityTagRepository,
    ProcessingHistoryRepository
)
from image_processor.core.exceptions import DatabaseError


class TestFileRepository:
    """Test FileRepository class."""
    
    @pytest.fixture
    def db_connection(self):
        """Create test database connection."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        
        config = DatabaseConfig(path=str(db_path))
        conn = DatabaseConnection(config)
        yield conn
        
        # Cleanup
        conn.close()
        if db_path.exists():
            db_path.unlink()
    
    @pytest.fixture
    def file_repo(self, db_connection):
        """Create FileRepository instance."""
        return FileRepository(db_connection)
    
    @pytest.fixture
    def sample_media_file(self):
        """Create sample MediaFile."""
        return MediaFile(
            drive_file_id="test_drive_id_123",
            filename="test_image.jpg",
            file_path="/test/path/test_image.jpg",
            file_size=1024000,
            mime_type="image/jpeg",
            created_date=datetime.now(),
            modified_date=datetime.now()
        )
    
    def test_create_file(self, file_repo, sample_media_file):
        """Test creating a file record."""
        file_id = file_repo.create(sample_media_file)
        assert file_id > 0
        
        # Verify file was created
        retrieved = file_repo.get_by_id(file_id)
        assert retrieved is not None
        assert retrieved.drive_file_id == sample_media_file.drive_file_id
        assert retrieved.filename == sample_media_file.filename
    
    def test_get_by_drive_id(self, file_repo, sample_media_file):
        """Test getting file by Google Drive ID."""
        file_id = file_repo.create(sample_media_file)
        
        retrieved = file_repo.get_by_drive_id(sample_media_file.drive_file_id)
        assert retrieved is not None
        assert retrieved.id == file_id
    
    def test_get_pending_files(self, file_repo):
        """Test getting pending files."""
        # Create files with different statuses
        for i in range(5):
            media_file = MediaFile(
                drive_file_id=f"pending_{i}",
                filename=f"pending_{i}.jpg",
                file_path=f"/test/pending_{i}.jpg",
                file_size=1024,
                mime_type="image/jpeg",
                created_date=datetime.now(),
                modified_date=datetime.now(),
                processing_status=ProcessingStatus.PENDING
            )
            file_repo.create(media_file)
        
        # Create a completed file
        completed_file = MediaFile(
            drive_file_id="completed_1",
            filename="completed.jpg",
            file_path="/test/completed.jpg",
            file_size=1024,
            mime_type="image/jpeg",
            created_date=datetime.now(),
            modified_date=datetime.now(),
            processing_status=ProcessingStatus.COMPLETED
        )
        file_repo.create(completed_file)
        
        # Get pending files
        pending = file_repo.get_pending_files()
        assert len(pending) == 5
        assert all(f.processing_status == ProcessingStatus.PENDING for f in pending)
        
        # Test with limit
        limited = file_repo.get_pending_files(limit=3)
        assert len(limited) == 3
    
    def test_update_status(self, file_repo, sample_media_file):
        """Test updating file status."""
        file_id = file_repo.create(sample_media_file)
        
        # Update to in_progress
        file_repo.update_status(file_id, ProcessingStatus.IN_PROGRESS)
        file = file_repo.get_by_id(file_id)
        assert file.processing_status == ProcessingStatus.IN_PROGRESS
        assert file.processed_at is None
        
        # Update to completed
        file_repo.update_status(file_id, ProcessingStatus.COMPLETED)
        file = file_repo.get_by_id(file_id)
        assert file.processing_status == ProcessingStatus.COMPLETED
        assert file.processed_at is not None
        
        # Update to failed with error
        file_repo.update_status(file_id, ProcessingStatus.FAILED, "Test error")
        file = file_repo.get_by_id(file_id)
        assert file.processing_status == ProcessingStatus.FAILED
    
    def test_exists(self, file_repo, sample_media_file):
        """Test checking if file exists."""
        assert not file_repo.exists(sample_media_file.drive_file_id)
        
        file_repo.create(sample_media_file)
        assert file_repo.exists(sample_media_file.drive_file_id)
    
    def test_get_processing_stats(self, file_repo):
        """Test getting processing statistics."""
        # Create files with different statuses
        statuses = [
            ProcessingStatus.PENDING,
            ProcessingStatus.PENDING,
            ProcessingStatus.IN_PROGRESS,
            ProcessingStatus.COMPLETED,
            ProcessingStatus.COMPLETED,
            ProcessingStatus.COMPLETED,
            ProcessingStatus.FAILED
        ]
        
        for i, status in enumerate(statuses):
            media_file = MediaFile(
                drive_file_id=f"stat_{i}",
                filename=f"stat_{i}.jpg",
                file_path=f"/test/stat_{i}.jpg",
                file_size=1024,
                mime_type="image/jpeg",
                created_date=datetime.now(),
                modified_date=datetime.now(),
                processing_status=status
            )
            file_repo.create(media_file)
        
        stats = file_repo.get_processing_stats()
        assert stats['pending'] == 2
        assert stats['in_progress'] == 1
        assert stats['completed'] == 3
        assert stats['failed'] == 1


class TestMetadataRepository:
    """Test MetadataRepository class."""
    
    @pytest.fixture
    def db_connection(self):
        """Create test database connection."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        
        config = DatabaseConfig(path=str(db_path))
        conn = DatabaseConnection(config)
        yield conn
        
        # Cleanup
        conn.close()
        if db_path.exists():
            db_path.unlink()
    
    @pytest.fixture
    def metadata_repo(self, db_connection):
        """Create MetadataRepository instance."""
        return MetadataRepository(db_connection)
    
    @pytest.fixture
    def file_repo(self, db_connection):
        """Create FileRepository instance."""
        return FileRepository(db_connection)
    
    @pytest.fixture
    def tag_repo(self, db_connection):
        """Create ActivityTagRepository instance."""
        return ActivityTagRepository(db_connection)
    
    @pytest.fixture
    def sample_metadata(self):
        """Create sample ExtractedMetadata."""
        return ExtractedMetadata(
            primary_subject="Group of people planting seedlings",
            visual_quality=4,
            has_people=True,
            people_count="3-5",
            is_indoor=False,
            social_media_score=5,
            social_media_reason="Great community engagement shot",
            marketing_score=4,
            marketing_use="Newsletter feature image",
            activity_tags=["gardening", "education"],
            season="spring",
            time_of_day="morning",
            mood_energy="energetic",
            color_palette="green, brown, blue"
        )
    
    def test_create_metadata(self, metadata_repo, file_repo, tag_repo, sample_metadata):
        """Test creating metadata record."""
        # Create file first
        media_file = MediaFile(
            drive_file_id="meta_test",
            filename="test.jpg",
            file_path="/test/test.jpg",
            file_size=1024,
            mime_type="image/jpeg",
            created_date=datetime.now(),
            modified_date=datetime.now()
        )
        file_id = file_repo.create(media_file)
        
        # Set file_id and create metadata
        sample_metadata.file_id = file_id
        metadata_id = metadata_repo.create(sample_metadata)
        assert metadata_id > 0
        
        # Add activity tags
        tag_repo.add_tags(file_id, sample_metadata.activity_tags)
        
        # Retrieve and verify
        retrieved = metadata_repo.get_by_file_id(file_id)
        assert retrieved is not None
        assert retrieved.primary_subject == sample_metadata.primary_subject
        assert retrieved.visual_quality == sample_metadata.visual_quality
        assert retrieved.has_people == sample_metadata.has_people
        assert set(retrieved.activity_tags) == set(sample_metadata.activity_tags)
    
    def test_validate_metadata(self, metadata_repo):
        """Test metadata validation."""
        invalid_metadata = ExtractedMetadata(
            file_id=1,
            primary_subject="Test",
            visual_quality=6,  # Invalid: should be 1-5
            has_people=False,
            people_count="none",
            is_indoor=True,
            social_media_score=3,
            social_media_reason="Average",
            marketing_score=3,
            marketing_use="General use",
            activity_tags=[]
        )
        
        with pytest.raises(DatabaseError):
            metadata_repo.create(invalid_metadata)
    
    def test_search_metadata(self, metadata_repo, file_repo, tag_repo):
        """Test searching metadata with filters."""
        # Create test data
        test_files = [
            {
                "file": MediaFile(
                    drive_file_id="search_1",
                    filename="garden_group.jpg",
                    file_path="/test/garden_group.jpg",
                    file_size=1024,
                    mime_type="image/jpeg",
                    created_date=datetime.now(),
                    modified_date=datetime.now(),
                    processing_status=ProcessingStatus.COMPLETED
                ),
                "metadata": ExtractedMetadata(
                    primary_subject="Group gardening session",
                    visual_quality=5,
                    has_people=True,
                    people_count="6-10",
                    is_indoor=False,
                    social_media_score=5,
                    social_media_reason="Perfect community shot",
                    marketing_score=5,
                    marketing_use="Hero image",
                    activity_tags=["gardening", "education"],
                    season="summer"
                )
            },
            {
                "file": MediaFile(
                    drive_file_id="search_2",
                    filename="cooking_indoor.jpg",
                    file_path="/test/cooking_indoor.jpg",
                    file_size=1024,
                    mime_type="image/jpeg",
                    created_date=datetime.now(),
                    modified_date=datetime.now(),
                    processing_status=ProcessingStatus.COMPLETED
                ),
                "metadata": ExtractedMetadata(
                    primary_subject="Kitchen cooking scene",
                    visual_quality=3,
                    has_people=True,
                    people_count="1-2",
                    is_indoor=True,
                    social_media_score=3,
                    social_media_reason="Average quality",
                    marketing_score=2,
                    marketing_use="Blog post",
                    activity_tags=["cooking"],
                    season="winter"
                )
            }
        ]
        
        # Insert test data
        for test_data in test_files:
            file_id = file_repo.create(test_data["file"])
            test_data["metadata"].file_id = file_id
            metadata_repo.create(test_data["metadata"])
            tag_repo.add_tags(file_id, test_data["metadata"].activity_tags)
            file_repo.update_status(file_id, ProcessingStatus.COMPLETED)
        
        # Test various searches
        
        # Search by activity tag
        results = metadata_repo.search({"activity_tags": "gardening"})
        assert len(results) == 1
        assert results[0]['filename'] == 'garden_group.jpg'
        
        # Search by visual quality
        results = metadata_repo.search({"min_visual_quality": 4})
        assert len(results) == 1
        
        # Search by indoor/outdoor
        results = metadata_repo.search({"is_indoor": False})
        assert len(results) == 1
        
        # Search by people count
        results = metadata_repo.search({"people_count": "6-10"})
        assert len(results) == 1
        
        # Combined search
        results = metadata_repo.search({
            "has_people": True,
            "min_social_media_score": 3,
            "activity_tags": ["gardening", "cooking"]
        })
        assert len(results) == 2


class TestActivityTagRepository:
    """Test ActivityTagRepository class."""
    
    @pytest.fixture
    def db_connection(self):
        """Create test database connection."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        
        config = DatabaseConfig(path=str(db_path))
        conn = DatabaseConnection(config)
        yield conn
        
        # Cleanup
        conn.close()
        if db_path.exists():
            db_path.unlink()
    
    @pytest.fixture
    def tag_repo(self, db_connection):
        """Create ActivityTagRepository instance."""
        return ActivityTagRepository(db_connection)
    
    @pytest.fixture
    def file_repo(self, db_connection):
        """Create FileRepository instance."""
        return FileRepository(db_connection)
    
    def test_add_tags(self, tag_repo, file_repo):
        """Test adding activity tags."""
        # Create file
        media_file = MediaFile(
            drive_file_id="tag_test",
            filename="test.jpg",
            file_path="/test/test.jpg",
            file_size=1024,
            mime_type="image/jpeg",
            created_date=datetime.now(),
            modified_date=datetime.now()
        )
        file_id = file_repo.create(media_file)
        
        # Add tags
        tags = ["gardening", "education", "children"]
        tag_repo.add_tags(file_id, tags)
        
        # Verify tags
        retrieved_tags = tag_repo.get_tags(file_id)
        assert set(retrieved_tags) == set(tags)
    
    def test_invalid_tag(self, tag_repo):
        """Test adding invalid tag."""
        with pytest.raises(DatabaseError):
            tag_repo.add_tags(1, ["invalid_tag"])
    
    def test_remove_tags(self, tag_repo, file_repo):
        """Test removing tags."""
        # Create file and add tags
        media_file = MediaFile(
            drive_file_id="remove_test",
            filename="test.jpg",
            file_path="/test/test.jpg",
            file_size=1024,
            mime_type="image/jpeg",
            created_date=datetime.now(),
            modified_date=datetime.now()
        )
        file_id = file_repo.create(media_file)
        
        tags = ["gardening", "education", "children"]
        tag_repo.add_tags(file_id, tags)
        
        # Remove specific tags
        tag_repo.remove_tags(file_id, ["education"])
        remaining = tag_repo.get_tags(file_id)
        assert "education" not in remaining
        assert "gardening" in remaining
        
        # Remove all tags
        tag_repo.remove_tags(file_id)
        assert len(tag_repo.get_tags(file_id)) == 0
    
    def test_get_tag_counts(self, tag_repo, file_repo):
        """Test getting tag counts."""
        # Create files with tags
        for i in range(3):
            media_file = MediaFile(
                drive_file_id=f"count_test_{i}",
                filename=f"test_{i}.jpg",
                file_path=f"/test/test_{i}.jpg",
                file_size=1024,
                mime_type="image/jpeg",
                created_date=datetime.now(),
                modified_date=datetime.now()
            )
            file_id = file_repo.create(media_file)
            
            if i < 2:
                tag_repo.add_tags(file_id, ["gardening"])
            if i < 1:
                tag_repo.add_tags(file_id, ["education"])
        
        counts = tag_repo.get_tag_counts()
        assert counts["gardening"] == 2
        assert counts["education"] == 1