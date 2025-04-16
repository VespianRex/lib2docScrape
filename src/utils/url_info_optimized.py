import functools
import idna
import re
import ipaddress
import posixpath
import logging
from enum import Enum, auto
from typing import Optional, Tuple, Any, Dict, List, Pattern
from urllib.parse import urlparse, urljoin, urlunparse, parse_qsl, urlencode, ParseResult, quote, unquote_plus

# Define URLType Enum
class URLType(Enum):
    INTERNAL = auto()
    EXTERNAL = auto()
    UNKNOWN = auto()

# Security Configuration
class URLSecurityConfig:
    """Security configuration for URL validation and sanitization."""
    ALLOWED_SCHEMES = {'http', 'https', 'file', 'ftp'}
    MAX_PATH_LENGTH = 2048
    MAX_QUERY_LENGTH = 2048
    PATH_SAFE_CHARS = "/:@-._~!$&'()*+,;="  # RFC 3986 + common allowed chars
    
    # Pre-compile all regex patterns for better performance
    INVALID_CHARS: Pattern = re.compile(r'[<>"\'\'\']')
    INVALID_PATH_TRAVERSAL: Pattern = re.compile(r'(?:^|/)\.\.\.(?:/|$)')  # Detects /../ or ../
    XSS_PATTERNS: Pattern = re.compile(
        r'<script|javascript:|vbscript:|data:text/html|onerror=|onload=|onmouseover=|onclick=|alert\(|eval\(|Function\(|setTimeout\(|setInterval\(|document\.|window\.|fromCharCode|String\.fromCodePoint|base64',
        re.IGNORECASE
    )
    SQLI_PATTERNS: Pattern = re.compile(r"'\s*OR\s*'|'\s*--|\s*UNION\s+SELECT", re.IGNORECASE)
    CMD_INJECTION_PATTERNS: Pattern = re.compile(r'[;`|&]')
    NULL_BYTE_PATTERN: Pattern = re.compile(r'%00|\x00')
    DOMAIN_LABEL_PATTERN: Pattern = re.compile(r'^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$', re.IGNORECASE)


