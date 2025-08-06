"""Repository classes for database operations."""

from datetime import datetime
from typing import List, Optional, Dict, Any
import logging

from ..core.models import (
    MediaFile, ExtractedMetadata, ProcessingStatus,
    ACTIVITY_TAGS, PEOPLE_COUNT_OPTIONS, SEASON_OPTIONS, TIME_OF_DAY_OPTIONS
)
from ..core.exceptions import DatabaseError
from .connection import DatabaseConnection

logger = logging.getLogger(__name__)


class FileRepository:
    """Repository for file operations."""
    
    def __init__(self, db_connection: DatabaseConnection):
        """Initialize file repository."""
        self.db = db_connection
    
    def create(self, media_file: MediaFile) -> int:
        """Create a new file record."""
        sql = """
            INSERT INTO files (
                drive_file_id, filename, file_path, file_size, width, height,
                mime_type, created_date, modified_date, processing_status, thumbnail_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor = self.db.execute(sql, (
            media_file.drive_file_id,
            media_file.filename,
            media_file.file_path,
            media_file.file_size,
            media_file.width,
            media_file.height,
            media_file.mime_type,
            media_file.created_date,
            media_file.modified_date,
            media_file.processing_status.value,
            media_file.thumbnail_path
        ))
        
        return cursor.lastrowid
    
    def get_by_id(self, file_id: int) -> Optional[MediaFile]:
        """Get a file by ID."""
        sql = "SELECT * FROM files WHERE id = ?"
        row = self.db.fetchone(sql, (file_id,))
        
        if row:
            return self._row_to_media_file(row)
        return None
    
    def get_by_drive_id(self, drive_file_id: str) -> Optional[MediaFile]:
        """Get a file by Google Drive ID."""
        sql = "SELECT * FROM files WHERE drive_file_id = ?"
        row = self.db.fetchone(sql, (drive_file_id,))
        
        if row:
            return self._row_to_media_file(row)
        return None
    
    def get_by_status(self, status: ProcessingStatus, limit: Optional[int] = None) -> List[MediaFile]:
        """Get files by processing status."""
        sql = "SELECT * FROM files WHERE processing_status = ? ORDER BY created_at"
        if limit:
            sql += f" LIMIT {limit}"
        
        rows = self.db.fetchall(sql, (status.value,))
        return [self._row_to_media_file(row) for row in rows]
    
    def get_pending_files(self, limit: Optional[int] = None) -> List[MediaFile]:
        """Get files pending processing."""
        return self.get_by_status(ProcessingStatus.PENDING, limit)
    
    def get_failed_files(self, limit: Optional[int] = None) -> List[MediaFile]:
        """Get files that failed processing."""
        return self.get_by_status(ProcessingStatus.FAILED, limit)
    
    def update_processing_status(self, file_id: int, status: ProcessingStatus, 
                               error_message: Optional[str] = None,
                               processed_at: Optional[datetime] = None) -> None:
        """Update file processing status."""
        sql = """
            UPDATE files 
            SET processing_status = ?, error_message = ?, processed_at = ?
            WHERE id = ?
        """
        
        if processed_at is None and status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]:
            processed_at = datetime.now()
        
        self.db.execute(sql, (status.value, error_message, processed_at, file_id))
    
    def update_status(self, file_id: int, status: ProcessingStatus, 
                     error_message: Optional[str] = None) -> None:
        """Update file processing status (backwards compatibility)."""
        self.update_processing_status(file_id, status, error_message)
    
    def update_thumbnail_path(self, file_id: int, thumbnail_path: str) -> None:
        """Update file thumbnail path."""
        sql = "UPDATE files SET thumbnail_path = ? WHERE id = ?"
        self.db.execute(sql, (thumbnail_path, file_id))
    
    def update_dimensions(self, file_id: int, width: int, height: int) -> None:
        """Update file dimensions."""
        sql = "UPDATE files SET width = ?, height = ? WHERE id = ?"
        self.db.execute(sql, (width, height, file_id))
    
    def exists(self, drive_file_id: str) -> bool:
        """Check if a file exists by Google Drive ID."""
        sql = "SELECT 1 FROM files WHERE drive_file_id = ?"
        return self.db.fetchone(sql, (drive_file_id,)) is not None
    
    def get_processing_stats(self) -> Dict[str, int]:
        """Get processing statistics."""
        sql = """
            SELECT processing_status, COUNT(*) as count
            FROM files
            GROUP BY processing_status
        """
        
        rows = self.db.fetchall(sql)
        return {row['processing_status']: row['count'] for row in rows}
    
    def get_detailed_stats(self) -> Dict[str, int]:
        """Get detailed statistics separating images and videos."""
        sql = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN mime_type LIKE 'image%' THEN 1 ELSE 0 END) as images,
                SUM(CASE WHEN mime_type LIKE 'video%' THEN 1 ELSE 0 END) as videos,
                SUM(CASE WHEN mime_type LIKE 'image%' AND processing_status = 'completed' THEN 1 ELSE 0 END) as images_completed,
                SUM(CASE WHEN mime_type LIKE 'image%' AND processing_status = 'pending' THEN 1 ELSE 0 END) as images_pending,
                SUM(CASE WHEN mime_type LIKE 'image%' AND processing_status = 'failed' THEN 1 ELSE 0 END) as images_failed
            FROM files
        """
        
        row = self.db.fetchone(sql)
        return {
            'total': row['total'],
            'images': row['images'],
            'videos': row['videos'],
            'images_completed': row['images_completed'],
            'images_pending': row['images_pending'],
            'images_failed': row['images_failed']
        }
    
    def _row_to_media_file(self, row) -> MediaFile:
        """Convert database row to MediaFile object."""
        return MediaFile(
            id=row['id'],
            drive_file_id=row['drive_file_id'],
            filename=row['filename'],
            file_path=row['file_path'],
            file_size=row['file_size'],
            width=row.get('width'),
            height=row.get('height'),
            mime_type=row['mime_type'],
            created_date=row['created_date'],
            modified_date=row['modified_date'],
            processing_status=ProcessingStatus(row['processing_status']),
            processed_at=row['processed_at'],
            thumbnail_path=row['thumbnail_path']
        )
    
    def get_file_with_drive_url(self, file_id: int) -> Optional[dict]:
        """Get file with Google Drive URL."""
        media_file = self.get_by_id(file_id)
        if not media_file:
            return None
        
        return {
            'id': media_file.id,
            'filename': media_file.filename,
            'file_path': media_file.file_path,
            'mime_type': media_file.mime_type,
            'processing_status': media_file.processing_status.value,
            'drive_url': f"https://drive.google.com/file/d/{media_file.drive_file_id}/view",
            'drive_download_url': f"https://drive.google.com/uc?id={media_file.drive_file_id}",
            'created_date': media_file.created_date,
            'processed_at': media_file.processed_at
        }


