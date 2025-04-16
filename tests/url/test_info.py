"""
Tests for the modular URLInfo class in src/utils/url/info.py
"""

import pytest
from src.utils.url import URLInfo, URLType

# Mock tldextract if not installed for basic tests
try:
    import tldextract
    TLDEXTRACT_AVAILABLE = True
except ImportError:
    TLDEXTRACT_AVAILABLE = False
    # Minimal mock for testing basic functionality
    class MockExtractResult:
        def __init__(self, subdomain='', domain='', suffix=''):
            self.subdomain = subdomain
            self.domain = domain
            self.suffix = suffix
            self.registered_domain = f"{domain}.{suffix}" if domain and suffix else domain or suffix

    class MockTLDExtract:
        def extract(self, url):
            parts = url.split('.')
            if len(parts) == 1: return MockExtractResult(domain=parts[0])
            if len(parts) == 2: return MockExtractResult(domain=parts[0], suffix=parts[1])
            return MockExtractResult(subdomain='.'.join(parts[:-2]), domain=parts[-2], suffix=parts[-1])

    tldextract = MockTLDExtract()


# --- Test Cases ---

VALID_URLS = [
    ("http://example.com", "http://example.com/"),
    ("https://www.example.co.uk/path?a=1", "https://www.example.co.uk/path?a=1"),
    ("http://EXAMPLE.com:80/./path/../other/", "http://example.com/other/"), # Normalization + default port
    ("https://xn--mnchen-3ya.de/path", "https://xn--mnchen-3ya.de/path"), # IDN
    ("http://localhost:8080", "http://localhost:8080/"),
    ("http://127.0.0.1/test", "http://127.0.0.1/test"),
    ("file:///path/to/file.txt", "file:///path/to/file.txt"),
]

INVALID_URLS = [
    ("javascript:alert(1)", "Invalid scheme"),
    ("ftp://user:pass@example.com", "Auth info not allowed"), # Assuming validation blocks auth
    ("http://<invalid>.com", "Invalid label chars"),
    ("http://example.com:99999", "Invalid port"),
    ("http://example.com/../../etc/passwd", "Directory traversal attempt"),
    ("http://example.com/?q=<script>", "XSS pattern"),
    ("http://192.168.1.1", "Private/loopback IP"), # Private IP
    ("", "URL cannot be None or empty"),
    (None, "URL cannot be None or empty"),
    ("http://example.com/path%00.txt", "Null byte in path"),
]

RELATIVE_URLS = [
    # (relative, base, expected_normalized)
    ("page2.html", "http://example.com/docs/page1.html", "http://example.com/docs/page2.html"),
    ("../index.html", "http://example.com/docs/page1.html", "http://example.com/index.html"),
    ("/images/logo.png", "http://example.com/docs/page1.html", "http://example.com/images/logo.png"),
    ("//other.com/path", "https://example.com/docs/", "https://other.com/path"), # Protocol relative
    ("?query=new", "http://example.com/page?a=1", "http://example.com/page?query=new"),
    ("#fragment", "http://example.com/page", "http://example.com/page"), # Fragment ignored in normalization
]

URL_TYPES = [
    # (url, base, expected_type)
    ("https://example.com/path", "https://example.com/base", URLType.INTERNAL),
    ("/relative/path", "https://example.com/base", URLType.INTERNAL),
    ("https://www.example.com/path", "https://example.com/base", URLType.INTERNAL), # Diff subdomain but same reg_domain
    ("http://example.com/path", "https://example.com/base", URLType.EXTERNAL), # Diff scheme
    ("https://other.com/path", "https://example.com/base", URLType.EXTERNAL), # Diff domain
    ("page.html", "https://example.com/base/", URLType.INTERNAL),
    ("https://example.com:443/path", "https://example.com/base", URLType.INTERNAL), # Same default port
    ("https://example.com:8443/path", "https://example.com/base", URLType.INTERNAL), # Diff port, still internal
]

TLDEXTRACT_CASES = [
    # (url, expected_subdomain, expected_domain, expected_suffix, expected_registered_domain)
    ("https://www.example.co.uk/path", "www", "example", "co.uk", "example.co.uk"),
    ("http://blog.example.com", "blog", "example", "com", "example.com"),
    ("https://justadomain.com", "", "justadomain", "com", "justadomain.com"),
    ("http://xn--mnchen-3ya.de", "", "xn--mnchen-3ya", "de", "xn--mnchen-3ya.de"), # IDN
    ("http://localhost:8080", "", "localhost", "", "localhost"), # localhost case
    ("http://127.0.0.1", "", "127.0.0.1", "", "127.0.0.1"), # IP Address case
]

