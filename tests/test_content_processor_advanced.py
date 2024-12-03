import pytest
from bs4 import BeautifulSoup
from src.processors.content_processor import ContentProcessor, ProcessorConfig
from src.utils.helpers import RateLimiter, Timer, URLProcessor, URLType, URLInfo

@pytest.fixture
def processor():
    return ContentProcessor(ProcessorConfig())

def test_basic_html_processing(processor):
    """Test basic HTML content processing."""
    html = """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <h1>Main Title</h1>
            <p>This is a test paragraph.</p>
            <div class="code">
                <pre>def test(): pass</pre>
            </div>
        </body>
    </html>
    """
    result = processor.process(html)
    assert "Main Title" in result
    assert "This is a test paragraph" in result
    assert "def test(): pass" in result

def test_code_block_extraction(processor):
    """Test extraction and formatting of code blocks."""
    html = """
    <div>
        <pre><code class="python">def example():
    return True</code></pre>
        <pre><code class="javascript">function test() {
    return true;
}</code></pre>
    </div>
    """
    result = processor.process(html)
    assert "def example():" in result
    assert "function test()" in result
    assert "python" in result.lower()
    assert "javascript" in result.lower()

def test_table_processing(processor):
    """Test processing of HTML tables."""
    html = """
    <table>
        <thead>
            <tr><th>Header 1</th><th>Header 2</th></tr>
        </thead>
        <tbody>
            <tr><td>Cell 1</td><td>Cell 2</td></tr>
            <tr><td>Cell 3</td><td>Cell 4</td></tr>
        </tbody>
    </table>
    """
    result = processor.process(html)
    assert "Header 1" in result
    assert "Header 2" in result
    assert "Cell 1" in result
    assert "Cell 4" in result
    # Check for table formatting
    assert "|" in result
    assert "-" in result

def test_list_processing(processor):
    """Test processing of ordered and unordered lists."""
    html = """
    <ul>
        <li>Item 1</li>
        <li>Item 2</li>
    </ul>
    <ol>
        <li>First</li>
        <li>Second</li>
    </ol>
    """
    result = processor.process(html)
    assert "* Item 1" in result or "- Item 1" in result
    assert "* Item 2" in result or "- Item 2" in result
    assert "1. First" in result
    assert "2. Second" in result

def test_link_processing(processor):
    """Test processing of HTML links."""
    html = """
    <a href="https://example.com">Example Link</a>
    <a href="relative/path">Relative Link</a>
    <a href="#section">Section Link</a>
    """
    result = processor.process(html)
    assert "Example Link" in result
    assert "https://example.com" in result
    assert "relative/path" in result
    assert "#section" in result

def test_image_processing(processor):
    """Test processing of images."""
    html = """
    <img src="test.jpg" alt="Test Image">
    <img src="https://example.com/img.png" alt="Remote Image">
    """
    result = processor.process(html)
    assert "Test Image" in result
    assert "test.jpg" in result
    assert "Remote Image" in result
    assert "https://example.com/img.png" in result

def test_heading_hierarchy(processor):
    """Test proper handling of heading hierarchy."""
    html = """
    <h1>Main Title</h1>
    <h2>Subtitle</h2>
    <h3>Section</h3>
    <h4>Subsection</h4>
    """
    result = processor.process(html)
    assert "# Main Title" in result
    assert "## Subtitle" in result
    assert "### Section" in result
    assert "#### Subsection" in result

def test_special_characters(processor):
    """Test handling of special characters and entities."""
    html = """
    <p>&copy; 2024</p>
    <p>&lt;example&gt;</p>
    <p>€ symbol</p>
    <p>漢字</p>
    """
    result = processor.process(html)
    assert "©" in result or "(c)" in result
    assert "<example>" in result
    assert "€" in result
    assert "漢字" in result

def test_content_cleanup(processor):
    """Test cleaning of problematic content."""
    html = """
    <div>
        <script>alert('test');</script>
        <style>.test { color: red; }</style>
        <p>Valid content</p>
        <!-- Comment -->
    </div>
    """
    result = processor.process(html)
    assert "alert" not in result
    assert "color: red" not in result
    assert "Valid content" in result
    assert "Comment" not in result

