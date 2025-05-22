import pytest
from src.utils.url.factory import create_url_info # Import the factory function
from src.utils.url import URLInfo, URLType # Keep URLInfo and URLType imports

class TestURLClassificationSubdomain:
    """Test URL classification edge cases involving subdomains."""

    @pytest.mark.parametrize("url, base_url, expected_type, description", [
        # Standard internal link within the same subdomain
        ("https://docs.example.com/api/v1", "https://docs.example.com/", URLType.INTERNAL, "Same subdomain, internal link"),
        ("/faq", "https://docs.example.com/", URLType.INTERNAL, "Relative link, same subdomain"),

        # Link to a different subdomain of the same parent domain
        ("https://blog.example.com", "https://docs.example.com/", URLType.INTERNAL, "Different subdomain, same parent domain - treated as internal"),
        ("//blog.example.com/latest", "https://docs.example.com/", URLType.INTERNAL, "Protocol-relative link to different subdomain"),

        # Link from a subdomain to the parent domain
        ("https://example.com/about", "https://docs.example.com/", URLType.INTERNAL, "Link from subdomain to parent domain"),

        # Link from parent domain to a subdomain
        ("https://docs.example.com/intro", "https://example.com/", URLType.INTERNAL, "Link from parent to known subdomain - treated as internal"), # Assuming subdomains are considered internal to the parent

        # Edge case: www vs non-www (depends on strictness, often treated as same logical site but technically different hosts)
        ("https://www.example.com", "https://example.com/", URLType.INTERNAL, "www vs non-www, same domain - often internal"), # Behavior might vary based on config
        ("https://example.com", "https://www.example.com/", URLType.INTERNAL, "non-www vs www, same domain - often internal"), # Behavior might vary based on config

        # Deeply nested subdomains
        ("https://api.internal.dev.example.com", "https://docs.example.com/", URLType.INTERNAL, "Deeply nested different subdomain"),
        ("https://api.internal.dev.example.com/status", "https://api.internal.dev.example.com/", URLType.INTERNAL, "Internal link within deeply nested subdomain"),

        # Relative link potentially crossing subdomain boundary (should resolve within base_url's domain)
        ("../marketing/campaign", "https://docs.example.com/team/", URLType.INTERNAL, "Relative path resolving within the base domain"), # Resolves to docs.example.com/marketing/campaign
    ])
    def test_subdomain_classification(self, url, base_url, expected_type, description):
        """Test internal/external classification with various subdomain scenarios."""
        # Use the factory function to create the URLInfo instance
        info = create_url_info(url, base_url=base_url)
        assert info.is_valid, f"URL should be valid: {description} ({url})"
        assert info.url_type == expected_type, f"Classification failed: {description} ({url} relative to {base_url})"

    # Consider adding tests based on a configuration option, e.g., `treat_subdomains_as_internal`
    # def test_subdomain_classification_with_config(self):
    #     # Assume a config setting allows treating all subdomains of example.com as internal
    #     # Use the factory function
    #     info_external = create_url_info("https://blog.example.com", base_url="https://docs.example.com/")
    #     assert info_external.url_type == URLType.EXTERNAL # Default behavior
    #
    #     # Hypothetical config change
    #     # url_config.treat_subdomains_as_internal = True
    #     # Use the factory function
    #     info_internal = create_url_info("https://blog.example.com", base_url="https://docs.example.com/") # Pass config or modify global state
    #     # assert info_internal.url_type == URLType.INTERNAL # Behavior with config