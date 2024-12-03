import pytest
from urllib.parse import urlparse, urlunparse
from src.utils.helpers import URLInfo

def test_urlunparse_behavior():
    """Test the basic behavior of urlunparse to understand its output type."""
    components = ('https', 'example.com', '/path', '', 'query=1', '')
    result = urlunparse(components)
    assert isinstance(result, str), f"urlunparse should return str, got {type(result)}"
    assert result == "https://example.com/path?query=1"

def test_url_info_creation_basic():
    """Test basic URL creation with different formats."""
    test_cases = [
        (
            "https://example.com",
            {
                "original": "https://example.com",
                "normalized": "https://example.com/",
                "scheme": "https",
                "netloc": "example.com",
                "path": "/",
                "is_valid": True
            }
        ),
        (
            "http://example.com:80",
            {
                "original": "http://example.com:80",
                "normalized": "http://example.com/",
                "scheme": "http",
                "netloc": "example.com",
                "path": "/",
                "is_valid": True
            }
        ),
        (
            "https://example.com:443",
            {
                "original": "https://example.com:443",
                "normalized": "https://example.com/",
                "scheme": "https",
                "netloc": "example.com",
                "path": "/",
                "is_valid": True
            }
        )
    ]
    
    for input_url, expected in test_cases:
        url_info = URLInfo.from_string(input_url)
        assert isinstance(url_info.normalized, str), f"normalized should be str, got {type(url_info.normalized)}"
        assert url_info.original == expected["original"]
        assert url_info.normalized == expected["normalized"]
        assert url_info.scheme == expected["scheme"]
        assert url_info.netloc == expected["netloc"]
        assert url_info.path == expected["path"]
        assert url_info.is_valid == expected["is_valid"]

def test_url_info_path_normalization():
    """Test path normalization with different path formats."""
    test_cases = [
        (
            "https://example.com/path/./to/../page",
            "https://example.com/path/page"
        ),
        (
            "https://example.com/path//double/slash",
            "https://example.com/path/double/slash"
        ),
        (
            "https://example.com/path/",
            "https://example.com/path/"  # Preserves trailing slash
        ),
        (
            "https://example.com/path///",
            "https://example.com/path/"  # Multiple trailing slashes normalized
        )
    ]
    
    for input_url, expected in test_cases:
        url_info = URLInfo.from_string(input_url)
        assert isinstance(url_info.normalized, str), f"normalized should be str, got {type(url_info.normalized)}"
        assert url_info.normalized == expected

def test_url_info_scheme_handling():
    """Test scheme handling with different inputs."""
    test_cases = [
        (
            "example.com",
            "http://example.com/"  # Default to http
        ),
        (
            "https://example.com",
            "https://example.com/"
        ),
        (
            "HTTP://example.com",
            "http://example.com/"  # Lowercase scheme
        ),
        (
            "//example.com",
            "http://example.com/"  # Protocol-relative URL
        )
    ]
    
    for input_url, expected in test_cases:
        url_info = URLInfo.from_string(input_url)
        assert isinstance(url_info.normalized, str), f"normalized should be str, got {type(url_info.normalized)}"
        assert url_info.normalized == expected

def test_url_info_query_handling():
    """Test query parameter handling."""
    test_cases = [
        (
            "https://example.com?query=1&param=2",
            "https://example.com/?query=1&param=2"
        ),
        (
            "https://example.com/?a=1&b=2&a=3",
            "https://example.com/?a=1&b=2&a=3"  # Preserve duplicate params
        ),
        (
            "https://example.com/path?",
            "https://example.com/path"  # Remove empty query
        )
    ]
    
    for input_url, expected in test_cases:
        url_info = URLInfo.from_string(input_url)
        assert isinstance(url_info.normalized, str), f"normalized should be str, got {type(url_info.normalized)}"
        assert url_info.normalized == expected

def test_url_info_fragment_handling():
    """Test fragment handling (should be removed)."""
    test_cases = [
        (
            "https://example.com/path#fragment",
            "https://example.com/path"
        ),
        (
            "https://example.com/path#fragment?query=1",
            "https://example.com/path"
        ),
        (
            "https://example.com/path#",
            "https://example.com/path"
        )
    ]
    
    for input_url, expected in test_cases:
        url_info = URLInfo.from_string(input_url)
        assert isinstance(url_info.normalized, str), f"normalized should be str, got {type(url_info.normalized)}"
        assert url_info.normalized == expected

def test_url_info_invalid_urls():
    """Test handling of invalid URLs."""
    test_cases = [
        "",  # Empty string
        None,  # None
        "not a url",  # Invalid format
        "http://",  # Missing netloc
        "http:///path",  # Missing netloc with path
        "///path",  # Missing scheme and netloc
    ]
    
    for input_url in test_cases:
        url_info = URLInfo.from_string(input_url)
        assert isinstance(url_info.normalized, str), f"normalized should be str, got {type(url_info.normalized)}"
        assert not url_info.is_valid
        assert url_info.scheme == ""
        assert url_info.netloc == ""

def test_url_info_immutability():
    """Test that URLInfo objects are immutable."""
    url_info = URLInfo.from_string("https://example.com")
    
    with pytest.raises(Exception):
        url_info.normalized = "something-else"
    
    with pytest.raises(Exception):
        url_info.scheme = "http"

