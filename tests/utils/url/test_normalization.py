"""Tests for the URL normalization module."""

from unittest.mock import patch

import pytest

from src.utils.url.normalization import (
    IDNA_AVAILABLE,
    is_default_port,
    normalize_hostname,
    normalize_path,
    normalize_url,
)


class TestNormalizeHostname:
    """Tests for the normalize_hostname function."""

    def test_normalize_hostname_empty(self):
        """Test normalize_hostname with empty hostname."""
        with pytest.raises(ValueError, match="hostname is empty"):
            normalize_hostname("")

    def test_normalize_hostname_ip_address(self):
        """Test normalize_hostname with IP address."""
        result = normalize_hostname("192.168.1.1")
        assert result == "192.168.1.1"

        # Test with uppercase and trailing dot
        result = normalize_hostname("192.168.1.1.")
        assert result == "192.168.1.1"

    def test_normalize_hostname_simple_domain(self):
        """Test normalize_hostname with simple domain."""
        result = normalize_hostname("example.com")
        assert result == "example.com"

        # Test with uppercase and trailing dot
        result = normalize_hostname("EXAMPLE.COM.")
        assert result == "example.com"

    def test_normalize_hostname_invalid_label(self):
        """Test normalize_hostname with invalid label."""
        with pytest.raises(
            ValueError, match="Hostname label cannot start or end with a hyphen"
        ):
            normalize_hostname("example-.com")

        with pytest.raises(
            ValueError, match="Hostname label cannot start or end with a hyphen"
        ):
            normalize_hostname("-example.com")

    def test_normalize_hostname_empty_label(self):
        """Test normalize_hostname with empty label."""
        with pytest.raises(ValueError, match="Invalid hostname structure"):
            normalize_hostname("example..com")

        with pytest.raises(ValueError, match="Invalid hostname"):
            normalize_hostname(".example.com")

    def test_normalize_hostname_label_too_long(self):
        """Test normalize_hostname with label too long."""
        long_label = "a" * 64
        with pytest.raises(ValueError, match="Hostname label too long"):
            normalize_hostname(f"{long_label}.com")

    @pytest.mark.skipif(not IDNA_AVAILABLE, reason="IDNA not available")
    def test_normalize_hostname_idna(self):
        """Test normalize_hostname with IDNA encoding."""
        # Test with non-ASCII characters
        result = normalize_hostname("例子.com")
        assert result.startswith("xn--")
        assert result.endswith(".com")

    @pytest.mark.skipif(IDNA_AVAILABLE, reason="IDNA is available")
    def test_normalize_hostname_without_idna(self):
        """Test normalize_hostname without IDNA encoding."""
        with patch("src.utils.url.normalization.IDNA_AVAILABLE", False):
            with patch("src.utils.url.normalization.idna", None):
                # Test with ASCII-only domain
                result = normalize_hostname("example.com")
                assert result == "example.com"

                # Test with invalid characters
                with pytest.raises(
                    ValueError, match="Invalid characters in hostname label"
                ):
                    normalize_hostname("example!.com")


class TestIsDefaultPort:
    """Tests for the is_default_port function."""

    def test_is_default_port_http(self):
        """Test is_default_port with HTTP."""
        assert is_default_port("http", 80) is True
        assert is_default_port("http", 8080) is False

    def test_is_default_port_https(self):
        """Test is_default_port with HTTPS."""
        assert is_default_port("https", 443) is True
        assert is_default_port("https", 8443) is False

    def test_is_default_port_unknown_scheme(self):
        """Test is_default_port with unknown scheme."""
        assert is_default_port("ftp", 21) is False
        assert is_default_port("unknown", 80) is False


