"""
CLI subcommands related to input plugins (e.g., RSS, API).
"""
from pathlib import Path
from typing import Optional
from forager.input.rss import RSSFetcher
from forager.input.rss_presenter import RSSPresenter
from forager.storage.sqlite import SQLiteStorage
from forager.config.manager import ConfigManager, ConfigError
from forager.config.config_sync import ConfigSynchronizer
import typer

app = typer.Typer(
    name="input",
    help="Run or test input plugin modules.",
    no_args_is_help=True,
)

@app.command("rss")
def rss(
    url: Optional[str] = typer.Argument(
        None, help="RSS feed URL to fetch. If omitted, load from config."
    ),
    config_path: Path = typer.Option(
        Path("config/subscriptions.yaml"),
        "--config",
        "-c",
        help="Path to subscriptions YAML file.",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    print_only: bool = typer.Option(
        False,
        "--print-only",
        "-p",
        help="Only print feed contents without storing to database.",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Use debug mode to show detailed information during fetching.",
    ),
) -> None:
    """
    Fetch and store RSS feeds.
    """
    if print_only:
        # Print-only mode
        if url:
            try:
                fetcher = RSSFetcher(url, debug=debug)
                presenter = RSSPresenter(fetcher)
                presenter.print_feed_summary()
            except Exception as e:
                typer.echo(f"[ERROR] Failed to fetch RSS feed {url}: {e}")
        else:
            # Process all feeds from config
            try:
                config_manager = ConfigManager(config_path)
                urls = config_manager.get_feed_urls()
                for url in urls:
                    try:
                        fetcher = RSSFetcher(url, debug=debug)
                        presenter = RSSPresenter(fetcher)
                        presenter.print_feed_summary()
                    except Exception as e:
                        typer.echo(f"[ERROR] Failed to fetch RSS feed {url}: {e}")
                        continue
            except ConfigError as e:
                typer.echo(f"[ERROR] {e}")
                raise typer.Exit(code=1)
    else:
        # Storage mode
        storage = SQLiteStorage(Path("data/forager.db"))
        try:
            if url:
                # Process single feed
                try:
                    fetcher = RSSFetcher(url, storage, debug=debug)
                    article_count = fetcher.process_feed(url, 3600)  # Default 1 hour interval
                    if article_count > 0:
                        typer.echo(f"[INFO] Saved {article_count} articles from {url}")
                    else:
                        typer.echo(f"[WARNING] No new articles found in {url}")
                except Exception as e:
                    typer.echo(f"[ERROR] Failed to process feed {url}: {e}")
            else:
                # Process all feeds from config
                if debug:
                    typer.echo("[INFO] Debug mode active - detailed information will be shown")
                
                # Modified to pass debug parameter
                results = RSSFetcher.process_feeds_from_config(config_path, storage, debug=debug)
                
                # Display results
                for feed_url, count in results.items():
                    if count > 0:
                        typer.echo(f"[INFO] Saved {count} articles from {feed_url}")
                    elif count == 0:
                        typer.echo(f"[WARNING] No new articles found in {feed_url}")
                    else:
                        typer.echo(f"[ERROR] Failed to process feed {feed_url}")
        finally:
            storage.close()

@app.command("sync")
def sync_config(
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