def test_performance(processor):
    """Test processing performance with large content."""
    # Generate large HTML content
    large_html = "<div>" + "<p>Test content</p>" * 1000 + "</div>"
    
    with Timer() as timer:
        result = processor.process(large_html)
    
    assert len(result) > 0
    assert timer.duration < 1.0  # Should process in under 1 second

def test_error_handling(processor):
    """Test handling of malformed HTML."""
    malformed_cases = [
        "<p>Unclosed paragraph",
        "<div><p>Nested unclosed</div>",
        "<<>>",
        None,
        "",
        "<html><body>Missing closing tags",
    ]
    
    for html in malformed_cases:
        result = processor.process(html)
        assert isinstance(result, str)
        assert len(result) >= 0  # Should not raise exception

def test_metadata_extraction(processor):
    """Test extraction of metadata from HTML."""
    html = """
    <html>
        <head>
            <meta name="description" content="Page description">
            <meta name="keywords" content="test, example">
            <meta property="og:title" content="Open Graph Title">
        </head>
        <body>
            <p>Content</p>
        </body>
    </html>
    """
    result = processor.process(html)
    metadata = processor.extract_metadata(html)
    assert metadata["description"] == "Page description"
    assert "test" in metadata["keywords"]
    assert metadata["og:title"] == "Open Graph Title"

def test_url_processor_normalization():
    """Test URL normalization with various cases."""
    processor = URLProcessor()
    
    # Test basic URL normalization
    assert processor.normalize_url("http://example.com/path/") == "http://example.com/path"
    assert processor.normalize_url("HTTP://EXAMPLE.COM/PATH") == "http://example.com/path"
    
    # Test Unicode domain handling
    unicode_url = "http://ünicode.com/path"
    normalized = processor.normalize_url(unicode_url)
    assert "xn--" in normalized  # Should contain IDNA prefix
    
    # Test base URL joining
    assert processor.normalize_url("/relative/path", "http://example.com") == "http://example.com/relative/path"

def test_url_type_detection():
    """Test URL type detection for different URLs."""
    processor = URLProcessor()
    base_url = "http://example.com"
    
    # Test internal URL
    internal = processor.process_url("http://example.com/docs", base_url)
    assert internal.url_type == URLType.INTERNAL
    
    # Test external URL
    external = processor.process_url("http://other-site.com", base_url)
    assert external.url_type == URLType.EXTERNAL
    
    # Test asset URL
    asset = processor.process_url("http://example.com/image.png", base_url)
    assert asset.url_type == URLType.ASSET

def test_url_validation():
    """Test URL validation for various cases."""
    processor = URLProcessor()
    
    # Test valid URL
    valid = processor.process_url("http://example.com")
    assert valid.is_valid
    assert not valid.error_msg
    
    # Test invalid URL
    invalid = processor.process_url("not-a-url")
    assert not invalid.is_valid
    assert invalid.error_msg
    
    # Test URL with invalid scheme
    invalid_scheme = processor.process_url("ftp://example.com")
    assert not invalid_scheme.is_valid
    assert "scheme" in invalid_scheme.error_msg.lower()

def test_url_processor_edge_cases():
    """Test URL processor with edge cases and special characters."""
    processor = URLProcessor()
    
    # Test empty URL
    empty = processor.process_url("")
    assert not empty.is_valid
    assert empty.error_msg
    
    # Test None URL
    none = processor.process_url(None)
    assert not none.is_valid
    assert none.error_msg
    
    # Test URL with special characters
    special = processor.process_url("http://example.com/path with spaces/")
    assert special.is_valid
    assert "%20" in special.normalized_url
    
    # Test URL with query parameters
    query = processor.process_url("http://example.com/path?param1=value1&param2=value2")
    assert query.is_valid
    assert "param1=value1" in query.normalized_url
    
    # Test URL with fragments
    fragment = processor.process_url("http://example.com/path#section1")
    assert fragment.is_valid
    assert "#" not in fragment.normalized_url  # Fragments should be removed