class TestNormalizePath:
    """Tests for the normalize_path function."""

    def test_normalize_path_empty(self):
        """Test normalize_path with empty path."""
        result = normalize_path("")
        assert result == "/"

    def test_normalize_path_root(self):
        """Test normalize_path with root path."""
        result = normalize_path("/")
        assert result == "/"

    def test_normalize_path_simple(self):
        """Test normalize_path with simple path."""
        result = normalize_path("/path/to/resource")
        assert result == "/path/to/resource"

    def test_normalize_path_dot_segments(self):
        """Test normalize_path with dot segments."""
        result = normalize_path("/path/./to/../resource")
        assert result == "/path/resource"

    def test_normalize_path_multiple_slashes(self):
        """Test normalize_path with multiple slashes."""
        result = normalize_path("/path//to///resource")
        assert result == "/path/to/resource"

    def test_normalize_path_trailing_slash(self):
        """Test normalize_path with trailing slash."""
        result = normalize_path("/path/to/resource/", preserve_trailing_slash=True)
        assert result == "/path/to/resource/"

        result = normalize_path("/path/to/resource/", preserve_trailing_slash=False)
        assert result == "/path/to/resource"

    def test_normalize_path_encoded_chars(self):
        """Test normalize_path with encoded characters."""
        result = normalize_path("/path/with%20space")
        assert result == "/path/with%20space"

    def test_normalize_path_backslashes(self):
        """Test normalize_path with backslashes."""
        result = normalize_path("/path\\to\\resource")
        assert result == "/path/to/resource"

    def test_normalize_path_null_byte(self):
        """Test normalize_path with null byte."""
        with pytest.raises(ValueError, match="Null byte detected"):
            normalize_path("/path/with%00null")

    def test_normalize_path_relative(self):
        """Test normalize_path with relative path."""
        result = normalize_path("path/to/resource")
        assert result == "path/to/resource"

        result = normalize_path("./path/to/resource")
        assert result == "path/to/resource"


class TestNormalizeUrl:
    """Tests for the normalize_url function."""

    def test_normalize_url_empty(self):
        """Test normalize_url with empty URL."""
        result = normalize_url("")
        assert result == ""

    def test_normalize_url_simple(self):
        """Test normalize_url with simple URL."""
        result = normalize_url("http://example.com/path")
        assert result == "http://example.com/path"

    def test_normalize_url_scheme_case(self):
        """Test normalize_url with uppercase scheme."""
        result = normalize_url("HTTP://example.com/path")
        assert result == "http://example.com/path"

    def test_normalize_url_hostname_case(self):
        """Test normalize_url with uppercase hostname."""
        result = normalize_url("http://EXAMPLE.COM/path")
        assert result == "http://example.com/path"

    def test_normalize_url_default_port(self):
        """Test normalize_url with default port."""
        result = normalize_url("http://example.com:80/path")
        assert result == "http://example.com/path"

        result = normalize_url("https://example.com:443/path")
        assert result == "https://example.com/path"

    def test_normalize_url_non_default_port(self):
        """Test normalize_url with non-default port."""
        result = normalize_url("http://example.com:8080/path")
        assert result == "http://example.com:8080/path"

    def test_normalize_url_path_normalization(self):
        """Test normalize_url with path normalization."""
        result = normalize_url("http://example.com/path/./to/../resource")
        assert result == "http://example.com/path/resource"

    def test_normalize_url_query_sorting(self):
        """Test normalize_url with query sorting."""
        result = normalize_url("http://example.com/path?b=2&a=1")
        assert result == "http://example.com/path?a=1&b=2"

    def test_normalize_url_fragment_removal(self):
        """Test normalize_url with fragment removal."""
        result = normalize_url("http://example.com/path#fragment")
        assert result == "http://example.com/path"

    def test_normalize_url_auth_info_removal(self):
        """Test normalize_url with auth info removal."""
        result = normalize_url("http://user:pass@example.com/path")
        assert result == "http://example.com/path"

    def test_normalize_url_empty_path_with_netloc(self):
        """Test normalize_url with empty path and netloc."""
        result = normalize_url("http://example.com")
        assert result == "http://example.com"

    def test_normalize_url_trailing_slash(self):
        """Test normalize_url with trailing slash."""
        result = normalize_url("http://example.com/path/")
        assert result == "http://example.com/path/"