class URLInfo:
    """
    Represents a URL, providing validation, normalization, and resolution. Immutable after creation.
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
        "__dict__",  # Added to allow cached_property to store values
    )

    # Reference security config values
    ALLOWED_SCHEMES = URLSecurityConfig.ALLOWED_SCHEMES
    MAX_PATH_LENGTH = URLSecurityConfig.MAX_PATH_LENGTH
    MAX_QUERY_LENGTH = URLSecurityConfig.MAX_QUERY_LENGTH
    INVALID_CHARS = URLSecurityConfig.INVALID_CHARS
    INVALID_PATH_TRAVERSAL = URLSecurityConfig.INVALID_PATH_TRAVERSAL
    XSS_PATTERNS = URLSecurityConfig.XSS_PATTERNS
    SQLI_PATTERNS = URLSecurityConfig.SQLI_PATTERNS
    CMD_INJECTION_PATTERNS = URLSecurityConfig.CMD_INJECTION_PATTERNS
    NULL_BYTE_PATTERN = URLSecurityConfig.NULL_BYTE_PATTERN
    PATH_SAFE_CHARS = URLSecurityConfig.PATH_SAFE_CHARS
    DOMAIN_LABEL_PATTERN = URLSecurityConfig.DOMAIN_LABEL_PATTERN
    
    # Common scheme default ports
    DEFAULT_PORTS = {
        'http': 80,
        'https': 443,
        'ftp': 21,
    }
    
    logger = logging.getLogger(__name__)

    def __init__(self, url: Optional[str], base_url: Optional[str] = None) -> None:
        """Initializes URLInfo."""
        self._raw_url: str = url or ""
        self.base_url: Optional[str] = base_url
        self._parsed: Optional[ParseResult] = None
        self._normalized_parsed: Optional[ParseResult] = None
        self._normalized_url: str = self._raw_url  # Default normalized to raw
        self.is_valid: bool = False
        self.error_message: Optional[str] = None
        self.url_type: URLType = URLType.UNKNOWN
        self._original_path_had_trailing_slash: bool = False
        self._initialized: bool = False

        if not url or not isinstance(url, str):
            self.error_message = "URL cannot be None or empty"
            self._normalized_url = ""
            self._initialized = True
            return

        try:
            # Capture trailing slash info before any parsing
            url_part = url.split('?', 1)[0].split('#', 1)[0]
            self._original_path_had_trailing_slash = url_part.endswith('/')

            self._parse_and_resolve()

            if self._parsed:
                validation_passed, error = self._validate(self._parsed)
                if validation_passed:
                    self.is_valid = True
                    self._normalize()
                    self.url_type = self._determine_url_type(self._normalized_url, self.base_url)
                else:
                    self.error_message = error
            else:
                if not self.error_message:
                    self.error_message = "URL parsing failed"

        except Exception as e:
            self.is_valid = False
            self.error_message = f"{type(e).__name__}: {str(e)}"

        if not self.is_valid:
            self._normalized_url = self._raw_url or ""
            self._normalized_parsed = None

        self._initialized = True

    def _parse_and_resolve(self) -> None:
        """Parses raw URL, resolves if relative, stores in self._parsed."""
        if not isinstance(self.raw_url, str) or not self.raw_url:
            self.error_message = "URL must be a non-empty string"
            return

        temp_raw_url = self.raw_url.strip()
        base_for_join = self.base_url

        # Early check for disallowed schemes
        if ':' in temp_raw_url:
            raw_scheme = temp_raw_url.split(':', 1)[0].lower()
            if raw_scheme in ['javascript', 'data']:
                self.error_message = f"Disallowed scheme: {raw_scheme}"
                return

        # Handle protocol-relative URLs (default to http)
        if temp_raw_url.startswith('//'):
            base_scheme = 'http'
            if base_for_join:
                parsed_base_scheme = urlparse(base_for_join).scheme
                if parsed_base_scheme:
                    base_scheme = parsed_base_scheme
            temp_raw_url = f"{base_scheme}:{temp_raw_url}"

        # Add default scheme (http) if missing and looks like a host
        elif not urlparse(temp_raw_url).scheme and not base_for_join and not temp_raw_url.startswith('file:'):
            if not temp_raw_url.startswith('/') and not re.match(r'^[a-zA-Z]:[\\\\]', temp_raw_url):
                potential_host = temp_raw_url.split('/')[0].split('?')[0].split(':')[0]
                if '.' in potential_host or potential_host.lower() == 'localhost':
                    temp_raw_url = "http://" + temp_raw_url  # Default HTTP

        # Resolve relative URLs
        resolved_url = temp_raw_url
        if base_for_join:
            try:
                # Ensure base URL has a scheme
                parsed_base = urlparse(base_for_join)
                if not parsed_base.scheme:
                    base_for_join = "http://" + base_for_join
                
                # Ensure base URL has proper trailing slash for directory-like paths
                if parsed_base.path:
                    # If path doesn't end with slash and doesn't look like a file (no extension)
                    if not parsed_base.path.endswith('/') and '.' not in parsed_base.path.split('/')[-1]:
                        base_for_join = base_for_join.rstrip('/') + '/'
                    # If path is empty, add a trailing slash
                    elif not parsed_base.path:
                        base_for_join = base_for_join.rstrip('/') + '/'
                
                # Join URLs properly
                resolved_url = urljoin(base_for_join, temp_raw_url)
            except ValueError as e:
                self.error_message = f"Resolution failed: {e}"
                return

        # Parse the resolved URL (remove fragment, remove auth)
        try:
            resolved_url_no_frag = resolved_url.split('#', 1)[0]
            parsed_temp = urlparse(resolved_url_no_frag)
            netloc = parsed_temp.netloc
            if '@' in netloc:
                netloc = netloc.split('@', 1)[1]
            self._parsed = parsed_temp._replace(netloc=netloc)
        except ValueError as e:
            self.error_message = f"Parsing failed: {e}"
            self._parsed = None

    def _validate(self, parsed: ParseResult) -> Tuple[bool, Optional[str]]:
        """Orchestrates validation checks."""
        checks = [
            (self._validate_scheme, parsed),
            (self._validate_netloc, parsed),
            (self._validate_port, parsed),
            (self._validate_path, parsed),
            (self._validate_query, parsed),
            (self._validate_security_patterns, parsed)
        ]
        for check_func, data in checks:
            is_ok, error = check_func(data)
            if not is_ok:
                return False, error
        return True, None

    # --- Validation Helpers ---
    def _validate_scheme(self, p: ParseResult) -> Tuple[bool, Optional[str]]:
        scheme = p.scheme.lower() if p.scheme else ''
        if not scheme or scheme not in self.ALLOWED_SCHEMES:
            return False, f"Invalid scheme: {p.scheme or 'None'}"
        return True, None

    def _validate_netloc(self, p: ParseResult) -> Tuple[bool, Optional[str]]:
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
                    if not all(self.DOMAIN_LABEL_PATTERN.match(l) for l in labels):
                        return False, f"Invalid label chars: {temp_host}"
                except idna.IDNAError as e:
                    return False, f"Invalid IDNA: {temp_host} ({e})"
                except Exception as e:
                    return False, f"Domain validation error: {e}"
        return True, None

    def _validate_port(self, p: ParseResult) -> Tuple[bool, Optional[str]]:
        if p.port is not None and not (0 <= p.port <= 65535):
            return False, f"Invalid port: {p.port}"
        return True, None

    def _validate_path(self, p: ParseResult) -> Tuple[bool, Optional[str]]:
        if len(p.path) > self.MAX_PATH_LENGTH:
            return False, "Path too long"
        try:
            decoded_path = unquote_plus(p.path)
            if self.INVALID_CHARS.search(decoded_path):
                return False, "Invalid chars in decoded path"
            norm_decoded = posixpath.normpath(decoded_path)
            if norm_decoded.startswith('../') or '/../' in norm_decoded:
                return False, "Path traversal attempt detected"
        except Exception as e:
            return False, f"Path decode/validation error: {e}"
        return True, None

    def _validate_query(self, p: ParseResult) -> Tuple[bool, Optional[str]]:
        if len(p.query) > self.MAX_QUERY_LENGTH:
            return False, "Query too long"
        try:
            decoded_query = unquote_plus(p.query)
            if self.INVALID_CHARS.search(decoded_query):
                return False, "Invalid chars in decoded query"
        except Exception as e:
            return False, f"Query decode/validation error: {e}"
        return True, None

    def _validate_security_patterns(self, p: ParseResult) -> Tuple[bool, Optional[str]]:
        """Check decoded path and query for other security patterns."""
        try:
            decoded_path = unquote_plus(p.path)
            decoded_query = unquote_plus(p.query)
            
            # Check for directory traversal attempts - more comprehensive check
            normalized_path = posixpath.normpath(decoded_path)
            if (normalized_path.startswith('../') or 
                '/../' in normalized_path or 
                normalized_path == '/..' or 
                self.INVALID_PATH_TRAVERSAL.search(decoded_path) or
                '..' in decoded_path.split('/')):
                return False, "Directory traversal attempt"
                
            # Check for XSS patterns
            if self.XSS_PATTERNS.search(decoded_path) or self.XSS_PATTERNS.search(decoded_query):
                return False, "XSS pattern"
                
            # Check for SQL injection patterns
            if self.SQLI_PATTERNS.search(decoded_path) or self.SQLI_PATTERNS.search(decoded_query):
                return False, "SQLi pattern"
                
            # Check for command injection patterns
            if self.CMD_INJECTION_PATTERNS.search(decoded_path) or self.CMD_INJECTION_PATTERNS.search(decoded_query):
                return False, "Cmd Injection pattern"
                
            # Check for null byte injection
            if self.NULL_BYTE_PATTERN.search(p.path) or self.NULL_BYTE_PATTERN.search(decoded_path):
                return False, "Null byte in path"
                
            if self.NULL_BYTE_PATTERN.search(p.query) or self.NULL_BYTE_PATTERN.search(decoded_query):
                return False, "Null byte in query"
                
            # Check for disallowed schemes in the path or query
            if 'javascript:' in decoded_path.lower() or 'javascript:' in decoded_query.lower():
                return False, "JavaScript scheme in path or query"
                
            if 'data:' in decoded_path.lower() or 'data:' in decoded_query.lower():
                return False, "Data scheme in path or query"
        except Exception as e:
            return False, f"Security check decode error: {e}"
        return True, None

    # --- Helper for Hostname Normalization ---
    @staticmethod
    def _normalize_hostname(hostname: str) -> str:
        """Normalize hostname to lowercase and handle IDN domains."""
        hostname_lower = hostname.lower().rstrip('.')
        try:
            # Check if hostname contains non-ASCII characters
            if not all(ord(c) < 128 for c in hostname_lower):
                # Properly encode IDN domains to Punycode
                return idna.encode(hostname_lower).decode('ascii')
            return hostname_lower
        except idna.IDNAError as e:
            raise ValueError(f"Invalid IDNA: {hostname}") from e

    # --- Normalization ---
    def _normalize(self) -> None:
        """Orchestrates normalization and sets _normalized_parsed, _normalized_url."""
        if not self._parsed or not self.is_valid:
            if self._normalized_url is None:
                self._normalized_url = self._raw_url or ""
            return
        try:
            p = self._parsed
            scheme = p.scheme.lower()
            
            # Normalize hostname - convert to lowercase and handle IDN domains
            hostname = p.hostname
            port = p.port
            netloc_norm = ""
            
            if hostname:
                # Normalize hostname: lowercase, remove trailing dot, Punycode encode IDN
                try:
                    hostname_norm = self._normalize_hostname(hostname)
                    netloc_norm = hostname_norm
                except (idna.IDNAError, ValueError) as e:
                    self.logger.warning(f"IDNA encoding failed for {hostname}: {e}. Falling back.")
                    netloc_norm = hostname.lower().rstrip('.')  # Fallback
                except Exception as e:
                    self.logger.error(f"Unexpected error normalizing hostname {hostname}: {e}")
                    netloc_norm = hostname.lower().rstrip('.')  # Fallback
            
            # Add port if it's not the default for the scheme
            if port is not None and not (scheme in self.DEFAULT_PORTS and port == self.DEFAULT_PORTS[scheme]):
                netloc_norm += f":{port}"

            # Normalize path
            path_norm = self._normalize_path(p.path)

            # Normalize query: preserve original order
            query_params = parse_qsl(p.query, keep_blank_values=True)
            # Encode query params correctly. No safe chars needed for standard encoding.
            query_norm = urlencode(query_params, doseq=True)

            # Ensure path is explicitly "/" if empty after normalization, before unparse
            if not path_norm or path_norm == ".":
                path_norm = "/"

            # Reconstruct normalized URL using urlunparse
            self._normalized_parsed = ParseResult(scheme, netloc_norm, path_norm, p.params, query_norm, '')
            self._normalized_url = urlunparse(self._normalized_parsed)

        except Exception as e:
            self.is_valid = False
            self.error_message = f"Normalization failed: {type(e).__name__}: {str(e)}"
            self._normalized_url = self._raw_url or ""
            self._normalized_parsed = None

    def _normalize_path(self, path: str) -> str:
        """Normalizes path: unquotes, resolves ., .., handles slashes, re-encodes."""
        if not path:
            return "/"

        original_had_trailing_slash = self._original_path_had_trailing_slash
        is_absolute = path.startswith('/')

        try:
            unquoted = unquote_plus(path)
        except Exception as e:
            self.logger.warning(f"Path unquoting failed for '{path}': {e}")
            unquoted = path

        # First, split the path into segments
        segments = unquoted.split('/')
        result = []
        
        # Process each segment according to RFC 3986
        for i, segment in enumerate(segments):
            # Skip empty segments except for the first one in absolute paths
            if segment == '' and (i > 0 or not is_absolute):
                continue
            # Skip '.' segments
            elif segment == '.':
                continue
            # Handle '..' segments
            elif segment == '..':
                if result and result[-1] != '' and result[-1] != '..':
                    result.pop()
                elif not is_absolute:
                    # For relative paths, keep '..' at the beginning
                    result.append('..')
            else:
                result.append(segment)
        
        # Reconstruct the path
        if is_absolute:
            # Ensure absolute paths start with /
            if not result or result[0] != '':
                result.insert(0, '')
            normalized = '/' + '/'.join(result[1:]) if len(result) > 1 else '/'
        else:
            normalized = '/'.join(result) if result else '.'
        
        # Preserve trailing slash if original had one
        if original_had_trailing_slash and not normalized.endswith('/') and normalized != '/':
            normalized += '/'
        
        # Re-quote the path with appropriate safe characters
        try:
            path_safe = self.PATH_SAFE_CHARS
            encoded_path = quote(normalized, safe=path_safe)
            return encoded_path
        except Exception as e:
            self.logger.error(f"Path encoding failed for '{normalized}': {e}")
            raise ValueError(f"Path encoding failed for '{normalized}': {e}")

    # --- Type Determination ---
    @staticmethod
    def _determine_url_type(normalized_url: Optional[str], base_url: Optional[str]) -> URLType:
        """Determines whether URL is internal or external relative to base_url."""
        if not normalized_url or not base_url:
            return URLType.UNKNOWN
        try:
            norm_p = urlparse(normalized_url)
            base_p = urlparse(base_url)
            
            # Match on scheme and netloc (case-insensitive)
            if (norm_p.scheme.lower() == base_p.scheme.lower() and 
                norm_p.netloc.lower() == base_p.netloc.lower()):
                return URLType.INTERNAL
            else:
                return URLType.EXTERNAL
        except Exception:
            return URLType.UNKNOWN

    # --- Public Properties ---
    @property
    def raw_url(self) -> str:
        return self._raw_url if self._raw_url is not None else ""

    @property
    def normalized_url(self) -> str:
        return self._normalized_url if self._normalized_url is not None else ""

    @property
    def scheme(self) -> str:
        if not self.is_valid:
            return ""
        p = self._normalized_parsed if self._normalized_parsed else self._parsed
        return p.scheme.lower() if p and p.scheme else ""

    @functools.cached_property
    def netloc(self) -> str:
        return self._normalized_parsed.netloc if self.is_valid and self._normalized_parsed else ""

    @functools.cached_property
    def path(self) -> str:
        return self._normalized_parsed.path if self.is_valid and self._normalized_parsed else ""

    @functools.cached_property
    def query(self) -> str:
        return self._normalized_parsed.query if self.is_valid and self._normalized_parsed else ""

    @property
    def port(self) -> Optional[int]:
        return self._parsed.port if self.is_valid and self._parsed else None

    @functools.cached_property
    def query_params(self) -> Dict[str, List[str]]:
        """Returns parsed query parameters as a dictionary of lists."""
        if not self.is_valid or not self._normalized_parsed or not self._normalized_parsed.query:
            return {}
        
        result: Dict[str, List[str]] = {}
        for key, value in parse_qsl(self._normalized_parsed.query, keep_blank_values=True):
            if key in result:
                result[key].append(value)
            else:
                result[key] = [value]
        return result

    @property
    def username(self) -> str:
        """Returns the username component of the URL, if present."""
        if not self.is_valid or not self._parsed:
            return ""
        # Extract username from the original parsed URL
        netloc = self._parsed.netloc
        if '@' in netloc:
            auth_part = netloc.split('@', 1)[0]
            if ':' in auth_part:
                return auth_part.split(':', 1)[0]
            return auth_part
        return ""

    @property
    def password(self) -> str:
        """Returns the password component of the URL, if present."""
        if not self.is_valid or not self._parsed:
            return ""
        # Extract password from the original parsed URL
        netloc = self._parsed.netloc
        if '@' in netloc:
            auth_part = netloc.split('@', 1)[0]
            if ':' in auth_part:
                return auth_part.split(':', 1)[1]
        return ""

    @property
    def fragment(self) -> str:
        """Returns the fragment (hash) component of the URL."""
        if not self.is_valid or not self._parsed:
            return ""
        # We need to get the fragment from the original URL since we strip it during parsing
        if '#' in self._raw_url:
            return self._raw_url.split('#', 1)[1]
        return ""

    @functools.cached_property
    def domain(self) -> str:
        """Returns the domain name."""
        return self._normalized_parsed.hostname if self.is_valid and self._normalized_parsed and self._normalized_parsed.hostname else ""

    @property
    def url(self) -> str:
        """Alias for normalized_url."""
        return self.normalized_url

    @functools.cached_property
    def root_domain(self) -> str:
        """Extracts the root domain (without subdomains)."""
        if not self.domain:
            return ""
            
        domain = self.domain
        parts = domain.split('.')
        
        # Handle special cases
        if domain == 'localhost' or len(parts) <= 2:
            return domain
            
        # Simple heuristic: could be improved with a PSL library
        # This assumes the domain has at least 2 parts (e.g., example.com)
        # The last part is the TLD, the part before it is the domain name
        if len(parts) > 2:
            # Check for country code TLDs with second-level domains like .co.uk
            if parts[-2] in ['co', 'com', 'org', 'net', 'ac', 'gov', 'edu'] and len(parts[-1]) == 2:
                if len(parts) > 3:
                    return f"{parts[-3]}.{parts[-2]}.{parts[-1]}"
                else:
                    return f"{parts[-2]}.{parts[-1]}"
            else:
                # Regular domain like example.com
                return f"{parts[-2]}.{parts[-1]}"
        
        return domain

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, URLInfo):
            return False
        return self.normalized_url == other.normalized_url

    def __hash__(self) -> int:
        return hash(self.normalized_url)

    def __str__(self) -> str:
        return self.normalized_url

    def __repr__(self) -> str:
        return f"URLInfo('{self.normalized_url}')"

    def __setattr__(self, name, value):
        if name != "_initialized" and getattr(self, "_initialized", False):
            raise AttributeError(f"Cannot modify immutable URLInfo: {name}")
        super().__setattr__(name, value)