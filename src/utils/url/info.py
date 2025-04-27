import functools
import logging
from typing import Optional, Tuple, Any, Dict, List
from urllib.parse import urlparse, urljoin, parse_qsl, ParseResult, urlunparse
import posixpath
import ipaddress # Import ipaddress for IP checking
import re # Import re for hostname label validation

# Try to import tldextract for better domain parsing
try:
    import tldextract
    TLDEXTRACT_AVAILABLE = True
except ImportError:
    TLDEXTRACT_AVAILABLE = False
    tldextract = None # Define tldextract as None if not available

# Import modular components
from .types import URLType
from .validation import validate_url
from .normalization import normalize_url, normalize_hostname, normalize_path # Updated import
from .security import URLSecurityConfig # Added import

# Removed duplicate normalize_path and normalize_hostname functions

logger = logging.getLogger(__name__)

class URLInfo:
    """
    Represents a URL, providing validation, normalization, and resolution
    by integrating modular validation and normalization functions.
    Immutable after creation.
    """
    __slots__ = (
        "_raw_url",
        "base_url",
        "_parsed",
        "_normalized_parsed",
        "_normalized_url",
        "is_valid",
        "error_message",
        "url_type",
        "_original_path_had_trailing_slash",
        "_initialized",
        "__dict__",  # Needed for functools.cached_property
    )

    def __init__(self, url: Optional[str], base_url: Optional[str] = None) -> None:
        """Initializes URLInfo."""
        self._raw_url: str = url or ""
        self.base_url: Optional[str] = base_url
        self._parsed: Optional[ParseResult] = None
        self._normalized_parsed: Optional[ParseResult] = None
        self._normalized_url: Optional[str] = None # Initialize as None
        self.is_valid: bool = False
        self.error_message: Optional[str] = None
        self.url_type: URLType = URLType.UNKNOWN
        self._original_path_had_trailing_slash: bool = False
        self._initialized: bool = False

        if not url or not isinstance(url, str):
            self.error_message = "URL cannot be None or empty"
            self._normalized_url = "" # Set normalized to empty string for invalid input
            self._initialized = True
            return

        try:
            logger.debug(f"URLInfo Init: raw_url='{self._raw_url}', base_url='{self.base_url}'")
            # --- Parsing and Resolution ---
            resolved_url_str = self._resolve_url(self._raw_url, self.base_url)
            if resolved_url_str is None: # _resolve_url sets error_message if needed
                 self._normalized_url = self._raw_url # Fallback for failed resolution
                 self._initialized = True
                 return
                 # Unreachable logger call removed

            logger.debug(f"URLInfo Resolved: resolved_url='{resolved_url_str}'")
            # Store if original path (before query/fragment) had a trailing slash
            url_part = self._raw_url.split('?', 1)[0].split('#', 1)[0]
            self._original_path_had_trailing_slash = url_part.endswith('/')

            # Parse the resolved URL (removes fragment automatically)
            self._parsed = urlparse(resolved_url_str)

            # Validate port after initial parsing (moved from validate_url for early exit)
            if self._parsed.port is not None and not (0 <= self._parsed.port <= 65535):
                self.is_valid = False
                self.error_message = f"Invalid port: {self._parsed.port}"
                self._normalized_url = resolved_url_str # Fallback before normalization
                self._initialized = True
                logger.debug(f"URLInfo Invalid Port: raw_url='{self._raw_url}', error='{self.error_message}'")
                return # Exit initialization

            logger.debug(f"URLInfo Parsed Resolved: parsed='{self._parsed}', original_trailing_slash={self._original_path_had_trailing_slash}")

            # --- Validation ---
            # Call the comprehensive validation function from validation module
            # This handles scheme, netloc, path/query lengths, and security patterns
            self.is_valid, self.error_message = validate_url(self._parsed)
            logger.debug(f"URLInfo Validation Result: is_valid={self.is_valid}, error='{self.error_message}'")

            if self.is_valid:
                # --- Normalization ---
                # Normalize the URL using the dedicated function from normalization module
                self._normalized_url = normalize_url(resolved_url_str, had_trailing_slash=self._original_path_had_trailing_slash)
                self._normalized_parsed = urlparse(self._normalized_url)
                logger.debug(f"URLInfo Normalized: normalized_url='{self._normalized_url}'")

                # --- Final Checks & Type Determination ---
                # Determine URL type (internal/external) based on normalized URL and base URL
                self.url_type = self._determine_url_type(self._normalized_url, self.base_url)
                logger.debug(f"URLInfo Type Determined: url_type='{self.url_type}'")
            else:
                # If validation failed, set normalized URL to the resolved string before normalization attempt
                self._normalized_url = resolved_url_str

        except ValueError as e:
            # Catch ValueErrors specifically (e.g., from port conversion, validation, normalization)
            self.is_valid = False
            self.error_message = f"ValueError: {str(e)}"
            # Use resolved_url_str if available, else raw_url
            self._normalized_url = resolved_url_str if 'resolved_url_str' in locals() else self._raw_url
            logger.warning(f"URLInfo ValueError: raw_url='{self._raw_url}', error='{self.error_message}'")

        except Exception as e:
            # Catch any other unexpected errors during processing
            self.is_valid = False
            # Ensure error message is set even in unexpected cases
            self.error_message = self.error_message or f"Unexpected error: {type(e).__name__}: {str(e)}"
            # Use resolved_url_str if available, else raw_url
            self._normalized_url = resolved_url_str if 'resolved_url_str' in locals() else self._raw_url
            logger.error(f"URLInfo Unexpected Error: raw_url='{self._raw_url}', error='{self.error_message}'", exc_info=True)

        # Fallback normalized URL if validation failed or error occurred
        # Ensure normalized_url is always a string, even if invalid
        if not self.is_valid:
            # If normalization didn't happen or failed, ensure normalized_url has a fallback
            if self._normalized_url is None:
                self._normalized_url = self._raw_url or ""
            # Ensure normalized_parsed is None if invalid
            self._normalized_parsed = None

        self._initialized = True
        logger.debug(f"URLInfo Init Complete: raw_url='{self._raw_url}', is_valid={self.is_valid}, norm_url='{self._normalized_url}', error='{self.error_message}'")

    def _resolve_url(self, url: str, base_url: Optional[str]) -> Optional[str]:
        """Resolves a potentially relative URL against a base URL."""
        if not isinstance(url, str) or not url:
            self.error_message = "URL must be a non-empty string for resolution"
            return None

        temp_raw_url = url.strip()
        base_for_join = base_url

        # Early check for disallowed schemes like javascript: or data:
        if ':' in temp_raw_url:
            raw_scheme = temp_raw_url.split(':', 1)[0].lower()
            if raw_scheme in ['javascript', 'data']:
                self.error_message = f"Disallowed scheme: {raw_scheme}"
                return None # Fail early

        # Handle protocol-relative URLs (e.g., //example.com)
        if temp_raw_url.startswith('//'):
            base_scheme = 'http' # Default to http
            if base_for_join:
                parsed_base_scheme = urlparse(base_for_join).scheme
                if parsed_base_scheme:
                    base_scheme = parsed_base_scheme
            temp_raw_url = f"{base_scheme}:{temp_raw_url}"

        # Add default scheme (http) if missing and looks like a host/path
        elif not urlparse(temp_raw_url).scheme and not base_for_join:
            # Avoid adding scheme to absolute file paths or Windows paths
            if not temp_raw_url.startswith('/') and not re.match(r'^[a-zA-Z]:[\\/]', temp_raw_url):
                # Check if it looks like a domain (contains '.') or 'localhost'
                potential_host = temp_raw_url.split('/')[0].split('?')[0].split(':')[0]
                if '.' in potential_host or potential_host.lower() == 'localhost':
                    temp_raw_url = "http://" + temp_raw_url

        # Resolve relative URLs using urljoin
        resolved_url = temp_raw_url
        if base_for_join:
            try:
                # Ensure base URL has a scheme for urljoin
                parsed_base = urlparse(base_for_join)
                if not parsed_base.scheme:
                    base_for_join = "http://" + base_for_join

                # urljoin handles relative path resolution
                resolved_url = urljoin(base_for_join, temp_raw_url)
            except ValueError as e:
                self.error_message = f"URL resolution failed: {e}"
                return None

        # Remove fragment identifier (#...) as it's not part of the canonical URL
        resolved_url_no_frag = resolved_url.split('#', 1)[0]

        # Userinfo (user:pass@) is handled during validation, not removed here.

        # Return the URL string without the fragment.
        return resolved_url_no_frag
    # If further error handling is needed here, it should be added explicitly.

        # The following lines were part of a removed try/except block and are now deleted.
        # # This parsing should ideally not fail if urljoin succeeded, but handle defensively
        # self.error_message = f"Post-resolution parsing failed: {e}"
        # return None

        # Return the URL string without the fragment.
        return resolved_url_no_frag

    def _determine_url_type(self, normalized_url: Optional[str], base_url: Optional[str]) -> URLType:
        """Determines if the URL is internal or external relative to the base URL."""
        if not self.is_valid or not normalized_url:
            return URLType.UNKNOWN

        if not base_url:
            return URLType.EXTERNAL # No base URL means everything is external

        try:
            base_info = URLInfo(base_url) # Parse the base URL
            if not base_info.is_valid:
                logger.warning(f"Base URL '{base_url}' is invalid, cannot determine URL type.")
                return URLType.UNKNOWN

            # Compare schemes first
            if self.scheme != base_info.scheme:
                logger.debug(f"Type determined EXTERNAL (scheme mismatch: {self.scheme} vs {base_info.scheme})")
                return URLType.EXTERNAL

            # Then compare registered domains (e.g., example.com)
            # Use properties that rely on tldextract if available
            if self.registered_domain and base_info.registered_domain:
                if self.registered_domain == base_info.registered_domain:
                    logger.debug(f"Type determined INTERNAL (registered domain match: {self.registered_domain})")
                    return URLType.INTERNAL
                else:
                    logger.debug(f"Type determined EXTERNAL (registered domain mismatch: {self.registered_domain} vs {base_info.registered_domain})")
                    return URLType.EXTERNAL
            else:
                # Fallback: Compare hostnames if tldextract failed or wasn't available
                # This might incorrectly classify subdomains as external
                logger.debug("Comparing hostnames as fallback for URL type determination.")
                if self.hostname == base_info.hostname:
                    logger.debug(f"Type determined INTERNAL (hostname fallback match: {self.hostname})")
                    return URLType.INTERNAL
                else:
                    logger.debug(f"Type determined EXTERNAL (hostname fallback mismatch: {self.hostname} vs {base_info.hostname})")
                    return URLType.EXTERNAL
        except Exception as e:
            logger.error(f"Error determining URL type for '{normalized_url}' against base '{base_url}': {e}", exc_info=True)
            return URLType.UNKNOWN

    # --- Properties --- #

    @property
    def raw_url(self) -> str:
        """The original, unmodified URL string."""
        return self._raw_url

    @functools.cached_property
    def normalized_url(self) -> str:
        """The normalized URL string."""
        if not self._initialized:
            raise RuntimeError("URLInfo not fully initialized.")
        # Ensure a string is always returned, even if invalid
        return self._normalized_url if self._normalized_url is not None else self._raw_url or ""

    @functools.cached_property
    def scheme(self) -> Optional[str]:
        """The URL scheme (e.g., 'http', 'https')."""
        p = self._normalized_parsed if self.is_valid else self._parsed
        return p.scheme if p else None

    @functools.cached_property
    def netloc(self) -> Optional[str]:
        """The network location (e.g., 'www.example.com:80')."""
        p = self._normalized_parsed if self.is_valid else self._parsed
        return p.netloc if p else None

    @functools.cached_property
    def hostname(self) -> Optional[str]:
        """The hostname (e.g., 'www.example.com'). Lowercased."""
        p = self._normalized_parsed if self.is_valid else self._parsed
        return p.hostname.lower() if p and p.hostname else None

    @functools.cached_property
    def port(self) -> Optional[int]:
        """The port number."""
        p = self._normalized_parsed if self.is_valid else self._parsed
        return p.port if p else None

    @functools.cached_property
    def path(self) -> Optional[str]:
        """The URL path (e.g., '/path/to/resource')."""
        p = self._normalized_parsed if self.is_valid else self._parsed
        return p.path if p else None

    @functools.cached_property
    def query(self) -> Optional[str]:
        """The query string (e.g., 'a=1&b=2')."""
        p = self._normalized_parsed if self.is_valid else self._parsed
        return p.query if p else None

    @functools.cached_property
    def query_params(self) -> Dict[str, List[str]]:
        """The query parameters as a dictionary."""
        params: Dict[str, List[str]] = {}
        if self.query:
            try:
                parsed_q = parse_qsl(self.query, keep_blank_values=True)
                for key, value in parsed_q:
                    params.setdefault(key, []).append(value)
            except Exception as e:
                logger.warning(f"Failed to parse query string '{self.query}': {e}")
        return params.copy() # Return a copy for immutability

    @functools.cached_property
    def fragment(self) -> Optional[str]:
        """The fragment identifier (e.g., 'section'). Based on raw URL."""
        # Fragment is removed during resolution/parsing, so get from raw URL
        try:
            return urlparse(self._raw_url).fragment or None
        except Exception:
            return None

    @functools.cached_property
    def is_secure(self) -> bool:
        """Checks if the URL uses a secure scheme (HTTPS or FTPS)."""
        return self.scheme in ('https', 'ftps')

    @functools.cached_property
    def is_absolute(self) -> bool:
        """Checks if the URL is absolute (has scheme and netloc)."""
        # Consider file scheme as absolute even without netloc
        return bool(self.scheme and (self.netloc or self.scheme == 'file'))

    @functools.cached_property
    def is_relative(self) -> bool:
        """Checks if the URL is relative."""
        return not self.is_absolute

    @functools.cached_property
    def is_ip_address(self) -> bool:
        """Checks if the hostname is an IP address."""
        if not self.hostname:
            return False
        try:
            ipaddress.ip_address(self.hostname)
            return True
        except ValueError:
            return False

    # --- TLDextract Properties (with fallback) --- #

    @functools.cached_property
    def _tld_extract_result(self) -> Optional[Any]:
        """Internal helper to cache tldextract result or fallback."""
        if not self.hostname or self.is_ip_address or self.hostname == 'localhost':
            return None # No TLD for IPs or localhost

        if TLDEXTRACT_AVAILABLE and tldextract:
            try:
                # Use hostname which is already normalized (lowercase, IDNA)
                return tldextract.extract(self.hostname)
            except Exception as e:
                logger.warning(f"tldextract failed for hostname '{self.hostname}': {e}")
                return None
        else:
            # Basic fallback if tldextract is not available
            parts = self.hostname.split('.')
            if len(parts) < 2:
                return None # Cannot determine TLD with less than 2 parts
            # Simple assumption: last part is suffix, second-to-last is domain
            # This is often wrong for multi-part TLDs (e.g., co.uk)
            class FallbackExtract:
                suffix = parts[-1]
                domain = parts[-2]
                # Ensure subdomain is None if no parts exist before domain/suffix
                subdomain = '.'.join(parts[:-2]) if len(parts) > 2 else None
                registered_domain = f"{domain}.{suffix}"
            return FallbackExtract()

    @functools.cached_property
    def domain_parts(self) -> Dict[str, Optional[str]]:
        """Returns a dictionary of domain components (subdomain, domain, suffix, registered_domain)."""
        # Prioritize checking for IP/localhost before using tldextract result
        if self.is_ip_address or self.hostname == 'localhost':
            # Handle IPs and localhost explicitly
            return {
                'subdomain': None, # Ensure subdomain is None
                'domain': self.hostname, # Treat the IP/localhost as the 'domain'
                'suffix': None,
                'registered_domain': self.hostname,
            }

        extract = self._tld_extract_result
        if extract:
            # Use tldextract result, ensuring subdomain is None if empty string
            sub = extract.subdomain
            return {
                'subdomain': sub if sub else None,
                'domain': extract.domain or None,
                'suffix': extract.suffix or None,
                'registered_domain': extract.registered_domain or None,
            }
        else:
            # Fallback if tldextract failed or hostname is unusual
            return {
                'subdomain': None,
                'domain': self.hostname, # Fallback domain to hostname
                'suffix': None,
                'registered_domain': self.hostname, # Fallback registered_domain to hostname
            }

    @functools.cached_property
    def subdomain(self) -> Optional[str]:
        """The subdomain part (e.g., 'www')."""
        return self.domain_parts.get('subdomain')

    @functools.cached_property
    def domain(self) -> Optional[str]:
        """The domain part (e.g., 'example' from 'www.example.com', or '[::1]' for IPv6)."""
        # Special handling for IP addresses where tldextract might return the full IP as domain
        parsed = self._normalized_parsed or self._parsed
        if parsed and parsed.hostname:
            try:
                # Check if hostname is an IP address
                ipaddress.ip_address(parsed.hostname)
                # For IPs, return the full hostname (including brackets for IPv6)
                return parsed.hostname
            except ValueError:
                # Not an IP address, rely on tldextract
                pass
        # Fallback to tldextract result if not an IP
        return self.domain_parts.get('domain')

    @functools.cached_property
    def suffix(self) -> Optional[str]:
        """The top-level domain (TLD) or suffix (e.g., 'com', 'co.uk')."""
        return self.domain_parts.get('suffix')

    @functools.cached_property
    def tld(self) -> Optional[str]:
        """Alias for suffix."""
        return self.suffix

    @functools.cached_property
    def registered_domain(self) -> Optional[str]:
        """The registered domain (e.g., 'example.com', 'example.co.uk')."""
        return self.domain_parts.get('registered_domain')

    @functools.cached_property
    def root_domain(self) -> Optional[str]:
        """Alias for registered_domain."""
        return self.registered_domain

    # --- Methods --- #

    def join(self, relative_url: str) -> 'URLInfo':
        """Joins a relative URL with the current URL (if valid)."""
        if not self.is_valid:
            raise ValueError("Cannot join with an invalid base URL")
        # Use the normalized URL as the base for joining
        return URLInfo(relative_url, base_url=self.normalized_url)

    def replace(self, **kwargs: Any) -> 'URLInfo':
        """Creates a new URLInfo object with specified components replaced."""
        if not self.is_valid or not self._normalized_parsed:
            raise ValueError("Cannot replace components on an invalid or unparsed URL")

        # Use the normalized parsed result as the base
        new_parsed = self._normalized_parsed._replace(**kwargs)
        new_url_str = urlunparse(new_parsed)

        # Create a new URLInfo instance from the modified string
        # Pass the original base_url if it existed
        return URLInfo(new_url_str, base_url=self.base_url)

    # --- Dunder Methods --- #

    def __str__(self) -> str:
        """Returns the normalized URL string."""
        return self.normalized_url

    def __repr__(self) -> str:
        """Returns a developer-friendly representation."""
        status = 'valid' if self.is_valid else f'invalid ({self.error_message})'
        return f"URLInfo(raw='{self._raw_url}', normalized='{self.normalized_url}', status='{status}')"

    def __eq__(self, other: object) -> bool:
        """Checks equality based on the normalized URL string."""
        if isinstance(other, URLInfo):
            # If both are valid, compare normalized URLs
            if self.is_valid and other.is_valid:
                return self.normalized_url == other.normalized_url
            # If both are invalid, compare raw URLs for potential equality check on input
            elif not self.is_valid and not other.is_valid:
                # Note: Comparing raw URLs for invalid instances might have limited use cases,
                # but allows distinguishing between different invalid inputs.
                return self._raw_url == other._raw_url
            # If one is valid and the other is invalid, they are not equal
            else:
                return False
        elif isinstance(other, str):
            # Compare normalized URL with the string
            return self.is_valid and self.normalized_url == other
        return NotImplemented

    def __hash__(self) -> int:
        """Computes hash based on the normalized URL for valid URLs, or raw URL for invalid ones."""
        # Hash should be consistent with __eq__ logic
        if self.is_valid:
            return hash(self.normalized_url)
        else:
            # Use raw URL for hashing invalid instances to match __eq__ logic
            return hash(self._raw_url)

    def __bool__(self) -> bool:
        """Returns True if the URL is valid, False otherwise."""
        return self.is_valid

    def __getstate__(self) -> Dict[str, Any]:
        """Prepare the object for pickling. Exclude cached properties."""
        state = {slot: getattr(self, slot) for slot in self.__slots__ if hasattr(self, slot) and slot != '__dict__'} # Exclude __dict__ explicitly
        # Add __dict__ back if it exists and contains cached_property data
        if hasattr(self, '__dict__') and self.__dict__:
            state['__dict__'] = self.__dict__.copy() # Copy to avoid modifying original
        return state

    def __setstate__(self, state: Dict[str, Any]) -> None:
        """Restore the object state from pickling."""
        # Restore __dict__ first if present
        if '__dict__' in state:
            self.__dict__.update(state['__dict__'])
            del state['__dict__']
        # Restore slotted attributes
        for slot, value in state.items():
            setattr(self, slot, value)
        # Ensure _initialized is set, default to False if missing in state
        if not hasattr(self, '_initialized'):
            self._initialized = False

    def __setattr__(self, name: str, value: Any) -> None:
        """Prevent modification of attributes after initialization."""
        # Allow setting attributes during __init__ (before _initialized is True)
        # Also allow modification of __dict__ for functools.cached_property
        if name == '__dict__' or not getattr(self, '_initialized', False):
            super().__setattr__(name, value)
        else:
            raise AttributeError(f"Cannot set attribute '{name}' on immutable URLInfo object")

