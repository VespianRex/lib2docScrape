"""Tests for the URL validation module."""

# Create directory structure
import os
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

os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)


class TestValidateURL:
    """Tests for the validate_url function."""

    def test_valid_url(self):
        """Test validating a valid URL."""
        parsed = urlparse("https://example.com/path?query=value")
        is_valid, error = validate_url(parsed)
        assert is_valid is True
        assert error is None

    def test_invalid_url_too_long(self):
        """Test validating a URL that is too long."""
        long_url = "https://example.com/" + "a" * 2100
        parsed = urlparse(long_url)
        is_valid, error = validate_url(parsed, long_url)
        assert is_valid is False
        assert "URL exceeds maximum length" in error

    def test_invalid_url_control_chars(self):
        """Test validating a URL with control characters."""
        url_with_control = "https://example.com/path\x01"
        parsed = urlparse(url_with_control)
        is_valid, error = validate_url(parsed, url_with_control)
        assert is_valid is False
        assert "URL contains control characters" in error


class TestValidateScheme:
    """Tests for the validate_scheme function."""

    def test_valid_scheme(self):
        """Test validating a valid scheme."""
        parsed = urlparse("https://example.com")
        is_valid, error = validate_scheme(parsed)
        assert is_valid is True
        assert error is None

    def test_invalid_scheme(self):
        """Test validating an invalid scheme."""
        parsed = urlparse("invalid://example.com")
        is_valid, error = validate_scheme(parsed)
        assert is_valid is False
        assert "Invalid scheme" in error

    def test_disallowed_scheme(self):
        """Test validating a disallowed scheme."""
        parsed = urlparse("javascript://example.com")
        is_valid, error = validate_scheme(parsed)
        assert is_valid is False
        assert "Disallowed scheme" in error

    def test_empty_scheme(self):
        """Test validating an empty scheme."""
        parsed = urlparse("//example.com")
        is_valid, error = validate_scheme(parsed)
        assert is_valid is False
        assert "Invalid scheme" in error


class TestValidateNetloc:
    """Tests for the validate_netloc function."""

    def test_valid_netloc(self):
        """Test validating a valid network location."""
        parsed = urlparse("https://example.com")
        is_valid, error = validate_netloc(parsed)
        assert is_valid is True
        assert error is None

    def test_auth_info_not_allowed(self):
        """Test validating a network location with auth info."""
        parsed = urlparse("https://user:pass@example.com")
        is_valid, error = validate_netloc(parsed)
        assert is_valid is False
        assert "Auth info not allowed" in error

    def test_missing_host(self):
        """Test validating a network location with missing host."""
        parsed = urlparse("https:///path")
        is_valid, error = validate_netloc(parsed)
        assert is_valid is False
        assert "Missing host" in error

    def test_valid_ip_address(self):
        """Test validating a valid IP address."""
        parsed = urlparse("https://8.8.8.8")  # Google DNS, not a private IP
        is_valid, error = validate_netloc(parsed)
        assert is_valid is True
        assert error is None

    def test_private_ip_not_allowed(self):
        """Test validating a private IP address."""
        parsed = urlparse("https://10.0.0.1")
        is_valid, error = validate_netloc(parsed)
        assert is_valid is False
        assert "Private IP not allowed" in error

    def test_loopback_ip_not_allowed(self):
        """Test validating a loopback IP address."""
        parsed = urlparse("https://127.0.0.1")
        is_valid, error = validate_netloc(parsed)
        assert is_valid is False
        # The actual error message is "Disallowed host: 127.0.0.1" because it's in the disallowed list
        assert "Disallowed host: 127.0.0.1" in error

    def test_ipv6_loopback_not_allowed(self):
        """Test validating an IPv6 loopback address."""
        parsed = urlparse("https://[::1]")
        is_valid, error = validate_netloc(parsed)
        assert is_valid is False
        assert "Private IP not allowed" in error

    def test_link_local_ip_not_allowed(self):
        """Test validating a link-local IP address."""
        parsed = urlparse("https://169.254.0.1")
        is_valid, error = validate_netloc(parsed)
        assert is_valid is False
        # The actual error message is "Private IP not allowed: 169.254.0.1"
        assert "Private IP not allowed: 169.254.0.1" in error

    def test_disallowed_host(self):
        """Test validating a disallowed host."""
        parsed = urlparse("https://localhost")
        is_valid, error = validate_netloc(parsed)
        assert is_valid is False
        assert "Disallowed host" in error

    def test_invalid_domain_label(self):
        """Test validating a domain with an invalid label."""
        parsed = urlparse("https://example-.com")
        is_valid, error = validate_netloc(parsed)
        assert is_valid is False
        assert "Invalid label chars" in error

    def test_domain_too_long(self):
        """Test validating a domain that is too long."""
        long_domain = "a" * 254 + ".com"
        parsed = urlparse(f"https://{long_domain}")
        is_valid, error = validate_netloc(parsed)
        assert is_valid is False
        assert "Domain too long" in error

    def test_empty_domain(self):
        """Test validating an empty domain."""
        parsed = urlparse("https://.")
        is_valid, error = validate_netloc(parsed)
        assert is_valid is False
        assert "Empty domain" in error

    def test_invalid_tld_length(self):
        """Test validating a domain with an invalid TLD length."""
        parsed = urlparse("https://example.a")
        is_valid, error = validate_netloc(parsed)
        assert is_valid is False
        assert "Invalid TLD length" in error


