"""
URL normalization functions.
"""

import functools
import posixpath

import logging
import re # Import re
import ipaddress # Import ipaddress
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse, ParseResult, quote, unquote

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

            # *** ADDED CHECK ***
            # *** MODIFIED CHECK ***
            # Check only for basic structural issues like leading/trailing hyphens.
            # Allow non-ASCII characters here; IDNA encoding/validation will handle them later if available.
            if label.startswith('-') or label.endswith('-'):
                 raise ValueError(f"Hostname label cannot start or end with a hyphen: '{label}'")
            # Basic check for Punycode structure if applicable
            if label.startswith('xn--') and not re.match(r'^xn--[a-z0-9-]{1,58}$', label, re.IGNORECASE):
                 raise ValueError(f"Invalid Punycode label structure: '{label}'")
            # Note: Character set validation is deferred to IDNA or the fallback check later.

        # Attempt IDNA encoding if available
        if IDNA_AVAILABLE and idna:
            try:
                ascii_host = idna.encode(normalized_host).decode("ascii")
            except idna.IDNAError as e:
                raise ValueError(f"Invalid hostname (IDNA error): {e}") from e

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
def normalize_path(path: str, preserve_trailing_slash: bool = False) -> str:
    """
    Normalizes a URL path according to RFC 3986 and common practices.

    - Resolves '.' and '..' segments
    - Collapses multiple slashes ('//') 
    - URL-decodes percent-encoded characters
    - Preserves a single trailing slash if present in the original path
    - Handles both absolute and relative paths correctly

    Args:
        path: URL path to normalize
        preserve_trailing_slash: Whether to preserve a trailing slash if present

    Returns:
        Normalized path

    Raises:
        ValueError: If path encoding fails
    """
    # Handle empty path explicitly
    if not path:
        return "/" # Revert to returning "/" for empty path
    
    # Detect trailing slash
    original_had_trailing_slash = path.endswith('/') and path != '/'
    original_was_just_slash = path == "/"
    
    # Fast path for already normalized root path
    if path == '/':
        return '/'
    
    try:
        # Use unquote NOT unquote_plus (plus is for query strings)
        # Decode the path to handle percent-encoded chars like %20, %2F (/)
        # Decoding allows correct resolution of '.' and '..' even if encoded
        unquoted = unquote(path)
        # SECURITY: Check for potentially harmful characters after decoding
        if '\x00' in unquoted:
            raise ValueError("Null byte detected in path after decoding")
    except Exception as e:
        logger.warning(f"Path unquoting failed for '{path}': {e}")
        # If decoding fails, it might indicate malformed encoding.
        # Proceeding with original path might be unsafe.
        raise ValueError(f"Path decoding failed: {e}") from e
    
    # Convert Windows-style backslashes to forward slashes
    unquoted = unquoted.replace('\\', '/')
    
    # Determine if this is an absolute path (starts with /)
    is_absolute = unquoted.startswith('/')
    
    # Collapse multiple consecutive slashes into one
    cleaned_path = _MULTIPLE_SLASH_PATTERN.sub('/', unquoted)
    
    # Use posixpath.normpath to properly handle directory traversal
    normalized = posixpath.normpath(cleaned_path)
    
    # normpath on Unix returns '.' for empty paths or single '.' relative paths.
    # It correctly resolves '..' segments.
    # We need to preserve the absolute/relative nature based on the *original* input.
    
    # If the original was absolute, ensure the result starts with / (unless it's just '/')
    if is_absolute and normalized != '/':
        if not normalized.startswith('/'):
             normalized = '/' + normalized
    # If the original was relative, ensure the result does NOT start with /
    # (unless normpath resolved it to an absolute path, which shouldn't happen from relative)
    elif not is_absolute:
        if normalized.startswith('/'):
             # This case should ideally not happen if posixpath.normpath works correctly on relative paths.
             # If it does, maybe strip the leading slash? Or log a warning?
             # For now, let's assume normpath preserves relativity correctly.
             pass
        elif normalized == '.':
             # If original was just '.' or './', normpath gives '.'. Return empty string for consistency?
             # Or keep '.' if that's the standard? Let's keep '.' for now.
             pass # Keep '.' as is for relative current directory indication

    # Add back trailing slash if requested and originally present
    if preserve_trailing_slash and original_had_trailing_slash and not normalized.endswith('/') and normalized != '/':
        normalized += '/'
    
    # Re-quote the path with appropriate safe characters from URLSecurityConfig
    # This ensures the final path is valid for use in a URL.
    # Characters like space, non-ASCII, etc., will be percent-encoded.
    try:
        # Use PATH_SAFE_CHARS from config
        path_safe = URLSecurityConfig.PATH_SAFE_CHARS
        # Encode the *normalized* path.
        # Decode -> Normalize -> Encode ensures correctness & safety.
        encoded_path = quote(normalized, safe=path_safe)
        return encoded_path
    except Exception as e:
        # This encoding should generally not fail unless there are very strange chars
        logger.error(f"Path encoding failed for '{normalized}': {e}")
        raise ValueError(f"Path re-encoding failed: {e}") from e

