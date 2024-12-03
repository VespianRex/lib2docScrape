"""Base components and utilities for the documentation crawler."""

import logging
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse, urlunparse


@dataclass
class URLInfo:
    """Information about a URL after normalization."""
    scheme: str
    netloc: str
    path: str
    normalized: str
    is_valid: bool

    @property
    def base_url(self) -> str:
        """Get the base URL (scheme + netloc)."""
        return f"{self.scheme}://{self.netloc}"

    @property
    def full_url(self) -> str:
        """Get the full normalized URL."""
        return self.normalized


def normalize_url(url: str) -> Optional[URLInfo]:
    """
    Normalize URL by removing default ports and standardizing format.
    
    Args:
        url: URL to normalize
        
    Returns:
        URLInfo object containing normalized URL components or None if invalid
    """
    try:
        parsed = urlparse(url)
        
        # Basic validation
        if not parsed.scheme or not parsed.netloc:
            logging.warning(f"Invalid URL format: {url}")
            return None
        
        # Remove default ports
        netloc = parsed.netloc
        if ':80' in netloc and parsed.scheme == 'http':
            netloc = netloc.replace(':80', '')
        if ':443' in netloc and parsed.scheme == 'https':
            netloc = netloc.replace(':443', '')
            
        # Ensure path starts with /
        path = parsed.path or '/'
        if not path.startswith('/'):
            path = '/' + path
            
        # Rebuild URL without default ports and fragments
        normalized = urlunparse((
            parsed.scheme,
            netloc,
            path,
            parsed.params,
            parsed.query,
            ''  # Remove fragments
        ))
        
        return URLInfo(
            scheme=parsed.scheme,
            netloc=netloc,
            path=path,
            normalized=normalized,
            is_valid=True
        )
        
    except Exception as e:
        logging.error(f"Error normalizing URL {url}: {str(e)}")
        return None


def is_valid_url(url: str) -> bool:
    """
    Check if a URL is valid.
    
    Args:
        url: URL to validate
        
    Returns:
        bool: True if URL is valid, False otherwise
    """
    try:
        result = normalize_url(url)
        return result is not None and result.is_valid
    except Exception:
        return False
