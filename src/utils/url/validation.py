"""
URL validation functions.
"""

import re
import idna
import ipaddress
import posixpath
from typing import Tuple, Optional
from urllib.parse import ParseResult, unquote_plus
import logging

from src.utils.url.security import URLSecurityConfig

logger = logging.getLogger(__name__)

def validate_url(parsed: ParseResult) -> Tuple[bool, Optional[str]]:
    """Orchestrates validation checks for a parsed URL."""
    checks = [
        (validate_scheme, parsed),
        (validate_netloc, parsed),
        (validate_port, parsed),
        (validate_path, parsed),
        (validate_query, parsed),
        (validate_security_patterns, parsed)
    ]
    for check_func, data in checks:
        is_ok, error = check_func(data)
        if not is_ok:
            return False, error
    return True, None

def validate_scheme(p: ParseResult) -> Tuple[bool, Optional[str]]:
    """Validate the URL scheme."""
    scheme = p.scheme.lower() if p.scheme else ''
    if not scheme or scheme not in URLSecurityConfig.ALLOWED_SCHEMES:
        return False, f"Invalid scheme: {p.scheme or 'None'}"
    return True, None

def validate_netloc(p: ParseResult) -> Tuple[bool, Optional[str]]:
    """Validate the URL network location component."""
    scheme = p.scheme.lower() if p.scheme else ''
    if not p.netloc and scheme != 'file':
        return False, "Missing netloc"
    if '@' in p.netloc:
        return False, "Auth info not allowed"
    hostname = p.hostname.lower() if p.hostname else None
    if not hostname and scheme != 'file':
        return False, "Missing host"
    if hostname:
        if hostname == 'localhost':
            return True, None
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback:
                return False, f"Private/loopback IP: {hostname}"
        except ValueError:
            if len(hostname) > 253:
                return False, "Domain too long"
            temp_host = hostname[:-1] if hostname.endswith('.') else hostname
            if not temp_host:
                return False, "Empty domain"
            labels = temp_host.split('.')
            if len(labels) < 2 and temp_host != 'localhost':
                return False, f"Invalid domain (no TLD?): {temp_host}"
            if any(not l or len(l) > 63 for l in labels):
                return False, "Invalid domain label"
            try:
                idna.encode(temp_host)  # Check IDNA
                if not all(URLSecurityConfig.DOMAIN_LABEL_PATTERN.match(l) for l in labels):
                    return False, f"Invalid label chars: {temp_host}"
            except idna.IDNAError as e:
                return False, f"Invalid IDNA: {temp_host} ({e})"
            except Exception as e:
                return False, f"Domain validation error: {e}"
    return True, None

def validate_port(p: ParseResult) -> Tuple[bool, Optional[str]]:
    """Validate the URL port."""
    if p.port is not None and not (0 <= p.port <= 65535):
        return False, f"Invalid port: {p.port}"
    return True, None

def validate_path(p: ParseResult) -> Tuple[bool, Optional[str]]:
    """Validate the URL path."""
    if len(p.path) > URLSecurityConfig.MAX_PATH_LENGTH:
        return False, "Path too long"
    try:
        decoded_path = unquote_plus(p.path)
        # Check for invalid characters first
        if URLSecurityConfig.INVALID_CHARS.search(decoded_path):
            return False, "Invalid chars in decoded path"
        # Path traversal is checked more robustly in validate_security_patterns after normalization attempt there.
        # Now normalize and check (covers edge cases normalization might reveal)
        norm_decoded = posixpath.normpath(decoded_path)
        # Check if normalization resulted in trying to go above root
        if norm_decoded.startswith('../') or norm_decoded == '/..':
             return False, "Path traversal attempt detected after normalization"
    except Exception as e:
        return False, f"Path decode/validation error: {e}"
    return True, None

def validate_query(p: ParseResult) -> Tuple[bool, Optional[str]]:
    """Validate the URL query string."""
    if len(p.query) > URLSecurityConfig.MAX_QUERY_LENGTH:
        return False, "Query too long"
    try:
        decoded_query = unquote_plus(p.query)
        if URLSecurityConfig.INVALID_CHARS.search(decoded_query):
            return False, "Invalid chars in decoded query"
    except Exception as e:
        return False, f"Query decode/validation error: {e}"
    return True, None

def validate_security_patterns(p: ParseResult) -> Tuple[bool, Optional[str]]:
    """Check decoded path and query for security patterns."""
    try:
        decoded_path = unquote_plus(p.path)
        decoded_query = unquote_plus(p.query)
        
        # Check for directory traversal attempts - more comprehensive check
        # Check for directory traversal attempts.
        # Normalize the path first.
        normalized_path = posixpath.normpath(decoded_path)

        # Check 1: Did normalization result in trying to go above the root?
        if normalized_path.startswith('../') or normalized_path == '/..':
            return False, "Path traversal attempt detected after normalization"

        # Check 2: Did the *original* path contain traversal patterns?
        # This catches cases like /../../etc/passwd which normalize to /etc/passwd
        # but still indicate traversal intent.
        if URLSecurityConfig.INVALID_PATH_TRAVERSAL.search(decoded_path):
            return False, "Directory traversal pattern detected in original path"
            
        # Check for XSS patterns
        if (URLSecurityConfig.XSS_PATTERNS.search(decoded_path) or 
            URLSecurityConfig.XSS_PATTERNS.search(decoded_query)):
            return False, "XSS pattern"
            
        # Check for SQL injection patterns
        if (URLSecurityConfig.SQLI_PATTERNS.search(decoded_path) or 
            URLSecurityConfig.SQLI_PATTERNS.search(decoded_query)):
            return False, "SQLi pattern"
            
        # Check for command injection patterns
        if (URLSecurityConfig.CMD_INJECTION_PATTERNS.search(decoded_path) or 
            URLSecurityConfig.CMD_INJECTION_PATTERNS.search(decoded_query)):
            return False, "Cmd Injection pattern"
            
        # Check for null byte injection
        if (URLSecurityConfig.NULL_BYTE_PATTERN.search(p.path) or 
            URLSecurityConfig.NULL_BYTE_PATTERN.search(decoded_path)):
            return False, "Null byte in path"
            
        if (URLSecurityConfig.NULL_BYTE_PATTERN.search(p.query) or 
            URLSecurityConfig.NULL_BYTE_PATTERN.search(decoded_query)):
            return False, "Null byte in query"
            
        # Check for disallowed schemes in the path or query
        if 'javascript:' in decoded_path.lower() or 'javascript:' in decoded_query.lower():
            return False, "JavaScript scheme in path or query"
            
        if 'data:' in decoded_path.lower() or 'data:' in decoded_query.lower():
            return False, "Data scheme in path or query"
    except Exception as e:
        return False, f"Security check decode error: {e}"
    return True, None