def test_url_processor_security():
    """Test URL processor security features."""
    processor = URLProcessor()
    
    # Test potentially malicious URLs
    malicious_urls = [
        "javascript:alert('xss')",
        "data:text/html,<script>alert('xss')</script>",
        "file:///etc/passwd",
        "http://example.com@evil.com",
        "http://evil.com/path/../../sensitive/data",
        "http://evil.com:80@example.com",
    ]
    
    for url in malicious_urls:
        result = processor.process_url(url)
        assert not result.is_valid
        assert result.error_msg

def test_url_processor_international():
    """Test URL processor with international domains and paths."""
    processor = URLProcessor()
    
    # Test international domains
    international_urls = {
        "http://münchen.de": "xn--mnchen-3ya.de",
        "http://ελληνικά.gr": "xn--qxaib9b7c.gr",
        "http://中国.cn": "xn--fiqs8s.cn",
        "http://日本.jp": "xn--wgv71a.jp"
    }
    
    for url, expected_domain in international_urls.items():
        result = processor.process_url(url)
        assert result.is_valid
        assert expected_domain in result.normalized_url
        
    # Test international paths
    path_url = processor.process_url("http://example.com/über/文档/ελληνικά")
    assert path_url.is_valid
    assert all(c in path_url.normalized_url for c in ['%', 'ber'])  # URL encoded

def test_url_processor_relative_paths():
    """Test URL processor with relative paths."""
    processor = URLProcessor()
    base_url = "http://example.com/docs/section1/"
    
    relative_paths = {
        "./page": "/docs/section1/page",
        "../page": "/docs/page",
        "../../page": "/page",
        "/page": "/page",
        "page": "/docs/section1/page",
        "../../../page": "/page",  # Should not go above root
    }
    
    for rel_path, expected in relative_paths.items():
        result = processor.process_url(rel_path, base_url)
        assert result.is_valid
        assert result.path == expected

def test_url_processor_asset_types():
    """Test URL processor asset type detection."""
    processor = URLProcessor()
    
    # Test various asset types
    asset_urls = {
        "http://example.com/image.jpg": URLType.ASSET,
        "http://example.com/style.css": URLType.ASSET,
        "http://example.com/script.js": URLType.ASSET,
        "http://example.com/document.pdf": URLType.ASSET,
        "http://example.com/image.PNG": URLType.ASSET,  # Case insensitive
        "http://example.com/path/to/image.jpeg": URLType.ASSET,
        "http://example.com/path.html": URLType.INTERNAL,
        "http://example.com/path/no-extension": URLType.INTERNAL,
    }
    
    for url, expected_type in asset_urls.items():
        result = processor.process_url(url, "http://example.com")
        assert result.url_type == expected_type

def test_url_processor_query_handling():
    """Test URL processor query parameter handling."""
    processor = URLProcessor()
    
    # Test query parameter normalization
    urls = {
        "http://example.com/?a=1&b=2": "http://example.com/?a=1&b=2",
        "http://example.com/?b=2&a=1": "http://example.com/?a=1&b=2",  # Sorted params
        "http://example.com/?a=1&&b=2": "http://example.com/?a=1&b=2",  # Remove duplicate &
        "http://example.com/?a=1&a=2": "http://example.com/?a=2",  # Last value wins
    }
    
    for url, expected in urls.items():
        result = processor.process_url(url)
        assert result.normalized_url == expected
        assert result.is_valid

def test_url_processor_scheme_handling():
    """Test URL processor scheme handling."""
    processor = URLProcessor()
    
    schemes = {
        "http://example.com": True,
        "https://example.com": True,
        "ftp://example.com": False,
        "sftp://example.com": False,
        "//example.com": False,
        "example.com": False,
    }
    
    for url, should_be_valid in schemes.items():
        result = processor.process_url(url)
        assert result.is_valid == should_be_valid
        if should_be_valid:
            assert result.normalized_url.startswith(('http://', 'https://'))

