"""Database schema definitions for Google Drive Image Processor."""

SCHEMA_VERSION = 2

SCHEMA_SQL = """
-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Files table: Core file information
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    drive_file_id TEXT UNIQUE NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    mime_type TEXT,
    created_date TIMESTAMP,
    modified_date TIMESTAMP,
    processing_status TEXT DEFAULT 'pending' CHECK (processing_status IN ('pending', 'in_progress', 'completed', 'failed')),
    processed_at TIMESTAMP,
    thumbnail_path TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Metadata table: AI-extracted metadata for permaculture community
CREATE TABLE IF NOT EXISTS metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    primary_subject TEXT NOT NULL,
    visual_quality INTEGER CHECK (visual_quality BETWEEN 1 AND 5),
    has_people BOOLEAN,
    people_count TEXT CHECK (people_count IN ('none', '1-2', '3-5', '6-10', '10+')),
    is_indoor BOOLEAN,
    social_media_score INTEGER CHECK (social_media_score BETWEEN 1 AND 5),
    social_media_reason TEXT,
    marketing_score INTEGER CHECK (marketing_score BETWEEN 1 AND 5),
    marketing_use TEXT,
    season TEXT CHECK (season IN ('spring', 'summer', 'fall', 'winter', 'unclear')),
    time_of_day TEXT CHECK (time_of_day IN ('morning', 'midday', 'evening', 'unclear')),
    mood_energy TEXT,
    color_palette TEXT,
    notes TEXT,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(file_id)
);

-- Activity tags table: Predefined permaculture activity categories
CREATE TABLE IF NOT EXISTS activity_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    tag_name TEXT NOT NULL CHECK (tag_name IN (
        'gardening', 'harvesting', 'education', 'construction', 
        'maintenance', 'cooking', 'celebration', 'children', 
        'animals', 'landscape', 'tools', 'produce'
    )),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(file_id, tag_name)
);

-- Processing history table: Track processing attempts
CREATE TABLE IF NOT EXISTS processing_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN ('started', 'completed', 'failed')),
    error_message TEXT,
    processing_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_files_status ON files(processing_status);
CREATE INDEX IF NOT EXISTS idx_files_drive_id ON files(drive_file_id);
CREATE INDEX IF NOT EXISTS idx_files_path ON files(file_path);
CREATE INDEX IF NOT EXISTS idx_metadata_file_id ON metadata(file_id);
CREATE INDEX IF NOT EXISTS idx_metadata_quality ON metadata(visual_quality);
CREATE INDEX IF NOT EXISTS idx_metadata_social ON metadata(social_media_score);
CREATE INDEX IF NOT EXISTS idx_metadata_marketing ON metadata(marketing_score);
CREATE INDEX IF NOT EXISTS idx_metadata_people ON metadata(has_people, people_count);
CREATE INDEX IF NOT EXISTS idx_tags_file_id ON activity_tags(file_id);
CREATE INDEX IF NOT EXISTS idx_tags_name ON activity_tags(tag_name);
CREATE INDEX IF NOT EXISTS idx_history_file_id ON processing_history(file_id);

-- Triggers to update the updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_files_timestamp 
AFTER UPDATE ON files
BEGIN
    UPDATE files SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
"""


def create_schema(connection):
    """Create the database schema."""
    cursor = connection.cursor()
    
    # Execute the schema SQL
    cursor.executescript(SCHEMA_SQL)
    
    # Insert schema version
    cursor.execute(
        "INSERT OR IGNORE INTO schema_version (version) VALUES (?)",
        (SCHEMA_VERSION,)
    )
    
    connection.commit()


def get_schema_version(connection):
    """Get the current schema version."""
    cursor = connection.cursor()
    
    # Check if schema_version table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
    )
    
    if not cursor.fetchone():
        return 0
    
    # Get the latest version
    cursor.execute("SELECT MAX(version) FROM schema_version")
    result = cursor.fetchone()
    
    return result[0] if result and result[0] else 0


def migrate_schema(connection):
    """Migrate schema to the latest version."""
    current_version = get_schema_version(connection)
    
    if current_version < SCHEMA_VERSION:
        print(f"Migrating schema from version {current_version} to {SCHEMA_VERSION}")
        
        # Migration from version 1 to 2: Add notes field
        if current_version < 2:
            cursor = connection.cursor()
            
            # Add notes column to metadata table
            cursor.execute("ALTER TABLE metadata ADD COLUMN notes TEXT")
            
            # Update schema version
            cursor.execute(
                "INSERT INTO schema_version (version) VALUES (?)",
                (2,)
            )
            
            connection.commit()
            print("Added notes field to metadata table")
        
        print(f"Schema migration complete to version {SCHEMA_VERSION}")
    else:
        print(f"Schema is up to date (version {current_version})")