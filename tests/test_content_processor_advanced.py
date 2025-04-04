from src.utils.url_info import URLInfo # Import the new class

def test_url_processor_port_handling():
    """Test URLInfo port handling during initialization."""
    # No need to instantiate URLProcessor anymore

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
        # Instantiate URLInfo directly
        url_info = URLInfo(url) # base_url is not needed for these tests
        if expected is None:
            # Check if invalid and potentially check error message
            assert not url_info.is_valid, f"URL '{url}' should be invalid but was valid."
            # Optional: Check specific error message if needed
            # assert "Invalid port" in url_info.error_message, f"URL '{url}' failed for wrong reason: {url_info.error_message}"
        else:
            # Check if valid and compare normalized URL
            assert url_info.is_valid, f"URL '{url}' should be valid but was invalid: {url_info.error_message}"
            assert url_info.normalized_url == expected, f"URL '{url}' normalized incorrectly. Expected: '{expected}', Got: '{url_info.normalized_url}'"
