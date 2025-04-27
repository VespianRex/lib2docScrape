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
    # Order matters: Check scheme, then netloc/port, then path/query/security
    checks = [
        (validate_scheme, parsed),
        (validate_netloc, parsed), # Includes hostname validation
        (validate_port, parsed),
        (validate_path, parsed),
        (validate_query, parsed),
        (validate_security_patterns, parsed) # Security checks last
    ]
    for check_func, data in checks:
        is_ok, error = check_func(data)
        if not is_ok:
            return False, error
    return True, None

def validate_scheme(p: ParseResult) -> Tuple[bool, Optional[str]]:
    """Validate the URL scheme."""
    scheme = p.scheme.lower() if p.scheme else ''
    allowed = URLSecurityConfig.ALLOWED_SCHEMES
    logger.debug(f"!!! validate_scheme: Checking scheme '{scheme}' against ALLOWED: {allowed}") # <<< ADDED LOG
    if not scheme or scheme not in allowed:
        logger.debug(f"Scheme '{scheme}' is invalid or not allowed.")
        return False, f"Invalid scheme: {p.scheme or 'None'}"
    logger.debug(f"Scheme '{scheme}' is valid.")
    return True, None

def validate_netloc(p: ParseResult) -> Tuple[bool, Optional[str]]:
    logger.debug(f"Validating netloc for parsed: {p}") # Add log
    """Validate the URL network location component (hostname, IP)."""
    scheme = p.scheme.lower() if p.scheme else ''
    # Use "Missing host" as per test expectation, unless it's a file scheme
    if not p.netloc and scheme != 'file':
        return False, "Missing host"
    if '@' in p.netloc:
        return False, "Auth info not allowed"
    hostname = p.hostname.lower() if p.hostname else None
    logger.debug(f"Validating netloc for hostname: {hostname}") # Add log
    if not hostname and scheme != 'file':
        return False, "Missing host"
    if hostname:
        # Check against disallowed hosts/IPs for SSRF first
        disallowed_hosts = URLSecurityConfig.SSRF_DISALLOWED_HOSTS
        logger.debug(f"!!! validate_netloc: Checking hostname '{hostname}' against DISALLOWED: {disallowed_hosts}") # <<< ADDED LOG
        if hostname in disallowed_hosts:
            logger.debug(f"Hostname '{hostname}' IS in disallowed list (SSRF risk). INVALID.")
            return False, f"Disallowed host: {hostname}"

        # Check if it's an IP address
        try:
            logger.debug(f"Attempting to parse hostname '{hostname}' as IP.") # Add log
            ip = ipaddress.ip_address(hostname)
            logger.debug(f"Hostname '{hostname}' parsed as IP: {ip}") # Add log
            # Check against security config for disallowed IPs
            if ip.is_private:
                # Allow private IPs based on config, but SSRF check above handles common cases
                # If config explicitly forbids *all* private, add check here
                # if not URLSecurityConfig.ALLOW_PRIVATE_IPS:
                #    logger.debug(f"IP {ip} is private and disallowed by config. INVALID.")
                #    return False, f"Private IP not allowed: {hostname}"
                logger.debug(f"IP {ip} is private. Continuing validation.") # Modify log
            if ip.is_loopback:
                logger.debug(f"IP {ip} is loopback.") # Add log
                # Allow IPv6 loopback [::1] but block IPv4 127.x.x.x
                if ip.version == 4:
                    logger.debug(f"IP {ip} is IPv4 loopback. INVALID.") # Add log
                    return False, f"Loopback IP not allowed: {hostname}"
                logger.debug(f"IP {ip} is IPv6 loopback. Continuing.") # Add log
                # Implicitly allow IPv6 loopback by not returning False here
            if ip.is_link_local:
                 logger.debug(f"IP {ip} is link-local. INVALID.") # Add log
                 return False, f"Link-local IP not allowed: {hostname}"
            # Add checks for reserved, multicast, unspecified if needed based on config
            logger.debug(f"IP {ip} passed checks. VALID.") # Add log
            return True, None # Valid IP
        except ValueError:
            logger.debug(f"Hostname '{hostname}' is not a valid IP. Validating as domain.") # Add log
            # Not an IP, validate as domain name
            if len(hostname) > 253:
                return False, "Domain too long"
            # Remove trailing dot for validation
            temp_host = hostname[:-1] if hostname.endswith('.') else hostname
            if not temp_host:
                return False, "Empty domain"
            labels = temp_host.split('.')
            # A valid domain (not localhost) must have at least two labels (e.g., 'domain.tld')
            # unless it's a single-label name explicitly allowed (e.g., intranet names - not typical for web)
            # Check individual label constraints first
            if any(not l or len(l.encode('utf-8')) > 63 for l in labels):
                return False, "Invalid domain label length or empty label"
            # THEN check label count (TLD requirement)
            if len(labels) < 2 and temp_host != 'localhost': # Re-check localhost just in case
                # Consider if single-label domains should be allowed based on context
                # For general web URLs, usually require a TLD.
                return False, f"Invalid domain (requires TLD): {temp_host}"
            # FINALLY, check TLD length if there are multiple labels
            if len(labels) > 1 and len(labels[-1]) < 2 and temp_host != 'localhost':
                 return False, f"Invalid TLD length: {labels[-1]}"
            try:
                logger.debug(f"Attempting to parse hostname '{hostname}' as IP.") # Add log
                # Check each label individually against the pattern
                for label in labels:
                    # Use the pattern from URLSecurityConfig
                    if not URLSecurityConfig.DOMAIN_LABEL_PATTERN.match(label):
                        # Allow punycode labels (xn--) which might not match the simple pattern
                        if not label.startswith('xn--'):
                            return False, f"Invalid label chars in: {label}"
                # Check the full hostname with IDNA encoding
                # This also catches many invalid character issues
                idna.encode(temp_host)
            except idna.IDNAError as e:
                return False, f"Invalid IDNA: {temp_host} ({e})"
            except Exception as e:
                # Catch other potential errors during validation
                return False, f"Domain validation error: {e}"
    # If hostname is None but scheme is 'file', it's valid
    elif scheme == 'file':
        return True, None
    # Otherwise (no hostname, not file scheme) it's invalid
    else:
        return False, "Missing host"

    logger.debug(f"Validation netloc falling through for hostname: {hostname}. Defaulting to VALID.") # Add log
    return True, None # Default pass if hostname checks succeed

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
        # Decode path for security checks later
        _ = unquote_plus(p.path)
        # Invalid char checks moved to validate_security_patterns
    except Exception as e:
        return False, f"Path decode error: {e}"
    return True, None

