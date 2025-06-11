#!/usr/bin/env python3
"""
Script to test the behavior of URLInfo class.
"""

from src.utils.url_info_tldextract import URLInfo


def test_url(url_str, base_url=None):
    """Test a URL and print its properties."""
    url = URLInfo(url_str, base_url=base_url)
    print(f"URL: {url_str}")
    if base_url:
        print(f"Base URL: {base_url}")
    print(f"Is valid: {url.is_valid}")
    print(f"Error: {url.error_message}")
    print(f"Normalized: {url.normalized_url}")
    print(f"Path: {url.path}")
    print("-" * 50)


# Test path traversal
test_url("http://example.com/path/../../../etc/passwd")

# Test trailing slashes
test_url("http://example.com/a/b/")
test_url("http://example.com/a/b")

# Test special characters
test_url("http://example.com/path/with/special/chars/!@#")

# Test invalid netloc
test_url("-example.com")

# Test localhost
test_url("localhost:8080")

# Test URL resolution with base URL
test_url("page.html", base_url="http://example.com/docs")
