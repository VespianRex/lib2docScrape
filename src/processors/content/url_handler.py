"""URL handling and sanitization functionality."""
import logging
from dataclasses import dataclass
from urllib.parse import urlparse

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class URLInfo:
    """Structured information about a URL."""
    original_url: str
    normalized_url: str = ""
    scheme: str = ""
    netloc: str = ""
    path: str = ""
    query: str = ""
    fragment: str = ""

    def __post_init__(self):
        dangerous_prefixes = ('javascript:', 'data:', 'vbscript:')
        low = self.original_url.strip().lower()
        if low.startswith(dangerous_prefixes):
            # Mark unsafe URLs as '#'
            self.normalized_url = '#'
            self.scheme = ''
            self.netloc = ''
            self.path = ''
            self.query = ''
            self.fragment = ''
        else:
            try:
                parsed = urlparse(self.original_url)
                hostname = parsed.hostname
                if hostname:
                    # Convert hostname to punycode
                    idna_netloc = hostname.encode('idna').decode('ascii')
                    port = f":{parsed.port}" if parsed.port else ""
                    new_parsed = parsed._replace(netloc=idna_netloc + port)
                else:
                    new_parsed = parsed

                # Manually reconstruct the URL, preserving trailing slash
                path = new_parsed.path
                if self.original_url.find("?") > 0 and self.original_url.find("?") == (self.original_url.rfind("/") + 1):
                  if path and not path.endswith('/'):
                    path += '/'
                print(f"Original URL: {self.original_url}, Path: {path}") # Debug print
                self.normalized_url = new_parsed.scheme + "://" + new_parsed.netloc + path
                if new_parsed.query:
                    self.normalized_url += "?" + new_parsed.query
                if new_parsed.fragment:
                    self.normalized_url += "#" + new_parsed.fragment

                self.scheme = new_parsed.scheme
                self.netloc = new_parsed.netloc
                self.path = new_parsed.path
                self.query = new_parsed.query
                self.fragment = new_parsed.fragment
            except Exception:
                self.normalized_url = self.original_url

    @property
    def is_secure(self):
        dangerous_prefixes = ('javascript:', 'data:', 'vbscript:')
        return not self.original_url.strip().lower().startswith(dangerous_prefixes)


def is_safe_url(url: str) -> bool:
    """Check if URL is safe to use."""
    if not url:
        return False
        
    # Allow data URLs only for images
    if url.startswith('data:'):
        return url.startswith('data:image/')
    
    # Check for dangerous protocols
    if any(url.lower().startswith(proto) for proto in [
        'javascript:', 'data:', 'vbscript:', 'file:', 'about:', 'blob:'
    ]):
        return False
    
    try:
        parsed = urlparse(url)
        return bool(parsed.netloc) and parsed.scheme in ['http', 'https', 'ftp', 'mailto']
    except Exception:
        return False


def sanitize_and_join_url(url: str, base_url: str = None) -> str:
    """Sanitize and join URLs, returning safe URLs or empty string."""
    if not url:
        return ''
        
    url = url.strip()
    if not url:
        return ''

    # Handle data URLs for images
    if url.startswith('data:image/'):
        return url

    # Check for dangerous protocols
    if any(url.lower().startswith(proto) for proto in [
        'javascript:', 'data:', 'vbscript:', 'file:', 'about:', 'blob:'
    ]):
        return ''

    try:
        if base_url:
            # Join with base URL if provided
            from urllib.parse import urljoin
            url = urljoin(base_url, url)
        
        # Parse and validate URL
        parsed = urlparse(url)
        if parsed.scheme and parsed.scheme not in ['http', 'https', 'ftp', 'mailto']:
            return ''
        
        return url
    except Exception as e:
        logger.warning(f"Error processing URL {url}: {str(e)}")
        return ''