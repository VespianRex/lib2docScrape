"""
src.utils.url.parsing
---------------------
Resolve a (possibly relative) URL string against an optional base URL.

It is intentionally minimal – higher‑level modules add validation.
"""

from __future__ import annotations

from urllib.parse import urljoin, urlparse

__all__ = ["resolve_url"]

# Schemes that are *never* allowed to proceed – avoid XSS / file injection etc.
_BLOCKED_SCHEMES = {"javascript", "data", "vbscript"}


def _looks_like_domain_no_scheme(raw: str) -> bool:
    """
    Quick heuristic: contains a dot, no spaces and no scheme delimiter.
    Example: 'www.example.com'
    """
    return "." in raw and "://" not in raw and not raw.startswith("//")


def resolve_url(url: str, base_url: str | None = None) -> str | None:
    """
    Resolve *url* against *base_url*.

    Returns
    -------
    str   – Fully‑qualified URL on success
    None  – If resolution fails or `url` contains a blocked scheme
    """
    if not url or not isinstance(url, str):
        return None
    candidate = url.strip()

    # ------------------------------------------------------------------ #
    #  Hard‑block dangerous schemes
    # ------------------------------------------------------------------ #
    if ":" in candidate.split("/", 1)[0]:
        scheme_part = candidate.split(":", 1)[0].lower()
        if scheme_part in _BLOCKED_SCHEMES:
            return None

    # ------------------------------------------------------------------ #
    #  Protocol‑relative (“//example.com”) – prepend scheme
    # ------------------------------------------------------------------ #
    if candidate.startswith("//"):
        scheme = urlparse(base_url).scheme if base_url else "http"
        candidate = f"{scheme}:{candidate}"

    # ------------------------------------------------------------------ #
    #  If base_url present → let stdlib handle join & path normalization
    # ------------------------------------------------------------------ #
    if base_url:
        try:
            # Ensure base has a scheme (urljoin needs one)
            if not urlparse(base_url).scheme:
                base_url = "http://" + base_url
            return urljoin(base_url, candidate)
        except ValueError:
            return None

    # ------------------------------------------------------------------ #
    #  No base_url – maybe the string is a bare domain lacking a scheme
    # ------------------------------------------------------------------ #
    parsed = urlparse(candidate)
    if not parsed.scheme and parsed.netloc:
        return "http://" + candidate
    if _looks_like_domain_no_scheme(candidate):
        return "http://" + candidate

    return candidate
