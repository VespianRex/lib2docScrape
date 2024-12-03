import hashlib
import logging
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from urllib.parse import urlparse, urljoin, urlunparse
from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel, Field, validator


class URLType(Enum):
    INTERNAL = "internal"
    EXTERNAL = "external"
    ASSET = "asset"
    UNKNOWN = "unknown"


class URLInfo(BaseModel):
    """Model for URL information."""
    raw_url: str = Field(description="Original raw URL")
    normalized_url: str = Field(description="Normalized URL")
    scheme: str = Field(description="URL scheme (http/https)")
    netloc: str = Field(description="Network location")
    path: str = Field(description="URL path")
    is_valid: bool = Field(description="URL validity flag")
    error_msg: str = Field(default="", description="Error message if invalid")

    @property
    def normalized(self) -> str:
        """Get normalized URL."""
        return self.normalized_url

    @property
    def original(self) -> str:
        """Get original URL."""
        return self.raw_url

    @property
    def domain(self) -> str:
        """Get domain name."""
        return self.netloc.split(':')[0]

    def __hash__(self):
        return hash(self.normalized_url)

    def __eq__(self, other):
        if not isinstance(other, URLInfo):
            return False
        return self.normalized_url == other.normalized_url

    @classmethod
    def from_string(cls, url: str, base_url: Optional[str] = None) -> 'URLInfo':
        """Create URLInfo from string."""
        try:
            # Handle None or empty URL
            if not url:
                return cls(
                    raw_url=url or "",
                    normalized_url="",
                    scheme="",
                    netloc="",
                    path="",
                    is_valid=False,
                    error_msg="Empty URL"
                )

            # Handle protocol-relative URLs
            if url.startswith('//'):
                url = 'http:' + url

            # Handle relative URLs
            if base_url and not url.startswith(('http://', 'https://')):
                url = urljoin(base_url, url)

            # Parse URL
            parsed = urlparse(url)
            
            # Normalize scheme
            scheme = parsed.scheme.lower() or 'http'
            
            # Normalize netloc
            netloc = parsed.netloc
            if not netloc and parsed.path:
                # Handle URLs like "example.com/path"
                path_parts = parsed.path.split('/', 1)
                netloc = path_parts[0]
                path = '/' + path_parts[1] if len(path_parts) > 1 else '/'
            else:
                path = parsed.path

            # Remove default ports
            if ':' in netloc:
                domain, port = netloc.split(':')
                if (scheme == 'http' and port == '80') or (scheme == 'https' and port == '443'):
                    netloc = domain

            # Normalize path
            if not path:
                path = '/'
            else:
                # Remove duplicate slashes
                path = re.sub(r'/+', '/', path)
                # Resolve . and .. in path
                segments = []
                for segment in path.split('/'):
                    if segment == '.' or not segment:
                        continue
                    elif segment == '..':
                        if segments:
                            segments.pop()
                    else:
                        segments.append(segment)
                path = '/' + '/'.join(segments)

            # Handle security checks
            if any(x in url.lower() for x in ['javascript:', 'data:', '<script', 'alert(', 'eval(']):
                return cls(
                    raw_url=url,
                    normalized_url="",
                    scheme="",
                    netloc="",
                    path="",
                    is_valid=False,
                    error_msg="Potentially malicious URL"
                )

            # Build normalized URL
            normalized = urlunparse((
                scheme,
                netloc,
                path,
                '',  # Remove params
                parsed.query,
                ''  # Remove fragment
            ))

            return cls(
                raw_url=url,
                normalized_url=normalized,
                scheme=scheme,
                netloc=netloc,
                path=path,
                is_valid=True
            )

        except Exception as e:
            return cls(
                raw_url=url or "",
                normalized_url="",
                scheme="",
                netloc="",
                path="",
                is_valid=False,
                error_msg=f"URL normalization failed: {str(e)}"
            )


