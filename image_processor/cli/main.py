"""Main CLI interface for Google Drive Image Processor."""

import click
import logging
from pathlib import Path
import sys
import os

from ..core.config import Config
from ..database import DatabaseConnection, FileRepository
from ..google_drive import GoogleDriveAuth, GoogleDriveService
from ..vision import VisionAnalysisService
from ..vision.together_client import TogetherVisionClient
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
    # Load environment variables from .env if present (without requiring python-dotenv)
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv()
    except Exception:
        env_path = Path('.env')
        if env_path.exists():
            try:
                for raw in env_path.read_text().splitlines():
                    line = raw.strip()
                    if not line or line.startswith('#') or '=' not in line:
                        continue
                    key, val = line.split('=', 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    os.environ.setdefault(key, val)
            except Exception:
                pass
    
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
@click.option('--limit', type=int, default=10, help='How many most-recent completed files to list')
@click.pass_context
def list_recent(ctx, limit):
    """List recently processed files with their database IDs."""
    config = load_config(ctx, check_credentials=False)
    try:
        db_connection = DatabaseConnection(config.database)
        with db_connection.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, filename, processed_at
                FROM files
                WHERE processing_status='completed'
                ORDER BY processed_at DESC
                LIMIT ?
                """,
                (limit,)
            )
            rows = cur.fetchall()
            if not rows:
                click.echo("No completed files yet.")
                return
            click.echo("ID\tProcessed At\tFilename")
            for row in rows:
                click.echo(f"{row[0]}\t{row[2]}\t{row[1]}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--limit', type=int, default=10, help='How many most-recent completed files to export')
@click.option('--output', type=click.Path(), default='llm_results.json', help='Path to write JSON results')
@click.pass_context
def export_results(ctx, limit, output):
    """Export recent LLM results to a JSON file (file info + extracted metadata)."""
    import json as _json
    from pathlib import Path as _P
    config = load_config(ctx, check_credentials=False)
    try:
        db = DatabaseConnection(config.database)
        file_repo = FileRepository(db)
        from ..database import MetadataRepository, ActivityTagRepository
        metadata_repo = MetadataRepository(db)
        tag_repo = ActivityTagRepository(db)

        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, filename, drive_file_id, file_path, mime_type, created_date, modified_date,
                       width, height, creator, description, processed_at
                FROM files
                WHERE processing_status='completed'
                ORDER BY processed_at DESC
                LIMIT ?
                """,
                (limit,)
            )
            rows = cur.fetchall()

        results = []
        for row in rows:
            file_id = row[0]
            meta = metadata_repo.get_by_file_id(file_id)
            tags = tag_repo.get_tags(file_id)
            results.append({
                'file': {
                    'id': file_id,
                    'filename': row[1],
                    'drive_file_id': row[2],
                    'path': row[3],
                    'mime_type': row[4],
                    'created_date': str(row[5]),
                    'modified_date': str(row[6]),
                    'width': row[7],
                    'height': row[8],
                    'creator': row[9],
                    'description': row[10],
                    'processed_at': str(row[11]),
                },
                'metadata': None if not meta else {
                    'primary_subject': meta.primary_subject,
                    'visual_quality': meta.visual_quality,
                    'has_people': meta.has_people,
                    'people_count': meta.people_count,
                    'is_indoor': meta.is_indoor,
                    'social_media_score': meta.social_media_score,
                    'social_media_reason': meta.social_media_reason,
                    'marketing_score': meta.marketing_score,
                    'marketing_use': meta.marketing_use,
                    'activity_tags': tags,
                    'season': meta.season,
                    'time_of_day': meta.time_of_day,
                    'mood_energy': meta.mood_energy,
                    'color_palette': meta.color_palette,
                    'file_path_notes': meta.notes,
                    'extracted_at': str(meta.extracted_at),
                }
            })

        _P(output).write_text(_json.dumps(results, indent=2))
        click.echo(f"✓ Exported {len(results)} records to {output}")
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
@click.option('--ab-compare', is_flag=True, help='Run A/B across two Together models and export JSON for comparison')
@click.option('--model-a', type=str, default='meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo', help='Together model A')
@click.option('--model-b', type=str, default='Qwen/Qwen2.5-VL-72B-Instruct', help='Together model B')
@click.option('--export', type=click.Path(), default='together_ab_results.json', help='Output JSON file for A/B')
@click.pass_context
def process(ctx, limit, file_id, ab_compare, model_a, model_b, export):
    """Process pending files with vision analysis."""
    config = load_config(ctx, check_credentials=True)
    
    try:
        click.echo("Initializing vision analysis service...")
        vision_service = VisionAnalysisService(config)
        
        if ab_compare:
            # A/B evaluate N images using Together AI on two models; export merged JSON
            from ..database import FileRepository
            config = load_config(ctx, check_credentials=True)
            db = DatabaseConnection(config.database)
            file_repo = FileRepository(db)
            # Fetch a larger window then take the first N images to avoid selecting videos
            window = max(200, (limit or 10) * 5)
            candidates = file_repo.get_pending_files(window)
            files = [f for f in candidates if str(f.mime_type).startswith('image/')][: (limit or 10)]
            tvc = TogetherVisionClient(max_tokens=config.vision_model.max_tokens, max_retries=config.vision_model.max_retries)

            results = []
            import time as _t
            for f in files:
                if not f.mime_type.startswith('image/'):
                    continue
                image_bytes = GoogleDriveService(config.google_drive, GoogleDriveAuth(config.google_drive.credentials_path)).download_file(f.drive_file_id)
                a = None
                b = None
                a_err = None
                b_err = None
                try:
                    a = tvc.analyze_image(image_bytes, f.filename, f.file_path, model_a)
                except Exception as e:
                    a_err = str(e)
                # small delay to avoid hammering endpoint
                _t.sleep(0.5)
                try:
                    b = tvc.analyze_image(image_bytes, f.filename, f.file_path, model_b)
                except Exception as e:
                    b_err = str(e)
                results.append({
                    'file': {
                        'id': f.id,
                        'drive_file_id': f.drive_file_id,
                        'filename': f.filename,
                        'path': f.file_path
                    },
                    'model_a': model_a,
                    'result_a': a,
                    'error_a': a_err,
                    'model_b': model_b,
                    'result_b': b,
                    'error_b': b_err
                })
            import json
            from pathlib import Path as _P
            _P(export).write_text(json.dumps(results, indent=2))
            click.echo(f"✓ Wrote A/B results for {len(results)} images to {export}")
            return

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