def test_url_processor_port_handling():
    """Test URL processor port handling."""
    processor = URLProcessor()
    
    port_urls = {
        "http://example.com:80": "http://example.com",  # Default HTTP port removed
        "https://example.com:443": "https://example.com",  # Default HTTPS port removed
        "http://example.com:8080": "http://example.com:8080",  # Non-default port kept
        "https://example.com:8443": "https://example.com:8443",  # Non-default port kept
        "http://example.com:": "http://example.com",  # Empty port removed
        "http://example.com:abc": None,  # Invalid port
        "http://example.com:65536": None,  # Port number too high
        "http://example.com:-80": None,  # Negative port
    }
    
    for url, expected in port_urls.items():
        result = processor.process_url(url)
        if expected is None:
            assert not result.is_valid
            assert "port" in result.error_msg.lower()
        else:
            assert result.is_valid
            assert result.normalized_url == expected

def test_url_processor_auth_handling():
    """Test URL processor authentication handling."""
    processor = URLProcessor()
    
    auth_urls = {
        "http://user:pass@example.com": False,  # Basic auth not allowed
        "http://user@example.com": False,  # Username only not allowed
        "http://:pass@example.com": False,  # Password only not allowed
        "http://example.com": True,  # No auth is fine
        "http://üser:päss@example.com": False,  # Unicode in auth not allowed
    }
    
    for url, should_be_valid in auth_urls.items():
        result = processor.process_url(url)
        assert result.is_valid == should_be_valid
        if not should_be_valid:
            assert "authentication" in result.error_msg.lower()

def test_url_processor_ip_handling():
    """Test URL processor IP address handling."""
    processor = URLProcessor()
    
    ip_urls = {
        "http://127.0.0.1": False,  # Localhost IP not allowed
        "http://127.0.0.1:8080": False,  # Localhost IP with port not allowed
        "http://0.0.0.0": False,  # All interfaces IP not allowed
        "http://192.168.1.1": False,  # Private IP not allowed
        "http://10.0.0.1": False,  # Private IP not allowed
        "http://172.16.0.1": False,  # Private IP not allowed
        "http://256.256.256.256": False,  # Invalid IP
        "http://1.2.3.4": True,  # Public IP allowed
        "http://[::1]": False,  # IPv6 localhost not allowed
        "http://[2001:db8::1]": True,  # Public IPv6 allowed
    }
    
    for url, should_be_valid in ip_urls.items():
        result = processor.process_url(url)
        assert result.is_valid == should_be_valid
        if not should_be_valid and "256" not in url:  # Skip invalid IP format
            assert any(x in result.error_msg.lower() for x in ["ip", "localhost", "private"])

def test_url_processor_unicode_normalization():
    """Test URL processor Unicode normalization."""
    processor = URLProcessor()
    
    unicode_tests = {
        # Different Unicode representations of same character
        "http://example.com/café": "http://example.com/caf%C3%A9",
        "http://example.com/cafe\u0301": "http://example.com/caf%C3%A9",
        # Mixed scripts
        "http://example.com/path/文字/test": "http://example.com/path/%E6%96%87%E5%AD%97/test",
        # Bidirectional text
        "http://example.com/hello/שלום/test": "http://example.com/hello/%D7%A9%D7%9C%D7%95%D7%9D/test",
        # Special characters
        "http://example.com/∞": "http://example.com/%E2%88%9E",
        # Emoji
        "http://example.com/📚": "http://example.com/%F0%9F%93%9A",
    }
    
    for url, expected in unicode_tests.items():
        result = processor.process_url(url)
        assert result.is_valid
        assert result.normalized_url == expected

def test_url_processor_domain_validation():
    """Test URL processor domain validation."""
    processor = URLProcessor()
    
    domain_tests = {
        "http://example": False,  # Missing TLD
        "http://example.": False,  # TLD dot only
        "http://.example.com": False,  # Leading dot
        "http://example..com": False,  # Consecutive dots
        "http://example.com..": False,  # Trailing dots
        "http://ex^mple.com": False,  # Invalid characters
        "http://exa mple.com": False,  # Spaces in domain
        "http://example.c": False,  # Single char TLD
        "http://example.com": True,  # Valid domain
        "http://sub.example.com": True,  # Valid subdomain
        "http://sub.sub.example.com": True,  # Multiple subdomains
        "http://" + "a"*63 + ".com": True,  # Max label length
        "http://" + "a"*64 + ".com": False,  # Label too long
        "http://" + ".".join(["a"]*10) + ".com": True,  # Multiple labels
    }
    
    for url, should_be_valid in domain_tests.items():
        result = processor.process_url(url)
        assert result.is_valid == should_be_valid
        if not should_be_valid:
            assert "domain" in result.error_msg.lower()

