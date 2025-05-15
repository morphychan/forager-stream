"""
Date and time utility functions.

This module provides helper functions for handling and converting dates and times
in various formats commonly found in RSS feeds and other data sources.
"""

import datetime
from email.utils import parsedate_to_datetime
from typing import Optional

try:
    from dateutil import parser as date_parser
    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False


def parse_date_flexible(date_str: str) -> datetime.datetime:
    """
    Parse a date string in various formats into a datetime object.
    
    This function tries different methods to parse the date:
    1. First attempts RFC 2822 format using email.utils.parsedate_to_datetime
    2. Falls back to dateutil.parser for ISO 8601 and other formats if available
    3. As a last resort, attempts basic ISO format parsing with strptime
    
    Args:
        date_str: Date string to parse
        
    Returns:
        Parsed datetime object
        
    Raises:
        ValueError: If the date string cannot be parsed
    """
    try:
        # First try RFC 2822 format (email header format)
        return parsedate_to_datetime(date_str)
    except Exception:
        # Then try ISO 8601 and other formats using dateutil if available
        if DATEUTIL_AVAILABLE:
            try:
                return date_parser.parse(date_str)
            except Exception:
                pass
        
        # Try some common formats as a last resort
        formats_to_try = [
            "%Y-%m-%dT%H:%M:%SZ",       # ISO 8601 format without timezone
            "%Y-%m-%dT%H:%M:%S.%fZ",    # ISO 8601 with milliseconds
            "%Y-%m-%d %H:%M:%S",        # Basic format
            "%Y-%m-%d",                 # Just date
        ]
        
        for fmt in formats_to_try:
            try:
                return datetime.datetime.strptime(date_str, fmt)
            except ValueError:
                continue
                
        # If we get here, all parsing attempts failed
        raise ValueError(f"Invalid date value or format: {date_str}")


def format_datetime_for_display(dt: datetime.datetime, include_time: bool = True) -> str:
    """
    Format a datetime object for user-friendly display.
    
    Args:
        dt: The datetime to format
        include_time: Whether to include the time component
        
    Returns:
        Formatted date string
    """
    if include_time:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    else:
        return dt.strftime("%Y-%m-%d") 