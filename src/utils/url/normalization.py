"""
URL normalization functions.
"""

import functools
import posixpath

import logging
import re # Import re
import ipaddress # Import ipaddress
from typing import Optional, Tuple
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse, ParseResult, quote, unquote_plus

# Try to import idna, but don't fail if it's missing for the helper function
try:
    import idna
    IDNA_AVAILABLE = True
except ImportError:
    idna = None
    IDNA_AVAILABLE = False

from src.utils.url.security import URLSecurityConfig

logger = logging.getLogger(__name__)

@functools.lru_cache(maxsize=512)
def normalize_hostname(hostname: str) -> str:
    """
    Normalize hostname by lowercasing, stripping trailing dot, handling IDNA,
    and validating label length/characters.

    Args:
        hostname: The hostname to normalize

    Returns:
        Normalized hostname (lowercase with IDNA encoding if needed)

    Raises:
        ValueError: If hostname is empty, contains invalid labels/characters,
                    or fails IDNA encoding.
    """
    if not hostname:
        raise ValueError("hostname is empty")

    # Handle potential IP addresses first
    try:
        ipaddress.ip_address(hostname)
        # If it's an IP address, just lowercase and strip dot
        return hostname.rstrip(".").lower()
    except ValueError:
        # Not an IP, proceed with domain normalization
        pass

    # Proceed with domain normalization (IDNA)
    try:
        # Strip trailing dot and lowercase before encoding
        normalized_host = hostname.rstrip(".").lower()

        # Explicitly check label length (max 63 octets per label)
        labels = normalized_host.split('.')
        for label in labels:
            if not label:
                 if label == '' and (normalized_host.endswith('.') or normalized_host.startswith('.')):
                      continue
                 elif '..' in normalized_host or normalized_host.startswith('.'):
                      raise ValueError("Invalid hostname structure (empty label)")

            # Check basic character length first
            if len(label) > 63:
                 raise ValueError(f"Hostname label too long (>{63} chars): '{label[:20]}...'")

        # Attempt IDNA encoding if available
        if IDNA_AVAILABLE and idna:
            ascii_host = idna.encode(normalized_host).decode("ascii")

            # Re-check label length *after* IDNA encoding (Punycode can expand length)
            ascii_labels = ascii_host.split('.')
            for label in ascii_labels:
                 if len(label.encode('utf-8')) > 63:
                      raise ValueError(f"Encoded hostname label too long (>{63} bytes): '{label[:20]}...'")

            # Basic check for invalid characters that might bypass idna
            if "<" in ascii_host or ">" in ascii_host:
                 raise ValueError("Invalid characters in hostname")
            return ascii_host
        else:
            # Fallback if idna is not available - apply stricter character validation
            logger.warning("idna library not found. Performing basic hostname normalization.")
            for label in labels:
                 # Check for invalid characters according to basic DNS rules
                 if not re.match(r'^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$', label, re.IGNORECASE):
                      if label: # Don't raise for empty label from trailing dot
                         raise ValueError(f"Invalid characters in hostname label (no IDNA): '{label}'")
            return normalized_host # Return the basic normalized host

    except idna.IDNAError as e:
        # Catch specific IDNA errors and raise as ValueError for consistency
        logger.warning(f"IDNA encoding failed for hostname '{hostname}': {e}")
        raise ValueError(f"Invalid hostname (IDNA error): {e}") from e
    except Exception as e:
        # Catch any other unexpected errors during normalization
        logger.error(f"Unexpected error normalizing hostname '{hostname}': {e}", exc_info=True)
        # Re-raise as ValueError for consistent error handling
        raise ValueError(f"Invalid hostname: {e}") from e


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
    # Use URLSecurityConfig for default ports
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
        # Return '/' if original had trailing slash and path was empty or just '/', else empty string
        return '/' if had_trailing_slash else ""

    is_absolute = path.startswith('/')

    # Fast path for already normalized root path
    if is_absolute and path == '/':
        # Only return '/' if the original had a trailing slash
        return '/' if had_trailing_slash else ''

    try:
        unquoted = unquote_plus(path)
    except Exception as e:
        logger.warning(f"Path unquoting failed for '{path}': {e}")
        unquoted = path # Use original path if unquoting fails

    # Use posixpath.normpath to properly handle directory traversal
    # First, collapse multiple consecutive slashes into one
    cleaned_path = _MULTIPLE_SLASH_PATTERN.sub('/', unquoted)
    normalized = posixpath.normpath(cleaned_path)

    # Ensure path starts with / if it was absolute originally
    if is_absolute and not normalized.startswith('/'):
        normalized = '/' + normalized
    elif not is_absolute and normalized.startswith('/'):
        # This case should be rare after normpath, but handle defensively
        normalized = normalized.lstrip('/') # Remove leading slash if it wasn't absolute

    # Special case: normpath turns empty paths or single dots into '.'
    # If absolute, '.' becomes '/' or '' based on trailing slash
    # If relative, '.' becomes ''
    if normalized == '.':
        if is_absolute:
            normalized = '/' if had_trailing_slash else ''
        else:
            normalized = '' # Represent relative current directory as empty

    # Preserve or remove trailing slash based on 'had_trailing_slash' flag
    # Add slash if original had one AND path is not empty/root AND doesn't already end with one
    if had_trailing_slash and normalized and normalized != '/' and not normalized.endswith('/'):
        normalized += '/'
    # Remove slash if original did NOT have one AND path is not just '/' AND it ends with one
    elif not had_trailing_slash and normalized != '/' and normalized.endswith('/'):
        normalized = normalized.rstrip('/')

    # Re-quote the path with appropriate safe characters from URLSecurityConfig
    try:
        # Use PATH_SAFE_CHARS from config
        path_safe = URLSecurityConfig.PATH_SAFE_CHARS
        encoded_path = quote(normalized, safe=path_safe)
        return encoded_path
    except Exception as e:
        logger.error(f"Path encoding failed for '{normalized}': {e}")
        raise ValueError(f"Path encoding failed for '{normalized}': {e}")

