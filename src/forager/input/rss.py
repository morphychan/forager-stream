import feedparser
from typing import List, Dict

class RSSFetcher:
    """Handles fetching and parsing RSS feeds."""

    def __init__(self, url: str):
        """
        Initialize with the URL of the RSS feed.

        Args:
            url (str): The URL of the RSS feed to fetch.
        """
        self.url = url

    def fetch(self) -> List[Dict[str, str]]:
        """
        Fetch and parse the provided RSS feed.

        Returns:
            List[Dict[str, str]]: A list of dictionaries containing
            the title, link, and published date of each article in the feed.
        """
        print(f"[INFO] Fetching RSS feed from: {self.url}")
        feed = feedparser.parse(self.url)

        if not feed.entries:
            print("[WARNING] No entries found in the feed.")
            return []

        articles = []
        for entry in feed.entries:
            article = {
                "title": entry.title,
                "link": entry.link,
                "published": entry.published,
            }
            articles.append(article)

        return articles