def test_url_processor_path_validation():
    """Test URL processor path validation."""
    processor = URLProcessor()
    
    path_tests = {
        "http://example.com/normal/path": True,
        "http://example.com/path/../normal": False,  # Path traversal
        "http://example.com/path/./normal": True,  # Current directory
        "http://example.com//double//slash": True,  # Double slashes normalized
        "http://example.com/path/": True,  # Trailing slash
        "http://example.com/path//////": True,  # Multiple trailing slashes normalized
        "http://example.com/path with spaces": True,  # Spaces encoded
        "http://example.com/path\with\\backslash": False,  # Backslashes not allowed
        "http://example.com/path<with>invalid": False,  # Invalid characters
        "http://example.com/" + "a"*2048: False,  # Path too long
        "http://example.com/%2e%2e/": False,  # Encoded path traversal
    }
    
    for url, should_be_valid in path_tests.items():
        result = processor.process_url(url)
        assert result.is_valid == should_be_valid
        if not should_be_valid:
            assert "path" in result.error_msg.lower()

def test_url_processor_query_validation():
    """Test URL processor query string validation."""
    processor = URLProcessor()
    
    query_tests = {
        "http://example.com?normal=value": True,
        "http://example.com?a=1&b=2": True,
        "http://example.com?": True,  # Empty query allowed
        "http://example.com?a=1&&b=2": True,  # Double & normalized
        "http://example.com?a=1#fragment": True,  # Fragment removed
        "http://example.com?a=1;b=2": False,  # Semicolon not allowed
        "http://example.com?a=1 &b=2": True,  # Space encoded
        "http://example.com?" + "x"*2048: False,  # Query too long
        "http://example.com?<script>": False,  # Script tags not allowed
        "http://example.com?%3Cscript%3E": False,  # Encoded script tags not allowed
    }
    
    for url, should_be_valid in query_tests.items():
        result = processor.process_url(url)
        assert result.is_valid == should_be_valid
        if not should_be_valid:
            assert "query" in result.error_msg.lower()

def test_url_processor_fragment_handling():
    """Test URL processor fragment handling."""
    processor = URLProcessor()
    
    fragment_tests = {
        "http://example.com#section": "http://example.com",
        "http://example.com#section#multiple": "http://example.com",
        "http://example.com#": "http://example.com",
        "http://example.com#1": "http://example.com",
        "http://example.com?query#fragment": "http://example.com?query",
    }
    
    for url, expected in fragment_tests.items():
        result = processor.process_url(url)
        assert result.is_valid
        assert result.normalized_url == expected
        assert "#" not in result.normalized_url

def test_rate_limiter():
    """Test rate limiter functionality."""
    limiter = RateLimiter(requests_per_second=2.0)  # 2 requests per second
    
    # First request should not wait
    start = time.time()
    limiter.wait()
    assert time.time() - start < 0.1  # Should be almost instant
    
    # Second request within the same second should wait
    start = time.time()
    limiter.wait()
    duration = time.time() - start
    assert 0.4 < duration < 0.6  # Should wait about 0.5 seconds
    
    # Test with very high rate
    fast_limiter = RateLimiter(requests_per_second=1000.0)
    start = time.time()
    fast_limiter.wait()
    assert time.time() - start < 0.01  # Should be almost instant

def test_retry_strategy():
    """Test retry strategy functionality."""
    strategy = RetryStrategy(
        max_retries=3,
        initial_delay=1.0,
        max_delay=5.0,
        backoff_factor=2.0
    )
    
    # Test delay progression
    expected_delays = [1.0, 2.0, 4.0]  # Each delay doubles
    for attempt, expected in enumerate(expected_delays, 1):
        delay = strategy.get_delay(attempt)
        assert delay == expected
    
    # Test max delay cap
    delay = strategy.get_delay(4)  # Would be 8.0, but capped at 5.0
    assert delay == 5.0
    
    # Test with different parameters
    custom_strategy = RetryStrategy(
        max_retries=5,
        initial_delay=0.1,
        max_delay=1.0,
        backoff_factor=3.0
    )
    
    delays = [custom_strategy.get_delay(i) for i in range(1, 7)]
    assert delays == [0.1, 0.3, 0.9, 1.0, 1.0, 1.0]  # Last three capped at max_delay

