"""
CLI subcommands related to input plugins (e.g., RSS, API).
"""
from pathlib import Path
from typing import Optional
from forager.input.rss import RSSFetcher
from forager.config.manager import ConfigManager, ConfigError
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
) -> None:
    """
    Fetch and print an RSS feed.
    """
    urls = [url] if url else []
    if not url:
        try:
            config_manager = ConfigManager(config_path)
            urls = config_manager.get_feed_urls()
        except ConfigError as e:
            typer.echo(f"[ERROR] {e}")
            raise typer.Exit(code=1)

    if not urls:
        typer.echo("[WARNING] No RSS feeds to fetch")
        raise typer.Exit(code=0)

    for url in urls:
        try:
            fetcher = RSSFetcher(url)
            articles = fetcher.fetch()
            typer.echo(f"[INFO] RSS feed fetched for: {url}")
            typer.echo(f"[INFO] Found {len(articles)} articles in the feed.")
            if articles:
                for article in articles:
                    typer.echo(f"Title: {article['title']}")
                    typer.echo(f"Link: {article['link']}")
                    typer.echo(f"Published: {article['published']}")
                    typer.echo("-" * 40)
            else:
                typer.echo("[WARNING] No articles found in the feed.")
        except Exception as e:
            typer.echo(f"[ERROR] Failed to fetch RSS feed {url}: {e}")
            continue
