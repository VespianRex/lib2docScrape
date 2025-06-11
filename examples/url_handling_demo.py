#!/usr/bin/env python
"""
URL Handling Demo Script

This script demonstrates the key features of the enhanced URL handling implementation.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.helpers import URLInfo, URLType  # noqa: E402


def separator(title):
    """Print a section separator with title."""
    print("\n" + "=" * 50)
    print(f" {title} ".center(50, "="))
    print("=" * 50 + "\n")


def main():
    """Demonstrate URL handling features."""
    print("URL Handling Demo")

    # Basic URL Parsing
    separator("Basic URL Parsing")
    url = "https://www.example.co.uk/path/to/page.html?query=value#fragment"
    url_info = URLInfo(url)

    print(f"Original URL: {url}")
    print(f"Normalized:   {url_info.normalized_url}")
    print("\nURL Components:")
    print(f"  Scheme:     {url_info.scheme}")
    print(f"  Netloc:     {url_info.netloc}")
    print(f"  Path:       {url_info.path}")
    print(f"  Query:      {url_info.query}")
    print(f"  Fragment:   {url_info.fragment}")

    # Domain Information
    separator("Domain Information (TLDExtract Features)")
    print(f"Full Domain:        {url_info.domain}")
    print(f"Registered Domain:  {url_info.registered_domain}")
    print(f"Root Domain:        {url_info.root_domain}")
    print(f"Subdomain:          {url_info.subdomain}")
    print(f"Suffix (TLD):       {url_info.suffix}")

    # Relative URL Resolution
    separator("Relative URL Resolution")
    base_url = "https://example.com/docs/index.html"
    relative_urls = [
        "../images/logo.png",
        "/about",
        "contact.html",
        "?version=2",
        "//cdn.example.com/script.js",
    ]

    print(f"Base URL: {base_url}")
    print("\nRelative URLs resolved:")
    for rel_url in relative_urls:
        resolved = URLInfo(rel_url, base_url=base_url)
        print(f"  {rel_url:<25} -> {resolved.normalized_url}")

    # URL Type Classification
    separator("URL Type Classification")
    base_url = "https://example.com/page"
    test_urls = [
        ("https://example.com/about", "Same domain"),
        ("https://blog.example.com", "Subdomain"),
        ("https://example.org", "Different TLD"),
        ("http://example.com", "Different scheme"),
        ("/contact", "Relative path"),
        ("page.html", "Relative file"),
    ]

    print(f"Base URL: {base_url}")
    print("\nURL Type Classification:")
    for test_url, description in test_urls:
        url_info = URLInfo(test_url, base_url=base_url)
        url_type = "Internal" if url_info.url_type == URLType.INTERNAL else "External"
        print(f"  {test_url:<30} -> {url_type:<10} ({description})")

    # IDN (International Domain Names)
    separator("International Domain Names")
    idn_urls = [
        "https://例子.测试",  # Chinese
        "https://παράδειγμα.δοκιμή",  # Greek
        "https://пример.испытание",  # Cyrillic
    ]

    print("IDN URL Handling:")
    for idn_url in idn_urls:
        url_info = URLInfo(idn_url)
        print(f"\nOriginal: {idn_url}")
        print(f"Normalized (Punycode): {url_info.normalized_url}")
        print("Domain components:")
        print(f"  Root domain: {url_info.root_domain}")
        print(f"  Suffix: {url_info.suffix}")

    # Security Validation
    separator("Security Validation")
    security_test_urls = [
        ("https://example.com/page", "Valid URL"),
        ("javascript:alert('XSS')", "JavaScript scheme"),
        ("https://example.com/<script>alert('XSS')</script>", "XSS in path"),
        ("https://example.com/page?id=1' OR '1'='1", "SQL injection"),
        ("https://example.com/../../../etc/passwd", "Path traversal"),
        ("data:text/html,<script>alert('XSS')</script>", "Data URL"),
    ]

    print("Security Validation Results:")
    for test_url, description in security_test_urls:
        url_info = URLInfo(test_url)
        status = "✓ Valid" if url_info.is_valid else "✗ Invalid"
        error = f": {url_info.error_message}" if not url_info.is_valid else ""
        print(f"  {status} - {test_url} ({description}){error}")


if __name__ == "__main__":
    main()
