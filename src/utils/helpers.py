import asyncio
import hashlib
import logging
import time
from typing import Optional, Union

import requests

from src.utils.url.factory import create_url_info  # Added import for factory

# Import the new modular implementation
from src.utils.url.info import URLInfo, URLType  # Corrected import path

# Note: The URLInfo BaseModel and URLType Enum are now defined in url_info.py
# The URLInfo.from_string classmethod is also removed as instantiation handles it.


class URLProcessor:
    """Handles URL processing, normalization and validation.

    This class is an adapter for the new URLInfo implementation.
    """

    # Define constants that match the expected configuration
    ALLOWED_SCHEMES = {"http", "https"}
    ASSET_EXTENSIONS = {
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".ico",
        ".css",
        ".js",
    }

    @staticmethod
    def normalize_url(url: str, base_url: Optional[str] = None) -> str:
        """Normalize URL to canonical form."""
        logging.warning(
            "URLProcessor.normalize_url is deprecated. Use create_url_info instead."
        )
        url_info = create_url_info(url, base_url)
        return url_info.normalized_url if url_info.is_valid else url

    @classmethod
    def _determine_url_type(cls, url: str, base_url: Optional[str] = None) -> URLType:
        """Determine URL type (internal, external, asset, unknown)."""
        url_info = create_url_info(url, base_url)
        return url_info.url_type

    @classmethod
    def process_url(cls, url: str, base_url: Optional[str] = None) -> URLInfo:
        """
        Processes a URL string, returning a URLInfo object containing
        validation status, normalized form, and other details.
        """
        # Return the new URLInfo implementation.
        # It now uses the shared security config from src.utils.url.security
        return create_url_info(url, base_url)


class RateLimiter:
    """Rate limiter using token bucket algorithm."""

    def __init__(self, requests_per_second: float):
        self.rate = requests_per_second
        self.last_check = time.time()  # Use time.time for consistency
        self.tokens = requests_per_second
        self.max_tokens = requests_per_second
        self._lock = asyncio.Lock()  # Use asyncio.Lock
        # Add a logger instance for more control if needed, or use the root logger
        self.logger = logging.getLogger(f"{__name__}.RateLimiter")

    async def acquire(self) -> float:  # Make method async
        """Acquire a token, returning the time to wait if necessary."""
        self.logger.debug(
            f"Attempting to acquire token. Current tokens (approx): {self.tokens:.4f}"
        )
        async with self._lock:  # Use async with
            now = time.time()  # Use time.time for consistency
            time_passed = now - self.last_check
            self.last_check = now  # Update last_check immediately

            current_tokens_before_replenish = self.tokens
            self.tokens += time_passed * self.rate
            if self.tokens > self.max_tokens:
                self.tokens = self.max_tokens

            self.logger.debug(
                f"Inside lock: now={now:.4f}, time_passed={time_passed:.4f}, "
                f"tokens_before_rep={current_tokens_before_replenish:.4f}, rate={self.rate}, "
                f"tokens_after_rep={self.tokens:.4f}"
            )

            if self.tokens < 1.0:  # Use 1.0 for clarity with float comparison
                wait_time = (1.0 - self.tokens) / self.rate
                # It's possible tokens became slightly positive after replenishment but still < 1
                # and wait_time could be negative if tokens > 1 due to precision.
                # Ensure wait_time is non-negative.
                wait_time = max(0, wait_time)
                self.logger.debug(
                    f"Not enough tokens ({self.tokens:.4f} < 1.0). "
                    f"Calculated wait_time={wait_time:.4f}s. Returning wait_time."
                )
                self.tokens -= 1.0  # Still consume a token even when waiting
                return wait_time
            else:
                self.tokens -= 1.0
                self.logger.debug(
                    f"Token acquired. Tokens remaining: {self.tokens:.4f}. "
                    f"Returning 0.0 wait time."
                )
                return 0.0


class RetryStrategy:
    """Implements exponential backoff retry strategy."""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for current attempt."""
        delay = min(
            self.initial_delay * (self.backoff_factor ** (attempt - 1)), self.max_delay
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
        return 1.0  # Both empty, perfect match
    if not text1 or not text2:
        return 0.0  # One empty, no similarity

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
            if text1[i - 1] == text2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])

    # Convert distance to similarity score (0 to 1)
    max_len = max(m, n)
    if max_len == 0:
        return 1.0
    return 1 - (dp[m][n] / max_len)


def generate_checksum(content: Union[str, bytes], algorithm: str = "sha256") -> str:
    """Generate checksum for content using specified algorithm."""
    if isinstance(content, str):
        content = content.encode("utf-8")

    hasher = hashlib.new(algorithm)
    hasher.update(content)
    return hasher.hexdigest()


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_str: Optional[str] = None,
) -> None:
    """Configure logging with specified parameters."""
    if format_str is None:
        format_str = "%(asctime)s [%(levelname)s] %(message)s"

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
        level=getattr(logging, level.upper()), handlers=handlers, format=format_str
    )


class Timer:
    """Context manager for timing operations."""

    def __init__(self, operation_name: str = "Operation"):
        self.operation_name = operation_name
        self.start_time = None
        self._duration = None

    def __enter__(self) -> "Timer":
        self.start_time = time.time()
        return self

    def __exit__(self, *args):
        end_time = time.time()
        if self.start_time is not None:
            self._duration = end_time - self.start_time
            logging.info(f"{self.operation_name} took {self._duration:.2f} seconds")
        else:
            logging.warning(
                f"{self.operation_name} timer exited without being entered."
            )

    async def __aenter__(self) -> "Timer":
        """Asynchronous entry point."""
        self.start_time = time.time()  # time.time() is synchronous, okay here
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Asynchronous exit point."""
        end_time = time.time()  # time.time() is synchronous, okay here
        if self.start_time is not None:
            self._duration = end_time - self.start_time
            logging.info(
                f"{self.operation_name} took {self._duration:.2f} seconds (async)"
            )
        else:
            logging.warning(
                f"{self.operation_name} timer exited without being entered (async)."
            )
        # Propagate exceptions if any occurred
        if exc_type:
            logging.error(
                f"Exception occurred within {self.operation_name} timer: {exc_val}"
            )
        # Return False to indicate exception (if any) should be propagated
        return False

    @property
    def duration(self) -> Optional[float]:
        return self._duration


def sanitize_and_join_url(url, base_url=None):
    """Sanitize and normalize URLs, and join with base URL if necessary."""
    if not url:
        return url

    try:
        # Use the new URLInfo implementation via the factory
        url_info = create_url_info(url, base_url)

        # If URL is invalid, return a safe alternative
        if not url_info.is_valid:
            logging.debug(
                f"Sanitize failed for invalid URL: {url_info.raw_url} ({url_info.error_message})"
            )
            return "#"

        # Return the normalized and resolved URL
        return url_info.url  # Use the .url property which includes fragment if present
    except Exception as e:
        logging.debug(f"Error sanitizing URL '{url}': {e}")
        return "#"  # Return safe URL on any error
