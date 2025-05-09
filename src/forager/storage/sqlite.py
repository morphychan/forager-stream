"""
SQLite storage backend for persisting RSS articles.
"""

import sqlite3
import logging
import json
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
            # Enable foreign keys
            self._conn.execute("PRAGMA foreign_keys = ON")
        return self._conn

    # Category management methods
    def create_category(self, name: str) -> int:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO categories (name) VALUES (?)",
                    (name,)
                )
                conn.commit()
                return cursor.lastrowid
        except sqlite3.Error as e:
            raise StorageError(f"Failed to create category: {e}")

    def get_category(self, category_id: int) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, name, created_at, updated_at FROM categories WHERE id = ?",
                    (category_id,)
                )
                row = cursor.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "name": row[1],
                        "created_at": row[2],
                        "updated_at": row[3]
                    }
                return None
        except sqlite3.Error as e:
            raise StorageError(f"Failed to get category: {e}")

    def get_categories(self) -> List[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, name, created_at, updated_at FROM categories"
                )
                return [
                    {
                        "id": row[0],
                        "name": row[1],
                        "created_at": row[2],
                        "updated_at": row[3]
                    }
                    for row in cursor.fetchall()
                ]
        except sqlite3.Error as e:
            raise StorageError(f"Failed to get categories: {e}")

    def update_category(self, category_id: int, name: str) -> bool:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE categories SET name = ? WHERE id = ?",
                    (name, category_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise StorageError(f"Failed to update category: {e}")

    def delete_category(self, category_id: int) -> bool:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM categories WHERE id = ?",
                    (category_id,)
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise StorageError(f"Failed to delete category: {e}")

    # Feed management methods
    def create_feed(
        self,
        category_id: int,
        name: str,
        url: str,
        poll_interval: int,
        status: str = 'active'
    ) -> int:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO rss_feeds 
                    (category_id, name, url, poll_interval, status)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (category_id, name, url, poll_interval, status)
                )
                conn.commit()
                return cursor.lastrowid
        except sqlite3.Error as e:
            raise StorageError(f"Failed to create feed: {e}")

    def get_feed(self, feed_id: int) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, category_id, name, url, poll_interval, status,
                           created_at, updated_at, last_error, last_error_at, deleted_at
                    FROM rss_feeds WHERE id = ?
                    """,
                    (feed_id,)
                )
                row = cursor.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "category_id": row[1],
                        "name": row[2],
                        "url": row[3],
                        "poll_interval": row[4],
                        "status": row[5],
                        "created_at": row[6],
                        "updated_at": row[7],
                        "last_error": row[8],
                        "last_error_at": row[9],
                        "deleted_at": row[10]
                    }
                return None
        except sqlite3.Error as e:
            raise StorageError(f"Failed to get feed: {e}")

    def get_feeds(
        self,
        category_id: Optional[int] = None,
        status: Optional[str] = None,
        include_deleted: bool = False
    ) -> List[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = """
                    SELECT id, category_id, name, url, poll_interval, status,
                           created_at, updated_at, last_error, last_error_at, deleted_at
                    FROM rss_feeds
                    WHERE 1=1
                """
                params = []
                
                if category_id is not None:
                    query += " AND category_id = ?"
                    params.append(category_id)
                
                if status is not None:
                    query += " AND status = ?"
                    params.append(status)
                
                if not include_deleted:
                    query += " AND deleted_at IS NULL"
                
                cursor.execute(query, params)
                return [
                    {
                        "id": row[0],
                        "category_id": row[1],
                        "name": row[2],
                        "url": row[3],
                        "poll_interval": row[4],
                        "status": row[5],
                        "created_at": row[6],
                        "updated_at": row[7],
                        "last_error": row[8],
                        "last_error_at": row[9],
                        "deleted_at": row[10]
                    }
                    for row in cursor.fetchall()
                ]
        except sqlite3.Error as e:
            raise StorageError(f"Failed to get feeds: {e}")

    def update_feed(self, feed_id: int, updates: Dict[str, Any]) -> bool:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                set_clauses = []
                params = []
                
                for key, value in updates.items():
                    if key in ['name', 'category_id', 'url', 'poll_interval', 'status']:
                        set_clauses.append(f"{key} = ?")
                        params.append(value)
                
                if not set_clauses:
                    return False
                
                query = f"UPDATE rss_feeds SET {', '.join(set_clauses)} WHERE id = ?"
                params.append(feed_id)
                
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise StorageError(f"Failed to update feed: {e}")

    def delete_feed(self, feed_id: int, hard_delete: bool = False) -> bool:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if hard_delete:
                    cursor.execute("DELETE FROM rss_feeds WHERE id = ?", (feed_id,))
                else:
                    cursor.execute(
                        "UPDATE rss_feeds SET deleted_at = ? WHERE id = ?",
                        (datetime.now().isoformat(), feed_id)
                    )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise StorageError(f"Failed to delete feed: {e}")

    def update_feed_error(self, feed_id: int, error: Optional[str]) -> bool:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE rss_feeds 
                    SET last_error = ?, last_error_at = ?
                    WHERE id = ?
                    """,
                    (error, datetime.now().isoformat() if error else None, feed_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise StorageError(f"Failed to update feed error: {e}")

    # Tag management methods
    def create_tag(self, name: str) -> int:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO tags (name) VALUES (?)",
                    (name,)
                )
                conn.commit()
                return cursor.lastrowid
        except sqlite3.Error as e:
            raise StorageError(f"Failed to create tag: {e}")

    def get_tag(self, tag_id: int) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, name, created_at, updated_at FROM tags WHERE id = ?",
                    (tag_id,)
                )
                row = cursor.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "name": row[1],
                        "created_at": row[2],
                        "updated_at": row[3]
                    }
                return None
        except sqlite3.Error as e:
            raise StorageError(f"Failed to get tag: {e}")

    def get_tags(self) -> List[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, name, created_at, updated_at FROM tags"
                )
                return [
                    {
                        "id": row[0],
                        "name": row[1],
                        "created_at": row[2],
                        "updated_at": row[3]
                    }
                    for row in cursor.fetchall()
                ]
        except sqlite3.Error as e:
            raise StorageError(f"Failed to get tags: {e}")

    def update_tag(self, tag_id: int, name: str) -> bool:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE tags SET name = ? WHERE id = ?",
                    (name, tag_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise StorageError(f"Failed to update tag: {e}")

    def delete_tag(self, tag_id: int) -> bool:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM tags WHERE id = ?",
                    (tag_id,)
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise StorageError(f"Failed to delete tag: {e}")

    def add_tag_to_feed(self, feed_id: int, tag_id: int) -> bool:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR IGNORE INTO feed_tags (feed_id, tag_id) VALUES (?, ?)",
                    (feed_id, tag_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise StorageError(f"Failed to add tag to feed: {e}")

    def remove_tag_from_feed(self, feed_id: int, tag_id: int) -> bool:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM feed_tags WHERE feed_id = ? AND tag_id = ?",
                    (feed_id, tag_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise StorageError(f"Failed to remove tag from feed: {e}")

    # Article management methods
    def save_article(self, feed_id: int, article: Dict[str, Any]) -> int:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO rss_articles 
                    (feed_id, title, link, published_at, status, summary, content, manual_labels)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        feed_id,
                        article["title"],
                        article["link"],
                        article["published_at"],
                        article.get("status", "new"),
                        article.get("summary"),
                        article.get("content"),
                        json.dumps(article.get("manual_labels")) if article.get("manual_labels") else None
                    )
                )
                conn.commit()
                return cursor.lastrowid
        except sqlite3.Error as e:
            raise StorageError(f"Failed to save article: {e}")

    def save_articles(self, feed_id: int, articles: List[Dict[str, Any]]) -> List[int]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                article_ids = []
                for article in articles:
                    cursor.execute(
                        """
                        INSERT INTO rss_articles 
                        (feed_id, title, link, published_at, status, summary, content, manual_labels)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            feed_id,
                            article["title"],
                            article["link"],
                            article["published_at"],
                            article.get("status", "new"),
                            article.get("summary"),
                            article.get("content"),
                            json.dumps(article.get("manual_labels")) if article.get("manual_labels") else None
                        )
                    )
                    article_ids.append(cursor.lastrowid)
                conn.commit()
                return article_ids
        except sqlite3.Error as e:
            raise StorageError(f"Failed to save articles: {e}")

    def get_article(self, article_id: int) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, feed_id, title, link, published_at, fetched_at, updated_at,
                           status, summary, content, deleted_at, manual_labels
                    FROM rss_articles WHERE id = ?
                    """,
                    (article_id,)
                )
                row = cursor.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "feed_id": row[1],
                        "title": row[2],
                        "link": row[3],
                        "published_at": row[4],
                        "fetched_at": row[5],
                        "updated_at": row[6],
                        "status": row[7],
                        "summary": row[8],
                        "content": row[9],
                        "deleted_at": row[10],
                        "manual_labels": json.loads(row[11]) if row[11] else None
                    }
                return None
        except sqlite3.Error as e:
            raise StorageError(f"Failed to get article: {e}")

    def get_articles(
        self,
        feed_id: Optional[int] = None,
        category_id: Optional[int] = None,
        tag_ids: Optional[List[int]] = None,
        status: Optional[str] = None,
        before_date: Optional[datetime] = None,
        after_date: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        include_deleted: bool = False
    ) -> List[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = """
                    SELECT DISTINCT a.id, a.feed_id, a.title, a.link, a.published_at,
                           a.fetched_at, a.updated_at, a.status, a.summary, a.content,
                           a.deleted_at, a.manual_labels
                    FROM rss_articles a
                    LEFT JOIN rss_feeds f ON a.feed_id = f.id
                    LEFT JOIN articles_tags at ON a.id = at.article_id
                    WHERE 1=1
                """
                params = []
                
                if feed_id is not None:
                    query += " AND a.feed_id = ?"
                    params.append(feed_id)
                
                if category_id is not None:
                    query += " AND f.category_id = ?"
                    params.append(category_id)
                
                if tag_ids:
                    placeholders = ','.join('?' * len(tag_ids))
                    query += f" AND at.tag_id IN ({placeholders})"
                    params.extend(tag_ids)
                
                if status is not None:
                    query += " AND a.status = ?"
                    params.append(status)
                
                if before_date:
                    query += " AND a.published_at < ?"
                    params.append(before_date.isoformat())
                
                if after_date:
                    query += " AND a.published_at > ?"
                    params.append(after_date.isoformat())
                
                if not include_deleted:
                    query += " AND a.deleted_at IS NULL"
                
                query += " ORDER BY a.published_at DESC"
                
                if limit is not None:
                    query += " LIMIT ?"
                    params.append(limit)
                
                if offset is not None:
                    query += " OFFSET ?"
                    params.append(offset)
                
                cursor.execute(query, params)
                return [
                    {
                        "id": row[0],
                        "feed_id": row[1],
                        "title": row[2],
                        "link": row[3],
                        "published_at": row[4],
                        "fetched_at": row[5],
                        "updated_at": row[6],
                        "status": row[7],
                        "summary": row[8],
                        "content": row[9],
                        "deleted_at": row[10],
                        "manual_labels": json.loads(row[11]) if row[11] else None
                    }
                    for row in cursor.fetchall()
                ]
        except sqlite3.Error as e:
            raise StorageError(f"Failed to get articles: {e}")

    def update_article(self, article_id: int, updates: Dict[str, Any]) -> bool:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                set_clauses = []
                params = []
                
                for key, value in updates.items():
                    if key in ['title', 'link', 'status', 'summary', 'content', 'manual_labels']:
                        if key == 'manual_labels' and value is not None:
                            value = json.dumps(value)
                        set_clauses.append(f"{key} = ?")
                        params.append(value)
                
                if not set_clauses:
                    return False
                
                query = f"UPDATE rss_articles SET {', '.join(set_clauses)} WHERE id = ?"
                params.append(article_id)
                
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise StorageError(f"Failed to update article: {e}")

    def delete_article(self, article_id: int, hard_delete: bool = False) -> bool:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if hard_delete:
                    cursor.execute("DELETE FROM rss_articles WHERE id = ?", (article_id,))
                else:
                    cursor.execute(
                        "UPDATE rss_articles SET deleted_at = ? WHERE id = ?",
                        (datetime.now().isoformat(), article_id)
                    )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise StorageError(f"Failed to delete article: {e}")

    def delete_articles(
        self,
        feed_id: Optional[int] = None,
        before_date: Optional[datetime] = None,
        hard_delete: bool = False
    ) -> int:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = "DELETE FROM rss_articles WHERE 1=1"
                params = []
                
                if feed_id is not None:
                    query += " AND feed_id = ?"
                    params.append(feed_id)
                
                if before_date:
                    query += " AND published_at < ?"
                    params.append(before_date.isoformat())
                
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount
        except sqlite3.Error as e:
            raise StorageError(f"Failed to delete articles: {e}")

    def add_tag_to_article(self, article_id: int, tag_id: int) -> bool:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR IGNORE INTO articles_tags (article_id, tag_id) VALUES (?, ?)",
                    (article_id, tag_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise StorageError(f"Failed to add tag to article: {e}")

    def remove_tag_from_article(self, article_id: int, tag_id: int) -> bool:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM articles_tags WHERE article_id = ? AND tag_id = ?",
                    (article_id, tag_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise StorageError(f"Failed to remove tag from article: {e}")

    def close(self) -> None:
        """Close the database connection."""
        if self._conn is not None:
            try:
                self._conn.close()
                self._conn = None
            except sqlite3.Error as e:
                logger.error(f"Error closing database connection: {e}")
                raise StorageError(f"Failed to close database connection: {e}")
