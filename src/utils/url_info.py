"""
Provides a consolidated class for URL parsing, validation, and normalization.
"""
import re
import ipaddress
from enum import Enum, auto
from typing import Optional, Tuple, Dict, Any
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
        self.raw_url: str = url
        self.base_url: Optional[str] = base_url
        self._parsed: Optional[ParseResult] = None # Stores the result of urlparse
        self.normalized_url: Optional[str] = None
        self.is_valid: bool = False
        self.error_message: Optional[str] = None
        self.url_type: URLType = URLType.UNKNOWN

        try:
            self._parse_and_resolve()
            self.is_valid, self.error_message = self._validate()

            if self.is_valid and self._parsed:
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

    def _parse_and_resolve(self):
        """Parses the raw URL and resolves it against the base URL if relative."""
        if not isinstance(self.raw_url, str):
            raise ValueError("URL must be a string")
        if not self.raw_url:
            raise ValueError("URL cannot be empty")

        # Use urljoin to handle relative URLs correctly
        resolved_url = urljoin(self.base_url, self.raw_url) if self.base_url else self.raw_url
        self._parsed = urlparse(resolved_url)

    def _validate(self) -> Tuple[bool, Optional[str]]:
        """Orchestrates all validation checks."""
        if not self._parsed:
             return False, "URL could not be parsed" # Should not happen if _parse runs first

        checks = [
            self._validate_security,
            self._validate_scheme,
            self._validate_port,
            self._validate_netloc,
            self._validate_path,
            self._validate_query,
        ]
        for check_func in checks:
            is_ok, error = check_func()
            if not is_ok:
                return False, error
        return True, None

    # --- Validation Helper Methods ---
    def _validate_security(self) -> Tuple[bool, Optional[str]]:
        """Check for common security risks like XSS."""
        if self.XSS_PATTERNS.search(self.raw_url): # Check raw url for patterns
             return False, "Potential XSS attempt detected in URL"
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
        path = self._parsed.path
        if self.INVALID_CHARS.search(path):
            return False, "URL path contains invalid characters"
        if self.INVALID_PATH_TRAVERSAL.search(path):
            return False, "URL path contains path traversal attempt"
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

        self._normalize_scheme_host()
        self._normalize_port()
        self._normalize_path()
        self._normalize_query()

        # Remove fragment and unparse
        self._parsed = self._parsed._replace(fragment='')
        self.normalized_url = urlunparse(self._parsed).rstrip('?') # Final cleanup

    def _normalize_scheme_host(self):
        """Lowercase scheme and hostname."""
        self._parsed = self._parsed._replace(scheme=self._parsed.scheme.lower())
        # Lowercase netloc, handling potential port
        netloc_parts = self._parsed.netloc.split(':', 1)
        domain = netloc_parts[0].lower()
        port = f":{netloc_parts[1]}" if len(netloc_parts) > 1 else ""
        self._parsed = self._parsed._replace(netloc=f"{domain}{port}")

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
        """Clean path segments and handle trailing slash."""
        # Use original URL to determine original slash presence accurately
        original_parsed_for_slash = urlparse(self.raw_url)
        original_path_for_slash = original_parsed_for_slash.path
        had_trailing_slash_orig = original_path_for_slash.endswith('/')

        # Clean segments: remove empty, '.', handle '..'
        path_segments = [s for s in self._parsed.path.split('/') if s]
        clean_segments = []
        for segment in path_segments:
            if segment == '.':
                continue
            elif segment == '..' and clean_segments:
                clean_segments.pop()
            elif segment != '..':
                clean_segments.append(segment)

        # Reconstruct path
        if not clean_segments: # Handle root path
             # Path should be '/' if original was '/' or ended with '/', otherwise empty
            _path = '/' if original_path_for_slash == '/' or had_trailing_slash_orig else ''
        else: # Handle non-root path
            _path = '/' + '/'.join(clean_segments)
            # Add trailing slash if original had one
            if had_trailing_slash_orig:
                _path += '/'
        self._parsed = self._parsed._replace(path=_path)

    def _normalize_query(self):
        """Sort query parameters."""
        if self._parsed.query:
            params = parse_qsl(self._parsed.query, keep_blank_values=True)
            # Add filtering logic here if needed based on config
            sorted_params = sorted(params)
            query_string = urlencode(sorted_params)
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
        return self._parsed.scheme if self.is_valid and self._parsed else None

    @property
    def netloc(self) -> Optional[str]:
        return self._parsed.netloc if self.is_valid and self._parsed else None

    @property
    def path(self) -> Optional[str]:
        return self._parsed.path if self.is_valid and self._parsed else None

    @property
    def query(self) -> Optional[str]:
         return self._parsed.query if self.is_valid and self._parsed else None

    # Add other properties as needed (e.g., params, fragment if kept)