@functools.lru_cache(maxsize=128)
def normalize_url(url: str, had_trailing_slash: bool = False) -> str:
    """Normalize a URL by handling common variations."""
    if not url:
        return ""

    # Parse the URL
    try:
        parsed = urlparse(url)
    except ValueError as e:
        logger.warning(f"Initial URL parsing failed for '{url}': {e}")
        # Cannot normalize if parsing fails, return original (or empty string?)
        # Returning original might be safer if caller expects a string
        return url

    # 1. Scheme: Lowercase
    scheme = parsed.scheme.lower()

    # 2. Hostname: Lowercase, IDNA encode, strip trailing dot
    hostname = parsed.hostname
    normalized_hostname = None
    if hostname:
        try:
            # Use the dedicated normalize_hostname function
            normalized_hostname = normalize_hostname(hostname)
        except ValueError as e:
            # If hostname normalization fails, the URL is invalid, but we might still
            # return a partially normalized version or the original URL.
            # For now, let's log and proceed with the original hostname for reconstruction.
            logger.warning(f"Hostname normalization failed for '{hostname}' in URL '{url}': {e}")
            # Keep original hostname for reconstruction if normalization fails
            normalized_hostname = hostname.lower() # Fallback to lowercased original

    # 3. Port: Remove if default for the scheme
    port = parsed.port
    if port and is_default_port(scheme, port):
        port = None # Remove default port

    # Reconstruct netloc with normalized hostname and potentially removed port
    netloc = normalized_hostname if normalized_hostname else ""
    if port:
        netloc = f"{netloc}:{port}"

    # 4. Path: Normalize using normalize_path function
    path = parsed.path
    try:
        # Pass the had_trailing_slash flag to normalize_path
        normalized_path = normalize_path(path, had_trailing_slash)
    except ValueError as e:
        # If path normalization fails, log and use original path
        logger.warning(f"Path normalization failed for '{path}' in URL '{url}': {e}")
        normalized_path = path # Fallback to original path

    # 5. Query: Sort parameters, re-encode
    query = parsed.query
    normalized_query = ""
    if query:
        try:
            # Parse, sort, and re-encode query parameters
            params = parse_qsl(query, keep_blank_values=True)
            # Sort by key, then by value for stability
            params.sort()
            # Use QUERY_SAFE_CHARS from config for encoding
            normalized_query = urlencode(params, safe=URLSecurityConfig.QUERY_SAFE_CHARS)
        except Exception as e:
            logger.warning(f"Query normalization failed for '{query}' in URL '{url}': {e}")
            normalized_query = query # Fallback to original query

    # Reconstruct the URL (fragment is intentionally removed)
    try:
        normalized_parsed = ParseResult(
            scheme=scheme,
            netloc=netloc,
            path=normalized_path,
            params="", # params are deprecated/rarely used
            query=normalized_query,
            fragment="" # Fragment removed
        )
        return urlunparse(normalized_parsed)
    except Exception as e:
        logger.error(f"Failed to unparse normalized URL components for '{url}': {e}")
        # Fallback to a reasonable reconstruction or original URL
        # Let's try reconstructing manually as a fallback
        reconstructed = f"{scheme}://{netloc}{normalized_path}"
        if normalized_query:
            reconstructed += f"?{normalized_query}"
        return reconstructed