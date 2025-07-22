"""Tests for database connection management."""

import pytest
import sqlite3
import tempfile
from pathlib import Path
import threading

from image_processor.core.config import DatabaseConfig
from image_processor.database.connection import DatabaseConnection
from image_processor.core.exceptions import DatabaseError


class TestDatabaseConnection:
    """Test database connection management."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database path."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            path = Path(f.name)
        yield path
        # Cleanup
        if path.exists():
            path.unlink()
    
    @pytest.fixture
    def db_config(self, temp_db_path):
        """Create a test database configuration."""
        return DatabaseConfig(
            type="sqlite",
            path=str(temp_db_path),
            backup_enabled=True,
            backup_interval_hours=24
        )
    
    @pytest.fixture
    def db_connection(self, db_config):
        """Create a test database connection."""
        return DatabaseConnection(db_config)
    
    def test_initialization(self, db_connection, temp_db_path):
        """Test database initialization."""
        assert temp_db_path.exists()
        
        # Check schema was created
        with db_connection.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check tables exist
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = [
                'activity_tags', 'files', 'metadata', 
                'processing_history', 'schema_version'
            ]
            for table in expected_tables:
                assert table in tables
    
    def test_connection_thread_safety(self, db_connection):
        """Test that connections are thread-local."""
        connections = []
        
        def get_connection():
            with db_connection.get_connection() as conn:
                connections.append(id(conn))
        
        # Get connections from different threads
        threads = []
        for _ in range(3):
            t = threading.Thread(target=get_connection)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # All connection IDs should be different
        assert len(set(connections)) == len(connections)
    
    def test_transaction_commit(self, db_connection):
        """Test transaction commit."""
        with db_connection.transaction() as conn:
            conn.execute(
                "INSERT INTO files (drive_file_id, filename, file_path) VALUES (?, ?, ?)",
                ('test_id', 'test.jpg', '/test/path')
            )
        
        # Check data was committed
        result = db_connection.fetchone(
            "SELECT filename FROM files WHERE drive_file_id = ?",
            ('test_id',)
        )
        assert result['filename'] == 'test.jpg'
    
    def test_transaction_rollback(self, db_connection):
        """Test transaction rollback on error."""
        try:
            with db_connection.transaction() as conn:
                conn.execute(
                    "INSERT INTO files (drive_file_id, filename, file_path) VALUES (?, ?, ?)",
                    ('test_id2', 'test2.jpg', '/test/path2')
                )
                # Force an error
                raise ValueError("Test error")
        except ValueError:
            pass
        
        # Check data was not committed
        result = db_connection.fetchone(
            "SELECT filename FROM files WHERE drive_file_id = ?",
            ('test_id2',)
        )
        assert result is None
    
    def test_execute_methods(self, db_connection):
        """Test execute helper methods."""
        # Test execute
        db_connection.execute(
            "INSERT INTO files (drive_file_id, filename, file_path) VALUES (?, ?, ?)",
            ('test_id3', 'test3.jpg', '/test/path3')
        )
        
        # Test fetchone
        result = db_connection.fetchone(
            "SELECT filename FROM files WHERE drive_file_id = ?",
            ('test_id3',)
        )
        assert result['filename'] == 'test3.jpg'
        
        # Test executemany
        files_data = [
            ('test_id4', 'test4.jpg', '/test/path4'),
            ('test_id5', 'test5.jpg', '/test/path5')
        ]
        db_connection.executemany(
            "INSERT INTO files (drive_file_id, filename, file_path) VALUES (?, ?, ?)",
            files_data
        )
        
        # Test fetchall
        results = db_connection.fetchall(
            "SELECT filename FROM files WHERE drive_file_id IN (?, ?)",
            ('test_id4', 'test_id5')
        )
        filenames = [r['filename'] for r in results]
        assert 'test4.jpg' in filenames
        assert 'test5.jpg' in filenames
    
    def test_foreign_keys_enabled(self, db_connection):
        """Test that foreign keys are enabled."""
        result = db_connection.fetchone("PRAGMA foreign_keys")
        assert result[0] == 1
    
    def test_wal_mode_enabled(self, db_connection):
        """Test that WAL mode is enabled."""
        result = db_connection.fetchone("PRAGMA journal_mode")
        assert result[0] == 'wal'
    
    def test_backup(self, db_connection, temp_db_path):
        """Test database backup functionality."""
        # Insert test data
        db_connection.execute(
            "INSERT INTO files (drive_file_id, filename, file_path) VALUES (?, ?, ?)",
            ('backup_test', 'backup.jpg', '/backup/path')
        )
        
        # Create backup
        backup_path = temp_db_path.with_suffix('.backup.db')
        db_connection.backup(backup_path)
        
        assert backup_path.exists()
        
        # Verify backup contains data
        backup_conn = sqlite3.connect(str(backup_path))
        cursor = backup_conn.cursor()
        cursor.execute(
            "SELECT filename FROM files WHERE drive_file_id = ?",
            ('backup_test',)
        )
        result = cursor.fetchone()
        assert result[0] == 'backup.jpg'
        
        backup_conn.close()
        backup_path.unlink()  # Cleanup