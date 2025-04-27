"""
src.utils.url.classification
----------------------------
Determine relationship between *url* and *base_url*.

The returned Enum is re‑used across the codebase.
"""

from __future__ import annotations

from typing import Optional
from urllib.parse import urlparse

from .types import URLType  # existing Enum


def _strip_www(host: str | None) -> str:
    if not host:
        return ""
    host = host.lower()
    return host[4:] if host.startswith("www.") else host


def determine_url_type(url: Optional[str], base_url: Optional[str]) -> URLType:
    """
    Very fast heuristic:

    • If either argument is missing   → UNKNOWN
    • Same stripped host              → INTERNAL (regardless of scheme)
    • Different hosts                 → EXTERNAL
    """
    if not url or not base_url:
        return URLType.UNKNOWN

    try:
        u, b = urlparse(url), urlparse(base_url)

        # Pure relative url (no netloc no scheme) → internal
        if not u.netloc and not u.scheme:
            return URLType.INTERNAL

        if _strip_www(u.hostname) == _strip_www(b.hostname):
            return URLType.INTERNAL if (u.scheme == b.scheme or not u.scheme or not b.scheme) else URLType.EXTERNAL
        return URLType.EXTERNAL
    except Exception:  # pragma: no cover (extreme edge cases)
        return URLType.UNKNOWN