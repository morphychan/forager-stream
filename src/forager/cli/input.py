"""
CLI subcommands related to input plugins (e.g., RSS, API).
"""

import typer

app = typer.Typer(
    name="input",
    help="Run or test input plugin modules.",
    no_args_is_help=True,
)

@app.command("rss-test")
def rss_test(url: str = typer.Argument(..., help="RSS feed URL to test.")) -> None:
    """
    Simulate fetching an RSS feed and print a placeholder result.
    """
    print(f"[FAKE] Simulating RSS fetch for: {url}")
    print("Title: Example Article")
    print("Link: https://example.com/article")
    print("Published: 2024-01-01")
