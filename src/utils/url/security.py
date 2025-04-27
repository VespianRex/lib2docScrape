"""
src.utils.url.security
----------------------
Centralised security scanning for URLs.

check_url_security(..) is intentionally *side‑effect free* so it can be
unit‑tested in isolation and used by higher‑level validators (URLInfo, crawlers).
"""

from __future__ import annotations

import re
import ipaddress
from typing import Optional, Tuple
from urllib.parse import ParseResult, unquote_plus # Added unquote_plus import

# --------------------------------------------------------------------------- #
#  Pattern registry & Config
# --------------------------------------------------------------------------- #

# Removed redundant _PATTERNS list

class URLSecurityConfig:
    """Configuration constants and patterns for URL security checks."""

    # Allowed URL schemes (Removed ftp, file based on test expectations)
    ALLOWED_SCHEMES = {'http', 'https'
                       # 'ftp', 'ftps', # Disallowed by tests
                       # 'file' # Disallowed by tests
                       }

    # Hosts/IPs disallowed to prevent SSRF and access to local resources
    SSRF_DISALLOWED_HOSTS = {
        'localhost',
        '127.0.0.1',
        # Add other loopback/link-local/metadata IPs as needed
        '169.254.169.254', # AWS metadata
        'metadata.google.internal', # GCP metadata
        # '[::1]', # Consider if IPv6 loopback should be blocked
    }

    # Default ports for schemes (used in normalization)
    DEFAULT_PORTS = {
        'http': 80,
        'https': 443,
        'ftp': 21,
        'ftps': 990,
    }

    # Maximum lengths for URL components (aligned with common limits like Apache's default LimitRequestLine)
    MAX_PATH_LENGTH = 2048
    MAX_QUERY_LENGTH = 2048

    # Basic pattern for valid domain labels (allows letters, numbers, hyphen but not at start/end)
    # Does not handle internationalized domain names (IDNA) directly here, handled separately.
    DOMAIN_LABEL_PATTERN = re.compile(r'^(?!-)[a-z0-9-]{1,63}(?<!-)$', re.IGNORECASE)

    # Characters generally considered invalid or dangerous in paths/queries
    # Includes control characters (excluding null byte), some high-bit chars, etc. Adjust as needed.
    # Removed backslash `\\` to allow it before path normalization handles it.
    INVALID_CHARS = re.compile(r'[\x01-\x1f\x7f-\x9f<>\"#%{}|\^~`[\]]') # Note: Excluded \x00

    # Patterns for detecting directory traversal attempts
    INVALID_PATH_TRAVERSAL = re.compile(r'(?:^|/)\.\.(?:/|$)') # Note: Escaped dots

    # Common XSS patterns (simplified examples, real-world patterns are more complex)
    XSS_PATTERNS = re.compile(r'<script|onerror=|onload=|javascript:', re.IGNORECASE)

    # Common SQL Injection patterns (simplified examples)
    SQLI_PATTERNS = re.compile(r"(--|;|'|\"|xp_)|(union\s+select)", re.IGNORECASE) # Use double quotes for raw string, escape inner double quote

    # Common Command Injection patterns (simplified examples)
    CMD_INJECTION_PATTERNS = re.compile(r'[;&|`$\(\)\{\}]') # Note: Escaped chars

    # Null byte pattern
    NULL_BYTE_PATTERN = re.compile(r'\x00') # Note: Escaped null byte

    # Characters safe for path encoding (includes '/')
    PATH_SAFE_CHARS = "/:@!$&'()*+,;="

    # Characters safe for query encoding
    QUERY_SAFE_CHARS = "/:@!$'()*+,;=?"

# --------------------------------------------------------------------------- #
#  Security Check Function (REMOVED)
# --------------------------------------------------------------------------- #

# Removed the redundant check_url_security function.
# Security checks are now handled within validation.py
