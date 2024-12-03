"""
lib2docscrape - A web scraping tool for library documentation.

This package provides tools for crawling, processing, and organizing library documentation
from various sources.
"""

from .base import URLInfo, normalize_url, is_valid_url

__version__ = "0.1.0"
__author__ = "Your Name"
__license__ = "MIT"

__all__ = [
    "URLInfo",
    "normalize_url",
    "is_valid_url",
]