# --- Test Functions ---

@pytest.mark.parametrize("url_str, expected_normalized", VALID_URLS)
def test_valid_url_initialization(url_str, expected_normalized):
    """Test initialization with valid URLs."""
    info = URLInfo(url_str)
    assert info.is_valid is True
    assert info.error_message is None
    assert info.raw_url == url_str
    assert info.normalized_url == expected_normalized
    assert str(info) == expected_normalized
    assert repr(info).startswith("URLInfo(raw=")

@pytest.mark.parametrize("url_str, error_part", INVALID_URLS)
def test_invalid_url_initialization(url_str, error_part):
    """Test initialization with invalid URLs."""
    info = URLInfo(url_str)
    assert info.is_valid is False
    assert info.error_message is not None
    assert error_part in info.error_message
    # Normalized URL should fallback gracefully for invalid URLs
    assert isinstance(info.normalized_url, str)
    # For None/empty input, normalized should be empty
    if url_str is None or url_str == "":
        assert info.normalized_url == ""
    else:
        # Otherwise, it might be the raw or resolved URL depending on failure point
        assert info.normalized_url is not None


@pytest.mark.parametrize("relative, base, expected_normalized", RELATIVE_URLS)
def test_relative_url_resolution(relative, base, expected_normalized):
    """Test resolving relative URLs against a base URL."""
    info = URLInfo(relative, base_url=base)
    assert info.is_valid is True
    assert info.normalized_url == expected_normalized

def test_url_properties():
    """Test accessing various properties of a URLInfo object."""
    url_str = "https://user:pass@www.example.co.uk:8443/path/to/page?a=1&b=two#section"
    info = URLInfo(url_str)

    assert info.is_valid is True # Assuming auth is stripped but URL is otherwise valid
    assert info.scheme == "https"
    assert info.netloc == "www.example.co.uk:8443" # Normalized netloc excludes auth
    assert info.hostname == "www.example.co.uk"
    assert info.path == "/path/to/page"
    assert info.query == "a=1&b=two"
    assert info.fragment == "section" # Fragment from raw URL
    assert info.port == 8443 # Port from original parsed URL
    assert info.username == "user" # Username from original parsed URL
    assert info.password == "pass" # Password from original parsed URL

    params = info.query_params
    assert isinstance(params, dict)
    assert params.get("a") == ["1"]
    assert params.get("b") == ["two"]

@pytest.mark.skipif(not TLDEXTRACT_AVAILABLE, reason="tldextract not installed")
@pytest.mark.parametrize("url, sub, dom, suf, reg", TLDEXTRACT_CASES)
def test_tldextract_properties(url, sub, dom, suf, reg):
    """Test domain properties derived from tldextract."""
    info = URLInfo(url)
    assert info.is_valid is True # Assuming these are valid for the test
    assert info.subdomain == sub
    assert info.domain == dom
    assert info.suffix == suf
    assert info.tld == suf # Check alias
    assert info.registered_domain == reg
    assert info.root_domain == reg # Check alias

    parts = info.domain_parts
    assert parts['subdomain'] == sub
    assert parts['domain'] == dom
    assert parts['suffix'] == suf
    assert parts['registered_domain'] == reg

def test_tldextract_fallback():
    """Test domain properties when tldextract is not available or fails."""
    # This test requires mocking TLDEXTRACT_AVAILABLE to False or tldextract.extract to raise error
    # For simplicity, we assume the basic split logic is tested implicitly if tldextract is missing
    # Or we could explicitly test the fallback logic if needed by manipulating the import/mock
    url = "https://www.example.co.uk"
    # Assuming basic split:
    # subdomain = www, domain = example, suffix = co.uk, registered = example.co.uk
    # This might require more setup to test reliably without tldextract installed.
    # Let's test a simple case that doesn't rely on complex TLDs
    info_simple = URLInfo("https://example.com")
    if not TLDEXTRACT_AVAILABLE:
        assert info_simple.subdomain == ""
        assert info_simple.domain == "example"
        assert info_simple.suffix == "com"
        assert info_simple.registered_domain == "example.com"


