"""Tests for Google Drive service."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from googleapiclient.errors import HttpError

from image_processor.core.config import GoogleDriveConfig
from image_processor.core.models import MediaFile, ProcessingStatus
from image_processor.google_drive.auth import GoogleDriveAuth
from image_processor.google_drive.service import GoogleDriveService, MEDIA_MIME_TYPES
from image_processor.core.exceptions import GoogleDriveError


class TestGoogleDriveService:
    """Test GoogleDriveService class."""
    
    @pytest.fixture
    def mock_auth(self):
        """Create mock GoogleDriveAuth."""
        auth = Mock(spec=GoogleDriveAuth)
        auth.get_service.return_value = MagicMock()
        return auth
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return GoogleDriveConfig(
            credentials_path="test_credentials.json",
            root_folder_id="test_root_folder",
            batch_size=100,
            rate_limit_delay=0.1
        )
    
    @pytest.fixture
    def service(self, config, mock_auth):
        """Create GoogleDriveService instance."""
        return GoogleDriveService(config, mock_auth)
    
    def test_is_media_file(self, service):
        """Test media file detection."""
        # Test image files
        assert service._is_media_file({'mimeType': 'image/jpeg'})
        assert service._is_media_file({'mimeType': 'image/png'})
        
        # Test video files
        assert service._is_media_file({'mimeType': 'video/mp4'})
        assert service._is_media_file({'mimeType': 'video/quicktime'})
        
        # Test non-media files
        assert not service._is_media_file({'mimeType': 'application/pdf'})
        assert not service._is_media_file({'mimeType': 'text/plain'})
        assert not service._is_media_file({'mimeType': 'application/vnd.google-apps.folder'})
    
    def test_create_media_file(self, service):
        """Test MediaFile creation from Google Drive data."""
        file_data = {
            'id': 'test_file_123',
            'name': 'test_image.jpg',
            'path': 'folder/test_image.jpg',
            'mimeType': 'image/jpeg',
            'size': '1024000',
            'createdTime': '2024-01-15T10:30:00Z',
            'modifiedTime': '2024-01-16T14:45:00Z'
        }
        
        media_file = service._create_media_file(file_data)
        
        assert media_file.drive_file_id == 'test_file_123'
        assert media_file.filename == 'test_image.jpg'
        assert media_file.file_path == 'folder/test_image.jpg'
        assert media_file.file_size == 1024000
        assert media_file.mime_type == 'image/jpeg'
        assert media_file.processing_status == ProcessingStatus.PENDING
        assert isinstance(media_file.created_date, datetime)
        assert isinstance(media_file.modified_date, datetime)
    
    def test_traverse_folder(self, service):
        """Test folder traversal."""
        # Mock the files().list() response
        mock_files_list = Mock()
        service.service.files().list = Mock(return_value=mock_files_list)
        
        # Track call count to handle recursive calls differently
        call_count = 0
        
        def mock_execute():
            nonlocal call_count
            call_count += 1
            
            if call_count == 1:
                # First call - return files and a subfolder
                return {
                    'files': [
                        {
                            'id': 'file1',
                            'name': 'image1.jpg',
                            'mimeType': 'image/jpeg',
                            'size': '1024',
                            'createdTime': '2024-01-15T10:00:00Z',
                            'modifiedTime': '2024-01-15T10:00:00Z'
                        },
                        {
                            'id': 'subfolder1',
                            'name': 'SubFolder',
                            'mimeType': 'application/vnd.google-apps.folder'
                        }
                    ],
                    'nextPageToken': None
                }
            else:
                # Subsequent calls (subfolder) - return empty
                return {
                    'files': [],
                    'nextPageToken': None
                }
        
        mock_files_list.execute = mock_execute
        
        # Collect results
        results = list(service._traverse_folder('test_folder'))
        
        # Should have 1 file (folders are traversed but not yielded)
        assert len(results) == 1
        assert results[0]['id'] == 'file1'
        assert results[0]['name'] == 'image1.jpg'
    
    def test_traverse_folder_with_pagination(self, service):
        """Test folder traversal with pagination."""
        mock_files_list = Mock()
        service.service.files().list = Mock(return_value=mock_files_list)
        
        # Mock paginated responses
        responses = [
            {
                'files': [
                    {'id': f'file{i}', 'name': f'image{i}.jpg', 'mimeType': 'image/jpeg'}
                    for i in range(1, 4)
                ],
                'nextPageToken': 'token1'
            },
            {
                'files': [
                    {'id': f'file{i}', 'name': f'image{i}.jpg', 'mimeType': 'image/jpeg'}
                    for i in range(4, 7)
                ],
                'nextPageToken': None
            }
        ]
        
        mock_files_list.execute.side_effect = responses
        
        # Collect results
        results = list(service._traverse_folder('test_folder'))
        
        assert len(results) == 6
        assert results[0]['id'] == 'file1'
        assert results[-1]['id'] == 'file6'
    
    def test_traverse_folder_permission_error(self, service):
        """Test handling of permission errors during traversal."""
        mock_files_list = Mock()
        service.service.files().list = Mock(return_value=mock_files_list)
        
        # Mock 403 permission error
        error_resp = Mock()
        error_resp.status = 403
        mock_files_list.execute.side_effect = HttpError(
            resp=error_resp,
            content=b'Permission denied'
        )
        
        # Should not raise, but return empty results
        results = list(service._traverse_folder('restricted_folder'))
        assert results == []
    
    def test_discover_media_files(self, service):
        """Test media file discovery."""
        # Mock traverse_folder to return test files
        test_files = [
            {
                'id': 'img1',
                'name': 'photo.jpg',
                'path': 'folder/photo.jpg',
                'mimeType': 'image/jpeg',
                'size': '2048000',
                'createdTime': '2024-01-15T10:00:00Z',
                'modifiedTime': '2024-01-15T10:00:00Z'
            },
            {
                'id': 'doc1',
                'name': 'document.pdf',
                'path': 'folder/document.pdf',
                'mimeType': 'application/pdf',
                'size': '512000',
                'createdTime': '2024-01-15T10:00:00Z',
                'modifiedTime': '2024-01-15T10:00:00Z'
            },
            {
                'id': 'vid1',
                'name': 'video.mp4',
                'path': 'folder/video.mp4',
                'mimeType': 'video/mp4',
                'size': '10485760',
                'createdTime': '2024-01-15T10:00:00Z',
                'modifiedTime': '2024-01-15T10:00:00Z'
            }
        ]
        
        with patch.object(service, '_traverse_folder', return_value=test_files):
            media_files = list(service.discover_media_files())
        
        # Should only return media files (image and video)
        assert len(media_files) == 2
        assert all(isinstance(f, MediaFile) for f in media_files)
        assert media_files[0].filename == 'photo.jpg'
        assert media_files[1].filename == 'video.mp4'
    
    def test_get_file_count(self, service):
        """Test file counting."""
        test_files = [
            {'id': 'img1', 'mimeType': 'image/jpeg'},
            {'id': 'img2', 'mimeType': 'image/png'},
            {'id': 'vid1', 'mimeType': 'video/mp4'},
            {'id': 'doc1', 'mimeType': 'application/pdf'},
            {'id': 'doc2', 'mimeType': 'text/plain'}
        ]
        
        with patch.object(service, '_traverse_folder', return_value=test_files):
            counts = service.get_file_count()
        
        assert counts['total'] == 5
        assert counts['images'] == 2
        assert counts['videos'] == 1
        assert counts['other'] == 2
    
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_rate_limiting(self, mock_sleep, service):
        """Test rate limiting behavior."""
        mock_files_list = Mock()
        service.service.files().list = Mock(return_value=mock_files_list)
        
        # Mock rate limit error followed by success
        error_resp = Mock()
        error_resp.status = 429
        mock_files_list.execute.side_effect = [
            HttpError(resp=error_resp, content=b'Rate limit exceeded'),
            {'files': [], 'nextPageToken': None}
        ]
        
        results = list(service._traverse_folder('test_folder'))
        
        # Should have called sleep for backoff
        mock_sleep.assert_called_with(30)
        assert results == []