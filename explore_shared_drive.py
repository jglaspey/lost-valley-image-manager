#!/usr/bin/env python3
"""Explore shared drive contents."""

from image_processor.core.config import Config
from image_processor.google_drive import GoogleDriveAuth

# Load config
config = Config.from_file('config/config.yaml')

# Connect to Google Drive
auth = GoogleDriveAuth(config.google_drive.credentials_path)
service = auth.get_service()

shared_drive_id = "0AJ70ibhTUUybUk9PVA"  # LV VIDEOS and Photos

print(f"Contents of 'LV VIDEOS and Photos' shared drive:")
print("-" * 60)

# List items in the shared drive
page_token = None
file_count = 0
folder_count = 0
image_count = 0

while True:
    results = service.files().list(
        q=f"trashed=false",
        corpora='drive',
        driveId=shared_drive_id,
        includeItemsFromAllDrives=True,
        supportsAllDrives=True,
        fields='nextPageToken, files(id, name, mimeType)',
        pageToken=page_token,
        pageSize=50
    ).execute()
    
    items = results.get('files', [])
    
    for item in items:
        if item['mimeType'] == 'application/vnd.google-apps.folder':
            print(f"📁 {item['name']}")
            print(f"   ID: {item['id']}")
            folder_count += 1
        else:
            file_count += 1
            if item['mimeType'].startswith('image/'):
                image_count += 1
                if image_count <= 5:  # Show first 5 images
                    print(f"🖼️  {item['name']}")
    
    page_token = results.get('nextPageToken', None)
    if page_token is None:
        break

print(f"\nSummary:")
print(f"Total folders: {folder_count}")
print(f"Total files: {file_count}")
print(f"Total images: {image_count}")