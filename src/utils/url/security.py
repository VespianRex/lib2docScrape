"""
src.utils.url.security
----------------------
Centralised security scanning for URLs.

check_url_security(..) is intentionally *side‑effect free* so it can be
unit‑tested in isolation and used by higher‑level validators (URLInfo, crawlers).
"""

from __future__ import annotations

import re

# --------------------------------------------------------------------------- #
#  Pattern registry & Config
# --------------------------------------------------------------------------- #

# Removed redundant _PATTERNS list

class URLSecurityConfig:
    """Configuration constants and patterns for URL security checks."""

    # Allowed URL schemes (Restricted to only HTTP and HTTPS for documentation scraping)
    ALLOWED_SCHEMES = {
        'http', 'https', 'file' # Add 'file' scheme
    }

    # Schemes explicitly disallowed (even if in ALLOWED_SCHEMES for some contexts)
    # Used for stricter security checks where needed.
    DISALLOWED_SCHEMES = {
        'javascript', # Prevent XSS via javascript: URIs
        'vbscript',   # Prevent XSS via vbscript: URIs
        'data',       # Prevent potential XSS or phishing via data: URIs
        'smb',        # Prevent potential SSRF or info disclosure via smb:
        'ftp',        # Disallow FTP as we're only scraping documentation
        'ftps',       # Disallow FTPS as we're only scraping documentation
        # 'file'        # Allow file scheme now
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
        # 'ftp': 21, # Removed as per test expectations
    }

    # Maximum lengths for URL components (aligned with common limits like Apache's default LimitRequestLine)
    MAX_PATH_LENGTH = 2048
    MAX_QUERY_LENGTH = 2048

    # Basic pattern for valid domain labels (allows letters, numbers, hyphen but not at start/end)
    # Does not handle internationalized domain names (IDNA) directly here, handled separately.
    # Restrict to ASCII characters only to prevent homograph attacks
    DOMAIN_LABEL_PATTERN = re.compile(r'^(?!-)[-a-zA-Z0-9]{1,63}(?<!-)$')

    # Characters generally considered invalid or dangerous in paths/queries
    # Includes control characters (excluding null byte), some high-bit chars, etc. Adjust as needed.
    # Removed backslash `\\` to allow it before path normalization handles it.
    INVALID_CHARS = re.compile(r'[\x01-\x1f\x7f-\x9f<>\"#%{}|\^~`[\]]') # Note: Excluded \x00
    
    # Control characters pattern - explicitly check for newlines and tabs
    CONTROL_CHARS_PATTERN = re.compile(r'[\n\t\r\f\v]')

    # Patterns for detecting directory traversal attempts
    INVALID_PATH_TRAVERSAL = re.compile(r'(?:^|/)\.\.(?:/|$)') # Note: Escaped dots

    # Common XSS patterns (simplified examples, real-world patterns are more complex)
    XSS_PATTERNS = re.compile(r'<script|onerror=|onload=|javascript:', re.IGNORECASE)

    # Common SQL Injection patterns (simplified examples)
    SQLI_PATTERNS = re.compile(r"(--|;|'|\"|xp_)|(union\s+select)", re.IGNORECASE) # Use double quotes for raw string, escape inner double quote

    # Common Command Injection patterns (simplified examples)
    CMD_INJECTION_PATTERNS = re.compile(r'[;|`$\(\)\{\}]') # Note: Escaped chars, removed '&'

    # Null byte pattern
    NULL_BYTE_PATTERN = re.compile(r'\x00') # Note: Escaped null byte

    # Characters safe for path encoding (includes '/')
    PATH_SAFE_CHARS = "/:@!$&'()*+,;="

    # Characters safe for query encoding
    QUERY_SAFE_CHARS = "/:@!$'()*+,;=?"

    # Basic set of potentially confusable characters for homograph detection
    # This is not exhaustive and primarily targets common Latin/Cyrillic mixups
    CONFUSABLE_CHARS = {
        'е': 'e', # Cyrillic 'е' vs Latin 'e'
        'о': 'o', # Cyrillic 'о' vs Latin 'o'
        'а': 'a', # Cyrillic 'а' vs Latin 'a'
        'і': 'i', # Cyrillic 'і' vs Latin 'i'
        'с': 'c', # Cyrillic 'с' vs Latin 'c'
        # Add more as needed, consider libraries like 'confusable_homoglyphs' for more robust detection
    }

    # More robust path traversal pattern (catches variations)
    # Looks for '..' preceded by '/' or start of string, or '..' followed by '/' or end of string
    # Also includes backslash variations and URL-encoded forms
    PATH_TRAVERSAL_PATTERN = re.compile(
        r'(?:(?:^|/|\\|%2f|%5c)\.\.(?:/|\\|%2f|%5c|$))' # ../, ..\, ..%2f, ..%5c
        r'|' 
        r'(?:(?:^|/|\\|%2f|%5c)%2e%2e(?:/|\\|%2f|%5c|$))' # %2e%2e/, %2e%2e\, etc.
        r'|' 
        r'(?:(?:^|/|\\|%2f|%5c)\.%2e(?:/|\\|%2f|%5c|$))' # \.%2e/, \.%2e\, etc.
        r'|' 
        r'(?:(?:^|/|\\|%2f|%5c)%2e\.(?:/|\\|%2f|%5c|$))' # %2e\./, %2e\.\, etc.
    , re.IGNORECASE)

# --------------------------------------------------------------------------- #
#  Security Check Function (REMOVED)
# --------------------------------------------------------------------------- #

# Removed the redundant check_url_security function.
# Security checks are now handled within validation.py
