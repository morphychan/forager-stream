from email.utils import parsedate_to_datetime
import feedparser
from typing import List, Dict, Optional
from pathlib import Path
import datetime
from forager.storage.sqlite import SQLiteStorage
from forager.config.manager import ConfigManager, ConfigError
from forager.input.preprocessor import URLPreprocessor
from forager.utils.feed_parser_adapter import FeedParserAdapter
from forager.utils.date_utils import parse_date_flexible

class RSSFetcher:
    """Handles fetching, parsing and storing RSS feeds."""

    def __init__(self, 
                 url: str, 
                 storage: Optional[SQLiteStorage] = None, 
                 feed_parser: Optional[FeedParserAdapter] = None, 
                 user_agent: Optional[str] = None,
                 debug: bool = False):
        """
        Initialize with the URL of the RSS feed.

        Args:
            url (str): The URL of the RSS feed to fetch.
            storage (Optional[SQLiteStorage]): Storage backend for persisting feeds and articles.
            feed_parser (Optional[FeedParserAdapter]): Feed parser with anti-scraping capabilities.
            user_agent (Optional[str]): Specific User-Agent to use for creating a new feed_parser if one isn't provided.
            debug (bool): Whether to use debug mode for fetching.
        """
        self.url = url
        self.storage = storage
        # if feed_parser is provided, use it, otherwise create a new one with the user_agent
        self.feed_parser = feed_parser or FeedParserAdapter.create_with_defaults(user_agent=user_agent)
        self.debug = debug

    def fetch_direct(self, include_details: bool = False) -> List[Dict[str, str]]:
        """
        Fetch and parse the provided RSS feed directly using feedparser without anti-scraping.
        Useful for debugging or when anti-scraping measures are not needed.

        Args:
            include_details (bool): Whether to include summary and content in the results. Defaults to False.

        Returns:
            List[Dict[str, str]]: A list of dictionaries containing
            the title, link, and published date of each article in the feed.
        """
        print(f"[DEBUG] Directly fetching RSS feed from: {self.url}")
        
        # Use feedparser directly without anti-scraping
        feed = feedparser.parse(self.url)

        if not feed.entries:
            print("[WARNING] No entries found in the feed.")
            return []

        articles = []
        for entry in feed.entries:
            article = {
                "title": entry.title,
                "link": entry.link,
                "published": entry.published
            }
            
            # Only include summary and content if requested
            if include_details:
                article["summary"] = entry.get("summary")
                article["content"] = entry.get("content", [{}])[0].get("value") if entry.get("content") else None
            
            articles.append(article)

        # process all articles
        articles = URLPreprocessor.process_articles(articles)

        return articles

    def fetch_direct_debug(self, include_details: bool = False) -> List[Dict[str, str]]:
        """
        Like fetch_direct, but with detailed debug output to the console.
        """
        print(f"[DEBUG] Directly fetching RSS feed from: {self.url}")
        
        feed = feedparser.parse(self.url)
        print(f"[DEBUG] bozo flag: {feed.bozo}")
        if feed.bozo:
            print(f"[DEBUG] bozo_exception: {feed.bozo_exception!r}")
        headers = getattr(feed, 'headers', None)
        if headers:
            print(f"[DEBUG] Content-Type: {headers.get('content-type')}")
        
        if not feed.entries:
            print("[WARNING] No entries found in the feed.")
            return []

        print(f"[DEBUG] Found {len(feed.entries)} entries; showing first 3:")
        for entry in feed.entries[:3]:
            print(f"  ▶ title: {entry.get('title')!r}")
            print(f"    link: {entry.get('link')}")
            print(f"    published: {entry.get('published', 'N/A')}")
            if include_details:
                print(f"    summary: {entry.get('summary')!r}")
                content = entry.get("content", [{}])
                content_value = content[0].get('value') if content else 'N/A'
                print(f"    content: {content_value!r}")

        articles = []
        for entry in feed.entries:
            article = {
                "title": entry.title,
                "link": entry.link,
                "published": entry.published
            }
            if include_details:
                article["summary"] = entry.get("summary")
                article["content"] = (
                    entry.get("content", [{}])[0].get("value")
                    if entry.get("content") else None
                )
            articles.append(article)

        return URLPreprocessor.process_articles(articles)

    def fetch_with_anti_scraping(self, include_details: bool = False) -> List[Dict[str, str]]:
        """
        Fetch and parse the provided RSS feed with anti-scraping measures.

        Args:
            include_details (bool): Whether to include summary and content in the results. Defaults to False.

        Returns:
            List[Dict[str, str]]: A list of dictionaries containing
            the title, link, and published date of each article in the feed.
        """
        print(f"[INFO] Fetching RSS feed with anti-scraping from: {self.url}")
        
        # use the feed parser to parse the feed
        try:
            if self.debug:
                print(f"[DEBUG] Using feed_parser with anti-scraping for: {self.url}")
            feed = self.feed_parser.parse(self.url, debug=self.debug)
            
            if not feed.entries:
                print("[WARNING] No entries found in the feed.")
                return []
            
            if self.debug:
                print(f"[DEBUG] Processing {len(feed.entries)} entries from feed")
            
            articles = []
            for entry in feed.entries:
                try:
                    if self.debug and hasattr(entry, 'title') and hasattr(entry, 'link'):
                        print(f"[DEBUG] Processing entry: {entry.title[:50]}... ({entry.link})")
                    
                    article = {
                        "title": entry.title,
                        "link": entry.link,
                        "published": entry.published
                    }
                    
                    # Only include summary and content if requested
                    if include_details:
                        article["summary"] = entry.get("summary")
                        article["content"] = entry.get("content", [{}])[0].get("value") if entry.get("content") else None
                    
                    articles.append(article)
                except Exception as e:
                    if self.debug:
                        print(f"[DEBUG] Error processing entry: {str(e)}")
                        if hasattr(entry, 'link'):
                            print(f"[DEBUG] Problem entry link: {entry.link}")
            
            # process all articles
            if self.debug:
                print(f"[DEBUG] Preprocessing {len(articles)} articles with URLPreprocessor")
            articles = URLPreprocessor.process_articles(articles)
            
            return articles
        except Exception as e:
            print(f"[ERROR] Failed to fetch feed with anti-scraping: {str(e)}")
            if self.debug:
                import traceback
                print(f"[DEBUG] Error traceback:\n{traceback.format_exc()}")
            return []

    def fetch(self, include_details: bool = False) -> List[Dict[str, str]]:
        """
        Fetch and parse the provided RSS feed using anti-scraping measures.
        This is the default method that should be used in production.

        Args:
            include_details (bool): Whether to include summary and content in the results. Defaults to False.

        Returns:
            List[Dict[str, str]]: A list of dictionaries containing
            the title, link, and published date of each article in the feed.
        """
        if self.debug:
            print("[DEBUG] Using direct debug mode for fetching")
            return self.fetch_direct_debug(include_details)
        else:
            return self.fetch_with_anti_scraping(include_details)

    def ensure_default_category(self) -> int:
        """Ensure default category exists and return its ID."""
        if not self.storage:
            raise ValueError("Storage backend not initialized")
            
        categories = self.storage.get_categories()
        for category in categories:
            if category["name"] == "Default":
                return category["id"]
        return self.storage.create_category("Default")

    def process_feed(self, name: str, interval: int, category_id: Optional[int] = None) -> int:
        """
        Process a single feed: fetch and store articles.
        新增 category_id 参数，优先使用传入的 category_id。
        """
        if not self.storage:
            raise ValueError("Storage backend not initialized")
        try:
            # check if the feed already exists  
            if self.debug:
                print(f"[DEBUG] Checking if feed exists: {self.url}")
            existing_feeds = self.storage.get_feeds()
            feed_exists = any(f["url"] == self.url for f in existing_feeds)
            if not feed_exists:
                # create a new feed
                if self.debug:
                    print(f"[DEBUG] Creating new feed in database: {self.url}")
                try:
                    # 优先用传入的 category_id
                    if category_id is None:
                        category_id = self.ensure_default_category()
                    if self.debug:
                        print(f"[DEBUG] Using category ID: {category_id}")
                    feed_id = self.storage.create_feed(
                        category_id=category_id,
                        name=name,
                        url=self.url,
                        poll_interval=interval,
                        status="active"
                    )
                    if self.debug:
                        print(f"[DEBUG] Created feed with ID: {feed_id}")
                except Exception as e:
                    print(f"[ERROR] Failed to create feed in database: {str(e)}")
                    raise
            else:
                # get the existing feed ID
                if self.debug:
                    print(f"[DEBUG] Feed already exists: {self.url}")
                try:
                    feed_id = next(f["id"] for f in existing_feeds if f["url"] == self.url)
                    if self.debug:
                        print(f"[DEBUG] Using existing feed ID: {feed_id}")
                except Exception as e:
                    print(f"[ERROR] Failed to get existing feed ID: {str(e)}")
                    raise
            # fetch articles - we don't need summary or content for database storage
            if self.debug:
                print(f"[DEBUG] Fetching articles for database storage")
            articles = self.fetch(include_details=False)
            if articles:
                # get existing articles
                if self.debug:
                    print(f"[DEBUG] Getting existing articles for feed ID: {feed_id}")
                try:
                    existing_articles = self.storage.get_articles(feed_id=feed_id)
                    existing_article_links = {article["link"] for article in existing_articles}
                    if self.debug:
                        print(f"[DEBUG] Found {len(existing_article_links)} existing articles")
                except Exception as e:
                    print(f"[ERROR] Failed to get existing articles: {str(e)}")
                    raise
                # get new articles
                new_articles = [article for article in articles if article["link"] not in existing_article_links]
                if self.debug:
                    print(f"[DEBUG] Found {len(new_articles)} new articles out of {len(articles)} total")
                db_articles = []
                for article in new_articles:
                    try:
                        if self.debug:
                            print(f"[DEBUG] Parsing date: {article['published']}")
                        published_dt = parse_date_flexible(article["published"])
                        if self.debug:
                            print(f"[DEBUG] Parsed date: {article['published']} -> {published_dt}")
                        db_article = {
                            "title": article["title"],
                            "link": article["link"],
                            "published_at": published_dt,
                            "status": "new"
                        }
                        db_articles.append(db_article)
                    except Exception as e:
                        print(f"[ERROR] Failed to process article {article['link']}: {str(e)}")
                        # Continue with other articles instead of failing completely
                # save articles
                if db_articles:
                    if self.debug:
                        print(f"[DEBUG] Saving {len(db_articles)} articles to database")
                    try:
                        article_ids = self.storage.save_articles(feed_id, db_articles)
                        saved_count = len(article_ids)
                        if self.debug:
                            print(f"[DEBUG] Successfully saved {saved_count} new articles (skipped {len(db_articles) - saved_count} duplicates)")
                            if article_ids:
                                print(f"[DEBUG] Article IDs: {article_ids}")
                    except Exception as e:
                        print(f"[ERROR] Failed to save articles to database: {str(e)}")
                        raise
                else:
                    if self.debug:
                        print("[DEBUG] No new articles to save")
                    article_ids = []
                if article_ids:
                    print(f"[INFO] Saved {len(article_ids)} articles from {self.url}")
                else:
                    print(f"[INFO] No new articles found in {self.url}")
                return len(article_ids)
            return 0
        except Exception as e:
            print(f"[ERROR] Exception in process_feed: {str(e)}")
            raise

    @classmethod
    def sync_categories_from_config(cls, config_feeds, storage) -> dict:
        """
        Make sure all categories in the config are inserted into the database, and return a mapping of {category name: category ID}.
        """
        # compatible with both objects and dicts
        category_names = set(
            getattr(feed, 'category', None) or (feed.get('category') if isinstance(feed, dict) else None) or 'Default'
            for feed in config_feeds
        )
        category_names = set(name.strip() for name in category_names)
        # query existing categories in the database
        db_categories = storage.get_categories()  # [{'id': 1, 'name': 'Default'}, ...]
        db_category_map = {c['name']: c['id'] for c in db_categories}
        # insert missing categories
        for name in category_names:
            if name not in db_category_map:
                new_id = storage.create_category(name)
                db_category_map[name] = new_id
        print(f"[INFO] Syncing categories from config: {category_names}")
        return db_category_map

    @classmethod
    def process_feeds_from_config(cls, config_path: Path, storage: SQLiteStorage, user_agent: Optional[str] = None, debug: bool = False) -> Dict[str, int]:
        """
        Process all feeds from config file.
        """
        if debug:
            print(f"[DEBUG] Loading feeds from config: {config_path}")
        try:
            config_manager = ConfigManager(config_path)
            feeds = config_manager.get_enabled_feeds()
            if debug:
                print(f"[DEBUG] Found {len(feeds)} enabled feeds in config")
                for i, feed in enumerate(feeds):
                    print(f"[DEBUG] Feed {i+1}: {feed.name} - {feed.url}")
            # 分类同步
            feed_dicts = [feed.__dict__ if hasattr(feed, '__dict__') else feed for feed in feeds]
            category_map = cls.sync_categories_from_config(feed_dicts, storage)
            # create a shared feed parser to reuse the HTTP session
            if debug:
                print("[DEBUG] Creating shared feed parser")
            feed_parser = FeedParserAdapter.create_with_defaults(user_agent=user_agent)
            results = {}
            for i, feed in enumerate(feeds):
                if debug:
                    print(f"\n[DEBUG] Processing feed {i+1}/{len(feeds)}: {feed.name} ({feed.url})")
                try:
                    # Get category name from feed
                    category_name = getattr(feed, 'category', None) or (feed.get('category') if isinstance(feed, dict) else None) or 'Default'
                    # Check if category exists in the map
                    if category_name.strip() in category_map:
                        category_id = category_map[category_name.strip()]
                    else:
                        # If Default is not in the map, use the first available category or create a new one
                        if 'Default' in category_map:
                            category_id = category_map['Default']
                        elif category_map:
                            # Use the first available category
                            first_category = next(iter(category_map.items()))
                            category_id = first_category[1]
                            print(f"[INFO] Category '{category_name}' not found, using '{first_category[0]}' instead")
                        else:
                            # Create a new category with the specified name
                            print(f"[INFO] Creating new category: {category_name}")
                            category_id = storage.create_category(category_name.strip())
                            category_map[category_name.strip()] = category_id
                    fetcher = cls(feed.url, storage, feed_parser=feed_parser, debug=debug)
                    # pass category_id to process_feed
                    article_count = fetcher.process_feed(feed.name, feed.interval, category_id=category_id)
                    results[feed.url] = article_count
                except Exception as e:
                    print(f"[ERROR] Failed to process feed {feed.url}: {e}")
                    if debug:
                        import traceback
                        print(f"[DEBUG] Error traceback:\n{traceback.format_exc()}")
                    try:
                        if debug:
                            print(f"[DEBUG] Updating error status for feed: {feed.url}")
                        existing_feeds = storage.get_feeds()
                        feed_id = next((f["id"] for f in existing_feeds if f["url"] == feed.url), None)
                        if feed_id:
                            if debug:
                                print(f"[DEBUG] Updating error status for feed ID: {feed_id}")
                            storage.update_feed_error(feed_id, str(e))
                        else:
                            if debug:
                                print(f"[DEBUG] Feed not found in database to update error status: {feed.url}")
                    except Exception as update_error:
                        print(f"[ERROR] Failed to update error status: {update_error}")
                    results[feed.url] = -1  # -1 means error
            return results
        except Exception as e:
            print(f"[ERROR] Failed to process feeds from config: {e}")
            import traceback
            if debug:
                print(f"[DEBUG] Error traceback:\n{traceback.format_exc()}")
            return {}
