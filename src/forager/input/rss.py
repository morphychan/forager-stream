import feedparser
from typing import List, Dict, Optional
from pathlib import Path
from forager.storage.sqlite import SQLiteStorage
from forager.config.manager import ConfigManager, ConfigError

class RSSFetcher:
    """Handles fetching, parsing and storing RSS feeds."""

    def __init__(self, url: str, storage: Optional[SQLiteStorage] = None):
        """
        Initialize with the URL of the RSS feed.

        Args:
            url (str): The URL of the RSS feed to fetch.
            storage (Optional[SQLiteStorage]): Storage backend for persisting feeds and articles.
        """
        self.url = url
        self.storage = storage

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
                "summary": entry.get("summary"),
                "content": entry.get("content", [{}])[0].get("value") if entry.get("content") else None
            }
            articles.append(article)

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

        # 检查 feed 是否已存在
        existing_feeds = self.storage.get_feeds()
        feed_exists = any(f["url"] == self.url for f in existing_feeds)
        
        if not feed_exists:
            # 创建新的 feed
            feed_id = self.storage.create_feed(
                category_id=self.ensure_default_category(),
                name=name,
                url=self.url,
                poll_interval=interval,
                status="active"
            )
        else:
            # 获取已存在的 feed ID
            feed_id = next(f["id"] for f in existing_feeds if f["url"] == self.url)
        
        # 获取文章
        articles = self.fetch()
        
        if articles:
            # 转换文章格式
            db_articles = []
            for article in articles:
                db_article = {
                    "title": article["title"],
                    "link": article["link"],
                    "published_at": article["published"],
                    "status": "new",
                    "summary": article.get("summary"),
                    "content": article.get("content")
                }
                db_articles.append(db_article)
            
            # 保存文章
            article_ids = self.storage.save_articles(feed_id, db_articles)
            return len(article_ids)
        return 0

    @classmethod
    def process_feeds_from_config(cls, config_path: Path, storage: SQLiteStorage) -> Dict[str, int]:
        """
        Process all feeds from config file.

        Args:
            config_path (Path): Path to the config file
            storage (SQLiteStorage): Storage backend

        Returns:
            Dict[str, int]: Dictionary mapping feed URLs to number of articles saved
        """
        config_manager = ConfigManager(config_path)
        feeds = config_manager.get_enabled_feeds()
        
        results = {}
        for feed in feeds:
            try:
                fetcher = cls(feed.url, storage)
                article_count = fetcher.process_feed(feed.name, feed.interval)
                results[feed.url] = article_count
            except Exception as e:
                # 获取 feed ID 并更新错误状态
                existing_feeds = storage.get_feeds()
                feed_id = next((f["id"] for f in existing_feeds if f["url"] == feed.url), None)
                if feed_id:
                    storage.update_feed_error(feed_id, str(e))
                results[feed.url] = -1  # 表示错误
        
        return results