class MetadataRepository:
    """Repository for metadata operations."""
    
    def __init__(self, db_connection: DatabaseConnection):
        """Initialize metadata repository."""
        self.db = db_connection
    
    def create(self, metadata: ExtractedMetadata) -> int:
        """Create metadata record."""
        # Validate metadata
        self._validate_metadata(metadata)
        
        sql = """
            INSERT INTO metadata (
                file_id, primary_subject, visual_quality, has_people, 
                people_count, is_indoor, social_media_score, social_media_reason,
                marketing_score, marketing_use, season, time_of_day,
                mood_energy, color_palette, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor = self.db.execute(sql, (
            metadata.file_id,
            metadata.primary_subject,
            metadata.visual_quality,
            metadata.has_people,
            metadata.people_count,
            metadata.is_indoor,
            metadata.social_media_score,
            metadata.social_media_reason,
            metadata.marketing_score,
            metadata.marketing_use,
            metadata.season,
            metadata.time_of_day,
            metadata.mood_energy,
            metadata.color_palette,
            metadata.notes
        ))
        
        return cursor.lastrowid
    
    def get_by_file_id(self, file_id: int) -> Optional[ExtractedMetadata]:
        """Get metadata by file ID."""
        sql = "SELECT * FROM metadata WHERE file_id = ?"
        row = self.db.fetchone(sql, (file_id,))
        
        if row:
            # Get activity tags
            tags_sql = "SELECT tag_name FROM activity_tags WHERE file_id = ?"
            tags_rows = self.db.fetchall(tags_sql, (file_id,))
            activity_tags = [row['tag_name'] for row in tags_rows]
            
            return self._row_to_metadata(row, activity_tags)
        return None
    
    def update(self, metadata: ExtractedMetadata) -> None:
        """Update existing metadata."""
        # Validate metadata
        self._validate_metadata(metadata)
        
        sql = """
            UPDATE metadata SET
                primary_subject = ?, visual_quality = ?, has_people = ?,
                people_count = ?, is_indoor = ?, social_media_score = ?,
                social_media_reason = ?, marketing_score = ?, marketing_use = ?,
                season = ?, time_of_day = ?, mood_energy = ?, color_palette = ?, notes = ?
            WHERE file_id = ?
        """
        
        self.db.execute(sql, (
            metadata.primary_subject,
            metadata.visual_quality,
            metadata.has_people,
            metadata.people_count,
            metadata.is_indoor,
            metadata.social_media_score,
            metadata.social_media_reason,
            metadata.marketing_score,
            metadata.marketing_use,
            metadata.season,
            metadata.time_of_day,
            metadata.mood_energy,
            metadata.color_palette,
            metadata.notes,
            metadata.file_id
        ))
    
    def search(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search metadata with filters."""
        sql = """
            SELECT f.*, m.*
            FROM files f
            JOIN metadata m ON f.id = m.file_id
            WHERE f.processing_status = 'completed'
        """
        
        params = []
        
        # Add filters
        if 'primary_subject' in filters:
            sql += " AND m.primary_subject LIKE ?"
            params.append(f"%{filters['primary_subject']}%")
        
        if 'min_visual_quality' in filters:
            sql += " AND m.visual_quality >= ?"
            params.append(filters['min_visual_quality'])
        
        if 'has_people' in filters:
            sql += " AND m.has_people = ?"
            params.append(filters['has_people'])
        
        if 'people_count' in filters:
            sql += " AND m.people_count = ?"
            params.append(filters['people_count'])
        
        if 'is_indoor' in filters:
            sql += " AND m.is_indoor = ?"
            params.append(filters['is_indoor'])
        
        if 'min_social_media_score' in filters:
            sql += " AND m.social_media_score >= ?"
            params.append(filters['min_social_media_score'])
        
        if 'min_marketing_score' in filters:
            sql += " AND m.marketing_score >= ?"
            params.append(filters['min_marketing_score'])
        
        if 'season' in filters:
            sql += " AND m.season = ?"
            params.append(filters['season'])
        
        if 'activity_tags' in filters:
            tags = filters['activity_tags']
            if isinstance(tags, str):
                tags = [tags]
            
            placeholders = ','.join(['?' for _ in tags])
            sql += f"""
                AND f.id IN (
                    SELECT file_id FROM activity_tags 
                    WHERE tag_name IN ({placeholders})
                )
            """
            params.extend(tags)
        
        # Add ordering
        order_by = filters.get('order_by', 'm.visual_quality DESC')
        sql += f" ORDER BY {order_by}"
        
        # Add limit
        if 'limit' in filters:
            sql += " LIMIT ?"
            params.append(filters['limit'])
        
        rows = self.db.fetchall(sql, tuple(params))
        
        # Convert to dict format with activity tags
        results = []
        for row in rows:
            # Get activity tags
            tags_sql = "SELECT tag_name FROM activity_tags WHERE file_id = ?"
            tags_rows = self.db.fetchall(tags_sql, (row['id'],))
            
            result = dict(row)
            result['activity_tags'] = [r['tag_name'] for r in tags_rows]
            results.append(result)
        
        return results
    
    def _validate_metadata(self, metadata: ExtractedMetadata) -> None:
        """Validate metadata values."""
        if not (1 <= metadata.visual_quality <= 5):
            raise DatabaseError("Visual quality must be between 1 and 5")
        
        if metadata.people_count not in PEOPLE_COUNT_OPTIONS:
            raise DatabaseError(f"Invalid people_count: {metadata.people_count}")
        
        if not (1 <= metadata.social_media_score <= 5):
            raise DatabaseError("Social media score must be between 1 and 5")
        
        if not (1 <= metadata.marketing_score <= 5):
            raise DatabaseError("Marketing score must be between 1 and 5")
        
        if metadata.season and metadata.season not in SEASON_OPTIONS:
            raise DatabaseError(f"Invalid season: {metadata.season}")
        
        if metadata.time_of_day and metadata.time_of_day not in TIME_OF_DAY_OPTIONS:
            raise DatabaseError(f"Invalid time_of_day: {metadata.time_of_day}")
    
    def _row_to_metadata(self, row, activity_tags: List[str]) -> ExtractedMetadata:
        """Convert database row to ExtractedMetadata object."""
        return ExtractedMetadata(
            file_id=row['file_id'],
            primary_subject=row['primary_subject'],
            visual_quality=row['visual_quality'],
            has_people=row['has_people'],
            people_count=row['people_count'],
            is_indoor=row['is_indoor'],
            social_media_score=row['social_media_score'],
            social_media_reason=row['social_media_reason'],
            marketing_score=row['marketing_score'],
            marketing_use=row['marketing_use'],
            activity_tags=activity_tags,
            season=row['season'],
            time_of_day=row['time_of_day'],
            mood_energy=row['mood_energy'],
            color_palette=row['color_palette'],
            notes=row['notes'],
            extracted_at=row['extracted_at']
        )


