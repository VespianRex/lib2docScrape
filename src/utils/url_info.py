"""URL information and validation utilities."""
import re
import unicodedata
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse, urljoin, urlunparse, quote, unquote

@dataclass(frozen=True)
class URLInfo:
    """Immutable URL information class."""
    raw_url: str
    normalized_url: str
    scheme: str
    netloc: str
    path: str
    is_valid: bool
    error_msg: str

    @classmethod
    def from_string(cls, url: str) -> 'URLInfo':
        """Create URLInfo from string URL."""
        if not url:
            return cls(
                raw_url=url,
                normalized_url='',
                scheme='',
                netloc='',
                path='',
                is_valid=False,
                error_msg='Empty URL'
            )

        # Normalize URL
        try:
            # Add scheme if missing
            if not url.startswith(('http://', 'https://')):
                url = 'http://' + url

            # Parse URL
            parsed = urlparse(url)
            
            # Validate scheme
            if parsed.scheme not in ('http', 'https'):
                return cls(
                    raw_url=url,
                    normalized_url='',
                    scheme='',
                    netloc='',
                    path='',
                    is_valid=False,
                    error_msg=f'Invalid scheme: {parsed.scheme}'
                )

            # Normalize components
            scheme = parsed.scheme.lower()
            netloc = parsed.netloc.lower()
            path = cls._normalize_path(parsed.path)
            query = parsed.query
            fragment = ''  # Ignore fragments

            # Build normalized URL
            normalized = urlunparse((
                scheme,
                netloc,
                path,
                '',  # params
                query,
                fragment
            ))

            # Validate URL components
            if not cls._is_valid_netloc(netloc):
                return cls(
                    raw_url=url,
                    normalized_url='',
                    scheme='',
                    netloc='',
                    path='',
                    is_valid=False,
                    error_msg=f'Invalid domain: {netloc}'
                )

            if not cls._is_valid_path(path):
                return cls(
                    raw_url=url,
                    normalized_url='',
                    scheme='',
                    netloc='',
                    path='',
                    is_valid=False,
                    error_msg=f'Invalid path: {path}'
                )

            # Create URLInfo
            return cls(
                raw_url=url,
                normalized_url=normalized,
                scheme=scheme,
                netloc=netloc,
                path=path,
                is_valid=True,
                error_msg=''
            )

        except Exception as e:
            return cls(
                raw_url=url,
                normalized_url='',
                scheme='',
                netloc='',
                path='',
                is_valid=False,
                error_msg=str(e)
            )

    @staticmethod
    def _normalize_path(path: str) -> str:
        """Normalize URL path."""
        if not path:
            return '/'

        # Normalize slashes
        path = re.sub(r'/+', '/', path)
        
        # Remove dot segments
        segments = []
        for segment in path.split('/'):
            if segment in ('', '.'):
                continue
            if segment == '..':
                if segments:
                    segments.pop()
                continue
            segments.append(segment)

        # Build normalized path
        normalized = '/' + '/'.join(segments)
        
        # Add trailing slash for directories
        if path.endswith('/'):
            normalized += '/'

        return normalized

    @staticmethod
    def _is_valid_netloc(netloc: str) -> bool:
        """Validate domain name."""
        if not netloc:
            return False

        # Check for invalid characters
        if re.search(r'[^a-z0-9.-]', netloc):
            return False

        # Check length constraints
        if len(netloc) > 255:
            return False

        # Check label constraints
        labels = netloc.split('.')
        if len(labels) < 2:
            return False

        for label in labels:
            if not label:
                return False
            if len(label) > 63:
                return False
            if label.startswith('-') or label.endswith('-'):
                return False

        return True

    @staticmethod
    def _is_valid_path(path: str) -> bool:
        """Validate URL path."""
        if not path:
            return False

        # Must start with slash
        if not path.startswith('/'):
            return False

        # Check for invalid characters
        if re.search(r'[^a-zA-Z0-9._~!$&\'()*+,;=:@/-]', unquote(path)):
            return False

        # Check for directory traversal
        if '..' in path.split('/'):
            return False

        return True

    def __eq__(self, other: object) -> bool:
        """Compare normalized URLs."""
        if not isinstance(other, URLInfo):
            return NotImplemented
        return self.normalized_url == other.normalized_url

    def __hash__(self) -> int:
        """Hash based on normalized URL."""
        return hash(self.normalized_url)
