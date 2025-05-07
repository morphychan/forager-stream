"""
CLI subcommands related to input plugins (e.g., RSS, API).
"""
from forager.input.rss import RSSFetcher
import typer

app = typer.Typer(
    name="input",
    help="Run or test input plugin modules.",
    no_args_is_help=True,
)

@app.command("rss")
def rss(url: str = typer.Argument(..., help="RSS feed URL to fetch.")) -> None:
    """
    Fetch and print an RSS feed.
    """
    fetcher = RSSFetcher(url)
    articles = fetcher.fetch()
    print(f"[INFO] RSS feed fetched for: {url}")
    print(f"[INFO] Found {len(articles)} articles in the feed.")
    if articles:
        for article in articles:
            print(f"Title: {article['title']}")
            print(f"Link: {article['link']}")
            print(f"Published: {article['published']}")
            print("-" * 40)
    else:
        print("[WARNING] No articles found in the feed.")
