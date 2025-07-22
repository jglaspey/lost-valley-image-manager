"""Google Drive authentication management."""

import os
import json
import logging
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..core.exceptions import GoogleDriveError

logger = logging.getLogger(__name__)

# If modifying these scopes, delete the token file.
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/drive.metadata.readonly'
]


class GoogleDriveAuth:
    """Handles Google Drive API authentication."""
    
    def __init__(self, credentials_path: str, token_path: Optional[str] = None):
        """Initialize Google Drive authentication.
        
        Args:
            credentials_path: Path to credentials.json file
            token_path: Path to store token.json file (optional)
        """
        self.credentials_path = Path(credentials_path)
        self.token_path = Path(token_path) if token_path else self.credentials_path.parent / 'token.json'
        self._creds = None
        
        if not self.credentials_path.exists():
            raise GoogleDriveError(f"Credentials file not found: {self.credentials_path}")
    
    def authenticate(self) -> Credentials:
        """Authenticate and return credentials.
        
        Returns:
            Google OAuth2 credentials
        """
        # Token file stores the user's access and refresh tokens
        if self.token_path.exists():
            try:
                self._creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)
                logger.info("Loaded credentials from token file")
            except Exception as e:
                logger.warning(f"Failed to load token file: {e}")
                self._creds = None
        
        # If there are no (valid) credentials available, let the user log in
        if not self._creds or not self._creds.valid:
            if self._creds and self._creds.expired and self._creds.refresh_token:
                try:
                    logger.info("Refreshing expired credentials")
                    self._creds.refresh(Request())
                except Exception as e:
                    logger.warning(f"Failed to refresh credentials: {e}")
                    self._creds = None
            
            if not self._creds:
                logger.info("Starting OAuth2 flow for new credentials")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), SCOPES
                )
                self._creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            self._save_credentials()
        
        return self._creds
    
    def _save_credentials(self) -> None:
        """Save credentials to token file."""
        try:
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_path, 'w') as token:
                token.write(self._creds.to_json())
            logger.info(f"Saved credentials to {self.token_path}")
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
    
    def get_service(self):
        """Get authenticated Google Drive service.
        
        Returns:
            Google Drive API service object
        """
        if not self._creds:
            self.authenticate()
        
        try:
            service = build('drive', 'v3', credentials=self._creds)
            logger.info("Successfully created Google Drive service")
            return service
        except HttpError as error:
            raise GoogleDriveError(f"Failed to create Google Drive service: {error}")
    
    def revoke_credentials(self) -> None:
        """Revoke stored credentials."""
        if self.token_path.exists():
            try:
                self.token_path.unlink()
                logger.info("Revoked stored credentials")
            except Exception as e:
                logger.error(f"Failed to remove token file: {e}")
        
        self._creds = None