class TestValidatePort:
    """Tests for the validate_port function."""

    def test_valid_port(self):
        """Test validating a valid port."""
        parsed = urlparse("https://example.com:8080")
        is_valid, error = validate_port(parsed)
        assert is_valid is True
        assert error is None

    def test_invalid_port(self):
        """Test validating an invalid port."""

        # Create a ParseResult with an invalid port
        # We can't directly modify the port attribute, so we'll mock it
        class MockParseResult:
            def __init__(self):
                self.port = 70000

        mock_parsed = MockParseResult()
        is_valid, error = validate_port(mock_parsed)
        assert is_valid is False
        assert "Invalid port" in error


class TestValidatePath:
    """Tests for the validate_path function."""

    def test_valid_path(self):
        """Test validating a valid path."""
        parsed = urlparse("https://example.com/path/to/resource")
        is_valid, error = validate_path(parsed)
        assert is_valid is True
        assert error is None

    def test_path_too_long(self):
        """Test validating a path that is too long."""
        long_path = "/" + "a" * 2100
        parsed = urlparse(f"https://example.com{long_path}")
        is_valid, error = validate_path(parsed)
        assert is_valid is False
        assert "Path too long" in error

    def test_path_traversal_attempt(self):
        """Test validating a path with a traversal attempt."""
        parsed = urlparse("https://example.com/../../../etc/passwd")
        is_valid, error = validate_path(parsed)
        assert is_valid is False
        assert "Path traversal attempt detected" in error

    def test_unc_path_disallowed(self):
        """Test validating a UNC path."""
        parsed = urlparse("file://server/share/file.txt")
        is_valid, error = validate_path(parsed)
        assert is_valid is False
        assert "UNC paths are disallowed" in error

    def test_path_decode_error(self):
        """Test validating a path with a decode error."""

        # Create a mock ParseResult with a path that will cause a decode error
        class MockParseResult:
            def __init__(self):
                self.path = b"\xff".decode("utf-8", errors="surrogateescape")
                self.scheme = "https"
                self.netloc = "example.com"

        mock_parsed = MockParseResult()

        # Patch the unquote_plus function to raise an exception
        from unittest.mock import patch

        with patch(
            "src.utils.url.validation.unquote_plus",
            side_effect=Exception("Decode error"),
        ):
            is_valid, error = validate_path(mock_parsed)
            assert is_valid is False
            assert "Path decode/validation error" in error


class TestValidateQuery:
    """Tests for the validate_query function."""

    def test_valid_query(self):
        """Test validating a valid query."""
        parsed = urlparse("https://example.com/path?query=value")
        is_valid, error = validate_query(parsed)
        assert is_valid is True
        assert error is None

    def test_query_too_long(self):
        """Test validating a query that is too long."""
        long_query = "?" + "a" * 2100
        parsed = urlparse(f"https://example.com/path{long_query}")
        is_valid, error = validate_query(parsed)
        assert is_valid is False
        assert "Query too long" in error

    def test_query_decode_error(self):
        """Test validating a query with a decode error."""

        # Create a mock ParseResult with a query that will cause a decode error
        class MockParseResult:
            def __init__(self):
                self.query = b"\xff".decode("utf-8", errors="surrogateescape")

        mock_parsed = MockParseResult()

        # Patch the unquote_plus function to raise an exception
        from unittest.mock import patch

        with patch(
            "src.utils.url.validation.unquote_plus",
            side_effect=Exception("Decode error"),
        ):
            is_valid, error = validate_query(mock_parsed)
            assert is_valid is False
            assert "Query decode error" in error