@functools.lru_cache(maxsize=128)
def normalize_url(url: str) -> str:
    """
    Normalize a URL by handling common variations.
    
    - Lowercases scheme and hostname
    - Removes default ports (80 for http, 443 for https)
    - Normalizes path component
    - Sorts query parameters
    - Removes fragments
    - Preserves trailing slashes in paths when appropriate
    - Handles empty paths correctly with authority
    """
    if not url:
        return ""

    # Parse the URL
    try:
        parsed = urlparse(url)
    except ValueError as e:
        logger.warning(f"Initial URL parsing failed for '{url}': {e}")
        # Cannot normalize if parsing fails, return original
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
            logger.warning(f"Hostname normalization failed for '{hostname}' in URL '{url}': {e}")
            # Keep original hostname for reconstruction if normalization fails
            normalized_hostname = hostname.lower() # Fallback to lowercased original

    # 3. Port: Remove if default for the scheme
    port = parsed.port
    if port and is_default_port(scheme, port):
        port = None # Remove default port

    # Reconstruct netloc with normalized hostname and potentially removed port
    # If hostname normalization failed, fall back to the original hostname
    netloc = normalized_hostname if normalized_hostname is not None else (hostname.lower() if hostname else '')
    
    # Preserve authentication info if present (username:password@host)
    if parsed.username or parsed.password:
        auth = ''
        if parsed.username:
            auth += parsed.username
        if parsed.password:
            auth += f":{parsed.password}"
        # Only add auth if we have a hostname
        if netloc:
            netloc = f"{auth}@{netloc}"
        else:
            # If no hostname but auth info, just use auth (unusual case)
            netloc = auth
    
    # Add port if non-default
    if port:
        netloc += f":{port}"
    # Explicitly remove auth info for normalization, regardless of security config
    if parsed.username or parsed.password:
        netloc = netloc.split('@')[-1]

    # 4. Path: Normalize using normalize_path function
    path = parsed.path
    original_had_trailing_slash = path.endswith('/') and path != '/'
    
    try:
        # Special case: If we have authority (netloc) and empty path, keep it empty
        # This ensures http://example.com -> http://example.com not http://example.com/
        if not path and netloc:
            normalized_path = ""
        else:
            # Otherwise normalize the path, preserving trailing slash if present
            normalized_path = normalize_path(path, preserve_trailing_slash=original_had_trailing_slash)
    except ValueError as e:
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
        # Ensure netloc is not empty when we have a hostname
        if not netloc and hostname:
            netloc = hostname.lower()
            # Re-add port if it was non-default
            if port:
                netloc += f":{port}"
        
        normalized_parsed = ParseResult(
            scheme=scheme,
            netloc=netloc,
            path=normalized_path, # Use path directly from normalize_path
            params=parsed.params, # Keep original params
            query=normalized_query,
            fragment="" # Fragment removed
        )
        
        result = urlunparse(normalized_parsed)
        # Double-check that we didn't end up with an empty result
        if not result and url:
            logger.warning(f"Normalization resulted in empty URL for '{url}', using fallback")
            # Fallback to a basic normalization
            return f"{scheme}://{hostname.lower()}{normalized_path}"
        return result
    except Exception as e:
        logger.error(f"Failed to unparse normalized URL components for '{url}': {e}")
        # Fallback to a reasonable reconstruction
        reconstructed = f"{scheme}://{hostname.lower() if hostname else netloc}{normalized_path}"
        if normalized_query:
            reconstructed += f"?{normalized_query}"
        return reconstructed
