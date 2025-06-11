"""Tests for the URL validation module."""

from urllib.parse import urlparse

from src.utils.url.validation import (
    detect_path_traversal,
    detect_unc_path,
    validate_netloc,
    validate_path,
    validate_port,
    validate_query,
    validate_scheme,
    validate_security_patterns,
    validate_url,
)


def test_validate_url_valid():
    """Test validate_url with valid URLs."""
    # Test with a valid HTTP URL
    parsed = urlparse("https://example.com/path")
    is_valid, error = validate_url(parsed)
    assert is_valid is True
    assert error is None

    # Test with a valid HTTP URL with query
    parsed = urlparse("https://example.com/path?query=value")
    is_valid, error = validate_url(parsed)
    assert is_valid is True
    assert error is None

    # Test with a valid file URL
    parsed = urlparse("file:///path/to/file.txt")
    is_valid, error = validate_url(parsed)
    assert is_valid is True
    assert error is None


def test_validate_url_invalid():
    """Test validate_url with invalid URLs."""
    # Test with an invalid scheme
    parsed = urlparse("ftp://example.com/")
    is_valid, error = validate_url(parsed)
    assert is_valid is False
    assert "Invalid scheme" in error or "Disallowed scheme" in error

    # Test with a URL containing control characters
    is_valid, error = validate_url(
        urlparse("http://example.com/path"), "http://example.com/path\x01"
    )
    assert is_valid is False
    assert "control characters" in error

    # Test with a URL exceeding maximum length
    long_url = "http://example.com/" + "a" * 2100
    is_valid, error = validate_url(urlparse(long_url), long_url)
    assert is_valid is False
    assert "maximum length" in error


def test_validate_scheme():
    """Test validate_scheme function."""
    # Test with valid schemes
    assert validate_scheme(urlparse("http://example.com"))[0] is True
    assert validate_scheme(urlparse("https://example.com"))[0] is True
    assert validate_scheme(urlparse("file:///path/to/file"))[0] is True

    # Test with invalid schemes
    assert validate_scheme(urlparse("ftp://example.com"))[0] is False
    assert validate_scheme(urlparse("javascript:alert(1)"))[0] is False
    assert validate_scheme(urlparse("data:text/html"))[0] is False

    # Test with empty scheme
    assert validate_scheme(urlparse("//example.com"))[0] is False


def test_validate_netloc():
    """Test validate_netloc function."""
    # Test with valid netloc
    assert validate_netloc(urlparse("https://example.com"))[0] is True
    assert validate_netloc(urlparse("https://sub.example.com"))[0] is True

    # Test with auth info (invalid)
    assert validate_netloc(urlparse("https://user:pass@example.com"))[0] is False

    # Test with missing hostname (invalid for http/https)
    assert validate_netloc(urlparse("https:///path"))[0] is False

    # Test with file scheme (valid without hostname)
    assert validate_netloc(urlparse("file:///path/to/file"))[0] is True

    # Test with IP addresses
    assert validate_netloc(urlparse("https://192.168.1.1"))[0] is False  # Private IP
    assert validate_netloc(urlparse("https://127.0.0.1"))[0] is False  # Loopback IP
    assert validate_netloc(urlparse("https://8.8.8.8"))[0] is True  # Public IP

    # Test with disallowed hosts
    assert validate_netloc(urlparse("https://localhost"))[0] is False
    assert validate_netloc(urlparse("https://127.0.0.1"))[0] is False

    # Test with invalid domain
    assert (
        validate_netloc(urlparse("https://invalid"))[0] is False
    )  # Single-label domain
    assert validate_netloc(urlparse("https://example..com"))[0] is False  # Double dot
    assert (
        validate_netloc(urlparse("https://example.com."))[0] is True
    )  # Trailing dot is valid


def test_validate_port():
    """Test validate_port function."""
    # Test with valid ports
    assert validate_port(urlparse("https://example.com:80"))[0] is True
    assert validate_port(urlparse("https://example.com:443"))[0] is True
    assert validate_port(urlparse("https://example.com:8080"))[0] is True

    # Test with invalid ports
    assert validate_port(urlparse("https://example.com:70000"))[0] is False
    assert validate_port(urlparse("https://example.com:-1"))[0] is False


def test_validate_path():
    """Test validate_path function."""
    # Test with valid paths
    assert validate_path(urlparse("https://example.com/path"))[0] is True
    assert validate_path(urlparse("https://example.com/path/to/resource"))[0] is True

    # Test with path traversal
    assert validate_path(urlparse("https://example.com/../etc/passwd"))[0] is False
    assert (
        validate_path(urlparse("https://example.com/path/../../etc/passwd"))[0] is False
    )

    # Test with UNC path
    assert validate_path(urlparse("file://server/share"))[0] is False


def test_validate_query():
    """Test validate_query function."""
    # Test with valid queries
    assert validate_query(urlparse("https://example.com/?param=value"))[0] is True
    assert (
        validate_query(urlparse("https://example.com/?param1=value1&param2=value2"))[0]
        is True
    )

    # Test with very long query
    long_query = "https://example.com/?" + "param=" + "a" * 2100
    assert validate_query(urlparse(long_query))[0] is False


def test_detect_path_traversal():
    """Test detect_path_traversal function."""
    # Test with path traversal attempts
    assert detect_path_traversal("../etc/passwd") is True
    assert detect_path_traversal("path/../../etc/passwd") is True
    assert detect_path_traversal("path/%2e%2e/etc/passwd") is True
    assert detect_path_traversal("path/..\\etc\\passwd") is True

    # Test with valid paths
    assert detect_path_traversal("/path/to/resource") is False
    assert detect_path_traversal("/path/with/dots/file.txt") is False


def test_detect_unc_path():
    """Test detect_unc_path function."""
    # Test with UNC paths
    assert detect_unc_path(urlparse("file://server/share")) is True
    # HTTP URLs with double slashes in path should be flagged as UNC for security
    assert detect_unc_path(urlparse("http://example.com//path")) is True

    # Test with path starting with double slashes
    parsed = urlparse("http://example.com")
    parsed = parsed._replace(path="//path")
    assert detect_unc_path(parsed) is True


def test_validate_security_patterns():
    """Test validate_security_patterns function."""
    # Test with valid URL
    assert (
        validate_security_patterns(urlparse("https://example.com/path?query=value"))[0]
        is True
    )

    # Test with null byte
    assert (
        validate_security_patterns(urlparse("https://example.com/path%00"))[0] is False
    )

    # Test with XSS pattern
    assert (
        validate_security_patterns(
            urlparse("https://example.com/path?query=<script>alert(1)</script>")
        )[0]
        is False
    )

    # Test with SQLi pattern
    assert (
        validate_security_patterns(
            urlparse("https://example.com/path?query=1' OR '1'='1")
        )[0]
        is False
    )

    # Test with command injection pattern
    assert (
        validate_security_patterns(urlparse("https://example.com/path?query=;ls -la"))[
            0
        ]
        is False
    )
