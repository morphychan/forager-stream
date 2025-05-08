"""
SQLite storage backend for persisting RSS articles.
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

from alembic.config import Config
from alembic import command
from forager.storage.base import BaseStorage, StorageError

logger = logging.getLogger(__name__)

class SQLiteStorage(BaseStorage):
    """
    SQLite implementation of BaseStorage.
    Stores articles in a local SQLite database.
    """

    def __init__(self, db_path: Path):
        """
        Initialize the SQLite connection and ensure database is up to date.

        Args:
            db_path: path to the SQLite .db file.
        """
        self.db_path = db_path
        self._conn = None
        self._run_migrations()

    def _run_migrations(self) -> None:
        """Run database migrations using Alembic."""
        try:
            # Ensure migrations directory exists
            migrations_dir = Path(__file__).parent / "migrations"
            if not migrations_dir.exists():
                raise StorageError("Migrations directory not found")

            # Create Alembic configuration
            alembic_cfg = Config()
            alembic_cfg.set_main_option("script_location", str(migrations_dir))
            alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{self.db_path}")

            # Run migrations
            command.upgrade(alembic_cfg, "head")
        except Exception as e:
            raise StorageError(f"Failed to run database migrations: {e}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
        return self._conn

    def save(self, feed_id: str, articles: List[Dict[str, Any]]) -> None:
        """
        Insert articles into the database. Ignores duplicates on link.

        Args:
            feed_id: the feed identifier.
            articles: list of article dicts.

        Raises:
            StorageError: If there is an error saving the articles.
            ValueError: If the articles list is empty or invalid.
        """
        super().save(feed_id, articles)  # This will validate the input
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                for art in articles:
                    try:
                        cursor.execute(
                            """
                            INSERT OR IGNORE INTO rss_articles
                            (feed_id, title, link, published)
                            VALUES (?, ?, ?, ?)
                            """,
                            (feed_id, art["title"], art["link"], art["published"]),
                        )
                    except sqlite3.Error as e:
                        logger.error(f"Failed to save article {art['link']}: {e}")
                        raise StorageError(f"Failed to save article: {e}")
                conn.commit()
        except sqlite3.Error as e:
            raise StorageError(f"Database error: {e}")

    def get_articles(self, feed_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve articles for a given feed.

        Args:
            feed_id: Unique identifier of the feed source.
            limit: Optional maximum number of articles to retrieve.

        Returns:
            List of article dictionaries.

        Raises:
            StorageError: If there is an error retrieving the articles.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = """
                    SELECT title, link, published, fetched_at
                    FROM rss_articles
                    WHERE feed_id = ?
                    ORDER BY published DESC
                """
                if limit:
                    query += f" LIMIT {limit}"
                
                cursor.execute(query, (feed_id,))
                articles = []
                for row in cursor.fetchall():
                    articles.append({
                        "title": row[0],
                        "link": row[1],
                        "published": row[2],
                        "fetched_at": row[3]
                    })
                return articles
        except sqlite3.Error as e:
            raise StorageError(f"Failed to retrieve articles: {e}")

    def delete_articles(self, feed_id: str, before_date: Optional[datetime] = None) -> int:
        """
        Delete articles for a given feed, optionally before a specific date.

        Args:
            feed_id: Unique identifier of the feed source.
            before_date: Optional datetime to delete articles before.

        Returns:
            Number of articles deleted.

        Raises:
            StorageError: If there is an error deleting the articles.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = "DELETE FROM rss_articles WHERE feed_id = ?"
                params = [feed_id]
                
                if before_date:
                    query += " AND published < ?"
                    params.append(before_date.isoformat())
                
                cursor.execute(query, params)
                deleted_count = cursor.rowcount
                conn.commit()
                return deleted_count
        except sqlite3.Error as e:
            raise StorageError(f"Failed to delete articles: {e}")

    def close(self) -> None:
        """
        Close the database connection.
        """
        if self._conn is not None:
            try:
                self._conn.close()
                self._conn = None
            except sqlite3.Error as e:
                logger.error(f"Error closing database connection: {e}")
                raise StorageError(f"Failed to close database connection: {e}")
