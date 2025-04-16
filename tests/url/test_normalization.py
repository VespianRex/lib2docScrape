"""
Tests for the URL normalization module.
"""

import pytest
from urllib.parse import urlparse
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
    assert is_default_port("ftp", 21)
    
    # Non-default ports
    assert not is_default_port("http", 8080)
    assert not is_default_port("https", 8443)
    assert not is_default_port("ftp", 2121)
    
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
    assert normalize_path("/path/to/directory", True) == "/path/to/directory/"
    
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
    parsed = urlparse("http://EXAMPLE.com/path")
    normalized_parsed, normalized_str = normalize_url(parsed)
    assert normalized_str == "http://example.com/path"
    assert normalized_parsed.scheme == "http"
    assert normalized_parsed.netloc == "example.com"
    assert normalized_parsed.path == "/path"
    
    # Test with a complex URL
    parsed = urlparse("HTTPS://User:Pass@EXAMPLE.COM:443/path/./to/../resource?a=1&b=2&a=3")
    normalized_parsed, normalized_str = normalize_url(parsed)
    assert normalized_str == "https://example.com/path/resource?a=1&b=2&a=3"
    assert normalized_parsed.scheme == "https"
    assert normalized_parsed.netloc == "example.com"  # No user:pass, default port removed
    assert normalized_parsed.path == "/path/resource"
    assert normalized_parsed.query == "a=1&b=2&a=3"
    
    # Test with IDN domain
    parsed = urlparse("http://ümlaut.com/path")
    normalized_parsed, normalized_str = normalize_url(parsed)
    assert "xn--mlaut-jva.com" in normalized_str
    assert normalized_parsed.netloc == "xn--mlaut-jva.com"
    
    # Test with non-default port
    parsed = urlparse("http://example.com:8080/path")
    normalized_parsed, normalized_str = normalize_url(parsed)
    assert normalized_str == "http://example.com:8080/path"
    assert normalized_parsed.netloc == "example.com:8080"
    
    # Test with trailing slash
    parsed = urlparse("http://example.com/path/")
    normalized_parsed, normalized_str = normalize_url(parsed, True)
    assert normalized_str == "http://example.com/path/"
    assert normalized_parsed.path == "/path/"