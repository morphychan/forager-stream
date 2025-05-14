"""
RSS content presentation module.

This module provides functionality for presenting RSS feed contents in various formats.
The RSSPresenter class handles the formatting and display of RSS feed data, separating
presentation logic from data fetching and storage.
"""

from typing import List, Dict, Optional
from datetime import datetime
from forager.input.rss import RSSFetcher


class RSSPresenter:
    """
    Handles the presentation of RSS feed contents.

    This class is responsible for formatting and displaying RSS feed data in various ways.
    It separates presentation logic from data fetching and storage concerns.

    Attributes:
        fetcher (RSSFetcher): The RSSFetcher instance used to fetch feed data.
    """

    def __init__(self, fetcher: RSSFetcher):
        """
        Initialize the RSSPresenter with an RSSFetcher instance.

        Args:
            fetcher (RSSFetcher): An instance of RSSFetcher to fetch feed data.
        """
        self.fetcher = fetcher

    def print_feed_summary(self, include_summary: bool = False) -> None:
        """
        Print a summary of the feed contents to the console.

        This method prints basic information about each article in the feed,
        including title, link, and publication date. Optionally includes
        article summaries if requested.

        Args:
            include_summary (bool): Whether to include article summaries in the output.
                                  Defaults to False.
        """
        articles = self.fetcher.fetch()
        if not articles:
            print("[WARNING] No articles found in the feed.")
            return

        print(f"[INFO] Found {len(articles)} articles in the feed.")
        
        # print the first article's fields
        if articles:
            print("\nAvailable feed entry fields:")
            print(", ".join(articles[0].keys()))
            print("-" * 40)
        
        for article in articles:
            self._print_article_summary(article, include_summary)

    def _print_article_summary(self, article: Dict[str, str], include_summary: bool) -> None:
        """
        Print summary information for a single article.

        Args:
            article (Dict[str, str]): The article data to print.
            include_summary (bool): Whether to include the article summary.
        """
        # print the current article's fields
        print(f"Article fields: {', '.join(article.keys())}")
        
        print(f"Title: {article['title']}")
        print(f"Link: {article['link']}")
        print(f"Published: {article['published']}")
        
        if include_summary and article.get('summary'):
            # Truncate summary if it's too long
            summary = article['summary']
            if len(summary) > 200:
                summary = summary[:200] + "..."
            print(f"Summary: {summary}")
        
        print("-" * 40)

    def print_feed_statistics(self) -> Dict[str, int]:
        """
        Print and return statistics about the feed.

        Returns:
            Dict[str, int]: A dictionary containing feed statistics.
        """
        articles = self.fetcher.fetch()
        if not articles:
            print("[WARNING] No articles found in the feed.")
            return {"total_articles": 0}

        # Calculate statistics
        stats = {
            "total_articles": len(articles),
            "articles_with_summary": sum(1 for a in articles if a.get('summary')),
            "articles_with_content": sum(1 for a in articles if a.get('content')),
        }

        # Print statistics
        print("\nFeed Statistics:")
        print(f"Total Articles: {stats['total_articles']}")
        print(f"Articles with Summary: {stats['articles_with_summary']}")
        print(f"Articles with Content: {stats['articles_with_content']}")

        return stats

    def format_article_as_markdown(self, article: Dict[str, str]) -> str:
        """
        Format a single article as markdown.

        Args:
            article (Dict[str, str]): The article data to format.

        Returns:
            str: The article formatted as markdown.
        """
        markdown = []
        markdown.append(f"# {article['title']}\n")
        markdown.append(f"Published: {article['published']}\n")
        markdown.append(f"Link: {article['link']}\n")
        
        if article.get('summary'):
            markdown.append("\n## Summary\n")
            markdown.append(article['summary'])
        
        return "\n".join(markdown)

    def export_to_markdown(self, output_path: str) -> bool:
        """
        Export the feed contents to a markdown file.

        Args:
            output_path (str): The path where the markdown file should be saved.

        Returns:
            bool: True if the export was successful, False otherwise.
        """
        try:
            articles = self.fetcher.fetch()
            if not articles:
                print("[WARNING] No articles to export.")
                return False

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"# Feed Contents\n\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n\n")
                
                for article in articles:
                    f.write(self.format_article_as_markdown(article))
                    f.write("\n\n---\n\n")

            print(f"[INFO] Successfully exported feed to {output_path}")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to export feed: {e}")
            return False 