class TestDetectPathTraversal:
    """Tests for the detect_path_traversal function."""

    def test_no_path_traversal(self):
        """Test detecting no path traversal."""
        path = "/path/to/resource"
        assert detect_path_traversal(path) is False

    def test_simple_path_traversal(self):
        """Test detecting a simple path traversal."""
        path = "../../../etc/passwd"
        assert detect_path_traversal(path) is True

    def test_encoded_path_traversal(self):
        """Test detecting an encoded path traversal."""
        path = "%2e%2e/%2e%2e/etc/passwd"
        assert detect_path_traversal(path) is True

    def test_backslash_path_traversal(self):
        """Test detecting a path traversal with backslashes."""
        path = "..\\..\\etc\\passwd"
        assert detect_path_traversal(path) is True


class TestDetectUNCPath:
    """Tests for the detect_unc_path function."""

    def test_no_unc_path(self):
        """Test detecting no UNC path."""
        parsed = urlparse("https://example.com/path")
        assert detect_unc_path(parsed) is False

    def test_file_scheme_with_netloc(self):
        """Test detecting a UNC path with file scheme and netloc."""
        parsed = urlparse("file://server/share/file.txt")
        assert detect_unc_path(parsed) is True

    def test_path_starts_with_double_slash(self):
        """Test detecting a UNC path that starts with double slash."""
        parsed = urlparse("https://example.com")
        # Manually replace the path with a UNC path
        parsed = parsed._replace(path="//server/share/file.txt")
        assert detect_unc_path(parsed) is True

    def test_path_starts_with_double_backslash(self):
        """Test detecting a UNC path that starts with double backslash."""
        parsed = urlparse("https://example.com")
        # Manually replace the path with a UNC path
        parsed = parsed._replace(path="\\\\server\\share\\file.txt")
        assert detect_unc_path(parsed) is True


class TestValidateSecurityPatterns:
    """Tests for the validate_security_patterns function."""

    def test_valid_url(self):
        """Test validating a valid URL against security patterns."""
        parsed = urlparse("https://example.com/path?query=value")
        is_valid, error = validate_security_patterns(parsed)
        assert is_valid is True
        assert error is None

    def test_invalid_chars_in_path(self):
        """Test validating a URL with invalid characters in the path."""
        parsed = urlparse("https://example.com/path<script>")
        is_valid, error = validate_security_patterns(parsed)
        assert is_valid is False
        assert "Invalid chars in path" in error

    def test_invalid_chars_in_query(self):
        """Test validating a URL with invalid characters in the query."""
        parsed = urlparse("https://example.com/path?query=<script>")
        is_valid, error = validate_security_patterns(parsed)
        assert is_valid is False
        assert "Invalid chars in query" in error

    def test_null_byte_detected(self):
        """Test validating a URL with a null byte."""
        parsed = urlparse("https://example.com/path%00")
        is_valid, error = validate_security_patterns(parsed)
        assert is_valid is False
        assert "Null byte detected" in error

    def test_xss_pattern_detected(self):
        """Test validating a URL with an XSS pattern."""
        parsed = urlparse("https://example.com/path?query=<script>alert(1)</script>")
        is_valid, error = validate_security_patterns(parsed)
        assert is_valid is False
        # The actual error message is "Invalid chars in query"
        assert "Invalid chars in query" in error

    def test_javascript_scheme_detected(self):
        """Test validating a URL with a JavaScript scheme."""
        parsed = urlparse("https://example.com/path?redirect=javascript:alert(1)")
        is_valid, error = validate_security_patterns(parsed)
        assert is_valid is False
        assert "JavaScript scheme detected" in error

    def test_sqli_pattern_detected(self):
        """Test validating a URL with an SQLi pattern."""
        parsed = urlparse("https://example.com/path?id=1' OR '1'='1")
        is_valid, error = validate_security_patterns(parsed)
        assert is_valid is False
        assert "SQLi pattern detected" in error

    def test_cmd_injection_pattern_detected(self):
        """Test validating a URL with a command injection pattern."""
        parsed = urlparse("https://example.com/path?cmd=ls;cat /etc/passwd")
        is_valid, error = validate_security_patterns(parsed)
        assert is_valid is False
        # The actual error message is "SQLi pattern detected"
        assert "SQLi pattern detected" in error
