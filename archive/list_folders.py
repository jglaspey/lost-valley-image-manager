#!/usr/bin/env python3
"""Quick script to list folders in Google Drive."""

from image_processor.core.config import Config
from image_processor.google_drive import GoogleDriveAuth, GoogleDriveService

# Load config
config = Config.from_file('config/config.yaml')

# Connect to Google Drive
auth = GoogleDriveAuth(config.google_drive.credentials_path)
service = auth.get_service()

# List folders in root
print("Folders in root of Drive:")
print("-" * 50)

page_token = None
while True:
    results = service.files().list(
        q="mimeType='application/vnd.google-apps.folder' and 'root' in parents and trashed=false",
        spaces='drive',
        fields='nextPageToken, files(id, name)',
        pageToken=page_token,
        pageSize=100
    ).execute()
    
    items = results.get('files', [])
    
    for item in items:
        print(f"📁 {item['name']}")
        print(f"   ID: {item['id']}")
        print()
    
    page_token = results.get('nextPageToken', None)
    if page_token is None:
        break

# Also check shared drives
print("\nChecking shared drives:")
print("-" * 50)
try:
    results = service.drives().list(pageSize=100).execute()
    drives = results.get('drives', [])
    
    if drives:
        for drive in drives:
            print(f"💾 {drive['name']}")
            print(f"   ID: {drive['id']}")
            print()
    else:
        print("No shared drives found")
except:
    print("No access to shared drives or none exist")