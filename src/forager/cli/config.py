"""
CLI subcommands related to configuration management.
"""
from pathlib import Path
from forager.storage.sqlite import SQLiteStorage
from forager.config.config_sync import ConfigSynchronizer
import typer

app = typer.Typer(
    name="config",
    help="Configuration management operations.",
    no_args_is_help=True,
)

@app.command("sync")
def sync(
    config_path: Path = typer.Option(
        Path("config/subscriptions.yaml"),
        "--config",
        "-c",
        help="Path to subscriptions YAML file.",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Use debug mode to show detailed information during syncing.",
    ),
) -> None:
    """
    Synchronize database with configuration file (config is the source of truth).
    """
    storage = SQLiteStorage(Path("data/forager.db"))
    try:
        typer.echo(f"[INFO] Starting sync from config file {config_path} to database...")
        
        # Create synchronizer
        synchronizer = ConfigSynchronizer(config_path, storage, debug=debug)
        
        # Execute sync (disable internal summary to avoid duplicate output)
        results = synchronizer.sync_feeds(print_summary=False)
        
        # Display results
        typer.echo(f"[INFO] Sync completed:")
        typer.echo(f"  - Created: {results['created']}")
        typer.echo(f"  - Updated: {results['updated']}")
        typer.echo(f"  - Deleted: {results['deleted']}")
        typer.echo(f"  - Unchanged: {results['unchanged']}")
        
        if results['errors']:
            typer.echo(f"[WARNING] Encountered {len(results['errors'])} errors during sync:")
            for error in results['errors']:
                typer.echo(f"  - {error}")
    finally:
        storage.close() 