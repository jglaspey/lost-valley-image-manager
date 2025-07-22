"""Tests for database schema."""

import pytest
import sqlite3
import tempfile
from pathlib import Path

from image_processor.database.schema import create_schema, get_schema_version, SCHEMA_VERSION


class TestDatabaseSchema:
    """Test database schema creation and management."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        
        conn = sqlite3.connect(str(db_path))
        yield conn
        
        # Cleanup
        conn.close()
        if db_path.exists():
            db_path.unlink()
    
    def test_create_schema(self, temp_db):
        """Test schema creation."""
        create_schema(temp_db)
        
        # Check all tables were created
        cursor = temp_db.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = [
            'activity_tags', 
            'files', 
            'metadata', 
            'processing_history', 
            'schema_version'
        ]
        
        for table in expected_tables:
            assert table in tables
    
    def test_schema_version(self, temp_db):
        """Test schema version tracking."""
        # Before schema creation
        assert get_schema_version(temp_db) == 0
        
        # After schema creation
        create_schema(temp_db)
        assert get_schema_version(temp_db) == SCHEMA_VERSION
    
    def test_files_table_structure(self, temp_db):
        """Test files table structure."""
        create_schema(temp_db)
        
        cursor = temp_db.cursor()
        cursor.execute("PRAGMA table_info(files)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        expected_columns = {
            'id': 'INTEGER',
            'drive_file_id': 'TEXT',
            'filename': 'TEXT',
            'file_path': 'TEXT',
            'file_size': 'INTEGER',
            'mime_type': 'TEXT',
            'created_date': 'TIMESTAMP',
            'modified_date': 'TIMESTAMP',
            'processing_status': 'TEXT',
            'processed_at': 'TIMESTAMP',
            'thumbnail_path': 'TEXT',
            'error_message': 'TEXT',
            'created_at': 'TIMESTAMP',
            'updated_at': 'TIMESTAMP'
        }
        
        for col, type_ in expected_columns.items():
            assert col in columns
            assert columns[col] == type_
    
    def test_metadata_table_structure(self, temp_db):
        """Test metadata table structure."""
        create_schema(temp_db)
        
        cursor = temp_db.cursor()
        cursor.execute("PRAGMA table_info(metadata)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        assert 'primary_subject' in columns
        assert 'visual_quality' in columns
        assert 'has_people' in columns
        assert 'people_count' in columns
        assert 'is_indoor' in columns
        assert 'social_media_score' in columns
        assert 'marketing_score' in columns
    
    def test_activity_tags_constraints(self, temp_db):
        """Test activity tags constraints."""
        create_schema(temp_db)
        
        # Valid tag
        cursor = temp_db.execute(
            "INSERT INTO files (drive_file_id, filename, file_path) VALUES (?, ?, ?)",
            ('test_id', 'test.jpg', '/test/path')
        )
        file_id = cursor.lastrowid
        
        temp_db.execute(
            "INSERT INTO activity_tags (file_id, tag_name) VALUES (?, ?)",
            (file_id, 'gardening')
        )
        
        # Invalid tag should fail
        with pytest.raises(sqlite3.IntegrityError):
            temp_db.execute(
                "INSERT INTO activity_tags (file_id, tag_name) VALUES (?, ?)",
                (file_id, 'invalid_tag')
            )
    
    def test_unique_constraints(self, temp_db):
        """Test unique constraints."""
        create_schema(temp_db)
        
        # Insert a file
        temp_db.execute(
            "INSERT INTO files (drive_file_id, filename, file_path) VALUES (?, ?, ?)",
            ('unique_test', 'test.jpg', '/test/path')
        )
        
        # Duplicate drive_file_id should fail
        with pytest.raises(sqlite3.IntegrityError):
            temp_db.execute(
                "INSERT INTO files (drive_file_id, filename, file_path) VALUES (?, ?, ?)",
                ('unique_test', 'test2.jpg', '/test/path2')
            )
    
    def test_foreign_key_constraints(self, temp_db):
        """Test foreign key constraints."""
        create_schema(temp_db)
        temp_db.execute("PRAGMA foreign_keys = ON")
        
        # Try to insert metadata for non-existent file
        with pytest.raises(sqlite3.IntegrityError):
            temp_db.execute(
                "INSERT INTO metadata (file_id, primary_subject) VALUES (?, ?)",
                (999, 'Test subject')
            )
    
    def test_check_constraints(self, temp_db):
        """Test check constraints."""
        create_schema(temp_db)
        
        # Insert a file
        cursor = temp_db.execute(
            "INSERT INTO files (drive_file_id, filename, file_path) VALUES (?, ?, ?)",
            ('check_test', 'test.jpg', '/test/path')
        )
        file_id = cursor.lastrowid
        
        # Invalid visual_quality (should be 1-5)
        with pytest.raises(sqlite3.IntegrityError):
            temp_db.execute(
                "INSERT INTO metadata (file_id, primary_subject, visual_quality) VALUES (?, ?, ?)",
                (file_id, 'Test', 6)
            )
        
        # Invalid people_count
        with pytest.raises(sqlite3.IntegrityError):
            temp_db.execute(
                "INSERT INTO metadata (file_id, primary_subject, people_count) VALUES (?, ?, ?)",
                (file_id, 'Test', 'invalid')
            )
    
    def test_indexes_created(self, temp_db):
        """Test that indexes are created."""
        create_schema(temp_db)
        
        cursor = temp_db.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
        )
        indexes = [row[0] for row in cursor.fetchall()]
        
        expected_indexes = [
            'idx_files_status',
            'idx_files_drive_id',
            'idx_files_path',
            'idx_metadata_file_id',
            'idx_metadata_quality',
            'idx_metadata_social',
            'idx_metadata_marketing',
            'idx_metadata_people',
            'idx_tags_file_id',
            'idx_tags_name',
            'idx_history_file_id'
        ]
        
        for idx in expected_indexes:
            assert idx in indexes