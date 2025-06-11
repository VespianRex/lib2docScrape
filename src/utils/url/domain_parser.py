import ipaddress
import logging
from types import MappingProxyType
from typing import Optional

# Try to import tldextract for better domain parsing
try:
    import tldextract

    TLDEXTRACT_AVAILABLE = True
except ImportError:
    TLDEXTRACT_AVAILABLE = False
    tldextract = None  # Define tldextract as None if not available

logger = logging.getLogger(__name__)


def extract_domain_parts(
    hostname: Optional[str],
) -> MappingProxyType[str, Optional[str]]:
    """
    Extracts domain parts (subdomain, domain, suffix, registered_domain)
    using tldextract if available, otherwise basic splitting.

    Args:
        hostname: The hostname string to parse.

    Returns:
        An immutable mapping containing the domain parts.
        Values can be None if extraction fails or not applicable (e.g., suffix for IP).
    """
    h = hostname
    if not h:
        logger.debug("extract_domain_parts: No hostname available.")
        return MappingProxyType(
            {
                "subdomain": None,
                "domain": None,
                "suffix": None,
                "registered_domain": None,
            }
        )

    sub: Optional[str] = None
    dom: Optional[str] = None
    suf: Optional[str] = None
    reg_dom: Optional[str] = None

    try:
        # Handle IPs and localhost explicitly first
        is_ip = False
        try:
            ipaddress.ip_address(h)
            is_ip = True
            dom = h  # For IPs, domain is the IP itself
            reg_dom = h
            logger.debug(f"extract_domain_parts: Hostname '{h}' is an IP address.")
        except ValueError:
            pass  # Not an IP

        if not is_ip:
            if h == "localhost":
                dom = "localhost"
                reg_dom = "localhost"
                logger.debug("extract_domain_parts: Hostname is 'localhost'.")
            elif TLDEXTRACT_AVAILABLE and tldextract:
                try:
                    # Use tldextract on the hostname
                    # Use include_psl_private_domains=True for better handling of things like blogspot.com
                    extracted = tldextract.extract(h, include_psl_private_domains=True)
                    # Assign parts, using None if empty string from tldextract for consistency
                    sub = extracted.subdomain or None  # Assign None if empty
                    dom = extracted.domain or None
                    suf = extracted.suffix or None
                    # Use tldextract's registered_domain directly if available,
                    # but for single-label domains, use the domain itself
                    reg_dom = extracted.registered_domain or None
                    if not reg_dom and dom and not suf:
                        # Single-label domain case: registered_domain should be the domain itself
                        reg_dom = dom
                    logger.debug(
                        f"extract_domain_parts: tldextract result for '{h}': {extracted}"
                    )
                except Exception as e:
                    logger.warning(
                        f"extract_domain_parts: tldextract failed for hostname '{h}': {e}. Falling back to basic split."
                    )
                    # Fallback to basic split on tldextract error
                    parts = h.split(".")
                    if len(parts) >= 3:
                        sub = ".".join(parts[:-2])
                        dom = parts[-2]
                        suf = parts[-1]
                        reg_dom = f"{dom}.{suf}"
                    elif len(parts) == 2:
                        sub = None  # Assign None for empty subdomain
                        dom = parts[0]
                        suf = parts[1]
                        reg_dom = f"{dom}.{suf}"
                    elif len(parts) == 1:
                        sub = None  # Assign None for empty subdomain
                        dom = parts[0]
                        suf = None
                        reg_dom = dom  # Single label domain
            else:
                # Basic fallback split if tldextract not available
                logger.debug(
                    f"extract_domain_parts: tldextract not available. Using basic split for '{h}'."
                )
                parts = h.split(".")
                if len(parts) >= 3:
                    sub = ".".join(parts[:-2])
                    dom = parts[-2]
                    suf = parts[-1]
                    reg_dom = f"{dom}.{suf}"
                elif len(parts) == 2:
                    sub = None  # Assign None for empty subdomain
                    dom = parts[0]
                    suf = parts[1]
                    reg_dom = f"{dom}.{suf}"
                elif len(parts) == 1:
                    sub = None  # Assign None for empty subdomain
                    dom = parts[0]
                    suf = None
                    reg_dom = dom

    except Exception as e:
        # Catch any unexpected error during domain parsing
        logger.error(
            f"extract_domain_parts: Unexpected error parsing hostname '{h}': {e}",
            exc_info=True,
        )
        # Return None for all parts on unexpected error
        sub, dom, suf, reg_dom = None, None, None, None

    result = {
        "subdomain": sub,
        "domain": dom,
        "suffix": suf,
        "registered_domain": reg_dom,
    }
    logger.debug(f"extract_domain_parts: Final result for '{h}': {result}")
    return MappingProxyType(result)
