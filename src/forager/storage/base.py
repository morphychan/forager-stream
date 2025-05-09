"""
Define the storage plugin interface (BaseStorage) for persisting articles.

This module provides an abstract base class that defines the interface for all storage
backends in the Forager system. Storage backends are responsible for persisting and
retrieving article data from various storage systems.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from datetime import datetime


class StorageError(Exception):
    """Base exception for storage-related errors."""
    pass


class BaseStorage(ABC):
    """Abstract base class for all storage backends.
    
    This class defines the interface that all storage backends must implement.
    Storage backends are responsible for persisting and retrieving article data
    from various storage systems (e.g., databases, file systems, etc.).
    """

    # Category management methods
    @abstractmethod
    def create_category(self, name: str) -> int:
        """
        Create a new category.

        Args:
            name: Name of the category.

        Returns:
            ID of the created category.

        Raises:
            StorageError: If there is an error creating the category.
            ValueError: If the category name is invalid or already exists.
        """
        pass

    @abstractmethod
    def get_category(self, category_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a category by ID.

        Args:
            category_id: ID of the category.

        Returns:
            Category data as a dict, or None if not found.

        Raises:
            StorageError: If there is an error retrieving the category.
        """
        pass

    @abstractmethod
    def get_categories(self) -> List[Dict[str, Any]]:
        """
        Get all categories.

        Returns:
            List of category dictionaries.

        Raises:
            StorageError: If there is an error retrieving the categories.
        """
        pass

    @abstractmethod
    def update_category(self, category_id: int, name: str) -> bool:
        """
        Update a category.

        Args:
            category_id: ID of the category to update.
            name: New name for the category.

        Returns:
            True if the category was updated, False if not found.

        Raises:
            StorageError: If there is an error updating the category.
            ValueError: If the new name is invalid or already exists.
        """
        pass

    @abstractmethod
    def delete_category(self, category_id: int) -> bool:
        """
        Delete a category and all its feeds.

        Args:
            category_id: ID of the category to delete.

        Returns:
            True if the category was deleted, False if not found.

        Raises:
            StorageError: If there is an error deleting the category.
        """
        pass

    # Feed management methods
    @abstractmethod
    def create_feed(
        self,
        category_id: int,
        name: str,
        url: str,
        poll_interval: int,
        status: str = 'active'
    ) -> int:
        """
        Create a new feed.

        Args:
            category_id: ID of the category this feed belongs to.
            name: Name of the feed.
            url: URL of the feed.
            poll_interval: Poll interval in seconds.
            status: Initial status of the feed (default: 'active').

        Returns:
            ID of the created feed.

        Raises:
            StorageError: If there is an error creating the feed.
            ValueError: If the feed data is invalid or URL already exists.
        """
        pass

    @abstractmethod
    def get_feed(self, feed_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a feed by ID.

        Args:
            feed_id: ID of the feed.

        Returns:
            Feed data as a dict, or None if not found.

        Raises:
            StorageError: If there is an error retrieving the feed.
        """
        pass

    @abstractmethod
    def get_feeds(
        self,
        category_id: Optional[int] = None,
        status: Optional[str] = None,
        include_deleted: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get feeds with optional filtering.

        Args:
            category_id: Optional category ID to filter by.
            status: Optional status to filter by.
            include_deleted: Whether to include soft-deleted feeds.

        Returns:
            List of feed dictionaries.

        Raises:
            StorageError: If there is an error retrieving the feeds.
        """
        pass

    @abstractmethod
    def update_feed(
        self,
        feed_id: int,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update a feed.

        Args:
            feed_id: ID of the feed to update.
            updates: Dict of fields to update and their new values.
                    Can include: name, category_id, url, poll_interval, status.

        Returns:
            True if the feed was updated, False if not found.

        Raises:
            StorageError: If there is an error updating the feed.
            ValueError: If the update data is invalid.
        """
        pass

    @abstractmethod
    def delete_feed(self, feed_id: int, hard_delete: bool = False) -> bool:
        """
        Delete a feed.

        Args:
            feed_id: ID of the feed to delete.
            hard_delete: If True, permanently delete the feed and its articles.
                        If False, soft delete by setting deleted_at.

        Returns:
            True if the feed was deleted, False if not found.

        Raises:
            StorageError: If there is an error deleting the feed.
        """
        pass

    @abstractmethod
    def update_feed_error(self, feed_id: int, error: Optional[str]) -> bool:
        """
        Update the last error for a feed.

        Args:
            feed_id: ID of the feed.
            error: Error message, or None to clear the error.

        Returns:
            True if the feed was updated, False if not found.

        Raises:
            StorageError: If there is an error updating the feed.
        """
        pass

    # Tag management methods
    @abstractmethod
    def create_tag(self, name: str) -> int:
        """
        Create a new tag.

        Args:
            name: Name of the tag.

        Returns:
            ID of the created tag.

        Raises:
            StorageError: If there is an error creating the tag.
            ValueError: If the tag name is invalid or already exists.
        """
        pass

    @abstractmethod
    def get_tag(self, tag_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a tag by ID.

        Args:
            tag_id: ID of the tag.

        Returns:
            Tag data as a dict, or None if not found.

        Raises:
            StorageError: If there is an error retrieving the tag.
        """
        pass

    @abstractmethod
    def get_tags(self) -> List[Dict[str, Any]]:
        """
        Get all tags.

        Returns:
            List of tag dictionaries.

        Raises:
            StorageError: If there is an error retrieving the tags.
        """
        pass

    @abstractmethod
    def update_tag(self, tag_id: int, name: str) -> bool:
        """
        Update a tag.

        Args:
            tag_id: ID of the tag to update.
            name: New name for the tag.

        Returns:
            True if the tag was updated, False if not found.

        Raises:
            StorageError: If there is an error updating the tag.
            ValueError: If the new name is invalid or already exists.
        """
        pass

    @abstractmethod
    def delete_tag(self, tag_id: int) -> bool:
        """
        Delete a tag.

        Args:
            tag_id: ID of the tag to delete.

        Returns:
            True if the tag was deleted, False if not found.

        Raises:
            StorageError: If there is an error deleting the tag.
        """
        pass

    @abstractmethod
    def add_tag_to_feed(self, feed_id: int, tag_id: int) -> bool:
        """
        Add a tag to a feed.

        Args:
            feed_id: ID of the feed.
            tag_id: ID of the tag to add.

        Returns:
            True if the tag was added, False if already present.

        Raises:
            StorageError: If there is an error adding the tag.
        """
        pass

    @abstractmethod
    def remove_tag_from_feed(self, feed_id: int, tag_id: int) -> bool:
        """
        Remove a tag from a feed.

        Args:
            feed_id: ID of the feed.
            tag_id: ID of the tag to remove.

        Returns:
            True if the tag was removed, False if not present.

        Raises:
            StorageError: If there is an error removing the tag.
        """
        pass

    # Article management methods (existing methods)
    @abstractmethod
    def save_article(self, feed_id: int, article: Dict[str, Any]) -> int:
        """
        Save a single article to storage.

        Args:
            feed_id: ID of the feed source.
            article: Article data as a dict with required fields:
                    - title: str
                    - link: str
                    - published_at: datetime
                    - summary: Optional[str]
                    - content: Optional[str]
                    - status: str (default: 'new')
                    - manual_labels: Optional[Dict[str, Any]]

        Returns:
            The ID of the saved article.

        Raises:
            StorageError: If there is an error saving the article.
            ValueError: If the article data is invalid.
        """
        pass

    @abstractmethod
    def save_articles(self, feed_id: int, articles: List[Dict[str, Any]]) -> List[int]:
        """
        Save multiple articles to storage.

        Args:
            feed_id: ID of the feed source.
            articles: List of article dicts, each with required fields as in save_article().

        Returns:
            List of IDs of the saved articles.

        Raises:
            StorageError: If there is an error saving the articles.
            ValueError: If any article data is invalid.
        """
        pass

    @abstractmethod
    def get_article(self, article_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single article by ID.

        Args:
            article_id: ID of the article to retrieve.

        Returns:
            Article data as a dict, or None if not found.

        Raises:
            StorageError: If there is an error retrieving the article.
        """
        pass

    @abstractmethod
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
        """
        Retrieve articles with various filtering options.

        Args:
            feed_id: Optional feed ID to filter by.
            category_id: Optional category ID to filter by.
            tag_ids: Optional list of tag IDs to filter by.
            status: Optional status to filter by.
            before_date: Optional datetime to get articles before.
            after_date: Optional datetime to get articles after.
            limit: Optional maximum number of articles to retrieve.
            offset: Optional offset for pagination.
            include_deleted: Whether to include soft-deleted articles.

        Returns:
            List of article dictionaries.

        Raises:
            StorageError: If there is an error retrieving the articles.
        """
        pass

    @abstractmethod
    def update_article(self, article_id: int, updates: Dict[str, Any]) -> bool:
        """
        Update an existing article.

        Args:
            article_id: ID of the article to update.
            updates: Dict of fields to update and their new values.

        Returns:
            True if the article was updated, False if not found.

        Raises:
            StorageError: If there is an error updating the article.
            ValueError: If the update data is invalid.
        """
        pass

    @abstractmethod
    def delete_article(self, article_id: int, hard_delete: bool = False) -> bool:
        """
        Delete an article.

        Args:
            article_id: ID of the article to delete.
            hard_delete: If True, permanently delete the article.
                        If False, soft delete by setting deleted_at.

        Returns:
            True if the article was deleted, False if not found.

        Raises:
            StorageError: If there is an error deleting the article.
        """
        pass

    @abstractmethod
    def delete_articles(
        self,
        feed_id: Optional[int] = None,
        before_date: Optional[datetime] = None,
        hard_delete: bool = False
    ) -> int:
        """
        Delete multiple articles matching criteria.

        Args:
            feed_id: Optional feed ID to delete articles from.
            before_date: Optional datetime to delete articles before.
            hard_delete: If True, permanently delete the articles.
                        If False, soft delete by setting deleted_at.

        Returns:
            Number of articles deleted.

        Raises:
            StorageError: If there is an error deleting the articles.
        """
        pass

    @abstractmethod
    def add_tag_to_article(self, article_id: int, tag_id: int) -> bool:
        """
        Add a tag to an article.

        Args:
            article_id: ID of the article.
            tag_id: ID of the tag to add.

        Returns:
            True if the tag was added, False if already present.

        Raises:
            StorageError: If there is an error adding the tag.
        """
        pass

    @abstractmethod
    def remove_tag_from_article(self, article_id: int, tag_id: int) -> bool:
        """
        Remove a tag from an article.

        Args:
            article_id: ID of the article.
            tag_id: ID of the tag to remove.

        Returns:
            True if the tag was removed, False if not present.

        Raises:
            StorageError: If there is an error removing the tag.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Close any open connections or resources.

        This method should be called when the storage backend is no longer needed.
        """
        pass


