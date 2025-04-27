import pytest
from src.utils.url import URLInfo

class TestURLNormalizationIDN:
    """Test URL normalization specifically for Internationalized Domain Names (IDN)."""

    @pytest.mark.parametrize("input_url, expected_normalized_url, description", [
        # Basic IDN
        ("https://例子.com", "https://xn--fsqu00a.com/", "Simple Chinese IDN"),
        ("https://bücher.de/", "https://xn--bcher-kva.de/", "German IDN with umlaut"),
        ("http://उदाहरण.परीक्षा", "http://xn--p1b6ci4b4b3a.xn--11b5bs3a9aj6g/", "Hindi IDN"),

        # IDN with path and query
        ("https://例子.com/path?query=测试", "https://xn--fsqu00a.com/path?query=测试", "Chinese IDN with path and query"),

        # Mixed ASCII and IDN
        ("https://subdomain.例子.com", "https://subdomain.xn--fsqu00a.com/", "IDN in TLD part"),
        ("https://例子.subdomain.com", "https://xn--fsqu00a.subdomain.com/", "IDN in subdomain part"),

        # Punycode input (should remain punycode)
        ("https://xn--fsqu00a.com", "https://xn--fsqu00a.com/", "Punycode input should not change"),

        # URLs that might fail IDNA encoding (e.g., invalid characters)
        # Note: The behavior might depend on the underlying IDNA library's strictness.
        # Assuming strict validation catches these.
        # ("https://invalid_char!.com", None, "Invalid characters for IDNA"), # Behavior depends on implementation

        # Uppercase IDN
        ("https://例子.COM", "https://xn--fsqu00a.com/", "Uppercase IDN TLD"),
    ])
    def test_idn_normalization(self, input_url, expected_normalized_url, description):
        """Test that IDN domains are correctly normalized to Punycode."""
        info = URLInfo(input_url)
        # IDNA normalization happens during initialization
        # We expect the `normalized_url` attribute to hold the Punycode version.
        # Assuming the implementation stores the normalized form.
        assert info.normalized_url == expected_normalized_url, f"Failed check: {description} ({input_url})"
        assert info.is_valid, f"URL should be valid after normalization: {description} ({input_url})"

    # Add tests for potential errors during IDNA processing if the library raises specific exceptions
    # def test_invalid_idn_handling(self):
    #     with pytest.raises(SomeIDNAError):
    #         URLInfo("https://invalid--domain.com") # Example invalid IDN format