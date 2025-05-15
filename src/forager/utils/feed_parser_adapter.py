"""
Feed parser utilities with anti-scraping capabilities.
"""
import io
import feedparser
from typing import Dict, Any, Optional, List
from forager.utils.http import HttpClient

class FeedParserAdapter:
    """
    Adapter for feedparser that uses the HttpClient for requests.
    Enables anti-scraping capabilities for RSS feed fetching.
    """
    
    def __init__(self, http_client: Optional[HttpClient] = None):
        """
        Initialize the adapter.
        
        Args:
            http_client: The HTTP client to use for requests.
                         If None, a default one will be created.
        """
        self.http_client = http_client or HttpClient.create_with_defaults()
    
    def parse(self, url: str, **kwargs) -> feedparser.FeedParserDict:
        """
        Parse a feed from a URL using the HTTP client.
        
        Args:
            url: The URL to fetch the feed from.
            **kwargs: Additional arguments to pass to feedparser.
            
        Returns:
            The parsed feed.
        """
        # Get content via HTTP client with anti-scraping capabilities
        response = self.http_client.get(url)
        
        # Ensure proper encoding for feedparser
        if response.encoding:
            response.encoding = response.apparent_encoding or 'utf-8'
        
        # Pass the content to feedparser
        return feedparser.parse(
            io.BytesIO(response.content),
            response_headers={
                'content-type': response.headers.get('content-type', '')
            },
            **kwargs
        )
    
    @classmethod
    def create_with_defaults(cls, user_agent: Optional[str] = None) -> 'FeedParserAdapter':
        """
        Create a FeedParserAdapter with default anti-scraping strategies.
        
        Args:
            user_agent: Optional fixed User-Agent to use.
            
        Returns:
            Configured FeedParserAdapter instance.
        """
        http_client = HttpClient.create_with_defaults(user_agent=user_agent)
        return cls(http_client=http_client) 