"""Vision analysis service for processing media files."""

import logging
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from .claude_client import ClaudeVisionClient as VisionClient
from ..core.config import Config
from ..core.models import MediaFile, ExtractedMetadata, ProcessingStatus
from ..database import DatabaseConnection, FileRepository, MetadataRepository, ActivityTagRepository
from ..google_drive import GoogleDriveAuth, GoogleDriveService
from ..core.exceptions import VisionAnalysisError, ProcessingError

logger = logging.getLogger(__name__)


class VisionAnalysisService:
    """Service for processing media files with vision analysis."""
    
    def __init__(self, config: Config):
        """Initialize the vision analysis service."""
        self.config = config
        self.vision_client = VisionClient(config.vision_model)
        
        # Initialize database connections
        self.db_connection = DatabaseConnection(config.database)
        self.file_repo = FileRepository(self.db_connection)
        self.metadata_repo = MetadataRepository(self.db_connection)
        self.activity_tag_repo = ActivityTagRepository(self.db_connection)
        
        # Initialize Google Drive service
        self.drive_auth = GoogleDriveAuth(config.google_drive.credentials_path)
        self.drive_service = GoogleDriveService(config.google_drive, self.drive_auth)
    
    def process_file(self, file_id: int) -> bool:
        """
        Process a single file with vision analysis.
        
        Args:
            file_id: Database ID of the file to process
            
        Returns:
            True if processing successful, False otherwise
        """
        try:
            # Get file from database
            media_file = self.file_repo.get_by_id(file_id)
            if not media_file:
                logger.error(f"File with ID {file_id} not found in database")
                return False
            
            logger.info(f"Processing file: {media_file.filename}")
            
            # Check if file is an image (skip videos entirely - don't mark as failed)
            if not self._is_image_file(media_file.mime_type):
                logger.info(f"Skipping non-image file: {media_file.filename} (type: {media_file.mime_type})")
                return False
            
            # Update status to in_progress
            self.file_repo.update_processing_status(
                file_id, 
                ProcessingStatus.IN_PROGRESS
            )
            
            try:
                # Download file from Google Drive
                image_data = self.drive_service.download_file(media_file.drive_file_id)
                
                # Analyze with vision model
                metadata_dict = self.vision_client.analyze_image(
                    image_data, 
                    media_file.filename,
                    media_file.file_path
                )
                
                # Create ExtractedMetadata object
                extracted_metadata = ExtractedMetadata(
                    primary_subject=metadata_dict['primary_subject'],
                    visual_quality=metadata_dict['visual_quality'],
                    has_people=metadata_dict['has_people'],
                    people_count=metadata_dict['people_count'],
                    is_indoor=metadata_dict['is_indoor'],
                    social_media_score=metadata_dict['social_media_score'],
                    social_media_reason=metadata_dict['social_media_reason'],
                    marketing_score=metadata_dict['marketing_score'],
                    marketing_use=metadata_dict['marketing_use'],
                    activity_tags=metadata_dict['activity_tags'],
                    season=metadata_dict.get('season'),
                    time_of_day=metadata_dict.get('time_of_day'),
                    mood_energy=metadata_dict.get('mood_energy'),
                    color_palette=metadata_dict.get('color_palette'),
                    notes=metadata_dict.get('notes'),
                    extracted_at=datetime.now(),
                    file_id=file_id
                )
                
                # Save metadata to database (idempotent)
                self.metadata_repo.upsert(extracted_metadata)
                
                # Save activity tags
                if extracted_metadata.activity_tags:
                    # Replace tags to avoid stale entries from previous runs
                    try:
                        self.activity_tag_repo.remove_tags(file_id)
                    except Exception:
                        pass
                    self.activity_tag_repo.add_tags(file_id, extracted_metadata.activity_tags)
                
                # Update file status to completed
                self.file_repo.update_processing_status(
                    file_id, 
                    ProcessingStatus.COMPLETED,
                    processed_at=datetime.now()
                )
                
                logger.info(f"Successfully processed {media_file.filename}")
                return True
                
            except Exception as e:
                # Update status to failed
                self.file_repo.update_processing_status(
                    file_id, 
                    ProcessingStatus.FAILED,
                    error_message=str(e)
                )
                logger.error(f"Failed to process {media_file.filename}: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing file ID {file_id}: {e}")
            return False
    
    def process_pending_files(self, limit: Optional[int] = None) -> dict:
        """
        Process all pending files.
        
        Args:
            limit: Maximum number of files to process
            
        Returns:
            Dictionary with processing statistics
        """
        try:
            # Get pending image files only
            all_pending = self.file_repo.get_by_status(ProcessingStatus.PENDING)
            pending_files = [f for f in all_pending if self._is_image_file(f.mime_type)]
            
            if limit:
                pending_files = pending_files[:limit]
            
            if not pending_files:
                logger.info("No pending image files to process")
                return {'processed': 0, 'failed': 0, 'skipped': 0}
            
            logger.info(f"Processing {len(pending_files)} pending image files")
            
            processed = 0
            failed = 0
            
            for media_file in pending_files:
                try:
                    success = self.process_file(media_file.id)
                    if success:
                        processed += 1
                    else:
                        failed += 1
                        
                except Exception as e:
                    logger.error(f"Error processing file {media_file.filename}: {e}")
                    failed += 1
            
            logger.info(f"Processing complete: {processed} successful, {failed} failed")
            
            return {
                'processed': processed,
                'failed': failed,
                'skipped': 0
            }
            
        except Exception as e:
            logger.error(f"Error in process_pending_files: {e}")
            raise ProcessingError(f"Failed to process pending files: {e}")
    
    def process_file_by_drive_id(self, drive_file_id: str) -> bool:
        """
        Process a file by its Google Drive ID.
        
        Args:
            drive_file_id: Google Drive file ID
            
        Returns:
            True if processing successful, False otherwise
        """
        try:
            # Find file in database
            media_file = self.file_repo.get_by_drive_id(drive_file_id)
            if not media_file:
                logger.error(f"File with Drive ID {drive_file_id} not found in database")
                return False
            
            return self.process_file(media_file.id)
            
        except Exception as e:
            logger.error(f"Error processing file with Drive ID {drive_file_id}: {e}")
            return False
    
    def reprocess_failed_files(self, limit: Optional[int] = None) -> dict:
        """
        Reprocess files that previously failed.
        
        Args:
            limit: Maximum number of files to reprocess
            
        Returns:
            Dictionary with processing statistics
        """
        try:
            # Get failed files
            failed_files = self.file_repo.get_by_status(ProcessingStatus.FAILED)
            
            if limit:
                failed_files = failed_files[:limit]
            
            if not failed_files:
                logger.info("No failed files to reprocess")
                return {'processed': 0, 'failed': 0, 'skipped': 0}
            
            logger.info(f"Reprocessing {len(failed_files)} failed files")
            
            processed = 0
            failed = 0
            
            for media_file in failed_files:
                try:
                    # Reset status to pending before processing
                    self.file_repo.update_processing_status(
                        media_file.id, 
                        ProcessingStatus.PENDING,
                        error_message=None
                    )
                    
                    success = self.process_file(media_file.id)
                    if success:
                        processed += 1
                    else:
                        failed += 1
                        
                except Exception as e:
                    logger.error(f"Error reprocessing file {media_file.filename}: {e}")
                    failed += 1
            
            logger.info(f"Reprocessing complete: {processed} successful, {failed} failed")
            
            return {
                'processed': processed,
                'failed': failed,
                'skipped': 0
            }
            
        except Exception as e:
            logger.error(f"Error in reprocess_failed_files: {e}")
            raise ProcessingError(f"Failed to reprocess failed files: {e}")
    
    def get_processing_stats(self) -> dict:
        """
        Get current processing statistics.
        
        Returns:
            Dictionary with processing statistics
        """
        return self.file_repo.get_processing_stats()
    
    def test_vision_connection(self) -> bool:
        """
        Test connection to vision model API.
        
        Returns:
            True if connection successful, False otherwise
        """
        return self.vision_client.test_connection()
    
    def _is_image_file(self, mime_type: str) -> bool:
        """
        Check if file is an image based on MIME type.
        
        Args:
            mime_type: File MIME type
            
        Returns:
            True if file is an image, False otherwise
        """
        image_mime_types = [
            'image/jpeg',
            'image/jpg', 
            'image/png',
            'image/gif',
            'image/bmp',
            'image/tiff',
            'image/webp',
            'image/heic',
            'image/heif'
        ]
        return mime_type.lower() in image_mime_types