# Example Usage (can be removed or kept for demonstration)
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    urls_to_test = [
        "http://example.com",
        "https://www.Example.co.uk:443/path/./../to/resource?a=1&b=2#section",
        "//google.com/",
        "page.html",
        "../images/logo.png",
        "javascript:alert('XSS')",
        "http://192.168.1.1/admin",
        "http://example.com/path%00null",
        "http://user:pass@example.com/",
        "http://xn--mnchen-3ya.de/", # IDN
        "http://localhost:8080/test",
        "file:///etc/passwd",
        "http://[::1]/", # IPv6 Loopback
        "",
        None,
    ]

    base = "https://example.com/docs/current/"

    for url_str in urls_to_test:
        print(f"--- Testing URL: {url_str} (Base: {base if url_str and not urlparse(url_str).scheme else 'None'}) ---")
        try:
            info = URLInfo(url_str, base_url=base if url_str and not urlparse(str(url_str)).scheme else None)
            print(f"  Raw:        {info.raw_url}")
            print(f"  Normalized: {info.normalized_url}")
            print(f"  Is Valid:   {info.is_valid}")
            if not info.is_valid:
                print(f"  Error:      {info.error_message}")
            else:
                print(f"  Scheme:     {info.scheme}")
                print(f"  Hostname:   {info.hostname}")
                print(f"  Port:       {info.port}")
                print(f"  Path:       {info.path}")
                print(f"  Query:      {info.query}")
                print(f"  Fragment:   {info.fragment}")
                print(f"  Type:       {info.url_type}")
                print(f"  Reg Domain: {info.registered_domain}")
                print(f"  DomainParts:{info.domain_parts}")
                print(f"  Is Secure:  {info.is_secure}")
                print(f"  Is Absolute:{info.is_absolute}")
                print(f"  Is IP Addr: {info.is_ip_address}")

            # Test join
            if info.is_valid:
                try:
                    joined_info = info.join("new_page.html?q=test")
                    print(f"  Joined URL: {joined_info.normalized_url}")
                except ValueError as e:
                    print(f"  Join failed: {e}")

            # Test replace
            if info.is_valid:
                try:
                    replaced_info = info.replace(scheme='ftp', port=2121)
                    print(f"  Replaced:   {replaced_info.normalized_url}")
                except ValueError as e:
                    print(f"  Replace failed: {e}")
                except Exception as e:
                     print(f"  Replace unexpected error: {e}")

        except Exception as e:
            print(f"  *** UNEXPECTED ERROR during URLInfo creation: {e} ***")
        print("-" * 20)
