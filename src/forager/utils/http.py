"""
HTTP utilities module with anti-scraping capabilities.
"""
import random
import time
from typing import Dict, Optional, List, Union, Callable, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class AntiScrapingStrategy:
    """Base class for anti-scraping strategies."""
    
    def apply_to_session(self, session: requests.Session) -> None:
        """Apply this strategy to a requests session."""
        pass

    def apply_to_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Apply this strategy to request headers."""
        return headers

    def pre_request(self) -> None:
        """Execute before making a request."""
        pass
    
    def post_request(self) -> None:
        """Execute after making a request."""
        pass


class UserAgentRotationStrategy(AntiScrapingStrategy):
    """Strategy for rotating User-Agent headers."""
    
    # Common browser User-Agents
    DEFAULT_USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
    ]
    
    def __init__(self, user_agents: Optional[List[str]] = None, fixed_user_agent: Optional[str] = None):
        """
        Initialize the User-Agent rotation strategy.
        
        Args:
            user_agents: List of User-Agent strings to rotate through.
            fixed_user_agent: A specific User-Agent to use instead of rotating.
        """
        self.user_agents = user_agents or self.DEFAULT_USER_AGENTS
        self.fixed_user_agent = fixed_user_agent
        
    def apply_to_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Apply a User-Agent to the headers."""
        headers = headers.copy()
        if self.fixed_user_agent:
            headers["User-Agent"] = self.fixed_user_agent
        else:
            headers["User-Agent"] = random.choice(self.user_agents)
        return headers


class RequestThrottlingStrategy(AntiScrapingStrategy):
    """Strategy for throttling requests to avoid rate limiting."""
    
    def __init__(self, min_delay: float = 1.0, max_delay: float = 3.0, jitter: bool = True):
        """
        Initialize the request throttling strategy.
        
        Args:
            min_delay: Minimum delay between requests in seconds.
            max_delay: Maximum delay between requests in seconds.
            jitter: Whether to use random jitter between min and max delay.
        """
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.jitter = jitter
        
    def pre_request(self) -> None:
        """Wait before making a request."""
        if self.jitter:
            delay = random.uniform(self.min_delay, self.max_delay)
        else:
            delay = self.min_delay
        time.sleep(delay)


class RetryStrategy(AntiScrapingStrategy):
    """Strategy for retrying failed requests."""
    
    def __init__(
        self, 
        retries: int = 3, 
        backoff_factor: float = 0.3,
        status_forcelist: Optional[List[int]] = None
    ):
        """
        Initialize the retry strategy.
        
        Args:
            retries: Number of retries.
            backoff_factor: Backoff factor for retry delay.
            status_forcelist: List of HTTP status codes to force retry.
        """
        self.retries = retries
        self.backoff_factor = backoff_factor
        self.status_forcelist = status_forcelist or [429, 500, 502, 503, 504]
    
    def apply_to_session(self, session: requests.Session) -> None:
        """Apply retry adapter to session."""
        retry = Retry(
            total=self.retries,
            read=self.retries,
            connect=self.retries,
            backoff_factor=self.backoff_factor,
            status_forcelist=self.status_forcelist,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)


class StandardHeadersStrategy(AntiScrapingStrategy):
    """Strategy for adding standard headers that most browsers use."""
    
    def apply_to_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Apply standard headers."""
        default_headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0"
        }
        
        # Copy headers to avoid modifying the original
        headers = headers.copy()
        
        # Only add default headers if they don't already exist
        for key, value in default_headers.items():
            if key not in headers:
                headers[key] = value
                
        return headers


class HttpClient:
    """HTTP client with anti-scraping capabilities."""
    
    def __init__(self, strategies: Optional[List[AntiScrapingStrategy]] = None):
        """
        Initialize the HTTP client.
        
        Args:
            strategies: List of anti-scraping strategies to use.
        """
        self.strategies = strategies or []
        self.session = self._create_session()
        
    def _create_session(self) -> requests.Session:
        """Create and configure a requests session."""
        session = requests.Session()
        
        # Apply session-level strategies
        for strategy in self.strategies:
            strategy.apply_to_session(session)
            
        return session
    
    def _prepare_headers(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Prepare request headers by applying all strategies."""
        # Start with provided headers or empty dict
        prepared_headers = headers.copy() if headers else {}
        
        # Apply header strategies
        for strategy in self.strategies:
            prepared_headers = strategy.apply_to_headers(prepared_headers)
            
        return prepared_headers
    
    def _execute_strategies(self, method: str) -> None:
        """Execute strategy methods before or after requests."""
        for strategy in self.strategies:
            if method == "pre":
                strategy.pre_request()
            elif method == "post":
                strategy.post_request()
    
    def get(self, url: str, headers: Optional[Dict[str, str]] = None, debug: bool = False, **kwargs) -> requests.Response:
        """
        Make a GET request with anti-scraping measures.
        
        Args:
            url: URL to request.
            headers: Additional headers to send.
            debug: Whether to print debug information during the request.
            **kwargs: Additional arguments to pass to requests.get.
            
        Returns:
            Response object.
        """
        if debug:
            print(f"[DEBUG] HTTP GET: {url}")
            
        prepared_headers = self._prepare_headers(headers)
        
        if debug:
            print(f"[DEBUG] Request headers: {prepared_headers}")
        
        # Pre-request strategies
        if debug:
            print("[DEBUG] Executing pre-request strategies")
        self._execute_strategies("pre")
        
        try:
            if debug:
                print("[DEBUG] Sending request...")
            response = self.session.get(url, headers=prepared_headers, **kwargs)
            if debug:
                print(f"[DEBUG] Response status: {response.status_code}")
                print(f"[DEBUG] Response headers: {dict(response.headers)}")
                print(f"[DEBUG] Response size: {len(response.content)} bytes")
        except Exception as e:
            if debug:
                print(f"[DEBUG] Request failed: {str(e)}")
            raise
        
        # Post-request strategies
        if debug:
            print("[DEBUG] Executing post-request strategies")
        self._execute_strategies("post")
        
        return response

    def post(self, url: str, headers: Optional[Dict[str, str]] = None, **kwargs) -> requests.Response:
        """
        Make a POST request with anti-scraping measures.
        
        Args:
            url: URL to request.
            headers: Additional headers to send.
            **kwargs: Additional arguments to pass to requests.post.
            
        Returns:
            Response object.
        """
        prepared_headers = self._prepare_headers(headers)
        
        # Pre-request strategies
        self._execute_strategies("pre")
        
        response = self.session.post(url, headers=prepared_headers, **kwargs)
        
        # Post-request strategies
        self._execute_strategies("post")
        
        return response

    @classmethod
    def create_with_defaults(cls, user_agent: Optional[str] = None) -> 'HttpClient':
        """
        Create an HttpClient with default anti-scraping strategies.
        
        Args:
            user_agent: Optional fixed User-Agent to use.
            
        Returns:
            Configured HttpClient instance.
        """
        strategies = [
            UserAgentRotationStrategy(fixed_user_agent=user_agent),
            StandardHeadersStrategy(),
            RequestThrottlingStrategy(min_delay=1.0, max_delay=3.0),
            RetryStrategy()
        ]
        return cls(strategies=strategies) 