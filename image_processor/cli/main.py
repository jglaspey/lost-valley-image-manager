"""Main CLI interface for Google Drive Image Processor."""

import click
import logging
from pathlib import Path
import sys

from ..core.config import Config
from ..database import DatabaseConnection, FileRepository
from ..google_drive import GoogleDriveAuth, GoogleDriveService
from ..vision import VisionAnalysisService
from ..utils.logging import setup_logging

logger = logging.getLogger(__name__)


@click.group()
@click.option('--config', '-c', 'config_path', 
              default='config/config.yaml',
              help='Path to configuration file')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, config_path, verbose):
    """Google Drive Image Processor CLI."""
    # Setup logging
    log_level = logging.DEBUG if verbose else logging.INFO
    setup_logging(log_level)
    
    # Store config in context
    ctx.ensure_object(dict)
    ctx.obj['config_path'] = config_path
    ctx.obj['verbose'] = verbose


def load_config(ctx, check_credentials=True):
    """Load configuration helper."""
    if 'config' not in ctx.obj:
        try:
            config = Config.from_file(ctx.obj['config_path'])
            config.validate(check_credentials=check_credentials)
            ctx.obj['config'] = config
        except Exception as e:
            click.echo(f"Error loading configuration: {e}", err=True)
            sys.exit(1)
    return ctx.obj['config']


