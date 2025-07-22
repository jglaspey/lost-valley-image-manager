"""Main CLI interface for Google Drive Image Processor."""

import click
import logging
from pathlib import Path
import sys

from ..core.config import Config
from ..database import DatabaseConnection, FileRepository
from ..google_drive import GoogleDriveAuth, GoogleDriveService
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
        
        click.echo("Processing statistics:")
        total = sum(stats.values())
        
        for status, count in sorted(stats.items()):
            percentage = (count / total * 100) if total > 0 else 0
            click.echo(f"  {status}: {count} ({percentage:.1f}%)")
        
        click.echo(f"\nTotal files: {total}")
        
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


if __name__ == '__main__':
    cli()