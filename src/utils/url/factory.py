import functools
import logging
from typing import Optional, Any, Dict, List, Tuple
from types import MappingProxyType
from urllib.parse import urlparse, parse_qsl, ParseResult, urlunparse, unquote_plus
import ipaddress

# Try to import tldextract for better domain parsing
try:
    import tldextract
    TLDEXTRACT_AVAILABLE = True
except ImportError:
    tldextract = None
    TLDEXTRACT_AVAILABLE = False
    logging.warning("tldextract not found. Domain parsing will be limited.")

# Import necessary components from other modules
from .types import URLType
from .validation import validate_url
from .normalization import normalize_url
from .security import URLSecurityConfig
from .domain_parser import extract_domain_parts
from .resolution import resolve_url
from .type_determiner import determine_url_type

# Import URLInfo (forward reference needed in type hints)
from .info import URLInfo

logger = logging.getLogger(__name__)

def create_url_info(url: Optional[str], base_url: Optional[str] = None) -> URLInfo:
    """
    Factory function to create and initialize a URLInfo object.
    Encapsulates the complex URL processing logic.
    """
    # This function will contain the logic previously in URLInfo.__init__
    # Initialize a URLInfo object with default values
    url_info = URLInfo() # Initialize with no arguments

    url_info._raw_url = url or ""
    url_info.base_url = base_url
    url_info._parsed = None
    url_info._normalized_parsed = None
    url_info._normalized_url = None
    url_info.is_valid = False
    url_info.error_message = None
    url_info.url_type = URLType.UNKNOWN
    url_info._original_path_had_trailing_slash = False
    url_info._original_fragment = None
    url_info._initialized = False # Will set to True at the end

    if not url or not isinstance(url, str):
        url_info.error_message = "URL cannot be None or empty"
        url_info._normalized_url = ""
        url_info._initialized = True
        return url_info

    # --- Initial Security Checks on Raw URL ---
    try:
        # Parse the raw URL early for initial security checks
        raw_parsed_for_path = urlparse(url_info._raw_url)

        # Check for control characters in the raw URL before any processing
        if URLSecurityConfig.CONTROL_CHARS_PATTERN.search(url_info._raw_url):
            url_info.is_valid = False
            url_info.error_message = "Control characters in URL"
            url_info._normalized_url = url_info._raw_url # Fallback
            url_info._initialized = True
            logger.debug(f"URLInfo Invalid (Control Chars): raw_url='{url_info._raw_url}', error='{url_info.error_message}'")
            return url_info # Exit initialization early

        # Check for null bytes in raw URL (decode first)
        # Use try-except for decoding robustness
        try:
            # Decode path and query separately to avoid issues with '#' or '?' in values
            decoded_path = unquote_plus(raw_parsed_for_path.path)
            decoded_query = unquote_plus(raw_parsed_for_path.query)
            if URLSecurityConfig.NULL_BYTE_PATTERN.search(decoded_path) or \
               URLSecurityConfig.NULL_BYTE_PATTERN.search(decoded_query):
                url_info.is_valid = False
                url_info.error_message = "Null byte detected in raw URL path or query"
                url_info._normalized_url = url_info._raw_url # Fallback
                url_info._initialized = True
                logger.debug(f"URLInfo Invalid (Null Byte Raw): raw_url='{url_info._raw_url}', error='{url_info.error_message}'")
                return url_info # Exit initialization early
        except Exception as decode_err:
            url_info.is_valid = False
            url_info.error_message = f"URL decoding failed during initial security check: {decode_err}"
            url_info._normalized_url = url_info._raw_url # Fallback
            url_info._initialized = True
            logger.warning(f"URLInfo Initial Security Check Decode Error: raw_url='{url_info._raw_url}', error='{url_info.error_message}'")
            return url_info


    except Exception as e:
         # Catch potential errors during early checks (e.g., urlparse issues on raw url)
         url_info.is_valid = False
         url_info.error_message = f"Error during initial security checks: {e}"
         url_info._normalized_url = url_info._raw_url # Fallback
         url_info._initialized = True
         logger.warning(f"URLInfo Initial Security Check Error: raw_url='{url_info._raw_url}', error='{url_info.error_message}'")
         return url_info

    # --- Proceed with Resolution, Parsing, Validation, Normalization ---
    resolved_url_str = url_info._raw_url # Initialize resolved_url_str for fallback

    try:
        logger.debug(f"URLInfo Init (Post-Security): raw_url='{url_info._raw_url}', base_url='{url_info.base_url}'")
        # --- Parsing and Resolution --- Resolve WITH fragment first
        try:
            resolved_url_str_with_frag = resolve_url(url_info._raw_url, url_info.base_url, keep_fragment=True)
        except ValueError as e:
            url_info.is_valid = False
            url_info.error_message = f"URL resolution failed: {e}"
            url_info._normalized_url = url_info._raw_url # Fallback for failed resolution
            url_info._initialized = True
            logger.warning(f"URLInfo Resolution Error: raw_url='{url_info._raw_url}', error='{url_info.error_message}'")
            return url_info # Exit initialization early

        # Store fragment before removing it
        url_info._original_fragment = urlparse(resolved_url_str_with_frag).fragment or None
        # Now remove fragment for further processing
        resolved_url_str = resolved_url_str_with_frag.split('#', 1)[0]

        logger.debug(f"URLInfo Resolved: resolved_url='{resolved_url_str}', fragment='{url_info._original_fragment}'")
        # Store if original path (before query/fragment) had a trailing slash
        url_part = url_info._raw_url.split('?', 1)[0].split('#', 1)[0]
        url_info._original_path_had_trailing_slash = url_part.endswith('/')

        # Parse the resolved URL (removes fragment automatically)
        url_info._parsed = urlparse(resolved_url_str)

        # Validate port after initial parsing (moved from validate_url for early exit)
        if url_info._parsed.port is not None and not (0 <= url_info._parsed.port <= 65535):
            url_info.is_valid = False
            url_info.error_message = f"Invalid port: {url_info._parsed.port}"
            url_info._normalized_url = resolved_url_str # Fallback before normalization
            url_info._initialized = True
            logger.debug(f"URLInfo Invalid Port: raw_url='{url_info._raw_url}', error='{url_info.error_message}'")
            return url_info # Exit initialization

        logger.debug(f"URLInfo Parsed Resolved: parsed='{url_info._parsed}', original_trailing_slash={url_info._original_path_had_trailing_slash}")

        # --- Pre-Normalization Validation ---
        # Validate the *resolved* parsed URL first for security issues
        logger.debug(f"URLInfo: About to call pre-normalization validate_url with parsed='{url_info._parsed}' for raw_url='{url_info._raw_url}'")
        _is_valid_pre_norm, _initial_error_message = validate_url(url_info._parsed, raw_url=url_info._raw_url) # Pass raw_url
        logger.debug(f"URLInfo Pre-Normalization Validation Result: is_valid={_is_valid_pre_norm}, error='{_initial_error_message}' for raw_url='{url_info._raw_url}'")

        # Proceed with normalization only if initial validation passed
        if _is_valid_pre_norm:
            # --- Normalization ---
            # Normalize the URL using the dedicated function from normalization module
            # This needs the resolved URL string and the original trailing slash info
            try:
                url_info._normalized_url = normalize_url(resolved_url_str)
                url_info._normalized_parsed = urlparse(url_info._normalized_url)
                logger.debug(f"URLInfo Normalized: normalized_url='{url_info._normalized_url}'")

                # --- Post-Normalization Validation ---
                # Re-validate the *normalized* URL to catch issues introduced by normalization
                logger.debug(f"URLInfo: About to call post-normalization validate_url with normalized_parsed='{url_info._normalized_parsed}' for raw_url='{url_info._raw_url}'")
                post_norm_valid, post_norm_error = validate_url(url_info._normalized_parsed, raw_url=url_info.normalized_url) # Pass normalized_url as raw_url context
                logger.debug(f"URLInfo Post-Normalization Validation Result: is_valid={post_norm_valid}, error='{post_norm_error}' for raw_url='{url_info._raw_url}' (normalized: '{url_info.normalized_url}')")
                if not post_norm_valid:
                    # If normalization created an invalid URL, mark as invalid
                    url_info.is_valid = False
                    url_info.error_message = f"Post-normalization validation failed: {post_norm_error}"
                    url_info._normalized_url = resolved_url_str # Fallback to pre-norm resolved URL
                    logger.warning(f"URLInfo Post-Normalization Invalid: raw_url='{url_info._raw_url}', normalized='{url_info._normalized_parsed}', error='{url_info.error_message}'")
                else:
                    # Set final validation status
                    url_info.is_valid = True
                    url_info.error_message = None
                    
                    # --- Final Checks & Type Determination ---
                    # Determine URL type (internal/external) based on normalized URL and base URL
                    base_is_valid = False
                    base_scheme = None
                    base_reg_domain = None
                    base_raw_url_log = "None"

                    if url_info.base_url:
                        # Create URLInfo for base_url to get its components
                        # This recursive call is safe as it won't go infinitely deep
                        # unless there's a circular base_url dependency, which is unlikely.
                        temp_base_url_info = create_url_info(url_info.base_url)
                        base_raw_url_log = temp_base_url_info.raw_url # For logging
                        if temp_base_url_info and temp_base_url_info.is_valid:
                             base_is_valid = True
                             # Extract components directly from the *parsed* base URL object
                             # Avoid relying on potentially uninitialized properties of temp_base_url_info
                             if temp_base_url_info._normalized_parsed:
                                 base_scheme = temp_base_url_info._normalized_parsed.scheme
                                 # Extract registered domain for the base URL
                                 base_domain_parts = extract_domain_parts(temp_base_url_info._normalized_parsed.hostname)
                                 base_reg_domain = base_domain_parts.get('registered_domain') if base_domain_parts else None
                             else: # Fallback if normalized_parsed isn't available (shouldn't happen if valid)
                                 base_scheme = None
                                 base_reg_domain = None
                                 base_is_valid = False # Mark as invalid if components missing
                                 logger.warning(f"Base URL '{url_info.base_url}' was valid but missing normalized components.")


                    # Extract components for the current URL from its normalized parsed result
                    current_scheme = url_info._normalized_parsed.scheme if url_info._normalized_parsed else None
                    current_netloc = url_info._normalized_parsed.netloc if url_info._normalized_parsed else None
                    current_hostname = url_info._normalized_parsed.hostname if url_info._normalized_parsed else None
                    current_domain_parts = extract_domain_parts(current_hostname)
                    current_reg_domain = current_domain_parts.get('registered_domain') if current_domain_parts else None


                    # Determine URL type using the extracted components
                    url_info.url_type = determine_url_type(
                        current_url_is_valid=url_info.is_valid, # Pass current validity status
                        current_scheme=current_scheme,
                        current_netloc=current_netloc,
                        current_reg_domain=current_reg_domain,
                        base_url_is_valid=base_is_valid,
                        base_scheme=base_scheme,
                        base_reg_domain=base_reg_domain,
                        raw_url=url_info.raw_url, # Pass raw URLs for logging
                        base_raw_url=base_raw_url_log
                    )
                    logger.debug(f"URLInfo Type Determined: url_type='{url_info.url_type}' for {url_info.raw_url} based on {url_info.base_url}")

            except ValueError as norm_err:
                # If normalization itself fails, the URL is invalid
                url_info.is_valid = False
                url_info.error_message = f"URL normalization failed: {norm_err}"
                url_info._normalized_url = resolved_url_str # Fallback
                url_info._normalized_parsed = None
                logger.warning(f"URLInfo Normalization Error: raw_url='{url_info._raw_url}', error='{url_info.error_message}'")
                # No return here, let it fall through to set _initialized
        else:
            # If pre-normalization validation failed, set normalized URL to the resolved string
            url_info.is_valid = False
            url_info.error_message = _initial_error_message
            url_info._normalized_url = resolved_url_str
            url_info._normalized_parsed = url_info._parsed # Use the parsed version that failed validation


    except ValueError as e:
        # Catch ValueErrors specifically (e.g., from port conversion, validation, normalization)
        url_info.is_valid = False
        url_info.error_message = f"ValueError: {str(e)}"
        # Use resolved_url_str if available, else raw_url
        url_info._normalized_url = resolved_url_str if 'resolved_url_str' in locals() else url_info._raw_url
        logger.warning(f"URLInfo ValueError: raw_url='{url_info._raw_url}', error='{url_info.error_message}'")

    except TypeError as e:
        # Catch TypeErrors specifically, often related to internal logic issues
        url_info.is_valid = False
        url_info.error_message = f"Internal TypeError: {e}"
        url_info._normalized_url = url_info._raw_url # Fallback
        logger.error(f"URLInfo Internal TypeError: raw_url='{url_info._raw_url}', error='{url_info.error_message}'", exc_info=True)

    except Exception as e:
        # Catch any other unexpected errors during initialization
        url_info.is_valid = False
        # Ensure error message is a simple string, handle potential complex exceptions
        try:
            # Try to get a concise error representation
            err_repr = repr(e)
        except Exception:
            err_repr = "(error representation failed)"
        url_info.error_message = f"Unexpected error during init: {type(e).__name__}: {err_repr[:100]}" # Limit length
        # Fallback normalized URL
        # Use resolved_url_str if available, else raw_url
        url_info._normalized_url = resolved_url_str if 'resolved_url_str' in locals() else url_info._raw_url
        logger.error(f"URLInfo Unexpected Error: raw_url='{url_info._raw_url}', error='{url_info.error_message}'", exc_info=True) # Log with traceback

    finally:
        # Ensure initialization flag is set regardless of success or failure
        url_info._initialized = True
        logger.debug(f"URLInfo Init Complete: raw_url='{url_info._raw_url}', is_valid={url_info.is_valid}, norm_url='{url_info._normalized_url}', error='{url_info.error_message}'")

    return url_info # Return the populated URLInfo object

# The rest of the initialization logic will be moved here in the next step.
# This includes the try...except blocks for security checks, resolution, parsing, validation, normalization, and type determination.