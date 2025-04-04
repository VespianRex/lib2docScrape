"""
Provides a consolidated class for URL parsing, validation, and normalization.
"""
import re
import ipaddress
from enum import Enum, auto
from typing import Optional, Tuple, Dict, Any
import urllib.parse # Import the whole module for quote_via
from urllib.parse import urlparse, urljoin, urlunparse, parse_qsl, urlencode, ParseResult

# Define URLType Enum (assuming it was previously in helpers or models)
class URLType(Enum):
    INTERNAL = auto()
    EXTERNAL = auto()
    UNKNOWN = auto()

class URLInfo:
    """
    Represents a URL and provides methods for validation and normalization.

    Attributes:
        raw_url (str): The original URL string provided.
        base_url (Optional[str]): The base URL used for resolving relative URLs.
        is_valid (bool): True if the URL passed all validation checks, False otherwise.
        error_message (Optional[str]): The reason for validation failure, if any.
        normalized_url (Optional[str]): The canonical, normalized URL string, if valid.
        parsed_url (Optional[ParseResult]): The parsed components of the normalized URL, if valid.
        url_type (URLType): The type of the URL (INTERNAL, EXTERNAL, UNKNOWN).
    """

    # Constants for validation (can be moved to a config later if needed)
    ALLOWED_SCHEMES = {'http', 'https'}
    MAX_PATH_LENGTH = 2048
    MAX_QUERY_LENGTH = 2048
    # Regex for potentially invalid characters in path (adjust as needed)
    INVALID_CHARS = re.compile(r'[<>"\']')
    # Regex for potential path traversal
    INVALID_PATH_TRAVERSAL = re.compile(r'\.\./|\.\.$')
    # Regex for common XSS patterns (basic examples)
    XSS_PATTERNS = re.compile(r'<script|alert\(|eval\(|onmouseover=|onclick=|onerror=', re.IGNORECASE)


    def __init__(self, url: str, base_url: Optional[str] = None):
        """
        Initializes URLInfo, performing parsing, validation, and normalization.
        """
        self._initialized = False # Flag to control setattr
        self.raw_url: str = url
        self.base_url: Optional[str] = base_url
        self._parsed: Optional[ParseResult] = None # Stores the result of urlparse
        self.normalized_url: Optional[str] = None
        self.is_valid: bool = False
        self.error_message: Optional[str] = None
        self.url_type: URLType = URLType.UNKNOWN

        try:
            self._parse_and_resolve()
            # Original order: Validate first
            self.is_valid, self.error_message = self._validate()

            if self.is_valid and self._parsed:
                # Normalize *after* validation passes
                self._normalize()
                # Determine type based on normalized URL and base URL
                self.url_type = self._determine_url_type(self.normalized_url, self.base_url)
            else:
                # If invalid, set normalized to raw for reference, type is UNKNOWN
                self.normalized_url = self.raw_url
                self.url_type = URLType.UNKNOWN

        except Exception as e:
            # Catch unexpected errors during the process
            self.is_valid = False
            self.error_message = f"Unexpected error during URL processing: {str(e)}"
            self.normalized_url = self.raw_url # Keep raw on unexpected error
            self.url_type = URLType.UNKNOWN
        # Mark initialization as complete
        self._initialized = True

    def _parse_and_resolve(self):
        """Parses the raw URL and resolves it against the base URL if relative."""
        if not isinstance(self.raw_url, str):
            raise ValueError("URL must be a string")
        if not self.raw_url:
            raise ValueError("URL cannot be empty")

        temp_raw_url = self.raw_url
        base_for_join = self.base_url

        # Handle protocol-relative URLs by adopting the base URL's scheme, or defaulting to http
        if temp_raw_url.startswith('//'):
            base_scheme = urlparse(base_for_join).scheme if base_for_join else 'http'
            temp_raw_url = f"{base_scheme}:{temp_raw_url}"
        # Add default http scheme if missing entirely and not protocol-relative
        elif not urlparse(temp_raw_url).scheme:
             temp_raw_url = "http://" + temp_raw_url

        # Use urljoin to handle relative URLs correctly
        resolved_url = urljoin(base_for_join, temp_raw_url) if base_for_join else temp_raw_url
        self._parsed = urlparse(resolved_url)

    def _validate(self) -> Tuple[bool, Optional[str]]:
        """Orchestrates all validation checks."""
        if not self._parsed:
             return False, "URL could not be parsed" # Should not happen if _parse runs first

        checks = [
            self._validate_security, # Run security check before normalization
            self._validate_scheme,
            self._validate_port,
            self._validate_netloc,
            self._validate_path, # Validates the *parsed* path
            self._validate_query,
        ]
        for check_func in checks:
            is_ok, error = check_func()
            if not is_ok:
                return False, error
        return True, None

    # --- Validation Helper Methods ---
    def _validate_security(self) -> Tuple[bool, Optional[str]]:
        """Check for common security risks like XSS in the resolved URL."""
        # Check the URL *after* potential resolution via urljoin
        resolved_url = urlunparse(self._parsed) if self._parsed else self.raw_url
        if self.XSS_PATTERNS.search(resolved_url):
             return False, "Potential XSS attempt detected in resolved URL"
        # Also check specifically for javascript:/data: schemes which bypass other checks
        if self._parsed and self._parsed.scheme.lower() in ['javascript', 'data']:
             return False, f"Disallowed scheme: {self._parsed.scheme}"
        return True, None

    def _validate_scheme(self) -> Tuple[bool, Optional[str]]:
        """Validate the URL scheme."""
        if not self._parsed.scheme or self._parsed.scheme.lower() not in self.ALLOWED_SCHEMES:
            return False, f"Invalid or unsupported URL scheme: {self._parsed.scheme}"
        return True, None

    def _validate_port(self) -> Tuple[bool, Optional[str]]:
        """Validate the port number if present."""
        # Validate port using the parsed integer value from urlparse
        port = self._parsed.port
        if port is not None and not (0 <= port <= 65535):
            return False, f"Invalid port number: {port}"
        # Note: urlparse already returns None for non-integer ports like 'abc'.
        # The non-numeric check in _validate_netloc provides an earlier, clearer error for that case.
        return True, None

    def _validate_netloc(self) -> Tuple[bool, Optional[str]]:
        """Validate the network location part (domain, IP, auth)."""
        netloc = self._parsed.netloc
        if not netloc:
             # Allow file paths if 'file' scheme is ever added
             if self._parsed.scheme not in ['file']:
                 return False, "URL missing network location (domain/IP)"
             # If file scheme, netloc can be empty

        if '@' in netloc:
            return False, "Authentication in URL not allowed"

        # Check for private IPs
        # Split netloc to get host part, ignoring port if present
        host_part = netloc.split(':', 1)[0]
        if not host_part: # Handle case like "http://:80"
             if self._parsed.scheme not in ['file']: # Allow empty host for file scheme
                 return False, "Missing host in network location"
             # else: host can be empty for file URLs like file:///path/to/file

        # Only perform IP/domain checks if host_part is not empty
        if host_part:
            try:
                ip_obj = ipaddress.ip_address(host_part)
                if (ip_obj.is_private or ip_obj.is_loopback or
                    ip_obj.is_unspecified or ip_obj.is_link_local):
                    return False, "Private/localhost IP not allowed"
            except ValueError:
                # Not an IP, validate as domain
                parts = host_part.split('.')
                if len(parts) < 2 and host_part != 'localhost': # Allow 'localhost' explicitly
                     return False, f"Invalid domain: missing TLD? ({host_part})"
                if any(not part for part in parts):
                     return False, "Invalid domain: empty label"
                # Check label length (max 63 chars per label), ignoring port if present
                if any(len(part.split(':')[0]) > 63 for part in parts):
                     return False, "Invalid domain: label too long"
                # Check total domain length (max 253 chars) - less critical, often handled by systems
                # if len(host_part) > 253:
                #     return False, "Invalid domain: total length too long"

        # Check if port part (if exists) is numeric
        if ':' in netloc:
            port_part = netloc.split(':', 1)[1]
            # Allow empty port (like 'http://example.com:') which _normalize_port handles
            if port_part and not port_part.isdigit():
                 return False, f"Invalid non-numeric port specified: '{port_part}'"

        return True, None

    def _validate_path(self) -> Tuple[bool, Optional[str]]:
        """Validate the URL path."""
        # Note: This validates the path *as parsed*, before path normalization removes '..' or '//'
        path = self._parsed.path
        if self.INVALID_CHARS.search(path):
            return False, "URL path contains invalid characters"
        # Path traversal check should happen *after* path normalization
        # if self.INVALID_PATH_TRAVERSAL.search(path):
        #     return False, "URL path contains path traversal attempt"
        if len(path) > self.MAX_PATH_LENGTH:
            return False, "URL path too long"
        return True, None

    def _validate_query(self) -> Tuple[bool, Optional[str]]:
        """Validate the URL query string."""
        if len(self._parsed.query) > self.MAX_QUERY_LENGTH:
            return False, "URL query too long"
        return True, None

    # --- Normalization Helper Methods ---
    def _normalize(self):
        """Orchestrates normalization steps on the internal _parsed object."""
        if not self._parsed: return # Should already be validated

        # Normalize components in order
        self._normalize_scheme_host()
        self._normalize_port()
        self._normalize_path() # Call path normalization here
        self._normalize_query()

        # Post-normalization validation (only path traversal now)
        if self.INVALID_PATH_TRAVERSAL.search(self._parsed.path):
             self.is_valid = False
             # Prioritize path traversal error message if validation hadn't failed already
             if self.error_message is None:
                  self.error_message = "URL path contains path traversal attempt after normalization"
             self.normalized_url = self.raw_url # Revert normalized_url
             self.url_type = URLType.UNKNOWN
             return # Stop further processing

        # Final unparse and cleanup
        self._finalize_normalization()

    def _finalize_normalization(self):
        """Final step to unparse the normalized components and set the attribute."""
        if not self._parsed or not self.is_valid: return # Check validity again
        # Remove fragment before final unparsing
        self._parsed = self._parsed._replace(fragment='')
        # Unparse and perform final cleanup: remove trailing '?' and trailing '/' from root
        temp_url = urlunparse(self._parsed).rstrip('?') # Remove trailing '?' if query was empty

        # Handle trailing slash based on path more carefully
        parsed_temp = urlparse(temp_url)
        if parsed_temp.path == '/' and temp_url.endswith('/'):
            # Keep trailing slash for root path like http://example.com/
            self.normalized_url = temp_url
        elif parsed_temp.path == '' and temp_url.endswith('/'):
             # Path is empty BUT urlunparse added a slash (e.g. http://example.com:80 -> http://example.com/)
             # Remove the slash in this specific case
             self.normalized_url = temp_url.rstrip('/')
        elif parsed_temp.path == '' and not temp_url.endswith('/'):
             # Path is empty and no slash (e.g. http://example.com after port removal), keep as is
             self.normalized_url = temp_url
        # For non-empty paths, urlunparse should preserve the slash correctly based on _normalize_path
        else:
             self.normalized_url = temp_url

    def _normalize_scheme_host(self):
        """Lowercase scheme, remove auth, lowercase and IDNA-encode hostname."""
        if not self._parsed: return
        # Lowercase scheme
        scheme = self._parsed.scheme.lower()

        # Remove auth and lowercase host
        netloc = self._parsed.netloc
        if '@' in netloc:
            netloc = netloc.split('@', 1)[1] # Discard auth part

        netloc_parts = netloc.split(':', 1)
        domain = netloc_parts[0].lower()
        port_part = f":{netloc_parts[1]}" if len(netloc_parts) > 1 else ""

        # IDNA encode domain if it contains non-ASCII characters
        try:
            # Check if domain needs encoding (basic check for non-ASCII)
            if not all(ord(c) < 128 for c in domain):
                 domain = domain.encode('idna').decode('ascii')
        except Exception as e:
             # If IDNA encoding fails, consider the URL invalid
             self.is_valid = False
             self.error_message = f"IDNA encoding failed for domain '{domain}': {e}"
             return # Stop normalization here if domain is invalid

        self._parsed = self._parsed._replace(scheme=scheme, netloc=f"{domain}{port_part}")

    def _normalize_port(self):
        """Remove default ports (80/443) or empty ports."""
        scheme = self._parsed.scheme
        netloc = self._parsed.netloc
        if ':' in netloc:
            domain, port_str = netloc.split(':', 1)
            # Remove port if empty or default for the scheme
            if port_str == '' or \
               (scheme == 'http' and port_str == '80') or \
               (scheme == 'https' and port_str == '443'):
                self._parsed = self._parsed._replace(netloc=domain)
            # Keep valid non-default ports (already validated)

    def _normalize_path(self):
        """Clean path segments (remove //, ., ..) and handle trailing slash."""
        if not self._parsed: return

        # Use original URL to determine original slash presence accurately
        original_parsed_for_slash = urlparse(self.raw_url)
        original_path_for_slash = original_parsed_for_slash.path
        had_trailing_slash_orig = original_path_for_slash.endswith('/')

        # Clean segments: remove empty (handles //), '.', handle '..'
        # Use self._parsed.path which reflects the state after _parse_and_resolve
        path_segments = self._parsed.path.split('/')
        clean_segments = []
        for segment in path_segments:
            if segment == '.' or segment == '': # Remove . and empty segments from //
                continue
            elif segment == '..':
                if clean_segments: # Only pop if there's something to pop
                    clean_segments.pop()
                # If clean_segments is empty, effectively ignore '..' at root level
            else: # It's a normal segment
                # Percent-encode the segment before appending
                clean_segments.append(urllib.parse.quote(segment, safe='/:'))

        # Reconstruct path
        if not clean_segments: # Handle root path
             # Path should always be '/' for root after normalization
             _path = '/'
        else: # Handle non-root path
            _path = '/' + '/'.join(clean_segments)
            # Add trailing slash if original had one AND it's not just the root
            if had_trailing_slash_orig and _path != '/':
                _path += '/'

        # Update the internal parsed object directly
        self._parsed = self._parsed._replace(path=_path)
        # No longer sets self.normalized_url here, _finalize_normalization does

    def _normalize_query(self):
        """Sort query parameters."""
        if self._parsed.query:
            params = parse_qsl(self._parsed.query, keep_blank_values=True)
            # Add filtering logic here if needed based on config
            sorted_params = sorted(params, key=lambda param: param[0]) # Sort by key only
            # Use quote_via=urllib.parse.quote to ensure spaces are %20, not +
            query_string = urlencode(sorted_params, doseq=True, quote_via=urllib.parse.quote)
            self._parsed = self._parsed._replace(query=query_string)
        else:
             self._parsed = self._parsed._replace(query='') # Ensure empty string

    # --- Type Determination ---
    @staticmethod
    def _determine_url_type(normalized_url: Optional[str], base_url: Optional[str]) -> URLType:
        """Determines if the URL is internal or external relative to the base URL."""
        if not normalized_url or not base_url:
            return URLType.UNKNOWN

        try:
            norm_parsed = urlparse(normalized_url)
            base_parsed = urlparse(base_url)

            # Simple check: same scheme and netloc means internal
            if (norm_parsed.scheme == base_parsed.scheme and
                norm_parsed.netloc == base_parsed.netloc):
                return URLType.INTERNAL
            else:
                return URLType.EXTERNAL
        except Exception:
            return URLType.UNKNOWN # Error during parsing

    # --- Public Properties ---
    # Define properties to access parts of the *normalized* URL if valid
    @property
    def scheme(self) -> Optional[str]:
        return self._parsed.scheme if self.is_valid and self._parsed else "" # Return "" if invalid

    @property
    def netloc(self) -> Optional[str]:
        # Return "" for invalid URLs, consistent with scheme property
        return self._parsed.netloc if self.is_valid and self._parsed else ""

    @property
    def path(self) -> Optional[str]:
        # Return the path from the *final* normalized state if valid
        if self.is_valid and self.normalized_url:
             try:
                  return urlparse(self.normalized_url).path
             except Exception:
                  return None # Should not happen if valid
        elif self._parsed: # If invalid but parsed, return parsed path
             return self._parsed.path
        return None

    @property
    def query(self) -> Optional[str]:
         # Return the query from the *final* normalized state if valid
         if self.is_valid and self.normalized_url:
              try:
                   return urlparse(self.normalized_url).query
              except Exception:
                   return None # Should not happen if valid
         elif self._parsed: # If invalid but parsed, return parsed query
              return self._parsed.query
         return None

    # Add other properties as needed (e.g., params, fragment if kept)


    def __eq__(self, other: object) -> bool:
        """Check equality based on the normalized URL."""
        if not isinstance(other, URLInfo):
            return NotImplemented
        # Consider valid URLs equal if their normalized forms match
        # Consider invalid URLs equal if their raw forms match (as normalized might be None or raw)
        if self.is_valid and other.is_valid:
            return self.normalized_url == other.normalized_url
        elif not self.is_valid and not other.is_valid:
            return self.raw_url == other.raw_url
        else:
            return False # One is valid, one is not

    def __hash__(self) -> int:
        """Generate hash based on the normalized URL if valid, otherwise raw URL."""
        if self.is_valid and self.normalized_url is not None:
            return hash(self.normalized_url)
        else:
            # Use raw_url for hashing invalid URLs to maintain consistency with __eq__
            return hash(self.raw_url)

    def __setattr__(self, name: str, value: Any):
        """Prevent setting attributes after initialization."""
        # Allow setting attributes during __init__ before _initialized is True
        if not getattr(self, '_initialized', False):
            super().__setattr__(name, value)
        # Allow setting internal attributes like _parsed even after init
        elif name.startswith('_'):
             super().__setattr__(name, value)
        else:
            raise AttributeError(f"Cannot set attribute '{name}' on immutable URLInfo object")
            return hash(self.raw_url)

