#!/usr/bin/env python3
"""
Claude Test Processor - Reprocess completed images with Claude 3.5 Haiku for comparison.

This script:
1. Finds all images with processing_status='completed' in image_metadata.db
2. Reprocesses the first 20 with Claude 3.5 Haiku using identical prompts
3. Saves results to claude_test.db for side-by-side comparison
"""

import os
import sys
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any
import json
from dataclasses import asdict
from dotenv import load_dotenv

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from image_processor.core.config import Config, VisionModelConfig
from image_processor.vision.claude_client import ClaudeVisionClient
from image_processor.database.connection import DatabaseConnection
from image_processor.utils.logging import setup_logging
from image_processor.google_drive.service import GoogleDriveService
from image_processor.google_drive.auth import GoogleDriveAuth

# Setup logging
logger = logging.getLogger(__name__)


def get_completed_files(db_path: str, limit: int = None) -> List[Dict[str, Any]]:
    """Get completed files from the original database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    cursor = conn.cursor()
    if limit:
        cursor.execute("""
            SELECT f.id, f.drive_file_id, f.filename, f.file_path, f.file_size, f.mime_type
            FROM files f
            WHERE f.processing_status = 'completed'
            ORDER BY f.id
            LIMIT ?
        """, (limit,))
    else:
        cursor.execute("""
            SELECT f.id, f.drive_file_id, f.filename, f.file_path, f.file_size, f.mime_type
            FROM files f
            WHERE f.processing_status = 'completed'
            ORDER BY f.id
        """)
    
    files = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return files


def clear_test_metadata(db_path: str, file_ids: List[int]):
    """Clear existing metadata for test files in the Claude test database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Clear metadata and activity tags for these files
    placeholders = ','.join('?' * len(file_ids))
    cursor.execute(f"DELETE FROM metadata WHERE file_id IN ({placeholders})", file_ids)
    cursor.execute(f"DELETE FROM activity_tags WHERE file_id IN ({placeholders})", file_ids)
    
    # Reset processing status to pending so we can reprocess
    cursor.execute(f"""
        UPDATE files 
        SET processing_status = 'pending', processed_at = NULL, error_message = NULL
        WHERE id IN ({placeholders})
    """, file_ids)
    
    conn.commit()
    conn.close()
    
    logger.info(f"Cleared metadata for {len(file_ids)} files in test database")


