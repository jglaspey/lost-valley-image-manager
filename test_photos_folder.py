#!/usr/bin/env python3
"""Test accessing the Photos folder in shared drive."""

from image_processor.core.config import Config
from image_processor.google_drive import GoogleDriveAuth

# Load config
config = Config.from_file('config/config.yaml')

# Connect to Google Drive
auth = GoogleDriveAuth(config.google_drive.credentials_path)
service = auth.get_service()

photos_folder_id = "1I9bH_ii-ImeCB6ojW9LIbY7p2wwqio-G"
shared_drive_id = "0AJ70ibhTUUybUk9PVA"

print("Checking Photos folder in shared drive...")
print("-" * 60)

# Get folder info
try:
    folder_info = service.files().get(
        fileId=photos_folder_id,
        supportsAllDrives=True,
        fields="id, name, mimeType"
    ).execute()
    print(f"✓ Found folder: {folder_info['name']}")
except Exception as e:
    print(f"✗ Error getting folder info: {e}")

# Count files in the Photos folder
print("\nCounting files in Photos folder...")
page_token = None
image_count = 0
total_count = 0

while True:
    results = service.files().list(
        q=f"'{photos_folder_id}' in parents and trashed=false",
        corpora='drive',
        driveId=shared_drive_id,
        includeItemsFromAllDrives=True,
        supportsAllDrives=True,
        fields='nextPageToken, files(id, name, mimeType)',
        pageToken=page_token,
        pageSize=100
    ).execute()
    
    items = results.get('files', [])
    
    for item in items:
        total_count += 1
        if item['mimeType'].startswith('image/'):
            image_count += 1
            if image_count <= 5:
                print(f"  🖼️ {item['name']}")
    
    page_token = results.get('nextPageToken', None)
    if page_token is None:
        break

print(f"\nTotal files: {total_count}")
print(f"Total images: {image_count}")