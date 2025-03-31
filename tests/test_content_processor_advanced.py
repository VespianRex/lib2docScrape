from src.utils.helpers import URLProcessor
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
        "http://example.com:-80": None  # Negative port
    }

    for url, expected in port_urls.items():
        result = processor.process_url(url)
        if expected is None:
            assert not result.is_valid
        else:
            assert result.is_valid
            assert result.normalized_url == expected
