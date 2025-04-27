from src.utils.url import URLInfo # Corrected import path

def test_url_processor_port_handling():
    """Test URLInfo port handling during initialization."""
    # No need to instantiate URLProcessor anymore

    port_urls = {
        "http://example.com:80": "http://example.com",  # Default HTTP port removed, no trailing slash
        "https://example.com:443": "https://example.com",  # Default HTTPS port removed, no trailing slash
        "http://example.com:8080": "http://example.com:8080",  # Non-default port kept, no trailing slash
        "https://example.com:8443": "https://example.com:8443",  # Non-default port kept, no trailing slash
        "http://example.com:": "http://example.com",  # Empty port removed, no trailing slash
        "http://example.com:abc": None,  # Invalid port
        "http://example.com:65536": None,  # Port number too high
        "http://example.com:80/": "http://example.com/", # Default HTTP port removed, trailing slash kept
        "http://example.com:-80": None  # Negative port
    }

    for url, expected in port_urls.items():
        # Instantiate URLInfo directly
        url_info = URLInfo(url) # base_url is not needed for these tests
        assert url_info.normalized_url == expected, f"URL '{url}' normalized incorrectly. Expected: '{expected}', Got: '{url_info.normalized_url}'"
