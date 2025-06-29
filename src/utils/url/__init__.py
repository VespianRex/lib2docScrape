"""
URL handling package for secure, normalized URL operations.

This package provides tools for URL parsing, validation, normalization and manipulation
with a focus on security and RFC compliance.
"""

from src.utils.url.info import URLInfo, URLType
from src.utils.url.security import URLSecurityConfig

from .factory import create_url_info

__all__ = ["URLInfo", "URLType", "URLSecurityConfig", "create_url_info"]