@cli.command()
@click.pass_context
def test_auth(ctx):
    """Test Google Drive authentication."""
    config = load_config(ctx, check_credentials=True)
    
    try:
        click.echo("Testing Google Drive authentication...")
        auth = GoogleDriveAuth(config.google_drive.credentials_path)
        service = auth.get_service()
        
        # Test by getting user info
        about = service.about().get(fields="user").execute()
        user = about.get('user', {})
        
        click.echo(f"✓ Successfully authenticated as: {user.get('displayName', 'Unknown')}")
        click.echo(f"  Email: {user.get('emailAddress', 'Unknown')}")
        
    except Exception as e:
        click.echo(f"✗ Authentication failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--folder-id', '-f', help='Google Drive folder ID to count files in')
@click.pass_context
def count_files(ctx, folder_id):
    """Count media files in Google Drive."""
    config = load_config(ctx, check_credentials=True)
    
    try:
        click.echo("Connecting to Google Drive...")
        auth = GoogleDriveAuth(config.google_drive.credentials_path)
        drive_service = GoogleDriveService(config.google_drive, auth)
        
        click.echo("Counting files...")
        counts = drive_service.get_file_count(folder_id)
        
        click.echo("\nFile counts:")
        click.echo(f"  Total files: {counts['total']}")
        click.echo(f"  Images: {counts['images']}")
        click.echo(f"  Videos: {counts['videos']}")
        click.echo(f"  Other: {counts['other']}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--folder-id', '-f', help='Google Drive folder ID to discover files in')
@click.option('--limit', '-l', type=int, help='Limit number of files to discover')
@click.pass_context
def discover(ctx, folder_id, limit):
    """Discover media files in Google Drive and add to database."""
    config = load_config(ctx, check_credentials=True)
    
    try:
        # Initialize services
        click.echo("Initializing services...")
        auth = GoogleDriveAuth(config.google_drive.credentials_path)
        drive_service = GoogleDriveService(config.google_drive, auth)
        
        db_connection = DatabaseConnection(config.database)
        file_repo = FileRepository(db_connection)
        
        # Start discovery
        click.echo("Starting file discovery...")
        discovered = 0
        skipped = 0
        
        for media_file in drive_service.discover_media_files(folder_id):
            if limit and discovered >= limit:
                break
            
            # Check if file already exists
            if file_repo.exists(media_file.drive_file_id):
                skipped += 1
                if skipped % 10 == 0:
                    click.echo(f"  Skipped {skipped} existing files...")
                continue
            
            # Add to database
            file_id = file_repo.create(media_file)
            discovered += 1
            
            if discovered % 10 == 0:
                click.echo(f"  Discovered {discovered} new files...")
        
        click.echo(f"\n✓ Discovery complete!")
        click.echo(f"  New files: {discovered}")
        click.echo(f"  Skipped (existing): {skipped}")
        
        # Show database stats
        stats = file_repo.get_processing_stats()
        click.echo(f"\nDatabase statistics:")
        for status, count in stats.items():
            click.echo(f"  {status}: {count}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        logger.exception("Discovery failed")
        sys.exit(1)


@cli.command()
@click.pass_context
def stats(ctx):
    """Show processing statistics."""
    config = load_config(ctx, check_credentials=False)
    
    try:
        db_connection = DatabaseConnection(config.database)
        file_repo = FileRepository(db_connection)
        
        stats = file_repo.get_processing_stats()
        
        # Get detailed stats by file type
        detailed_stats = file_repo.get_detailed_stats()
        
        click.echo("=== File Type Summary ===")
        click.echo(f"Total files: {detailed_stats['total']}")
        click.echo(f"Images: {detailed_stats['images']}")
        click.echo(f"Videos: {detailed_stats['videos']}")
        
        click.echo("\n=== Image Processing Status ===")
        click.echo(f"Completed: {detailed_stats['images_completed']}")
        click.echo(f"Pending: {detailed_stats['images_pending']}")
        click.echo(f"Failed: {detailed_stats['images_failed']}")
        
        if detailed_stats['images_failed'] > 0:
            click.echo("\n⚠️  Failed images need attention - these are actual processing errors")
        
        if detailed_stats['images_pending'] > 0:
            click.echo(f"\n▶️  Ready to process {detailed_stats['images_pending']} pending images")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--file-id', type=int, required=True, help='Database ID of file to show')
@click.pass_context
def show_file(ctx, file_id):
    """Show detailed information about a specific file."""
    config = load_config(ctx, check_credentials=False)
    
    try:
        from ..database import MetadataRepository, ActivityTagRepository
        
        db_connection = DatabaseConnection(config.database)
        file_repo = FileRepository(db_connection)
        metadata_repo = MetadataRepository(db_connection)
        tag_repo = ActivityTagRepository(db_connection)
        
        # Get file with URLs
        file_info = file_repo.get_file_with_drive_url(file_id)
        if not file_info:
            click.echo(f"File with ID {file_id} not found", err=True)
            sys.exit(1)
        
        # Get metadata if available
        metadata = metadata_repo.get_by_file_id(file_id)
        
        # Display file info
        click.echo(f"=== File Information ===")
        click.echo(f"ID: {file_info['id']}")
        click.echo(f"Filename: {file_info['filename']}")
        click.echo(f"Path: {file_info['file_path']}")
        click.echo(f"Type: {file_info['mime_type']}")
        click.echo(f"Status: {file_info['processing_status']}")
        click.echo(f"Google Drive URL: {file_info['drive_url']}")
        click.echo(f"Direct Download: {file_info['drive_download_url']}")
        
        if metadata:
            click.echo(f"\n=== Analysis Results ===")
            click.echo(f"Subject: {metadata.primary_subject}")
            click.echo(f"Visual Quality: {metadata.visual_quality}/5")
            click.echo(f"Has People: {metadata.has_people} ({metadata.people_count})")
            click.echo(f"Indoor/Outdoor: {'Indoor' if metadata.is_indoor else 'Outdoor'}")
            click.echo(f"Social Media Score: {metadata.social_media_score}/5 - {metadata.social_media_reason}")
            click.echo(f"Marketing Score: {metadata.marketing_score}/5 - {metadata.marketing_use}")
            
            if metadata.activity_tags:
                click.echo(f"Activity Tags: {', '.join(metadata.activity_tags)}")
            
            if metadata.season:
                click.echo(f"Season: {metadata.season}")
            
            if metadata.notes:
                click.echo(f"\nContext Notes:")
                click.echo(f"{metadata.notes}")
        else:
            click.echo(f"\n=== Analysis Results ===")
            click.echo("Not yet processed")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def init_db(ctx):
    """Initialize the database schema."""
    config = load_config(ctx, check_credentials=False)
    
    try:
        click.echo("Initializing database...")
        db_connection = DatabaseConnection(config.database)
        click.echo(f"✓ Database initialized at: {config.database.path}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def test_vision(ctx):
    """Test vision model connection."""
    config = load_config(ctx, check_credentials=False)
    
    try:
        click.echo("Testing vision model connection...")
        vision_service = VisionAnalysisService(config)
        
        if vision_service.test_vision_connection():
            click.echo("✓ Vision model connection successful")
        else:
            click.echo("✗ Vision model connection failed", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--limit', '-l', type=int, help='Limit number of files to process')
@click.option('--file-id', type=int, help='Process specific file by database ID')
@click.pass_context
def process(ctx, limit, file_id):
    """Process pending files with vision analysis."""
    config = load_config(ctx, check_credentials=True)
    
    try:
        click.echo("Initializing vision analysis service...")
        vision_service = VisionAnalysisService(config)
        
        if file_id:
            # Process specific file
            click.echo(f"Processing file ID {file_id}...")
            success = vision_service.process_file(file_id)
            
            if success:
                click.echo("✓ File processed successfully")
            else:
                click.echo("✗ File processing failed", err=True)
                sys.exit(1)
        else:
            # Process pending files
            click.echo("Processing pending files...")
            results = vision_service.process_pending_files(limit)
            
            click.echo(f"\nProcessing complete!")
            click.echo(f"  Processed: {results['processed']}")
            click.echo(f"  Failed: {results['failed']}")
            
            # Show updated stats
            stats = vision_service.get_processing_stats()
            click.echo(f"\nDatabase statistics:")
            for status, count in sorted(stats.items()):
                click.echo(f"  {status}: {count}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        logger.exception("Processing failed")
        sys.exit(1)


@cli.command()
@click.option('--limit', '-l', type=int, help='Limit number of files to reprocess')
@click.pass_context
def reprocess_failed(ctx, limit):
    """Reprocess files that previously failed."""
    config = load_config(ctx, check_credentials=True)
    
    try:
        click.echo("Initializing vision analysis service...")
        vision_service = VisionAnalysisService(config)
        
        click.echo("Reprocessing failed files...")
        results = vision_service.reprocess_failed_files(limit)
        
        click.echo(f"\nReprocessing complete!")
        click.echo(f"  Processed: {results['processed']}")
        click.echo(f"  Failed: {results['failed']}")
        
        # Show updated stats
        stats = vision_service.get_processing_stats()
        click.echo(f"\nDatabase statistics:")
        for status, count in sorted(stats.items()):
            click.echo(f"  {status}: {count}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        logger.exception("Reprocessing failed")
        sys.exit(1)


if __name__ == '__main__':
    cli()