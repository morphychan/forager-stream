"""
CLI subcommands related to input plugins (e.g., RSS, API).
"""
from pathlib import Path
from typing import Optional
from forager.input.rss import RSSFetcher
from forager.storage.sqlite import SQLiteStorage
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
    print_only: bool = typer.Option(
        False,
        "--print-only",
        "-p",
        help="Only print feed contents without storing to database.",
    ),
) -> None:
    """
    Fetch and store RSS feeds.
    """
    if print_only:
        # 只打印模式
        if url:
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
                        if article.get('summary'):
                            typer.echo(f"Summary: {article['summary']}")
                        typer.echo("-" * 40)
                else:
                    typer.echo("[WARNING] No articles found in the feed.")
            except Exception as e:
                typer.echo(f"[ERROR] Failed to fetch RSS feed {url}: {e}")
        else:
            # 从配置文件读取 URLs
            try:
                config_manager = ConfigManager(config_path)
                urls = config_manager.get_feed_urls()
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
                                if article.get('summary'):
                                    typer.echo(f"Summary: {article['summary']}")
                                typer.echo("-" * 40)
                        else:
                            typer.echo("[WARNING] No articles found in the feed.")
                    except Exception as e:
                        typer.echo(f"[ERROR] Failed to fetch RSS feed {url}: {e}")
                        continue
            except ConfigError as e:
                typer.echo(f"[ERROR] {e}")
                raise typer.Exit(code=1)
    else:
        # 存储模式
        storage = SQLiteStorage(Path("data/forager.db"))
        try:
            if url:
                # 处理单个 feed
                try:
                    fetcher = RSSFetcher(url, storage)
                    article_count = fetcher.process_feed(url, 3600)  # 默认1小时间隔
                    if article_count > 0:
                        typer.echo(f"[INFO] Saved {article_count} articles from {url}")
                    else:
                        typer.echo(f"[WARNING] No new articles found in {url}")
                except Exception as e:
                    typer.echo(f"[ERROR] Failed to process feed {url}: {e}")
            else:
                # 处理配置文件中的所有 feeds
                results = RSSFetcher.process_feeds_from_config(config_path, storage)
                
                # 显示结果
                for feed_url, count in results.items():
                    if count > 0:
                        typer.echo(f"[INFO] Saved {count} articles from {feed_url}")
                    elif count == 0:
                        typer.echo(f"[WARNING] No new articles found in {feed_url}")
                    else:
                        typer.echo(f"[ERROR] Failed to process feed {feed_url}")
        finally:
            storage.close()
