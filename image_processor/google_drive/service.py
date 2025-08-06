"""Google Drive service for file operations."""

import time
import logging
from typing import List, Optional, Dict, Any, Generator
from datetime import datetime

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
import io

from ..core.models import MediaFile, ProcessingStatus
from ..core.config import GoogleDriveConfig
from ..core.exceptions import GoogleDriveError
from .auth import GoogleDriveAuth

logger = logging.getLogger(__name__)

# MIME types for media files
IMAGE_MIME_TYPES = [
    'image/jpeg',
    'image/jpg',
    'image/png',
    'image/gif',
    'image/bmp',
    'image/tiff',
    'image/webp',
    'image/heic',
    'image/heif',
    'image/heic-sequence',
    'image/heif-sequence'
]

VIDEO_MIME_TYPES = [
    'video/mp4',
    'video/mpeg',
    'video/quicktime',
    'video/x-msvideo',
    'video/x-ms-wmv',
    'video/webm'
]

MEDIA_MIME_TYPES = IMAGE_MIME_TYPES + VIDEO_MIME_TYPES


class GoogleDriveService:
    """Service for interacting with Google Drive API."""
    
    def __init__(self, config: GoogleDriveConfig, auth: GoogleDriveAuth):
        """Initialize Google Drive service.
        
        Args:
            config: Google Drive configuration
            auth: Google Drive authentication instance
        """
        self.config = config
        self.auth = auth
        self.service = auth.get_service()
        self._rate_limit_delay = config.rate_limit_delay
    
    def discover_media_files(self, folder_id: Optional[str] = None) -> Generator[MediaFile, None, None]:
        """Discover all media files in Google Drive.
        
        Args:
            folder_id: Optional folder ID to start discovery from
        
        Yields:
            MediaFile objects for each discovered media file
        """
        start_folder = folder_id or self.config.root_folder_id or 'root'
        logger.info(f"Starting media file discovery from folder: {start_folder}")
        
        # Check if folder is in a shared drive
        shared_drive_id = self._get_shared_drive_id(start_folder)
        if shared_drive_id:
            logger.info(f"Folder is in shared drive: {shared_drive_id}")
        
        discovered_count = 0
        
        # Process the starting folder and all subfolders
        for file_data in self._traverse_folder(start_folder, shared_drive_id=shared_drive_id):
            if self._is_media_file(file_data):
                media_file = self._create_media_file(file_data)
                discovered_count += 1
                
                if discovered_count % 100 == 0:
                    logger.info(f"Discovered {discovered_count} media files so far...")
                
                yield media_file
        
        logger.info(f"Discovery complete. Total media files found: {discovered_count}")
    
    def _traverse_folder(self, folder_id: str, path: str = "", shared_drive_id: Optional[str] = None) -> Generator[Dict[str, Any], None, None]:
        """Recursively traverse folders and yield all files.
        
        Args:
            folder_id: Google Drive folder ID
            path: Current folder path for tracking
            shared_drive_id: Optional shared drive ID if folder is in a shared drive
        
        Yields:
            File metadata dictionaries
        """
        try:
            # Get folder name if not root
            if folder_id != 'root' and not path:
                folder_info = self._get_file_info(folder_id, shared_drive_id)
                if folder_info:
                    path = folder_info.get('name', '')
            
            # List all items in the folder
            page_token = None
            
            while True:
                query = f"'{folder_id}' in parents and trashed = false"
                
                try:
                    # Build list parameters
                    list_params = {
                        'q': query,
                        'pageSize': self.config.batch_size,
                        'fields': "nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, parents)",
                        'pageToken': page_token
                    }
                    
                    # Add shared drive parameters if needed
                    if shared_drive_id:
                        list_params.update({
                            'corpora': 'drive',
                            'driveId': shared_drive_id,
                            'includeItemsFromAllDrives': True,
                            'supportsAllDrives': True
                        })
                    
                    results = self.service.files().list(**list_params).execute()
                    
                    items = results.get('files', [])
                    
                    for item in items:
                        item['path'] = f"{path}/{item['name']}" if path else item['name']
                        
                        if item['mimeType'] == 'application/vnd.google-apps.folder':
                            # Recursively process subfolder
                            logger.debug(f"Entering folder: {item['path']}")
                            yield from self._traverse_folder(item['id'], item['path'], shared_drive_id)
                        else:
                            # Yield file
                            yield item
                    
                    page_token = results.get('nextPageToken')
                    if not page_token:
                        break
                    
                    # Rate limiting
                    time.sleep(self._rate_limit_delay)
                    
                except HttpError as error:
                    if error.resp.status == 403:
                        logger.warning(f"Permission denied for folder {folder_id}: {error}")
                        break
                    elif error.resp.status == 429:
                        logger.warning("Rate limit hit, backing off...")
                        time.sleep(30)  # Back off for 30 seconds
                        continue
                    else:
                        raise GoogleDriveError(f"Error listing files in folder {folder_id}: {error}")
                        
        except Exception as e:
            logger.error(f"Error traversing folder {folder_id}: {e}")
            raise GoogleDriveError(f"Failed to traverse folder: {e}")
    
    def _get_file_info(self, file_id: str, shared_drive_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get detailed information about a file.
        
        Args:
            file_id: Google Drive file ID
            shared_drive_id: Optional shared drive ID if file is in a shared drive
        
        Returns:
            File metadata dictionary or None if error
        """
        try:
            get_params = {
                'fileId': file_id,
                'fields': "id, name, mimeType, size, createdTime, modifiedTime, parents"
            }
            
            # Add shared drive support if needed
            if shared_drive_id:
                get_params['supportsAllDrives'] = True
            
            file_info = self.service.files().get(**get_params).execute()
            
            return file_info
            
        except HttpError as error:
            logger.error(f"Error getting file info for {file_id}: {error}")
            return None
    
    def download_file(self, file_id: str, output_path: str = None) -> bytes:
        """Download a file from Google Drive.
        
        Args:
            file_id: Google Drive file ID
            output_path: Optional local path to save the file (if None, returns bytes)
        
        Returns:
            File content as bytes, or raises GoogleDriveError on failure
        """
        try:
            request = self.service.files().get_media(fileId=file_id)
            
            if output_path:
                # Download to file
                with io.FileIO(output_path, 'wb') as fh:
                    downloader = MediaIoBaseDownload(fh, request)
                    done = False
                    
                    while not done:
                        status, done = downloader.next_chunk()
                        if status:
                            logger.debug(f"Download {int(status.progress() * 100)}% complete")
                
                logger.info(f"Downloaded file {file_id} to {output_path}")
                
                # Read and return the file content
                with open(output_path, 'rb') as f:
                    return f.read()
            else:
                # Download to memory
                buffer = io.BytesIO()
                downloader = MediaIoBaseDownload(buffer, request)
                done = False
                
                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        logger.debug(f"Download {int(status.progress() * 100)}% complete")
                
                logger.debug(f"Downloaded file {file_id} to memory")
                return buffer.getvalue()
            
        except HttpError as error:
            logger.error(f"Error downloading file {file_id}: {error}")
            raise GoogleDriveError(f"Failed to download file {file_id}: {error}")
    
    def download_file_to_path(self, file_id: str, output_path: str) -> bool:
        """Download a file from Google Drive to a specific path.
        
        Args:
            file_id: Google Drive file ID
            output_path: Local path to save the file
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.download_file(file_id, output_path)
            return True
        except GoogleDriveError:
            return False
    
    def _is_media_file(self, file_data: Dict[str, Any]) -> bool:
        """Check if a file is a media file based on MIME type.
        
        Args:
            file_data: File metadata dictionary
        
        Returns:
            True if file is a media file, False otherwise
        """
        mime_type = file_data.get('mimeType', '')
        return mime_type in MEDIA_MIME_TYPES
    
    def _create_media_file(self, file_data: Dict[str, Any]) -> MediaFile:
        """Create MediaFile object from Google Drive file data.
        
        Args:
            file_data: File metadata dictionary
        
        Returns:
            MediaFile object
        """
        # Parse timestamps
        created_time = file_data.get('createdTime')
        modified_time = file_data.get('modifiedTime')
        
        if created_time:
            created_date = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
        else:
            created_date = datetime.now()
        
        if modified_time:
            modified_date = datetime.fromisoformat(modified_time.replace('Z', '+00:00'))
        else:
            modified_date = created_date
        
        return MediaFile(
            drive_file_id=file_data['id'],
            filename=file_data['name'],
            file_path=file_data.get('path', file_data['name']),
            file_size=int(file_data.get('size', 0)),
            mime_type=file_data['mimeType'],
            created_date=created_date,
            modified_date=modified_date,
            processing_status=ProcessingStatus.PENDING
        )
    
    def _get_shared_drive_id(self, folder_id: str) -> Optional[str]:
        """Get the shared drive ID if the folder is in a shared drive.
        
        Args:
            folder_id: Google Drive folder ID
            
        Returns:
            Shared drive ID or None if not in a shared drive
        """
        if folder_id == 'root':
            return None
            
        try:
            # Get file info with drive ID
            file_info = self.service.files().get(
                fileId=folder_id,
                fields="driveId",
                supportsAllDrives=True
            ).execute()
            
            return file_info.get('driveId')
            
        except HttpError:
            # If we can't get info, assume it's not in a shared drive
            return None
    
    def get_file_count(self, folder_id: Optional[str] = None) -> Dict[str, int]:
        """Get count of files by type in a folder.
        
        Args:
            folder_id: Optional folder ID to count from
        
        Returns:
            Dictionary with counts by file type
        """
        start_folder = folder_id or self.config.root_folder_id or 'root'
        
        # Check if folder is in a shared drive
        shared_drive_id = self._get_shared_drive_id(start_folder)
        
        counts = {
            'total': 0,
            'images': 0,
            'videos': 0,
            'other': 0
        }
        
        for file_data in self._traverse_folder(start_folder, shared_drive_id=shared_drive_id):
            counts['total'] += 1
            
            mime_type = file_data.get('mimeType', '')
            if mime_type in IMAGE_MIME_TYPES:
                counts['images'] += 1
            elif mime_type in VIDEO_MIME_TYPES:
                counts['videos'] += 1
            else:
                counts['other'] += 1
        
        return counts