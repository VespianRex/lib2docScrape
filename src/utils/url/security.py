"""
Security configuration and validation for URL handling.
"""

import re

class URLSecurityConfig:
    """Security configuration for URL validation and sanitization."""
    ALLOWED_SCHEMES = {'http', 'https', 'file', 'ftp'}
    MAX_PATH_LENGTH = 2048
    MAX_QUERY_LENGTH = 2048
    PATH_SAFE_CHARS = "/:@-._~!$&'()*+,;="  # RFC 3986 + common allowed chars
    
    # Pre-compile all regex patterns for better performance
    INVALID_CHARS = re.compile(r'[<>"\'\'\']')
    INVALID_PATH_TRAVERSAL = re.compile(r'(?:^|/)\.\.(?:/|$)')  # Detects /../ or ../
    XSS_PATTERNS = re.compile(
        r'<script|javascript:|vbscript:|data:text/html|onerror=|onload=|onmouseover=|onclick=|alert\(|eval\(|Function\(|setTimeout\(|setInterval\(|document\.|window\.|fromCharCode|String\.fromCodePoint|base64',
        re.IGNORECASE
    )
    SQLI_PATTERNS = re.compile(r"'\s*OR\s*'|'\s*--|\s*UNION\s+SELECT", re.IGNORECASE)
    CMD_INJECTION_PATTERNS = re.compile(r'[;`|]') # Removed '&' as it's common in query strings
    NULL_BYTE_PATTERN = re.compile(r'%00|\x00')
    DOMAIN_LABEL_PATTERN = re.compile(r'^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$', re.IGNORECASE)

    # Default ports for schemes
    DEFAULT_PORTS = {
        'http': 80,
        'https': 443,
        'ftp': 21,
        'ftps': 990,
    }