import re
from urllib.parse import urljoin, urlparse, urlunparse
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from ..utils.helpers import URLInfo

@dataclass
class LinkProcessorConfig:
    """Configuration for the LinkProcessor."""
    base_url: Optional[str] = None
    allowed_schemes: List[str] = None
    allowed_domains: List[str] = None

    def __post_init__(self):
        if self.allowed_schemes is None:
            self.allowed_schemes = ['http', 'https']
        if self.allowed_domains is None:
            self.allowed_domains = []

class LinkProcessor:
    """Process and validate URLs and extract links from HTML content."""

    def __init__(self, config: Optional[Dict] = None):
        """Initialize with optional configuration."""
        if isinstance(config, dict):
            self.config = LinkProcessorConfig(
                base_url=config.get('base_url'),
                allowed_schemes=config.get('allowed_schemes', ['http', 'https']),
                allowed_domains=config.get('allowed_domains', [])
            )
        else:
            self.config = LinkProcessorConfig()

    def process_link(self, url: str) -> Dict:
        """Process a single URL and return its components and validation status."""
        if not url:
            return {
                'url': '',
                'scheme': '',
                'netloc': '',
                'path': '',
                'query': '',
                'fragment': '',
                'is_valid': False,
                'is_relative': True,
                'is_internal': False,
                'normalized_url': ''
            }

        try:
            # First check for malicious URLs
            if any(url.lower().startswith(prefix) for prefix in [
                'javascript:', 'data:', 'vbscript:', 'file:', 'about:', 'blob:'
            ]):
                return {
                    'url': url,
                    'scheme': '',
                    'netloc': '',
                    'path': '',
                    'query': '',
                    'fragment': '',
                    'is_valid': False,
                    'is_relative': False,
                    'is_internal': False,
                    'normalized_url': ''
                }

            # Handle protocol-relative URLs
            if url.startswith('//'):
                url = 'https:' + url

            # Normalize and validate the URL
            try:
                normalized_url = self.normalize_url(url)
            except Exception:
                normalized_url = url

            # Handle relative URLs
            if self.config.base_url and not urlparse(url).netloc:
                full_url = urljoin(self.config.base_url, url)
            else:
                full_url = url

            parsed = urlparse(full_url)
            scheme = parsed.scheme or 'https'
            
            result = {
                'url': url,
                'normalized_url': normalized_url,
                'scheme': scheme,
                'netloc': parsed.netloc,
                'path': parsed.path or '/',
                'query': parsed.query,
                'fragment': parsed.fragment,
                'is_valid': True,
                'is_relative': not bool(urlparse(url).netloc),
                'is_internal': self._is_internal_url(full_url)
            }

            # Validate scheme
            if scheme not in self.config.allowed_schemes:
                result['is_valid'] = False

            # Validate domain if allowed_domains is specified
            if self.config.allowed_domains and parsed.netloc:
                if not any(parsed.netloc.endswith(domain) for domain in self.config.allowed_domains):
                    result['is_valid'] = False

            # Additional validation
            if '..' in parsed.path or '%2e%2e' in parsed.path.lower():
                result['is_valid'] = False

            # Check for unsafe characters
            if re.search(r'[<>\[\]{}|\^]', url):
                result['is_valid'] = False

            return result

        except Exception as e:
            # Return invalid result instead of raising
            return {
                'url': url,
                'scheme': '',
                'netloc': '',
                'path': '',
                'query': '',
                'fragment': '',
                'is_valid': False,
                'is_relative': True,
                'is_internal': False,
                'normalized_url': '',
                'error': str(e)
            }

    def process_links(self, urls: List[str]) -> List[Dict]:
        """Process multiple URLs and return their information."""
        return [self.process_link(url) for url in urls]

    def normalize_url(self, url: str) -> str:
        """Normalize URL by resolving paths and removing fragments."""
        try:
            if not url:
                return url

            # Handle protocol-relative URLs
            if url.startswith('//'):
                url = 'https:' + url

            # Handle relative URLs
            if self.config.base_url and not urlparse(url).netloc:
                url = urljoin(self.config.base_url, url)

            # Parse and normalize
            parsed = urlparse(url)
            netloc = parsed.netloc
            path = re.sub(r'/+', '/', parsed.path)  # Normalize multiple slashes
            
            # Normalize path segments
            segments = []
            for segment in path.split('/'):
                if segment in ('', '.'):
                    continue
                elif segment == '..':
                    if segments:
                        segments.pop()
                else:
                    segments.append(segment)
            
            # Rebuild path
            normalized_path = '/' + '/'.join(segments)
            
            # Rebuild URL without fragment
            return urlunparse((
                parsed.scheme or 'https',
                netloc,
                normalized_path,
                '',  # params
                parsed.query,
                ''  # fragment
            ))

        except Exception:
            return url

    def extract_links(self, soup: BeautifulSoup, base_url: Optional[str] = None) -> List[str]:
        """Extract, process, and return a list of unique, valid URL strings from links."""
        seen_urls: Set[str] = set()
        extracted_urls = []

        # Update internal config base_url if provided
        original_config_base_url = self.config.base_url
        if base_url:
             self.config.base_url = base_url

        for a in soup.find_all('a', href=True):
            href = a.get('href', '').strip()
            if not href:
                continue

            try:
                # Process the link to get normalized URL and validity
                # Use the potentially updated base_url from config
                link_info = self.process_link(href)

                # Use the normalized URL for checks and storage
                normalized_url = link_info.get('normalized_url')

                if link_info.get('is_valid') and normalized_url:
                    # Skip if we've seen this normalized URL
                    if normalized_url in seen_urls:
                        continue

                    # Add the valid, normalized URL to the list
                    seen_urls.add(normalized_url)
                    extracted_urls.append(normalized_url)

            except Exception as e: # Catch potential errors during processing
                 print(f"Error processing link '{href}': {e}") # Basic error logging
                 continue
        
        # Restore original config base_url if it was temporarily changed
        self.config.base_url = original_config_base_url

        return extracted_urls

    def extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text content using regex."""
        url_pattern = r'https?://[^\s<>"\']+|/[^\s<>"\']+(?=[\s<>"\']|$)'
        return re.findall(url_pattern, text)

    def _is_internal_url(self, url: str) -> bool:
        """Check if URL is internal based on base_url configuration."""
        if not self.config.base_url:
            return False
            
        base_domain = urlparse(self.config.base_url).netloc
        url_domain = urlparse(url).netloc
        
        return not url_domain or url_domain == base_domain
