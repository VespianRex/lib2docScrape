from typing import Optional
from urllib.parse import urljoin, urlparse


def resolve_url(url: str, base: Optional[str], keep_fragment: bool = False) -> str:
    """
    Resolves a URL against a base URL, handling potential errors.

    Args:
        url: The URL string to resolve.
        base: The base URL string, or None.
        keep_fragment: Whether to keep the fragment identifier.

    Returns:
        The resolved URL string.

    Raises:
        ValueError: If URL resolution fails.
    """
    try:
        # Use urljoin for robust relative URL resolution
        resolved_url = urljoin(base or "", url)
    except ValueError as e:
        # Catch errors during urljoin (e.g., malformed base or relative part)
        raise ValueError(f"URL resolution failed: {e}") from e

    # Remove fragment identifier (#...) only if keep_fragment is False
    if not keep_fragment:
        resolved_url = resolved_url.split("#", 1)[0]

    # Userinfo (user:pass@) is handled during validation, not removed here.

    # Return the resolved URL string.
    return resolved_url


if __name__ == "__main__":
    # Example Usage
    base = "https://example.com/docs/current/"
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
        "http://xn--mnchen-3ya.de/",  # IDN
        "http://localhost:8080/test",
        "file:///etc/passwd",
        "http://[::1]/",  # IPv6 Loopback
        "",
        None,
        "invalid url string",
    ]

    for url_str in urls_to_test:
        print(
            f"--- Testing URL: {url_str} (Base: {base if url_str and not urlparse(str(url_str)).scheme else 'None'}) ---"
        )
        try:
            resolved = resolve_url(
                url_str, base if url_str and not urlparse(str(url_str)).scheme else None
            )
            print(f"  Resolved: {resolved}")
            resolved_with_frag = resolve_url(
                url_str,
                base if url_str and not urlparse(str(url_str)).scheme else None,
                keep_fragment=True,
            )
            print(f"  Resolved (with fragment): {resolved_with_frag}")
        except ValueError as e:
            print(f"  Resolution failed: {e}")
        except Exception as e:
            print(f"  *** UNEXPECTED ERROR during resolution: {e} ***")
        print("-" * 20)
