import re
import time
import asyncio # Add asyncio import
import idna
import hashlib
import logging
import threading
import asyncio # Ensure asyncio is imported
import asyncio # Ensure asyncio is imported
import requests
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from urllib.parse import urlparse, urljoin, urlunparse, parse_qs, parse_qsl, urlencode
from enum import Enum, auto # Added auto
from dataclasses import dataclass, field # Added field
from pydantic import BaseModel, Field, validator
import ipaddress
from .url_info import URLInfo, URLType # Import the new class and Enum


# Note: The URLInfo BaseModel and URLType Enum are now defined in url_info.py
# The URLInfo.from_string classmethod is also removed as instantiation handles it.


class URLProcessor:
    """Handles URL processing, normalization and validation."""
    ALLOWED_SCHEMES = {'http', 'https'}
    ASSET_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.css', '.js'}
    MAX_PATH_LENGTH = 2048
    MAX_QUERY_LENGTH = 2048
    PRIVATE_IP_PATTERNS = [
        re.compile(r'^127\.'),
        re.compile(r'^10\.'),
        re.compile(r'^172\.(1[6-9]|2[0-9]|3[0-1])\.'),
        re.compile(r'^192\.168\.'),
        re.compile(r'^0\.0\.0\.0'),
        re.compile(r'^::1$'),
    ]
    INVALID_CHARS = re.compile(r'[\<\>\[\]\{\}\|\\\^]')
    INVALID_PATH_TRAVERSAL = re.compile(r'(?:^|/)\.{2}(?:/|$)')

    @staticmethod
    def normalize_url(url: str, base_url: Optional[str] = None) -> str:
        """Normalize URL to canonical form."""
        # Import removed as URLNormalizer is deprecated
        # This method itself is likely unused now and relies on removed code.
        # Returning original URL for now to avoid breaking calls, but should be removed later.
        logging.warning("URLProcessor.normalize_url is deprecated and likely unused.")
        return url

    @classmethod
    def _determine_url_type(cls, url: str, base_url: Optional[str] = None) -> URLType:
        """Determine URL type (internal, external, asset, unknown)."""
        if not url:
            return URLType.UNKNOWN

        try:
            parsed_url = urlparse(url)
            
            # Check if it's an asset
            if any(parsed_url.path.lower().endswith(ext) for ext in cls.ASSET_EXTENSIONS):
                return URLType.ASSET

            # If no base_url, treat as external
            if not base_url:
                return URLType.EXTERNAL

            # Parse base URL for comparison
            parsed_base = urlparse(base_url)

            # Check if internal
            if (not parsed_url.netloc or 
                parsed_url.netloc.lower() == parsed_base.netloc.lower()):
                return URLType.INTERNAL

            return URLType.EXTERNAL

        except Exception:
            return URLType.UNKNOWN

    @classmethod
    def process_url(cls, url: str, base_url: Optional[str] = None) -> URLInfo:
        """
        Processes a URL string, returning a URLInfo object containing
        validation status, normalized form, and other details.
        """
        # All logic is now encapsulated within the URLInfo class constructor
        return URLInfo(url, base_url)


class RateLimiter:
    """Rate limiter using token bucket algorithm."""
    def __init__(self, requests_per_second: float):
        self.rate = requests_per_second
        self.last_check = asyncio.get_event_loop().time() # Use event loop time
        self.tokens = requests_per_second
        self.max_tokens = requests_per_second
        self._lock = asyncio.Lock() # Use asyncio.Lock

    async def acquire(self) -> float: # Make method async
        """Acquire a token, returning the time to wait if necessary."""
        async with self._lock: # Use async with
            now = asyncio.get_event_loop().time() # Use event loop time
            time_passed = now - self.last_check
            logging.debug(f"RateLimiter: now={now}, last_check={self.last_check}, time_passed={time_passed}")
            self.tokens = min(self.max_tokens, self.tokens + time_passed * self.rate)
            logging.debug(f"RateLimiter: tokens replenished to {self.tokens}")
            self.last_check = now

            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.rate
                logging.debug(f"RateLimiter: tokens < 1 ({self.tokens}), need to wait {wait_time}s")
                return wait_time

            self.tokens -= 1
            logging.debug(f"RateLimiter: acquired token, tokens remaining {self.tokens}")
            return 0.0


