import logging
from typing import TYPE_CHECKING, Optional

from .types import URLType

# Use TYPE_CHECKING for forward references to avoid circular imports
if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def determine_url_type(
    current_url_is_valid: bool,
    current_scheme: Optional[str],
    current_netloc: Optional[str],  # Needed to check if URL looks relative
    current_reg_domain: Optional[str],
    base_url_is_valid: bool,
    base_scheme: Optional[str],
    base_reg_domain: Optional[str],
    raw_url: str = "N/A",  # For logging
    base_raw_url: str = "N/A",  # For logging
) -> URLType:
    """
    Determines if a URL is internal, external, or unknown relative to a base URL,
    using pre-computed components.

    Args:
        current_url_is_valid: Whether the current URL passed validation.
        current_scheme: Scheme of the current URL (e.g., 'https'). Can be None for relative URLs.
        current_netloc: Netloc of the current URL (e.g., 'www.example.com'). Can be None for relative URLs.
        current_reg_domain: Registered domain of the current URL (e.g., 'example.com'). Can be None.
        base_url_is_valid: Whether the base URL passed validation.
        base_scheme: Scheme of the base URL.
        base_reg_domain: Registered domain of the base URL.
        raw_url: The original raw URL string (for logging).
        base_raw_url: The original base URL string (for logging).


    Returns:
        URLType: The determined type of the URL.
    """
    logger.debug(
        f"Determining type for '{raw_url}' against base '{base_raw_url}' (current_is_valid={current_url_is_valid})"
    )

    if not current_url_is_valid:
        logger.debug("Returning UNKNOWN (current URL is invalid)")
        return URLType.UNKNOWN

    if not base_url_is_valid:
        # If there's no valid base URL, any valid absolute URL is external.
        # Relative URLs without a base are effectively invalid/unknown in this context.
        if not current_scheme and not current_netloc:
            logger.debug("Returning UNKNOWN (relative URL with no valid base)")
            return URLType.UNKNOWN
        else:
            logger.debug("Returning EXTERNAL (no valid base URL provided)")
            return URLType.EXTERNAL

    # --- Both current and base URLs are valid ---

    logger.debug(
        f"Comparing: current_scheme='{current_scheme}', base_scheme='{base_scheme}', current_reg_domain='{current_reg_domain}', base_reg_domain='{base_reg_domain}'"
    )

    # Handle relative URLs: If scheme and netloc are missing, it's internal by definition (resolved against base)
    if not current_scheme and not current_netloc:
        logger.debug(
            "CONDITION MET: Relative URL (no scheme/netloc). Returning INTERNAL."
        )
        return URLType.INTERNAL

    # Handle file schemes: if both are file schemes, they are internal to the "filesystem host"
    # This check should come after the relative URL check and scheme mismatch check,
    # but before the registered_domain check.
    if current_scheme == "file" and base_scheme == "file":
        logger.debug(
            "CONDITION MET: Both current and base are file schemes. Returning INTERNAL."
        )
        return URLType.INTERNAL

    # Check if both registered domains could be determined for absolute URLs
    # (This is mainly for http/https schemes now, as file schemes are handled above)
    if not current_reg_domain or not base_reg_domain:
        logger.debug(
            "Returning EXTERNAL (missing registered domain info for current or base URL, and not a file-to-file comparison)"
        )
        # Treat as external if domain info is missing for comparison
        return URLType.EXTERNAL

    # Allow http -> https upgrade as internal
    schemes_match = (current_scheme == base_scheme) or (
        base_scheme == "http" and current_scheme == "https"
    )

    # Internal if schemes match (or upgrade) and registered domains match
    # Allow different subdomains of the same registered domain to be considered internal.
    domains_match = (
        current_reg_domain is not None and current_reg_domain == base_reg_domain
    )

    if schemes_match and domains_match:
        logger.debug(
            "CONDITION MET: Schemes match: True, Registered Domains match: True. Returning INTERNAL."
        )
        return URLType.INTERNAL
    else:
        # Log specific reason for EXTERNAL classification
        reason = []
        if not schemes_match:
            reason.append(f"Schemes mismatch ('{current_scheme}' vs '{base_scheme}')")
        if not domains_match:
            reason.append(
                f"Domains mismatch ('{current_reg_domain}' vs '{base_reg_domain}')"
            )
        logger.debug(
            f"CONDITION NOT MET: Schemes match: {schemes_match}, Domains match: {domains_match}. Returning EXTERNAL. Reason: {'; '.join(reason)}"
        )
        return URLType.EXTERNAL
