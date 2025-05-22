import pytest
from src.utils.url.factory import create_url_info # Import the factory function
from src.utils.url import URLInfo # Keep URLInfo import for type hinting if needed elsewhere

class TestURLNormalizationIDN:
    """Test URL normalization specifically for Internationalized Domain Names (IDN)."""

    @pytest.mark.parametrize("input_url, expected_normalized_url, description", [
        # Basic IDN
        ("https://例子.com", "https://xn--fsqu00a.com", "Simple Chinese IDN"), # Removed trailing slash
        ("https://bücher.de/", "https://xn--bcher-kva.de/", "German IDN with umlaut"), # Keep slash as input had it
        ("http://उदाहरण.परीक्षा", "http://xn--p1b6ci4b4b3a.xn--11b5bs3a9aj6g", "Hindi IDN"), # Removed trailing slash

        # IDN with path and query
        ("https://例子.com/path?query=测试", "https://xn--fsqu00a.com/path?query=%E6%B5%8B%E8%AF%95", "Chinese IDN with path and query"),

        # Mixed ASCII and IDN
        ("https://subdomain.例子.com", "https://subdomain.xn--fsqu00a.com", "IDN in TLD part"), # Removed trailing slash
        ("https://例子.subdomain.com", "https://xn--fsqu00a.subdomain.com", "IDN in subdomain part"), # Removed trailing slash

        # Punycode input (should remain punycode)
        ("https://xn--fsqu00a.com", "https://xn--fsqu00a.com", "Punycode input should not change"), # Removed trailing slash

        # URLs that might fail IDNA encoding (e.g., invalid characters)
        # Note: The behavior might depend on the underlying IDNA library's strictness.
        # Assuming strict validation catches these.
        # ("https://invalid_char!.com", None, "Invalid characters for IDNA"), # Behavior depends on implementation

        # Uppercase IDN
        ("https://例子.COM", "https://xn--fsqu00a.com", "Uppercase IDN TLD"), # Removed trailing slash
    ])
    def test_idn_normalization(self, input_url, expected_normalized_url, description):
        """Test that IDN domains are correctly normalized to Punycode and query params encoded."""
        # Use the factory function to create the URLInfo instance
        info = create_url_info(input_url)
        # IDNA normalization happens during initialization
        # We expect the `normalized_url` attribute to hold the Punycode version.
        # Assuming the implementation stores the normalized form.
        assert info.normalized_url == expected_normalized_url, f"Failed check: {description} ({input_url})"
        assert info.is_valid, f"URL should be valid after normalization: {description} ({input_url})"

    # Add tests for potential errors during IDNA processing if the library raises specific exceptions
    # def test_invalid_idn_handling(self):
    #     with pytest.raises(SomeIDNAError):
    #         # Use the factory function for invalid URL creation as well
    #         create_url_info("https://invalid--domain.com") # Example invalid IDN format
