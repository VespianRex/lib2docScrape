"""
Tests for the URL normalization module.
"""

import pytest
import urllib.parse
from src.utils.url.normalization import (
    normalize_hostname, normalize_path, normalize_url, is_default_port
)

def test_normalize_hostname():
    """Test hostname normalization."""
    # Lowercase conversion
    assert normalize_hostname("EXAMPLE.COM") == "example.com"
    
    # Remove trailing dot
    assert normalize_hostname("example.com.") == "example.com"
    
    # IDN conversion
    assert normalize_hostname("ümlaut.com") == "xn--mlaut-jva.com"
    
    # Mixed case IDN
    assert normalize_hostname("ÜmLaUt.com") == "xn--mlaut-jva.com"
    
    # Handle errors
    with pytest.raises(ValueError):
        normalize_hostname("a"*300)  # Too long

def test_is_default_port():
    """Test default port detection."""
    # Common default ports
    assert is_default_port("http", 80)
    assert is_default_port("https", 443)
    # assert is_default_port("ftp", 21) # Removed as FTP is no longer a default scheme
    
    # Non-default ports
    assert not is_default_port("http", 8080)
    assert not is_default_port("https", 8443)
    # assert not is_default_port("ftp", 2121) # Removed as FTP is no longer a default scheme
    
    # Unknown scheme
    assert not is_default_port("unknown", 80)

def test_normalize_path():
    """Test path normalization."""
    # Keep absolute paths absolute
    assert normalize_path("/path/to/resource") == "/path/to/resource"
    
    # Handle empty paths
    assert normalize_path("") == "/"
    
    # Resolve dot segments
    assert normalize_path("/path/./to/../resource") == "/path/resource"
    
    # Preserve trailing slash if specified
    assert normalize_path("/path/to/directory/", True) == "/path/to/directory/"
    assert normalize_path("/path/to/directory") == "/path/to/directory"
    # Removed assertions passing full URLs to normalize_path
    # assert normalize_path("http://example.com") == "http://example.com/" # Incorrect usage
    # assert normalize_path("http://example.com/") == "http://example.com/" # Incorrect usage
    assert normalize_path("/", True) == "/"

    # Properly encode special characters
    assert normalize_path("/path with spaces") == "/path%20with%20spaces"
    assert normalize_path("/ümlaut") == "/%C3%BCmlaut"
    
    # Handle relative paths
    assert normalize_path("path/to/resource") == "path/to/resource"
    assert normalize_path("./path") == "path"
    assert normalize_path("../path") == "../path"
    assert normalize_path("path/../../resource") == "../resource"

def test_normalize_url():
    """Test URL normalization."""
    # Test with a simple URL
    url_simple = "http://EXAMPLE.com/path"
    normalized_str_simple = normalize_url(url_simple)
    assert normalized_str_simple == "http://example.com/path"
    # Verify components by parsing the normalized string
    parsed_simple = urllib.parse.urlparse(normalized_str_simple)
    assert parsed_simple.scheme == "http"
    assert parsed_simple.netloc == "example.com"
    assert parsed_simple.path == "/path"

    # Test with a complex URL
    url_complex = "HTTPS://User:Pass@EXAMPLE.COM:443/path/./to/../resource?a=1&b=2&a=3"
    normalized_str_complex = normalize_url(url_complex)
    assert normalized_str_complex == "https://example.com/path/resource?a=1&a=3&b=2"
    # Verify components by parsing the normalized string
    parsed_complex = urllib.parse.urlparse(normalized_str_complex)
    assert parsed_complex.scheme == "https"
    assert parsed_complex.netloc == "example.com"  # No user:pass, default port removed
    assert parsed_complex.path == "/path/resource"
    assert parsed_complex.query == "a=1&a=3&b=2"

    # Test with IDN domain
    url_idn = "http://ümlaut.com/path"
    normalized_str_idn = normalize_url(url_idn)
    assert normalized_str_idn == "http://xn--mlaut-jva.com/path"
    # Verify components by parsing the normalized string
    parsed_idn = urllib.parse.urlparse(normalized_str_idn)
    assert parsed_idn.netloc == "xn--mlaut-jva.com"

    # Test with non-default port
    url_port = "http://example.com:8080/path"
    normalized_str_port = normalize_url(url_port)
    assert normalized_str_port == "http://example.com:8080/path"
    # Verify components by parsing the normalized string
    parsed_port = urllib.parse.urlparse(normalized_str_port)
    assert parsed_port.netloc == "example.com:8080"

    # Test with trailing slash (handled internally by normalize_url calling normalize_path)
    url_trailing = "http://example.com/path/"
    normalized_str_trailing = normalize_url(url_trailing) # Removed had_trailing_slash argument
    assert normalized_str_trailing == "http://example.com/path/"
    # Verify components by parsing the normalized string
    parsed_trailing = urllib.parse.urlparse(normalized_str_trailing)
    assert parsed_trailing.path == "/path/"