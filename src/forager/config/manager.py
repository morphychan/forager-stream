"""
Configuration management module for Forager.
"""
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
import yaml
from dataclasses import dataclass, field
from datetime import timedelta

@dataclass
class FeedConfig:
    """Configuration for a single RSS feed."""
    id: str
    name: str
    url: str
    interval: int
    enabled: bool
    category: Optional[str] = None
    string_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)

class ConfigError(Exception):
    """Base exception for configuration errors."""
    pass

class ConfigValidationError(ConfigError):
    """Exception raised when configuration validation fails."""
    pass

class ConfigManager:
    """Manages configuration loading and validation."""
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self._config: Optional[Dict[str, Any]] = None
        self._feeds: Optional[List[FeedConfig]] = None

    def load(self) -> None:
        """Load configuration from file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML format in config file: {e}")
        except FileNotFoundError:
            raise ConfigError(f"Config file not found: {self.config_path}")
        except Exception as e:
            raise ConfigError(f"Could not read config: {e}")

    def validate(self) -> None:
        """Validate configuration structure and content."""
        if not self._config:
            raise ConfigError("Configuration not loaded")

        if not isinstance(self._config, dict):
            raise ConfigValidationError("Config file must contain a dictionary")

        feeds = self._config.get("feeds", [])
        if not isinstance(feeds, list):
            raise ConfigValidationError("'feeds' must be a list in config file")

        self._feeds = []
        for i, feed in enumerate(feeds):
            if not isinstance(feed, dict):
                raise ConfigValidationError(f"Feed at index {i} must be a dictionary")
            
            required_fields = {'id', 'name', 'url', 'interval', 'enabled'}
            missing_fields = required_fields - set(feed.keys())
            if missing_fields:
                raise ConfigValidationError(
                    f"Feed '{feed.get('id', f'at index {i}')}' missing required fields: {missing_fields}"
                )

            try:
                self._feeds.append(FeedConfig(
                    id=feed['id'],
                    name=feed['name'],
                    url=feed['url'],
                    interval=int(feed['interval']),
                    enabled=bool(feed['enabled']),
                    category=feed.get('category'),
                    string_id=feed.get('string_id'),
                    tags=feed.get('tags', [])
                ))
            except (ValueError, TypeError) as e:
                raise ConfigValidationError(
                    f"Invalid value in feed '{feed.get('id', f'at index {i}')}': {e}"
                )

    def get_enabled_feeds(self) -> List[FeedConfig]:
        """Get list of enabled feeds."""
        if not self._feeds:
            self.load()
            self.validate()
        return [feed for feed in self._feeds if feed.enabled]

    def get_feed_urls(self) -> List[str]:
        """Get list of URLs from enabled feeds."""
        return [feed.url for feed in self.get_enabled_feeds()] 