def test_calculate_similarity():
    """Test text similarity calculation."""
    # Test exact matches
    assert calculate_similarity("test text", "test text") == 1.0
    assert calculate_similarity("", "") == 0.0
    
    # Test partial matches
    assert 0.3 < calculate_similarity("hello world", "hello there") < 0.7
    assert 0.0 < calculate_similarity("python programming", "programming in python") < 1.0
    
    # Test case insensitivity
    assert calculate_similarity("Hello World", "hello world") == 1.0
    
    # Test with different word orders
    assert calculate_similarity("python is great", "great is python") == 1.0
    
    # Test with special characters
    assert calculate_similarity("hello, world!", "hello world") == 1.0

def test_generate_checksum():
    """Test checksum generation."""
    # Test string input
    text = "test content"
    checksum1 = generate_checksum(text)
    checksum2 = generate_checksum(text)
    assert isinstance(checksum1, str)
    assert len(checksum1) == 64  # SHA-256 produces 64 char hex string
    assert checksum1 == checksum2  # Same input should produce same checksum
    
    # Test bytes input
    bytes_input = b"test content"
    assert generate_checksum(bytes_input) == generate_checksum(text)
    
    # Test dictionary input
    dict_input = {"key": "value", "number": 123}
    dict_checksum = generate_checksum(dict_input)
    assert isinstance(dict_checksum, str)
    assert len(dict_checksum) == 64
    
    # Test different inputs produce different checksums
    assert generate_checksum("test1") != generate_checksum("test2")
    assert generate_checksum({"a": 1}) != generate_checksum({"a": 2})

def test_timer():
    """Test timer context manager."""
    import time
    
    # Test basic timing
    with Timer("test_operation") as timer:
        time.sleep(0.1)
    assert timer.duration >= 0.1
    
    # Test nested timers
    with Timer("outer") as outer:
        time.sleep(0.1)
        with Timer("inner") as inner:
            time.sleep(0.1)
    assert outer.duration >= 0.2
    assert inner.duration >= 0.1
    
    # Test timer with exception
    try:
        with Timer("error_operation"):
            raise ValueError("test error")
    except ValueError:
        pass  # Timer should still work even if operation fails

def test_setup_logging(tmp_path):
    """Test logging configuration."""
    log_file = tmp_path / "test.log"
    
    # Test basic configuration
    setup_logging(level="INFO")
    
    # Test with file handler
    setup_logging(level="DEBUG", log_file=str(log_file))
    assert log_file.exists()
    
    # Test custom format
    custom_format = '%(levelname)s - %(message)s'
    setup_logging(level="INFO", format_string=custom_format)
    
    # Test logging output
    import logging
    logger = logging.getLogger('test_logger')
    test_message = "Test log message"
    logger.info(test_message)
    
    # Verify file contents
    log_content = log_file.read_text()
    assert test_message in log_content

def test_url_processor_normalize_url():
    """Test URL normalization method."""
    processor = URLProcessor()
    
    # Test basic normalization
    assert processor.normalize_url("HTTP://EXAMPLE.COM") == "http://example.com"
    assert processor.normalize_url("http://example.com/") == "http://example.com"
    
    # Test with base URL
    assert processor.normalize_url("/path", "http://example.com") == "http://example.com/path"
    assert processor.normalize_url("subpath", "http://example.com/path/") == "http://example.com/path/subpath"
    
    # Test with query parameters
    assert processor.normalize_url("http://example.com/?a=1") == "http://example.com?a=1"
    
    # Test with fragments
    assert processor.normalize_url("http://example.com/#section") == "http://example.com"
    
    # Test with Unicode
    unicode_url = "http://ünicode.com/päth"
    normalized = processor.normalize_url(unicode_url)
    assert "xn--" in normalized  # Should contain IDNA prefix
    
    # Test error cases
    with pytest.raises(ValueError):
        processor.normalize_url("invalid://example.com")

