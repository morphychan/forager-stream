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

    @abstractmethod
    def save(self, feed_id: str, articles: List[Dict[str, Any]]) -> None:
        """
        Persist a list of article dicts for the given feed.

        Args:
            feed_id: Unique identifier of the feed source.
            articles: List of articles, each as a dict with at least
                     'title', 'link', 'published' keys.

        Raises:
            StorageError: If there is an error saving the articles.
            ValueError: If the articles list is empty or invalid.
        """
        if not articles:
            raise ValueError("Articles list cannot be empty")
        
        for article in articles:
            required_keys = {'title', 'link', 'published'}
            if not all(key in article for key in required_keys):
                raise ValueError(f"Article missing required keys: {required_keys}")

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Close any open connections or resources.

        This method should be called when the storage backend is no longer needed.
        """
        pass


