from src.utils.url.factory import create_url_info  # Import the factory function


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
        "http://example.com:80/": "http://example.com/",  # Default HTTP port removed, trailing slash kept
        "http://example.com:-80": None,  # Negative port
    }

    for url, expected in port_urls.items():
        # Use the factory function to create the URLInfo instance
        url_info = create_url_info(url)  # base_url is not needed for these tests
        # For invalid URLs where expected is None, check if is_valid is False
        if expected is None:
            assert not url_info.is_valid, f"URL '{url}' should be invalid."
        else:
            assert url_info.is_valid, f"URL '{url}' should be valid."
            assert (
                url_info.normalized_url == expected
            ), f"URL '{url}' normalized incorrectly. Expected: '{expected}', Got: '{url_info.normalized_url}'"