def test_url_processor_determine_type():
    """Test URL type determination."""
    processor = URLProcessor()
    base_url = "http://example.com"
    
    # Test internal URLs
    assert processor._determine_url_type("http://example.com/page", base_url) == URLType.INTERNAL
    assert processor._determine_url_type("/page", base_url) == URLType.INTERNAL
    
    # Test external URLs
    assert processor._determine_url_type("http://other.com", base_url) == URLType.EXTERNAL
    assert processor._determine_url_type("https://example.org", base_url) == URLType.EXTERNAL
    
    # Test asset URLs
    assert processor._determine_url_type("http://example.com/image.jpg", base_url) == URLType.ASSET
    assert processor._determine_url_type("http://example.com/style.css", base_url) == URLType.ASSET
    assert processor._determine_url_type("http://example.com/script.js", base_url) == URLType.ASSET
    
    # Test unknown URLs
    assert processor._determine_url_type("http://example.com/page.unknown", base_url) == URLType.INTERNAL
    assert processor._determine_url_type("", base_url) == URLType.UNKNOWN

def test_rate_limiter_wait():
    """Test rate limiter wait functionality."""
    # Test normal rate limiting
    limiter = RateLimiter(requests_per_second=10.0)
    start_time = time.time()
    
    # First request should not wait
    limiter.wait()
    first_duration = time.time() - start_time
    assert first_duration < 0.01  # Should be almost instant
    
    # Second request should wait
    limiter.wait()
    second_duration = time.time() - start_time
    assert 0.09 < second_duration < 0.11  # Should wait about 0.1 seconds
    
    # Test very low rate
    slow_limiter = RateLimiter(requests_per_second=1.0)
    start_time = time.time()
    slow_limiter.wait()
    slow_limiter.wait()
    duration = time.time() - start_time
    assert 0.9 < duration < 1.1  # Should wait about 1 second
    
    # Test very high rate
    fast_limiter = RateLimiter(requests_per_second=1000.0)
    start_time = time.time()
    for _ in range(10):
        fast_limiter.wait()
    duration = time.time() - start_time
    assert duration < 0.1  # Should be very quick

def test_url_processor_process_url():
    """Test URL processing method."""
    processor = URLProcessor()
    base_url = "http://example.com"
    
    # Test valid internal URL
    info = processor.process_url("http://example.com/page", base_url)
    assert info.is_valid
    assert info.normalized_url == "http://example.com/page"
    assert info.url_type == URLType.INTERNAL
    assert info.domain == "example.com"
    assert info.path == "/page"
    assert info.error_msg is None
    
    # Test valid external URL
    info = processor.process_url("https://other.com/page", base_url)
    assert info.is_valid
    assert info.normalized_url == "https://other.com/page"
    assert info.url_type == URLType.EXTERNAL
    assert info.domain == "other.com"
    assert info.path == "/page"
    
    # Test asset URL
    info = processor.process_url("http://example.com/image.jpg", base_url)
    assert info.is_valid
    assert info.url_type == URLType.ASSET
    
    # Test invalid URL
    info = processor.process_url("invalid://example.com", base_url)
    assert not info.is_valid
    assert info.url_type == URLType.UNKNOWN
    assert info.error_msg is not None
    
    # Test relative URL
    info = processor.process_url("/page", base_url)
    assert info.is_valid
    assert info.normalized_url == "http://example.com/page"
    assert info.url_type == URLType.INTERNAL

def test_timer_duration():
    """Test timer duration property."""
    timer = Timer("test_operation")
    
    # Test before entering context
    assert timer.duration is None
    
    # Test within context
    with timer as t:
        time.sleep(0.1)
        # Duration should be available but less than sleep time
        # (since we're checking before the context exit)
        assert 0 < t.duration < 0.1
    
    # Test after context
    assert 0.1 <= timer.duration <= 0.15
    
    # Test multiple operations
    with timer:
        time.sleep(0.1)
    # Should update duration
    assert 0.1 <= timer.duration <= 0.15