def test_url_info_equality():
    """Test URL equality comparisons."""
    url1 = URLInfo.from_string("https://example.com/path/")
    url2 = URLInfo.from_string("https://example.com/path/")
    url3 = URLInfo.from_string("https://example.com/other/")
    
    assert url1 == url2
    assert url1 != url3
    assert hash(url1) == hash(url2)
    assert hash(url1) != hash(url3)

def test_url_info_type_safety():
    """Test type safety of URL components."""
    url = URLInfo.from_string("https://example.com/path?query=1#fragment")
    
    assert isinstance(url.normalized, str)
    assert isinstance(url.original, str)
    assert isinstance(url.scheme, str)
    assert isinstance(url.netloc, str)
    assert isinstance(url.path, str)
    assert isinstance(url.is_valid, bool)

def test_url_info_edge_cases():
    """Test edge cases in URL handling."""
    test_cases = [
        # Unicode domains
        ("http://ünicode.com", "http://xn--nicode-2ya.com/"),
        # Very long URLs
        ("http://example.com/" + "a" * 500, "http://example.com/" + "a" * 500),
        # URLs with multiple query parameters
        ("http://example.com?a=1&b=2&c=3", "http://example.com/?a=1&b=2&c=3"),
        # URLs with special characters
        ("http://example.com/path with spaces", "http://example.com/path%20with%20spaces"),
        # URLs with authentication
        ("http://user:pass@example.com", "http://example.com/"),
        # URLs with port numbers
        ("http://example.com:8080", "http://example.com:8080/"),
        # URLs with fragments
        ("http://example.com#section1", "http://example.com/"),
        # URLs with multiple slashes
        ("http://example.com//path///to//file", "http://example.com/path/to/file"),
    ]

    for input_url, expected in test_cases:
        url_info = URLInfo.from_string(input_url)
        assert isinstance(url_info.normalized, str)
        assert url_info.normalized == expected

def test_url_info_security():
    """Test handling of potentially malicious URLs."""
    test_cases = [
        # XSS attempts
        ("http://example.com/<script>alert('xss')</script>", False),
        # SQL injection attempts
        ("http://example.com/page?id=1' OR '1'='1", False),
        # Directory traversal attempts
        ("http://example.com/../../../etc/passwd", False),
        # Protocol confusion
        ("javascript:alert('xss')", False),
        ("data:text/html,<script>alert('xss')</script>", False),
        # Shell command injection
        ("http://example.com/`rm -rf /`", False),
        # Null byte injection
        ("http://example.com/page%00.html", False),
    ]

    for input_url, expected_valid in test_cases:
        url_info = URLInfo.from_string(input_url)
        assert url_info.is_valid == expected_valid

def test_url_info_relative_paths():
    """Test handling of relative paths."""
    base_url = "http://example.com/docs/page1.html"
    test_cases = [
        # Same directory
        ("page2.html", "http://example.com/docs/page2.html"),
        # Parent directory
        ("../index.html", "http://example.com/index.html"),
        # Root directory
        ("/images/logo.png", "http://example.com/images/logo.png"),
        # Current directory
        ("./style.css", "http://example.com/docs/style.css"),
        # Multiple parent directories
        ("../../assets/img.jpg", "http://example.com/assets/img.jpg"),
        # Absolute URL (should remain unchanged)
        ("http://other.com/page.html", "http://other.com/page.html"),
    ]

    for input_path, expected in test_cases:
        url_info = URLInfo.from_string(input_path, base_url=base_url)
        assert url_info.normalized == expected

def test_url_info_query_parameters():
    """Test handling of query parameters."""
    test_cases = [
        # Basic query parameters
        (
            "http://example.com?param1=value1",
            "http://example.com/?param1=value1"
        ),
        # Multiple parameters
        (
            "http://example.com?param1=value1&param2=value2",
            "http://example.com/?param1=value1&param2=value2"
        ),
        # Parameters with special characters
        (
            "http://example.com?q=test%20space",
            "http://example.com/?q=test%20space"
        ),
        # Empty parameters
        (
            "http://example.com?param1=&param2=",
            "http://example.com/?param1=&param2="
        ),
        # Duplicate parameters
        (
            "http://example.com?param=1&param=2",
            "http://example.com/?param=1&param=2"
        ),
        # Parameters with array notation
        (
            "http://example.com?arr[]=1&arr[]=2",
            "http://example.com/?arr[]=1&arr[]=2"
        ),
    ]

    for input_url, expected in test_cases:
        url_info = URLInfo.from_string(input_url)
        assert url_info.normalized == expected

def test_url_info_performance():
    """Test URL processing performance with a large number of URLs."""
    import time
    urls = [
        f"http://example{i}.com/path/to/page?param={i}"
        for i in range(1000)
    ]
    
    start_time = time.time()
    for url in urls:
        url_info = URLInfo.from_string(url)
        assert url_info.is_valid
    end_time = time.time()
    
    processing_time = end_time - start_time
    assert processing_time < 5.0  # Should process 1000 URLs in under 5 seconds