class RetryStrategy:
    """Implements exponential backoff retry strategy."""
    def __init__(self, max_retries: int = 3, initial_delay: float = 1.0,
                 max_delay: float = 60.0, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for current attempt."""
        delay = min(
            self.initial_delay * (self.backoff_factor ** (attempt - 1)),
            self.max_delay
        )
        return delay

    def should_retry(self, attempt: int, exception: Exception) -> bool:
        """Determine if another retry should be attempted."""
        return attempt < self.max_retries and isinstance(
            exception, (requests.exceptions.RequestException, IOError)
        )


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts using Levenshtein distance."""
    # Handle cases with empty strings
    if not text1 and not text2:
        return 1.0 # Both empty, perfect match
    if not text1 or not text2:
        return 0.0 # One empty, no similarity
    
    # Convert to lowercase for comparison
    text1 = text1.lower()
    text2 = text2.lower()
    
    # Calculate Levenshtein distance
    m, n = len(text1), len(text2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
        
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if text1[i-1] == text2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
    
    # Convert distance to similarity score (0 to 1)
    max_len = max(m, n)
    if max_len == 0:
        return 1.0
    return 1 - (dp[m][n] / max_len)


def generate_checksum(content: Union[str, bytes], algorithm: str = 'sha256') -> str:
    """Generate checksum for content using specified algorithm."""
    if isinstance(content, str):
        content = content.encode('utf-8')
    
    hasher = hashlib.new(algorithm)
    hasher.update(content)
    return hasher.hexdigest()


def setup_logging(level: str = "INFO", log_file: Optional[str] = None,
                 format_str: Optional[str] = None) -> None:
    """Configure logging with specified parameters."""
    if format_str is None:
        format_str = '%(asctime)s [%(levelname)s] %(message)s'
    
    handlers = []
    
    # Always add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(format_str))
    handlers.append(console_handler)
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(format_str))
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        handlers=handlers,
        format=format_str
    )


class Timer:
    """Context manager for timing operations."""
    def __init__(self, operation_name: str = "Operation"):
        self.operation_name = operation_name
        self.start_time = None
        self._duration = None

    def __enter__(self) -> 'Timer':
        self.start_time = time.time()
        return self

    def __exit__(self, *args):
        end_time = time.time()
        if self.start_time is not None:
            self._duration = end_time - self.start_time
            logging.info(f"{self.operation_name} took {self._duration:.2f} seconds")
        else:
            logging.warning(f"{self.operation_name} timer exited without being entered.")

    async def __aenter__(self) -> 'Timer':
        """Asynchronous entry point."""
        self.start_time = time.time() # time.time() is synchronous, okay here
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Asynchronous exit point."""
        end_time = time.time() # time.time() is synchronous, okay here
        if self.start_time is not None:
            self._duration = end_time - self.start_time
            logging.info(f"{self.operation_name} took {self._duration:.2f} seconds (async)")
        else:
            logging.warning(f"{self.operation_name} timer exited without being entered (async).")
        # Propagate exceptions if any occurred
        if exc_type:
            logging.error(f"Exception occurred within {self.operation_name} timer: {exc_val}")
        # Return False to indicate exception (if any) should be propagated
        return False

    @property
    def duration(self) -> Optional[float]:
        return self._duration


def sanitize_and_join_url(url, base_url=None):
    """Sanitize and normalize URLs, and join with base URL if necessary."""
    if not url:
        return url

    # Handle data URLs
    if url.startswith('data:'):
        return url

    # Check null/empty URLs
    if not url:
        return '#'

    try:
        # Normalize URL first
        normalized_url = url.strip().lower()

        # Check for dangerous protocols first
        if any(normalized_url.startswith(proto) for proto in ['javascript:', 'data:', 'vbscript:']):
            return '#'

        # Handle relative URLs
        if base_url and not normalized_url.startswith(('http://', 'https://', 'mailto:', 'tel:', 'ftp://')):
            resolved_url = urljoin(base_url, url)
            return resolved_url

        return url
    except Exception:
        return '#'  # Return safe URL on any error