class ActivityTagRepository:
    """Repository for activity tag operations."""
    
    def __init__(self, db_connection: DatabaseConnection):
        """Initialize activity tag repository."""
        self.db = db_connection
    
    def add_tags(self, file_id: int, tags: List[str]) -> None:
        """Add activity tags for a file."""
        # Validate tags
        for tag in tags:
            if tag not in ACTIVITY_TAGS:
                raise DatabaseError(f"Invalid activity tag: {tag}")
        
        # Insert tags
        sql = "INSERT OR IGNORE INTO activity_tags (file_id, tag_name) VALUES (?, ?)"
        params = [(file_id, tag) for tag in tags]
        self.db.executemany(sql, params)
    
    def remove_tags(self, file_id: int, tags: Optional[List[str]] = None) -> None:
        """Remove activity tags for a file."""
        if tags is None:
            # Remove all tags
            sql = "DELETE FROM activity_tags WHERE file_id = ?"
            self.db.execute(sql, (file_id,))
        else:
            # Remove specific tags
            placeholders = ','.join(['?' for _ in tags])
            sql = f"DELETE FROM activity_tags WHERE file_id = ? AND tag_name IN ({placeholders})"
            params = [file_id] + tags
            self.db.execute(sql, tuple(params))
    
    def get_tags(self, file_id: int) -> List[str]:
        """Get activity tags for a file."""
        sql = "SELECT tag_name FROM activity_tags WHERE file_id = ?"
        rows = self.db.fetchall(sql, (file_id,))
        return [row['tag_name'] for row in rows]
    
    def get_tag_counts(self) -> Dict[str, int]:
        """Get count of files for each tag."""
        sql = """
            SELECT tag_name, COUNT(DISTINCT file_id) as count
            FROM activity_tags
            GROUP BY tag_name
            ORDER BY count DESC
        """
        
        rows = self.db.fetchall(sql)
        return {row['tag_name']: row['count'] for row in rows}


class ProcessingHistoryRepository:
    """Repository for processing history operations."""
    
    def __init__(self, db_connection: DatabaseConnection):
        """Initialize processing history repository."""
        self.db = db_connection
    
    def add_entry(self, file_id: int, status: str, error_message: Optional[str] = None,
                  processing_time_ms: Optional[int] = None) -> None:
        """Add a processing history entry."""
        sql = """
            INSERT INTO processing_history (file_id, status, error_message, processing_time_ms)
            VALUES (?, ?, ?, ?)
        """
        
        self.db.execute(sql, (file_id, status, error_message, processing_time_ms))
    
    def get_file_history(self, file_id: int) -> List[Dict[str, Any]]:
        """Get processing history for a file."""
        sql = """
            SELECT * FROM processing_history 
            WHERE file_id = ? 
            ORDER BY created_at DESC
        """
        
        rows = self.db.fetchall(sql, (file_id,))
        return [dict(row) for row in rows]