"""
URL normalization functions.
"""

import functools
import idna
import posixpath
import logging
import re
from typing import Optional, Tuple
from urllib.parse import parse_qsl, urlencode, urlunparse, ParseResult, quote, unquote_plus

from src.utils.url.security import URLSecurityConfig

logger = logging.getLogger(__name__)

@functools.lru_cache(maxsize=512)
def normalize_hostname(hostname: str) -> str:
    """
    Normalize hostname to lowercase and handle IDN domains.
    
    Args:
        hostname: The hostname to normalize
        
    Returns:
        Normalized hostname (lowercase with IDN encoding if needed)
        
    Raises:
        ValueError: If hostname cannot be properly encoded as IDN
    """
    hostname_lower = hostname.lower().rstrip('.')
    try:
        # Fast path for ASCII-only hostnames (most common case)
        if all(ord(c) < 128 for c in hostname_lower):
            return hostname_lower
        # Properly encode IDN domains to Punycode
        return idna.encode(hostname_lower).decode('ascii')
    except idna.IDNAError as e:
        raise ValueError(f"Invalid IDNA: {hostname}") from e

@functools.lru_cache(maxsize=128)
def is_default_port(scheme: str, port: int) -> bool:
    """
    Check if a port is the default for a scheme.
    
    Args:
        scheme: URL scheme
        port: Port number
        
    Returns:
        True if the port is the default for the scheme, False otherwise
    """
    return scheme in URLSecurityConfig.DEFAULT_PORTS and port == URLSecurityConfig.DEFAULT_PORTS[scheme]

# Regex pattern for collapsing multiple slashes - compile once for better performance
_MULTIPLE_SLASH_PATTERN = re.compile(r'/+')

@functools.lru_cache(maxsize=256)
def normalize_path(path: str, had_trailing_slash: bool = False) -> str:
    """
    Normalize URL path: unquote, resolve dots, handle slashes, re-encode.
    
    Args:
        path: URL path to normalize
        had_trailing_slash: Whether the original path had a trailing slash
    
    Returns:
        Normalized path
        
    Raises:
        ValueError: If path encoding fails
    """
    if not path:
        # Return empty string for empty path to match test expectations
        return ""

    is_absolute = path.startswith('/')

    # Fast path for already normalized paths
    if is_absolute and path == '/':
        return '/'

    try:
        unquoted = unquote_plus(path)
    except Exception as e:
        logger.warning(f"Path unquoting failed for '{path}': {e}")
        unquoted = path

    # Use posixpath.normpath to properly handle directory traversal
    # This correctly resolves patterns like '../' according to path semantics
    # First, collapse multiple consecutive slashes into one
    cleaned_path = _MULTIPLE_SLASH_PATTERN.sub('/', unquoted)
    normalized = posixpath.normpath(cleaned_path)
    
    # Ensure path starts with / if it was absolute originally
    if is_absolute and not normalized.startswith('/'):
        normalized = '/' + normalized
    elif not is_absolute and normalized.startswith('/'):
        normalized = normalized[1:]
        
    # Special case: normpath turns empty paths into '.'  
    if normalized == '.' and is_absolute:
        normalized = '/'
    elif normalized == '.' and not is_absolute:
        normalized = ''

    # Preserve trailing slash if original had one and path is not just root
    if had_trailing_slash and normalized != '/' and not normalized.endswith('/'):
        normalized += '/'

    # Re-quote the path with appropriate safe characters
    try:
        path_safe = URLSecurityConfig.PATH_SAFE_CHARS
        encoded_path = quote(normalized, safe=path_safe)
        return encoded_path
    except Exception as e:
        logger.error(f"Path encoding failed for '{normalized}': {e}")
        raise ValueError(f"Path encoding failed for '{normalized}': {e}")

@functools.lru_cache(maxsize=128)
def normalize_url(parsed: ParseResult, had_trailing_slash: bool = False) -> Tuple[ParseResult, str]:
    """
    Normalize a parsed URL.
    
    Args:
        parsed: The parsed URL components
        had_trailing_slash: Whether the original path had a trailing slash
        
    Returns:
        Tuple of (normalized ParseResult, normalized URL string)
    """
    if not parsed:
        return parsed, ""
        
    try:
        scheme = parsed.scheme.lower()
        
        # Normalize hostname
        hostname = parsed.hostname
        port = parsed.port
        netloc_norm = ""
        
        if hostname:
            try:
                hostname_norm = normalize_hostname(hostname)
                netloc_norm = hostname_norm
            except (idna.IDNAError, ValueError) as e:
                logger.warning(f"IDNA encoding failed for {hostname}: {e}. Falling back.")
                netloc_norm = hostname.lower().rstrip('.')  # Fallback
            except Exception as e:
                logger.error(f"Unexpected error normalizing hostname {hostname}: {e}")
                netloc_norm = hostname.lower().rstrip('.')  # Fallback
        
        # Add port if it's not the default for the scheme
        if port is not None and not is_default_port(scheme, port):
            netloc_norm += f":{port}"

        # Normalize path
        path_norm = normalize_path(parsed.path, had_trailing_slash)

        # Normalize query: preserve original order
        query_params = parse_qsl(parsed.query, keep_blank_values=True)
        # Encode query params correctly
        query_norm = urlencode(query_params, doseq=True)

        # Ensure path is explicitly "/" if empty after normalization and netloc exists
        if (not path_norm or path_norm == ".") and netloc_norm:
            path_norm = "/"
        elif not path_norm: # Handle cases with no netloc (e.g., file URLs) where path shouldn't be "/"
            path_norm = ""


        # Reconstruct normalized URL
        normalized_parsed = ParseResult(scheme, netloc_norm, path_norm, parsed.params, query_norm, '')
        normalized_url = urlunparse(normalized_parsed)

        # Removed special case that removed trailing slash for root paths.
        # The logic above now ensures root paths have a trailing slash.

        return normalized_parsed, normalized_url

    except Exception as e:
        logger.error(f"Normalization failed: {type(e).__name__}: {str(e)}")
        raise ValueError(f"URL normalization failed: {str(e)}")
        logger.error(f"Normalization failed: {type(e).__name__}: {str(e)}")
        raise ValueError(f"URL normalization failed: {str(e)}")