def process_file_with_claude(client: ClaudeVisionClient, drive_service: GoogleDriveService, 
                           file_info: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single file with Claude."""
    try:
        # Download file data from Google Drive
        file_data = drive_service.download_file(file_info['drive_file_id'])
        
        # Analyze with Claude
        metadata = client.analyze_image(
            image_data=file_data,
            filename=file_info['filename'],
            file_path=file_info['file_path']
        )
        
        return metadata
        
    except Exception as e:
        logger.error(f"Failed to process {file_info['filename']}: {e}")
        raise


def save_metadata_to_db(db_path: str, file_id: int, metadata: Dict[str, Any]):
    """Save extracted metadata to the test database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Insert metadata
        cursor.execute("""
            INSERT OR REPLACE INTO metadata (
                file_id, primary_subject, visual_quality, has_people, people_count,
                is_indoor, social_media_score, social_media_reason, marketing_score,
                marketing_use, season, time_of_day, mood_energy, color_palette, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            file_id,
            metadata.get('primary_subject', ''),
            metadata.get('visual_quality', 3),
            metadata.get('has_people', False),
            metadata.get('people_count', 'none'),
            metadata.get('is_indoor', False),
            metadata.get('social_media_score', 3),
            metadata.get('social_media_reason', ''),
            metadata.get('marketing_score', 3),
            metadata.get('marketing_use', ''),
            metadata.get('season'),
            metadata.get('time_of_day'),
            metadata.get('mood_energy'),
            metadata.get('color_palette'),
            metadata.get('notes', '')
        ))
        
        # Insert activity tags
        for tag in metadata.get('activity_tags', []):
            cursor.execute("""
                INSERT OR IGNORE INTO activity_tags (file_id, tag_name)
                VALUES (?, ?)
            """, (file_id, tag))
        
        # Update file status
        cursor.execute("""
            UPDATE files 
            SET processing_status = 'completed', processed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (file_id,))
        
        conn.commit()
        logger.info(f"Saved metadata for file ID {file_id}")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to save metadata for file ID {file_id}: {e}")
        raise
    finally:
        conn.close()


def main():
    """Main processing function."""
    # Load environment variables
    load_dotenv()
    
    # Setup logging
    setup_logging(logging.INFO)
    logger.info("Starting Claude 2-pass test processor")
    
    # Check for API key
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("ERROR: ANTHROPIC_API_KEY not found in .env file")
        print("Please add your Claude API key to the .env file")
        return 1
    
    try:
        # Load config
        config = Config.from_file("config/config.yaml")
        
        # Override vision config for Claude
        vision_config = VisionModelConfig(
            model_type="claude-3-5-haiku-20241022",
            provider="claude",
            temperature=0.4,
            max_tokens=500,
            max_retries=3,
            timeout_seconds=30,
            prompt_template=config.vision_model.prompt_template  # Use same prompt
        )
        
        # Initialize Claude client
        claude_client = ClaudeVisionClient(vision_config)
        
        # Test connection
        logger.info("Testing Claude API connection...")
        if not claude_client.test_connection():
            print("ERROR: Failed to connect to Claude API")
            return 1
        print("✓ Claude API connection successful")
        
        # Initialize Google Drive service
        logger.info("Initializing Google Drive service...")
        drive_auth = GoogleDriveAuth(config.google_drive.credentials_path)
        drive_service = GoogleDriveService(config.google_drive, drive_auth)
        print("✓ Google Drive service initialized")
        
        # Get completed files from original database
        logger.info("Getting completed files from original database...")
        original_db = "image_metadata.db"
        test_db = "claude_2pass.db"
        
        completed_files = get_completed_files(original_db)  # Process ALL completed files
        print(f"✓ Found {len(completed_files)} completed files to reprocess")
        
        if not completed_files:
            print("No completed files found to reprocess")
            return 0
        
        # Clear existing metadata in test database
        file_ids = [f['id'] for f in completed_files]
        clear_test_metadata(test_db, file_ids)
        
        # Process each file with Claude
        logger.info("Processing files with Claude 3.5 Haiku...")
        success_count = 0
        
        for i, file_info in enumerate(completed_files, 1):
            print(f"Processing {i}/{len(completed_files)}: {file_info['filename']}")
            
            try:
                # Process with Claude
                metadata = process_file_with_claude(claude_client, drive_service, file_info)
                
                # Save to test database
                save_metadata_to_db(test_db, file_info['id'], metadata)
                
                success_count += 1
                print(f"  ✓ Completed successfully")
                
            except Exception as e:
                logger.error(f"Failed to process {file_info['filename']}: {e}")
                print(f"  ✗ Failed: {e}")
                continue
        
        print(f"\n✓ Processing complete!")
        print(f"Successfully processed: {success_count}/{len(completed_files)} files")
        print(f"Results saved to: {test_db}")
        print("\nTo compare results:")
        print(f"  Original (Gemma):    sqlite3 {original_db}")
        print(f"  Claude (1-pass):     sqlite3 cloudtest.db")
        print(f"  Claude (2-pass):     sqlite3 {test_db}")
        print("\nExample comparison query:")
        print('  SELECT f.filename, m.primary_subject, m.visual_quality, m.social_media_score FROM files f JOIN metadata m ON f.id = m.file_id LIMIT 10;')
        
        return 0
        
    except Exception as e:
        logger.error(f"Test processor failed: {e}")
        print(f"ERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())