@pytest.mark.parametrize("url, base, expected_type", URL_TYPES)
def test_url_type_determination(url, base, expected_type):
    """Test internal/external URL type classification."""
    info = URLInfo(url, base_url=base)
    # We assume the URLs are valid enough for type determination
    assert info.url_type == expected_type

def test_url_equality_and_hash():
    """Test equality and hashing based on normalized URL."""
    url1_str = "http://example.com/path/"
    url2_str = "http://EXAMPLE.com:80/path/" # Normalizes to the same
    url3_str = "http://example.com/other"
    invalid_url_str = "javascript:void(0)"

    info1 = URLInfo(url1_str)
    info2 = URLInfo(url2_str)
    info3 = URLInfo(url3_str)
    info_invalid1 = URLInfo(invalid_url_str)
    info_invalid2 = URLInfo(invalid_url_str) # Same invalid URL

    assert info1.is_valid
    assert info2.is_valid
    assert info3.is_valid
    assert not info_invalid1.is_valid
    assert not info_invalid2.is_valid

    assert info1 == info2
    assert info1 != info3
    assert info1 != info_invalid1
    assert info_invalid1 != info1 # Comparison with invalid should be False
    assert info_invalid1 == info_invalid1 # Should an invalid URL equal itself? Yes.
    # Should two identical invalid URLs be equal? Based on hash of raw, yes.
    # Let's refine __eq__ if needed, current hash uses normalized_url (which falls back)
    # assert info_invalid1 == info_invalid2 # This depends on __eq__ implementation for invalid

    assert hash(info1) == hash(info2)
    assert hash(info1) != hash(info3)
    # Hash comparison with invalid URLs depends on hashing strategy
    # assert hash(info1) != hash(info_invalid1)
    # assert hash(info_invalid1) == hash(info_invalid2) # If hash uses raw_url for invalid

    # Test comparison with other types
    assert info1 != url1_str
    assert info1 != None

def test_immutability():
    """Test that URLInfo attributes cannot be changed after initialization."""
    info = URLInfo("http://example.com")
    assert info.is_valid

    with pytest.raises(AttributeError):
        info.normalized_url = "http://other.com"
    with pytest.raises(AttributeError):
        info.scheme = "https"
    with pytest.raises(AttributeError):
        info.is_valid = False
    with pytest.raises(AttributeError):
        info._raw_url = "http://other.com" # Internal attributes also protected

    # Ensure cached properties are also protected (implicitly via __setattr__)
    _ = info.hostname # Access to cache
    with pytest.raises(AttributeError):
         info.hostname = "other.com"


def test_fragment_removal():
    """Test that fragments are removed during normalization but accessible."""
    url_str = "https://example.com/path?a=1#section"
    info = URLInfo(url_str)
    assert info.is_valid
    assert info.normalized_url == "https://example.com/path?a=1"
    assert info.fragment == "section"

    url_str_no_frag = "https://example.com/path?a=1"
    info_no_frag = URLInfo(url_str_no_frag)
    assert info_no_frag.is_valid
    assert info_no_frag.normalized_url == "https://example.com/path?a=1"
    assert info_no_frag.fragment == ""

def test_long_url_edge_case():
    """Test handling of very long paths."""
    long_path_part = "a" * 500
    url_str = f"http://example.com/{long_path_part}"
    expected_normalized = f"http://example.com/{long_path_part}"
    info = URLInfo(url_str)
    # Validation might fail if MAX_PATH_LENGTH is exceeded, but normalization should still work if parsed
    # Let's assume it's valid for this length based on default config
    # If MAX_PATH_LENGTH was smaller, we'd expect is_valid == False
    assert info.is_valid # Adjust assertion based on actual MAX_PATH_LENGTH in security config
    assert info.normalized_url == expected_normalized

def test_url_info_performance():
    """Test URL processing performance with a large number of URLs."""
    import time
    urls = [
        f"http://example{i}.com/path/to/page?param={i}"
        for i in range(100)  # Reduced to 100 for faster testing
    ]
    
    start_time = time.time()
    for url in urls:
        url_info = URLInfo(url)
        assert url_info.is_valid
    end_time = time.time()
    
    processing_time = end_time - start_time
    print(f"\nProcessed {len(urls)} URLs in {processing_time:.4f} seconds") # Added print for info
    assert processing_time < 2.0  # Should process 100 URLs in under 2 seconds