class URLProcessor:
    """Handles URL processing, normalization and validation."""

    ALLOWED_SCHEMES = {'http', 'https'}
    ASSET_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.css', '.js'}

    @staticmethod
    def normalize_url(url: str, base_url: Optional[str] = None) -> str:
        """Normalize URL by handling Unicode domains and joining with base URL if needed."""
        try:
            if base_url and not bool(urlparse(url).netloc):
                url = urljoin(base_url, url)

            parsed = urlparse(url)
            # Convert domain to ASCII using IDNA encoding
            if parsed.netloc:
                ascii_domain = idna.encode(parsed.netloc).decode('ascii')
                # Reconstruct URL with encoded domain
                url = urlunparse(parsed._replace(netloc=ascii_domain))

            return url.rstrip('/')
        except Exception as e:
            raise ValueError(f"URL normalization failed: {str(e)}")

    @classmethod
    def process_url(cls, url: str, base_url: Optional[str] = None) -> URLInfo:
        """Process URL and return comprehensive URL information."""
        try:
            normalized = cls.normalize_url(url, base_url)
            parsed = urlparse(normalized)

            # Basic validation
            if not parsed.scheme or parsed.scheme not in cls.ALLOWED_SCHEMES:
                return URLInfo(
                    raw_url=url,
                    normalized_url=normalized,
                    scheme=parsed.scheme,
                    netloc=parsed.netloc,
                    path=parsed.path,
                    is_valid=False,
                    error_msg="Invalid or unsupported URL scheme"
                )

            # Determine URL type
            url_type = cls._determine_url_type(normalized, base_url)

            return URLInfo(
                raw_url=url,
                normalized_url=normalized,
                scheme=parsed.scheme,
                netloc=parsed.netloc,
                path=parsed.path,
                is_valid=True
            )

        except Exception as e:
            return URLInfo(
                raw_url=url,
                normalized_url=url,
                scheme='unknown',
                netloc='',
                path='',
                is_valid=False,
                error_msg=str(e)
            )

    @classmethod
    def _determine_url_type(cls, url: str, base_url: Optional[str] = None) -> URLType:
        """Determine URL type based on extension and relation to base URL."""
        parsed = urlparse(url)
        path_lower = parsed.path.lower()

        # Check if it's an asset URL
        if any(path_lower.endswith(ext) for ext in cls.ASSET_EXTENSIONS):
            return URLType.ASSET

        # Check if internal/external
        if base_url:
            base_domain = urlparse(base_url).netloc
            if parsed.netloc == base_domain:
                return URLType.INTERNAL
            return URLType.EXTERNAL

        return URLType.UNKNOWN


class RateLimiter:
    """Rate limiter for controlling request frequency."""

    def __init__(self, requests_per_second: float = 1.0):
        """
        Initialize rate limiter.

        Args:
            requests_per_second: Maximum requests per second
        """
        self.min_interval = 1.0 / requests_per_second
        self.last_request = 0.0

    def wait(self) -> None:
        """Wait if necessary to maintain rate limit."""
        now = time.time()
        elapsed = now - self.last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request = time.time()


class RetryStrategy:
    """Implements exponential backoff retry strategy."""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0
    ):
        """
        Initialize retry strategy.

        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            backoff_factor: Factor to increase delay by after each retry
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor

    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay for current attempt.

        Args:
            attempt: Current attempt number

        Returns:
            Delay in seconds
        """
        delay = self.initial_delay * (self.backoff_factor ** (attempt - 1))
        return min(delay, self.max_delay)


class Timer:
    """Context manager for timing code execution."""

    def __init__(self, name: str = "Operation"):
        """
        Initialize timer.

        Args:
            name: Name of the operation being timed
        """
        self.name = name
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def __enter__(self) -> 'Timer':
        """Start timing."""
        self.start_time = time.time()
        return self

    def __exit__(self, *args: Any) -> None:
        """Stop timing and log duration."""
        self.end_time = time.time()
        duration = self.end_time - (self.start_time or 0.0)
        logging.info(f"{self.name} took {duration:.2f} seconds")

    @property
    def duration(self) -> Optional[float]:
        """Get operation duration."""
        if self.start_time is None or self.end_time is None:
            return None
        return self.end_time - self.start_time


def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate text similarity using Jaccard similarity of word sets.

    Args:
        text1: First text
        text2: Second text

    Returns:
        Similarity score between 0 and 1
    """
    # Tokenize and create sets
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    # Calculate Jaccard similarity
    intersection = len(words1 & words2)
    union = len(words1 | words2)

    return intersection / union if union > 0 else 0.0


def generate_checksum(content: Union[str, bytes, Dict[str, Any]]) -> str:
    """
    Generate SHA-256 checksum of content.

    Args:
        content: Content to generate checksum for

    Returns:
        Hexadecimal checksum string
    """
    if isinstance(content, dict):
        content = str(sorted(content.items()))
    elif isinstance(content, str):
        content = content.encode('utf-8')

    return hashlib.sha256(content).hexdigest()


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
):
    """
    Setup logging configuration.

    Args:
        level: Logging level
        log_file: Optional log file path
        format_string: Optional log format string
    """
    if not format_string:
        format_string = '%(asctime)s [%(levelname)s] %(message)s'

    handlers = []

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(format_string))
    handlers.append(console_handler)

    # File handler if specified
    if log_file:
        # Create a rotating file handler that overwrites the file each run
        file_handler = logging.FileHandler(log_file, mode='w')
        file_handler.setFormatter(logging.Formatter(format_string))
        handlers.append(file_handler)

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        handlers=handlers,
        force=True  # Override any existing configuration
    )

    # Set more verbose logging for our module
    logging.getLogger('lib2docscrape').setLevel(logging.DEBUG)