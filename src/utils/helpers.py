import re
import time
import idna
import hashlib
import logging
import threading
import requests
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from urllib.parse import urlparse, urljoin, urlunparse, parse_qs, parse_qsl, urlencode
from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel, Field, validator
import ipaddress


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
    error_msg: Optional[str] = Field(default=None, description="Error message if invalid")
    url_type: URLType = Field(default=URLType.UNKNOWN, description="URL type")

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
        if not url:
            raise ValueError("URL cannot be empty")

        # Handle relative URLs
        if base_url and not urlparse(url).netloc:
            url = urljoin(base_url, url)

        # Parse the URL
        parsed = urlparse(url)
        
        # Convert to lowercase and handle Unicode domains
        netloc = parsed.netloc.lower()
        if netloc:
            try:
                # Convert Unicode domain to IDNA
                ascii_domain = idna.encode(netloc.split(':')[0]).decode('ascii')
                if ':' in netloc:
                    port = netloc.split(':')[1]
                    if ((parsed.scheme == 'http' and port == '80') or 
                        (parsed.scheme == 'https' and port == '443')):
                        netloc = ascii_domain
                    else:
                        netloc = f"{ascii_domain}:{port}"
                else:
                    netloc = ascii_domain
            except Exception:
                # If IDNA encoding fails, keep original
                pass

        # Normalize path
        path = parsed.path.lower()
        if not path:
            path = '/'
        elif len(path) > 1:
            path = path.rstrip('/')

        # Handle query parameters
        if parsed.query:
            # Parse and sort query parameters
            params = parse_qsl(parsed.query, keep_blank_values=True)
            # Group by parameter name and keep last value
            param_dict = {}
            for k, v in params:
                param_dict[k] = v
            # Sort parameters by name
            sorted_params = sorted(param_dict.items())
            query = urlencode(sorted_params)
        else:
            query = ''

        # Rebuild URL without fragment
        normalized = urlunparse((
            parsed.scheme.lower(),
            netloc,
            path,
            '',  # params
            query,
            ''  # fragment
        ))

        return normalized

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
        """Process URL and return comprehensive URL information."""
        try:
            if not isinstance(url, str):
                raise ValueError("URL must be a string")

            if not url:
                raise ValueError("URL cannot be empty")

            # First normalize the URL
            normalized = cls.normalize_url(url, base_url)
            parsed = urlparse(normalized)

            # Basic validation
            if not parsed.scheme or parsed.scheme not in cls.ALLOWED_SCHEMES:
                raise ValueError(f"Invalid or unsupported URL scheme: {parsed.scheme}")

            # Check for invalid characters
            if cls.INVALID_CHARS.search(parsed.path):
                raise ValueError("URL contains invalid characters")

            # Check for path traversal
            if cls.INVALID_PATH_TRAVERSAL.search(parsed.path):
                raise ValueError("URL contains path traversal")

            # Check path length
            if len(parsed.path) > cls.MAX_PATH_LENGTH:
                raise ValueError("URL path too long")

            # Check query length
            if len(parsed.query) > cls.MAX_QUERY_LENGTH:
                raise ValueError("URL query too long")

            # Check for authentication
            if '@' in parsed.netloc:
                raise ValueError("Authentication in URL not allowed")

            # Check for private IPs
            if parsed.netloc:
                ip = parsed.netloc.split(':')[0]
                try:
                    ip_obj = ipaddress.ip_address(ip)
                    if (ip_obj.is_private or ip_obj.is_loopback or 
                        ip_obj.is_unspecified or ip_obj.is_link_local):
                        raise ValueError("Private/localhost IP not allowed")
                except ValueError:
                    # Not an IP address, continue with domain validation
                    pass

            # Check domain
            if parsed.netloc:
                parts = parsed.netloc.split('.')
                if len(parts) < 2:
                    raise ValueError("Invalid domain: missing TLD")
                if any(not part for part in parts):
                    raise ValueError("Invalid domain: empty label")
                if any(len(part) > 63 for part in parts):
                    raise ValueError("Invalid domain: label too long")

            # Determine URL type
            url_type = cls._determine_url_type(normalized, base_url)

            return URLInfo(
                raw_url=url,
                normalized_url=normalized,
                scheme=parsed.scheme,
                netloc=parsed.netloc,
                path=parsed.path,
                is_valid=True,
                error_msg=None,
                url_type=url_type
            )

        except Exception as e:
            return URLInfo(
                raw_url=url,
                normalized_url=url if isinstance(url, str) else "",
                scheme='unknown',
                netloc='',
                path='',
                is_valid=False,
                error_msg=str(e),
                url_type=URLType.UNKNOWN
            )


class RateLimiter:
    """Rate limiter using token bucket algorithm."""
    def __init__(self, requests_per_second: float):
        self.rate = requests_per_second
        self.last_check = time.time()
        self.tokens = requests_per_second
        self.max_tokens = requests_per_second
        self._lock = threading.Lock()

    def acquire(self) -> float:
        """Acquire a token, returning the time to wait if necessary."""
        with self._lock:
            now = time.time()
            time_passed = now - self.last_check
            self.tokens = min(self.max_tokens, self.tokens + time_passed * self.rate)
            self.last_check = now

            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.rate
                return wait_time

            self.tokens -= 1
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
    if not text1 or not text2:
        return 0.0
    
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
        self._duration = end_time - self.start_time
        logging.info(f"{self.operation_name} took {self._duration:.2f} seconds")

    @property
    def duration(self) -> Optional[float]:
        return self._duration