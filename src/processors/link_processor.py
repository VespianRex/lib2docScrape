"""Link processor module for handling and validating URLs and links."""

from typing import Dict, Any, List, Optional, Set
from urllib.parse import urljoin, urlparse
import re

class LinkProcessor:
    """Processes and validates links and URLs."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the link processor with optional configuration.
        
        Args:
            config: Optional configuration dictionary with processing rules
        """
        self.config = config or {}
        self.base_url = self.config.get('base_url', '')
        self.allowed_schemes = set(self.config.get('allowed_schemes', ['http', 'https']))
        self.allowed_domains = set(self.config.get('allowed_domains', []))

    def process_link(self, url: str) -> Dict[str, Any]:
        """Process a single URL and return its components and validation status.
        
        Args:
            url: The URL to process
            
        Returns:
            Dict containing processed URL information
        """
        try:
            # Resolve relative URLs if base_url is provided
            if self.base_url and not bool(urlparse(url).netloc):
                url = urljoin(self.base_url, url)
            
            parsed = urlparse(url)
            is_valid = self._validate_url(parsed)
            
            return {
                'url': url,
                'scheme': parsed.scheme,
                'netloc': parsed.netloc,
                'path': parsed.path,
                'params': parsed.params,
                'query': parsed.query,
                'fragment': parsed.fragment,
                'is_valid': is_valid,
                'is_relative': not bool(parsed.netloc),
                'is_internal': self._is_internal_link(parsed)
            }
        except Exception as e:
            raise ValueError(f"Failed to process link: {str(e)}")

    def process_links(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Process multiple URLs and return their processed information.
        
        Args:
            urls: List of URLs to process
            
        Returns:
            List of processed URL information
        """
        return [self.process_link(url) for url in urls]

    def _validate_url(self, parsed_url: urlparse) -> bool:
        """Validate a parsed URL against configuration rules."""
        # Check scheme
        if parsed_url.scheme and parsed_url.scheme not in self.allowed_schemes:
            return False
        
        # Check domain if allowed_domains is specified
        if self.allowed_domains and parsed_url.netloc:
            domain = parsed_url.netloc.lower().split(':')[0]  # Remove port if present
            if not any(domain.endswith(d) for d in self.allowed_domains):
                return False
        
        # Check for common issues
        if parsed_url.netloc:
            # Check for invalid characters in domain, allowing for ports
            domain = parsed_url.netloc.split(':')[0]  # Remove port if present
            if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*$', domain):
                return False
        
        return True

    def _is_internal_link(self, parsed_url: urlparse) -> bool:
        """Check if a URL is internal based on the base_url."""
        if not self.base_url:
            return False
        
        base_parsed = urlparse(self.base_url)
        return (not parsed_url.netloc or 
                parsed_url.netloc == base_parsed.netloc)

    def normalize_url(self, url: str) -> str:
        """Normalize a URL by resolving relative paths and removing fragments.
        
        Args:
            url: The URL to normalize
            
        Returns:
            Normalized URL string
        """
        if not url:
            return url
            
        # Handle protocol-relative URLs
        if url.startswith('//'):
            url = f'https:{url}'
            
        # Parse the URL
        parsed = urlparse(url)
        
        # If it's a relative URL and we have a base_url, resolve it
        if not parsed.netloc and self.base_url:
            url = urljoin(self.base_url, url)
            parsed = urlparse(url)
            
        # Remove fragments
        url = parsed.geturl().split('#')[0]
        
        # Normalize path
        if parsed.path:
            # Split path into segments
            segments = parsed.path.split('/')
            normalized = []
            for segment in segments:
                if segment == '.' or not segment:
                    continue
                elif segment == '..':
                    if normalized:
                        normalized.pop()
                else:
                    normalized.append(segment)
            
            # Reconstruct the URL with normalized path
            path = '/' + '/'.join(normalized)
            if parsed.netloc:
                scheme = parsed.scheme or 'https'
                url = f"{scheme}://{parsed.netloc}{path}"
                if parsed.query:
                    url = f"{url}?{parsed.query}"
            else:
                url = path
                if parsed.query:
                    url = f"{url}?{parsed.query}"
                    
        return url

    def extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text content.
        
        Args:
            text: Text content to extract URLs from
            
        Returns:
            List of extracted URLs
        """
        # URL pattern matching both http(s) and relative URLs
        url_pattern = r'(?:https?://[^\s<>"]+|/[^\s<>"]+)'
        return re.findall(url_pattern, text)

    def extract_links(self, soup, base_url: str = None) -> List[Dict[str, Any]]:
        """Extract and process links from a BeautifulSoup object.
        
        Args:
            soup: BeautifulSoup object containing HTML content
            base_url: Optional base URL for resolving relative links
            
        Returns:
            List of dictionaries containing processed link information
        """
        if base_url:
            self.base_url = base_url
            
        links = []
        seen_urls = set()  # Track normalized URLs to avoid duplicates
        
        for link in soup.find_all('a', href=True):
            url = link['href']
            text = link.get_text(strip=True)
            
            # Skip empty URLs
            if not url:
                continue
                
            # Process and normalize the URL
            processed = self.process_link(url)
            normalized_url = self.normalize_url(processed['url'])
            
            # Skip if we've seen this URL before
            if normalized_url in seen_urls:
                continue
                
            seen_urls.add(normalized_url)
            processed['text'] = text
            processed['url'] = normalized_url
            
            # Only include valid URLs with allowed schemes
            if processed['is_valid']:
                links.append(processed)
            
        return links