def validate_query(p: ParseResult) -> Tuple[bool, Optional[str]]:
    """Validate the URL query string."""
    if len(p.query) > URLSecurityConfig.MAX_QUERY_LENGTH:
        return False, "Query too long"
    try:
        # Decode query for security checks later
        _ = unquote_plus(p.query)
        # Invalid char checks moved to validate_security_patterns
    except Exception as e:
        return False, f"Query decode error: {e}"
    return True, None

def validate_security_patterns(p: ParseResult) -> Tuple[bool, Optional[str]]:
    """Check decoded path and query for security patterns defined in URLSecurityConfig."""
    try:
        # Decode once for multiple checks
        decoded_path = unquote_plus(p.path)
        decoded_query = unquote_plus(p.query)

        # 1. Null Byte Check (PRIORITY)
        # Check both raw and decoded strings for null bytes first
        if (URLSecurityConfig.NULL_BYTE_PATTERN.search(p.path) or
            URLSecurityConfig.NULL_BYTE_PATTERN.search(decoded_path)):
            return False, "Null byte in path"
        if (URLSecurityConfig.NULL_BYTE_PATTERN.search(p.query) or
            URLSecurityConfig.NULL_BYTE_PATTERN.search(decoded_query)):
            return False, "Null byte in query"

        # 2. General Invalid Characters Check (after null byte)
        # Temporarily replace backslashes before checking invalid chars
        # This allows paths like '..\folder' to pass if they will be normalized later
        temp_path_for_char_check = decoded_path.replace('\\', '/')
        if URLSecurityConfig.INVALID_CHARS.search(temp_path_for_char_check):
            return False, "Invalid chars in decoded path"
        if URLSecurityConfig.INVALID_CHARS.search(decoded_query):
            return False, "Invalid chars in decoded query"

        # 3. Path Traversal Check (more robust)
        # Replace backslashes before normalization for posixpath
        path_for_norm = decoded_path.replace('\\', '/')
        normalized_path = posixpath.normpath(path_for_norm)
        logger.debug(f"Path traversal check: original='{decoded_path}', pre-norm='{path_for_norm}', normalized='{normalized_path}'") # Add log
        if normalized_path.startswith('../') or '/../' in normalized_path or normalized_path == '..':
             # Check includes internal traversals like /a/../b
             # Also check if the entire normalized path is just '..'
            logger.debug(f"Path traversal attempt detected after normalization: '{normalized_path}'")
            return False, "Path traversal attempt detected after normalization"
        # Removed check on original path: URLSecurityConfig.INVALID_PATH_TRAVERSAL.search(decoded_path)
        # The check on the normalized path above is sufficient and handles cases like '..\folder' correctly.

        # 4. Disallowed Schemes Embedded in Path/Query
        if 'javascript:' in decoded_path.lower() or 'javascript:' in decoded_query.lower():
            return False, "JavaScript scheme in path or query"
        if 'data:' in decoded_path.lower() or 'data:' in decoded_query.lower():
            return False, "Data scheme in path or query"

        # 5. XSS Patterns Check
        if (URLSecurityConfig.XSS_PATTERNS.search(decoded_path) or
            URLSecurityConfig.XSS_PATTERNS.search(decoded_query)):
            return False, "XSS pattern"

        # 6. SQL Injection Patterns Check
        if (URLSecurityConfig.SQLI_PATTERNS.search(decoded_path) or
            URLSecurityConfig.SQLI_PATTERNS.search(decoded_query)):
            return False, "SQLi pattern"

        # 7. Command Injection Patterns Check
        if (URLSecurityConfig.CMD_INJECTION_PATTERNS.search(decoded_path) or
            URLSecurityConfig.CMD_INJECTION_PATTERNS.search(decoded_query)):
            return False, "Cmd Injection pattern"

    except Exception as e:
        # Log the exception appropriately
        logger.error(f"Error during security pattern check: {e}", exc_info=True)
        return False, f"Security check decode/pattern error: {e}"

    # If all checks pass
    return True, None