@cli.command()
@click.pass_context
def repair_schema(ctx):
    """Repair database schema by adding any missing columns/tables for v4."""
    config = load_config(ctx, check_credentials=False)

    try:
        db_connection = DatabaseConnection(config.database)
        with db_connection.get_connection() as conn:
            cur = conn.cursor()

            # Ensure files table has required columns
            cur.execute("PRAGMA table_info(files)")
            cols = {row[1] for row in cur.fetchall()}
            added = []

            if 'width' not in cols:
                cur.execute("ALTER TABLE files ADD COLUMN width INTEGER")
                added.append('width')
            if 'height' not in cols:
                cur.execute("ALTER TABLE files ADD COLUMN height INTEGER")
                added.append('height')
            if 'creator' not in cols:
                cur.execute("ALTER TABLE files ADD COLUMN creator TEXT")
                added.append('creator')
            if 'description' not in cols:
                cur.execute("ALTER TABLE files ADD COLUMN description TEXT")
                added.append('description')

            # Ensure metadata_versions table exists
            cur.executescript(
                """
                CREATE TABLE IF NOT EXISTS metadata_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
                    version INTEGER NOT NULL,
                    data_json TEXT NOT NULL,
                    edited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    edited_by TEXT,
                    UNIQUE(file_id, version)
                );
                CREATE INDEX IF NOT EXISTS idx_versions_file_id ON metadata_versions(file_id);
                """
            )

            # Ensure metadata table has file_path_notes column (migration from notes)
            cur.execute("PRAGMA table_info(metadata)")
            mcols = {row[1] for row in cur.fetchall()}
            if 'file_path_notes' not in mcols:
                cur.execute("ALTER TABLE metadata ADD COLUMN file_path_notes TEXT")
                # Backfill from legacy 'notes' if present
                if 'notes' in mcols:
                    try:
                        cur.execute("UPDATE metadata SET file_path_notes = COALESCE(file_path_notes, notes)")
                    except Exception:
                        pass

            # Ensure schema_version table exists and record v4
            cur.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY, applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
            cur.execute("INSERT OR IGNORE INTO schema_version (version) VALUES (?)", (4,))

            msg = "Schema repair complete. Added: " + (", ".join(added) if added else "nothing")
            click.echo(msg)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        logger.exception("Schema repair failed")
        sys.exit(1)


