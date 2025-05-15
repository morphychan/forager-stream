from email.utils import parsedate_to_datetime
import feedparser
from typing import List, Dict, Optional
from pathlib import Path
from forager.storage.sqlite import SQLiteStorage
from forager.config.manager import ConfigManager, ConfigError
from forager.input.preprocessor import URLPreprocessor
from forager.utils.feed_parser_adapter import FeedParserAdapter

class RSSFetcher:
    """Handles fetching, parsing and storing RSS feeds."""

    def __init__(self, 
                 url: str, 
                 storage: Optional[SQLiteStorage] = None, 
                 feed_parser: Optional[FeedParserAdapter] = None, 
                 user_agent: Optional[str] = None):
        """
        Initialize with the URL of the RSS feed.

        Args:
            url (str): The URL of the RSS feed to fetch.
            storage (Optional[SQLiteStorage]): Storage backend for persisting feeds and articles.
            feed_parser (Optional[FeedParserAdapter]): Feed parser with anti-scraping capabilities.
            user_agent (Optional[str]): Specific User-Agent to use for creating a new feed_parser if one isn't provided.
        """
        self.url = url
        self.storage = storage
        # if feed_parser is provided, use it, otherwise create a new one with the user_agent
        self.feed_parser = feed_parser or FeedParserAdapter.create_with_defaults(user_agent=user_agent)

    def fetch(self) -> List[Dict[str, str]]:
        """
        Fetch and parse the provided RSS feed.

        Returns:
            List[Dict[str, str]]: A list of dictionaries containing
            the title, link, and published date of each article in the feed.
        """
        print(f"[INFO] Fetching RSS feed from: {self.url}")
        
        # use the feed parser to parse the feed
        feed = self.feed_parser.parse(self.url)

        if not feed.entries:
            print("[WARNING] No entries found in the feed.")
            return []

        articles = []
        for entry in feed.entries:
            article = {
                "title": entry.title,
                "link": entry.link,
                "published": entry.published,
                "summary": entry.get("summary"),
                "content": entry.get("content", [{}])[0].get("value") if entry.get("content") else None
            }
            articles.append(article)

        # process all articles
        articles = URLPreprocessor.process_articles(articles)

        return articles

    def ensure_default_category(self) -> int:
        """Ensure default category exists and return its ID."""
        if not self.storage:
            raise ValueError("Storage backend not initialized")
            
        categories = self.storage.get_categories()
        for category in categories:
            if category["name"] == "Default":
                return category["id"]
        return self.storage.create_category("Default")

    def process_feed(self, name: str, interval: int) -> int:
        """
        Process a single feed: fetch and store articles.

        Args:
            name (str): Name of the feed
            interval (int): Poll interval in seconds

        Returns:
            int: Number of articles saved
        """
        if not self.storage:
            raise ValueError("Storage backend not initialized")

        # check if the feed already exists  
        existing_feeds = self.storage.get_feeds()
        feed_exists = any(f["url"] == self.url for f in existing_feeds)
        
        if not feed_exists:
            # create a new feed
            feed_id = self.storage.create_feed(
                category_id=self.ensure_default_category(),
                name=name,
                url=self.url,
                poll_interval=interval,
                status="active"
            )
        else:
            # get the existing feed ID
            feed_id = next(f["id"] for f in existing_feeds if f["url"] == self.url)
        
        # fetch articles
        articles = self.fetch()
        
        if articles:
            # get existing articles
            existing_articles = self.storage.get_articles(feed_id=feed_id)
            existing_article_links = {article["link"] for article in existing_articles}

            # get new articles
            new_articles = [article for article in articles if article["link"] not in existing_article_links]
            db_articles = []
            for article in new_articles:
                db_article = {
                    "title": article["title"],
                    "link": article["link"],
                    "published_at": parsedate_to_datetime(article["published"]),
                    "status": "new"
                }
                db_articles.append(db_article)
            
            # save articles
            article_ids = self.storage.save_articles(feed_id, db_articles)
            if new_articles:
                print(f"[INFO] Found {len(new_articles)} new articles out of {len(articles)} total")
            else:
                print(f"[INFO] No new articles found out of {len(articles)} total")
            return len(article_ids)
        return 0

    @classmethod
    def process_feeds_from_config(cls, config_path: Path, storage: SQLiteStorage, user_agent: Optional[str] = None) -> Dict[str, int]:
        """
        Process all feeds from config file.

        Args:
            config_path (Path): Path to the config file
            storage (SQLiteStorage): Storage backend
            user_agent (Optional[str]): Custom User-Agent to use for all requests

        Returns:
            Dict[str, int]: Dictionary mapping feed URLs to number of articles saved
        """
        config_manager = ConfigManager(config_path)
        feeds = config_manager.get_enabled_feeds()
        
        # create a shared feed parser to reuse the HTTP session
        feed_parser = FeedParserAdapter.create_with_defaults(user_agent=user_agent)
        
        results = {}
        for feed in feeds:
            try:
                fetcher = cls(feed.url, storage, feed_parser=feed_parser)
                article_count = fetcher.process_feed(feed.name, feed.interval)
                results[feed.url] = article_count
            except Exception as e:
                # get the feed ID and update the error status
                existing_feeds = storage.get_feeds()
                feed_id = next((f["id"] for f in existing_feeds if f["url"] == feed.url), None)
                if feed_id:
                    storage.update_feed_error(feed_id, str(e))
                results[feed.url] = -1  # -1 means error
        
        return results
