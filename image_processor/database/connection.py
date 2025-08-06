"""Database connection management."""

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Optional
import logging
from datetime import datetime

from ..core.config import DatabaseConfig
from ..core.exceptions import DatabaseError
from .schema import create_schema, get_schema_version, migrate_schema, SCHEMA_VERSION

logger = logging.getLogger(__name__)


def adapt_datetime(ts):
    """Adapter for datetime to ISO format string."""
    return ts.isoformat()


def convert_datetime(ts):
    """Converter from ISO format string to datetime."""
    return datetime.fromisoformat(ts.decode())


# Register the adapter and converter
sqlite3.register_adapter(datetime, adapt_datetime)
sqlite3.register_converter("TIMESTAMP", convert_datetime)


class DatabaseConnection:
    """Manages SQLite database connections with thread safety."""
    
    def __init__(self, config: DatabaseConfig):
        """Initialize database connection manager."""
        self.config = config
        self.db_path = Path(config.path)
        self._local = threading.local()
        self._lock = threading.Lock()
        
        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database schema
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database with schema."""
        with self.get_connection() as conn:
            current_version = get_schema_version(conn)
            
            if current_version < SCHEMA_VERSION:
                logger.info(
                    f"Initializing database schema (current: {current_version}, target: {SCHEMA_VERSION})"
                )
                create_schema(conn)
                migrate_schema(conn)
                logger.info("Database schema initialized successfully")
            else:
                logger.info(f"Database schema is up to date (version {current_version})")
    
    def _get_thread_connection(self) -> sqlite3.Connection:
        """Get or create a connection for the current thread."""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = self._create_connection()
        return self._local.connection
    
    def _create_connection(self) -> sqlite3.Connection:
        """Create a new SQLite connection."""
        try:
            conn = sqlite3.connect(
                str(self.db_path),
                timeout=30.0,
                isolation_level=None,  # Autocommit mode
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Optimize for concurrent reads
            conn.execute("PRAGMA journal_mode = WAL")
            
            # Set row factory for dict-like access
            conn.row_factory = sqlite3.Row
            
            return conn
            
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to create database connection: {e}")
    
    @contextmanager
    def get_connection(self):
        """Get a database connection for the current thread."""
        conn = self._get_thread_connection()
        try:
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            raise DatabaseError(f"Database operation failed: {e}")
    
    @contextmanager
    def transaction(self):
        """Execute operations within a transaction."""
        conn = self._get_thread_connection()
        
        # Start transaction
        conn.execute("BEGIN")
        
        try:
            yield conn
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
    
    def close(self):
        """Close the connection for the current thread."""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
    
    def close_all(self):
        """Close all connections (call from main thread only)."""
        with self._lock:
            # Note: This only closes the current thread's connection
            # In a multi-threaded app, each thread should close its own connection
            self.close()
    
    def execute(self, sql: str, params: Optional[tuple] = None):
        """Execute a single SQL statement."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                return cursor.execute(sql, params)
            return cursor.execute(sql)
    
    def executemany(self, sql: str, params_list: list):
        """Execute a SQL statement multiple times with different parameters."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            return cursor.executemany(sql, params_list)
    
    def fetchone(self, sql: str, params: Optional[tuple] = None):
        """Execute a query and fetch one result."""
        cursor = self.execute(sql, params)
        return cursor.fetchone()
    
    def fetchall(self, sql: str, params: Optional[tuple] = None):
        """Execute a query and fetch all results."""
        cursor = self.execute(sql, params)
        return cursor.fetchall()
    
    def backup(self, backup_path: Optional[Path] = None):
        """Create a backup of the database."""
        if backup_path is None:
            backup_path = self.db_path.with_suffix('.backup.db')
        
        with self.get_connection() as conn:
            backup_conn = sqlite3.connect(str(backup_path))
            try:
                conn.backup(backup_conn)
                logger.info(f"Database backed up to {backup_path}")
            finally:
                backup_conn.close()