@cli.command()
@click.option('--include-videos', is_flag=True, help='Also reset non-image files (videos/others).')
@click.pass_context
def reset_status(ctx, include_videos):
    """Reset processing status to pending for files (images by default)."""
    config = load_config(ctx, check_credentials=False)

    try:
        db_connection = DatabaseConnection(config.database)
        with db_connection.get_connection() as conn:
            cur = conn.cursor()
            if include_videos:
                cur.execute("UPDATE files SET processing_status='pending', processed_at=NULL, error_message=NULL")
                updated = cur.rowcount
            else:
                cur.execute("UPDATE files SET processing_status='pending', processed_at=NULL, error_message=NULL WHERE mime_type LIKE 'image%'")
                updated = cur.rowcount
        click.echo(f"Reset processing status to 'pending' for {updated} files.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        logger.exception("Reset status failed")
        sys.exit(1)

@cli.command()
@click.option('--batch-size', type=int, default=100, help='Number of files per backfill batch')
@click.option('--resume-from-id', type=int, default=0, help='Resume backfill after this file id')
@click.option('--limit', type=int, default=0, help='Stop after updating this many files (0 = no limit)')
@click.pass_context
def backfill_drive_metadata(ctx, batch_size, resume_from_id, limit):
    """Backfill missing creator/description/dimensions from Google Drive for existing files."""
    config = load_config(ctx, check_credentials=True)

    try:
        click.echo("Initializing Drive backfill...")
        auth = GoogleDriveAuth(config.google_drive.credentials_path)
        drive_service = GoogleDriveService(config.google_drive, auth)

        db_connection = DatabaseConnection(config.database)
        file_repo = FileRepository(db_connection)

        updated = 0
        last_id = resume_from_id

        while True:
            batch = file_repo.get_missing_drive_fields_batch(last_id=last_id, batch_size=batch_size)
            if not batch:
                break

            click.echo(f"Processing batch starting after id {last_id} (size={len(batch)})...")

            for media_file in batch:
                try:
                    # Fetch fresh file info from Drive
                    info = drive_service._get_file_info(media_file.drive_file_id)
                    if not info:
                        continue

                    # Build derived fields similar to discover path
                    # Creator
                    creator = None
                    owners = (info.get('owners') or []) if isinstance(info.get('owners'), list) else []
                    if owners:
                        owner0 = owners[0]
                        creator = owner0.get('displayName') or owner0.get('emailAddress')
                    if not creator:
                        last_user = info.get('lastModifyingUser') or {}
                        creator = last_user.get('displayName') or last_user.get('emailAddress')

                    description = info.get('description')

                    # Dimensions
                    width = None
                    height = None
                    img_meta = info.get('imageMediaMetadata') or {}
                    vid_meta = info.get('videoMediaMetadata') or {}
                    width = img_meta.get('width') or vid_meta.get('width')
                    height = img_meta.get('height') or vid_meta.get('height')
                    try:
                        width = int(width) if width is not None else None
                        height = int(height) if height is not None else None
                    except Exception:
                        width = None if width is None else width
                        height = None if height is None else height

                    # Update DB (only fill missing using COALESCE inside repo)
                    file_repo.update_drive_metadata(media_file.id, creator, description, width, height)

                    updated += 1
                    last_id = media_file.id

                    if limit and updated >= limit:
                        click.echo(f"Reached limit {limit}, stopping.")
                        click.echo(f"Updated {updated} files. Last processed id: {last_id}")
                        return

                except Exception as e:
                    logger.warning(f"Backfill error for file id {media_file.id}: {e}")
                    last_id = media_file.id
                    continue

        click.echo(f"Backfill complete. Updated {updated} files. Last processed id: {last_id}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        logger.exception("Backfill failed")
        sys.exit(1)

if __name__ == '__main__':
    cli()