"""Link processor module for handling and validating URLs and links."""

from typing import Dict, Any, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
import re
import idna
import ipaddress
from dataclasses import dataclass
from bs4 import BeautifulSoup

@dataclass
class LinkConfig:
    """Configuration for link processing."""
    base_url: str = ''
    allowed_schemes: Set[str] = None
    allowed_domains: Set[str] = None
    max_url_length: int = 2048
    max_query_length: int = 1024
    max_path_length: int = 1024
    block_private_ips: bool = True
    sanitize_fragments: bool = True
    normalize_idna: bool = True
    sort_query_params: bool = True
    remove_default_ports: bool = True
    strip_authentication: bool = True
    allowed_ports: Set[int] = None
    blocked_extensions: Set[str] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.allowed_schemes is None:
            self.allowed_schemes = {'http', 'https'}
        if self.allowed_ports is None:
            self.allowed_ports = {80, 443, 8080, 8443}
        if self.blocked_extensions is None:
            self.blocked_extensions = {'.exe', '.dll', '.bat', '.sh', '.jar', '.app'}

class LinkProcessor:
    """Processes and validates links and URLs."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the link processor with optional configuration.
        
        Args:
            config: Optional configuration dictionary with processing rules
        """
        self.config = LinkConfig(**config) if config else LinkConfig()
        self._url_pattern = re.compile(
            r'(?:(?:https?|ftp):\/\/)?'  # scheme
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # port
            r'(?:\/[^\"\'<>\s\[\]\{\}\|\\^`\s]+)?'  # path
            r'(?:\?[^\"\'<>\s\[\]\{\}\|\\^`\s]*)?'  # query string
            r'(?:#[^\"\'<>\s\[\]\{\}\|\\^`\s]*)?',  # fragment
            re.IGNORECASE
        )

    def process_link(self, url: str) -> Dict[str, Any]:
        """Process a single URL and return its components and validation status.
        
        Args:
            url: The URL to process
            
        Returns:
            Dict containing processed URL information
        """
        try:
            # Handle protocol-relative URLs
            if url.startswith('//'):
                url = f'https:{url}'

            # Resolve relative URLs if base_url is provided
            if self.config.base_url and not bool(urlparse(url).netloc):
                url = urljoin(self.config.base_url, url)
            
            parsed = urlparse(url)
            validation_result, issues = self._validate_url(parsed)
            normalized_url = self._normalize_url(parsed) if validation_result else url
            
            return {
                'original_url': url,
                'normalized_url': normalized_url,
                'scheme': parsed.scheme or '',
                'netloc': parsed.netloc,
                'path': parsed.path,
                'params': parsed.params,
                'query': parsed.query,
                'fragment': parsed.fragment,
                'is_valid': validation_result,
                'validation_issues': issues,
                'is_relative': not bool(parsed.netloc),
                'is_internal': self._is_internal_link(parsed),
                'is_secure': parsed.scheme == 'https',
                'has_auth': '@' in parsed.netloc,
                'port': parsed.port,
                'domain': parsed.hostname,
                'query_params': parse_qs(parsed.query)
            }
        except Exception as e:
            return {
                'original_url': url,
                'normalized_url': '',
                'is_valid': False,
                'validation_issues': [str(e)],
                'is_relative': True,
                'is_internal': False,
                'is_secure': False
            }

    def _validate_url(self, parsed_url: urlparse) -> Tuple[bool, List[str]]:
        """Validate a parsed URL against configuration rules."""
        issues = []
        
        # Check URL length
        full_url = parsed_url.geturl()
        if len(full_url) > self.config.max_url_length:
            issues.append(f"URL exceeds maximum length of {self.config.max_url_length}")

        # Check scheme
        if parsed_url.scheme and parsed_url.scheme not in self.config.allowed_schemes:
            issues.append(f"Scheme '{parsed_url.scheme}' not allowed")

        # Check domain and port
        if parsed_url.netloc:
            domain = parsed_url.hostname or ''
            port = parsed_url.port

            # Check for private IPs
            if self.config.block_private_ips and domain:
                try:
                    ip = ipaddress.ip_address(domain)
                    if ip.is_private:
                        issues.append("Private IP addresses not allowed")
                except ValueError:
                    pass  # Not an IP address

            # Check domain format
            if domain:
                try:
                    idna.encode(domain)
                except idna.IDNAError:
                    issues.append("Invalid domain encoding")

            # Check port
            if port is not None and port not in self.config.allowed_ports:
                issues.append(f"Port {port} not allowed")

        # Check path length and extension
        if parsed_url.path:
            if len(parsed_url.path) > self.config.max_path_length:
                issues.append(f"Path exceeds maximum length of {self.config.max_path_length}")
            
            ext = parsed_url.path.lower().split('.')[-1] if '.' in parsed_url.path else ''
            if f'.{ext}' in self.config.blocked_extensions:
                issues.append(f"File extension '.{ext}' not allowed")

        # Check query length
        if parsed_url.query and len(parsed_url.query) > self.config.max_query_length:
            issues.append(f"Query string exceeds maximum length of {self.config.max_query_length}")

        return len(issues) == 0, issues

    def _normalize_url(self, parsed_url: urlparse) -> str:
        """Normalize a URL by applying various transformations."""
        # Start with scheme and netloc
        scheme = parsed_url.scheme or 'https'
        netloc = parsed_url.netloc

        # Handle IDNA encoding for domain
        if self.config.normalize_idna and netloc:
            try:
                domain = parsed_url.hostname or ''
                port = f":{parsed_url.port}" if parsed_url.port else ''
                netloc = idna.encode(domain).decode('ascii') + port
            except idna.IDNAError:
                pass

        # Remove default ports if configured
        if self.config.remove_default_ports and netloc:
            if ':80' in netloc and scheme == 'http':
                netloc = netloc.replace(':80', '')
            elif ':443' in netloc and scheme == 'https':
                netloc = netloc.replace(':443', '')

        # Strip authentication if configured
        if self.config.strip_authentication and '@' in netloc:
            netloc = netloc.split('@')[1]

        # Normalize path
        path = self._normalize_path(parsed_url.path)

        # Sort query parameters if configured
        query = parsed_url.query
        if self.config.sort_query_params and query:
            params = parse_qs(query, keep_blank_values=True)
            sorted_params = []
            for key in sorted(params.keys()):
                sorted_params.extend((key, val) for val in sorted(params[key]))
            query = urlencode(sorted_params)

        # Build normalized URL
        url_parts = [
            f"{scheme}://" if scheme else '',
            netloc,
            path,
            f"?{query}" if query else '',
            f"#{parsed_url.fragment}" if parsed_url.fragment and not self.config.sanitize_fragments else ''
        ]
        
        return ''.join(url_parts)

    def _normalize_path(self, path: str) -> str:
        """Normalize URL path."""
        if not path:
            return '/'

        # Split path into segments
        segments = path.split('/')
        normalized = []
        
        for segment in segments:
            if segment in ('', '.'):
                continue
            elif segment == '..':
                if normalized:
                    normalized.pop()
            else:
                normalized.append(segment)

        # Ensure leading slash
        return '/' + '/'.join(normalized)

    def _is_internal_link(self, parsed_url: urlparse) -> bool:
        """Check if a URL is internal based on the base_url."""
        if not self.config.base_url:
            return False
        
        base_parsed = urlparse(self.config.base_url)
        return (not parsed_url.netloc or 
                parsed_url.netloc.lower() == base_parsed.netloc.lower())

    def extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text content."""
        if not text:
            return []
        
        matches = self._url_pattern.finditer(text)
        return [match.group() for match in matches]

    def extract_links(self, soup: BeautifulSoup, base_url: Optional[str] = None) -> List[Dict[str, Any]]:
        """Extract and process links from a BeautifulSoup object."""
        if base_url:
            old_base = self.config.base_url
            self.config.base_url = base_url

        try:
            links = []
            for tag in soup.find_all(['a', 'link', 'script', 'img', 'iframe', 'source']):
                url = None
                if tag.name == 'a' and tag.get('href'):
                    url = tag['href']
                elif tag.name in ('link', 'script', 'img', 'iframe', 'source') and tag.get('src'):
                    url = tag['src']

                if url:
                    link_info = self.process_link(url)
                    link_info['element_type'] = tag.name
                    link_info['attributes'] = dict(tag.attrs)
                    links.append(link_info)

            return links
        finally:
            if base_url:
                self.config.base_url = old_base

    def process_links(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Process multiple URLs and return their processed information."""
        return [self.process_link(url) for url in urls if url]
