import pytest

from src.crawler import CrawlTarget
from src.utils.url import URLType  # Use the modular implementation directly
from src.utils.url.factory import create_url_info  # Import the factory function

# Mark all tests in this file as slow integration tests
pytestmark = [pytest.mark.slow, pytest.mark.integration]


class TestURLIntegration:
    """Test integration of the new URLInfo implementation with other components."""

    def test_crawler_url_handling(self):
        """Test that the crawler properly works with the new URLInfo implementation."""

        # Test URL normalization and validation integration
        # Test that URLs are properly normalized and validated
        test_url = "https://example.com/"
        url_info = create_url_info(test_url)

        # Verify URL normalization works
        assert url_info.is_valid
        assert (
            url_info.normalized_url == "https://example.com/"
        )  # Trailing slash preserved for root

        # Test that the crawler config accepts valid URLs
        crawl_target = CrawlTarget(url=url_info.normalized_url)

        # Verify the target URL is properly set
        assert crawl_target.url == "https://example.com/"

        # Test URL type classification
        assert url_info.url_type.name == "EXTERNAL"  # No base URL provided

        # Test with a base URL
        base_url = "https://example.com/docs/"
        relative_url = "/api/reference"
        url_info_with_base = create_url_info(relative_url, base_url=base_url)

        assert url_info_with_base.is_valid
        assert url_info_with_base.normalized_url == "https://example.com/api/reference"
        assert url_info_with_base.url_type.name == "INTERNAL"

    def test_url_type_classification(self):
        """Test URL type classification in a real-world scenario."""
        base_url = "https://example.com/docs/index.html"

        # Internal URLs (same domain)
        internal_urls = [
            "https://example.com/about",
            "/contact",  # Relative URL
            "page.html",  # Relative URL
            "https://example.com/docs/api?version=2",
        ]

        # External URLs (different domain)
        external_urls = [
            "https://github.com",
            "https://api.example.org",
            "http://example.com",  # Different scheme
        ]

        # Verify internal URL classification
        for url in internal_urls:
            # Use the factory function
            info = create_url_info(url, base_url=base_url)
            assert info.url_type == URLType.INTERNAL, f"Expected {url} to be internal"

        # Verify external URL classification
        for url in external_urls:
            # Use the factory function
            info = create_url_info(url, base_url=base_url)
            assert info.url_type == URLType.EXTERNAL, f"Expected {url} to be external"

    def test_url_security_validation(self):
        """Test security validation in an integration context."""
        # Create a set of potentially malicious URLs
        malicious_urls = [
            "javascript:alert('XSS')",
            "https://example.com/<script>alert('XSS')</script>",
            "https://example.com/page?id=1' OR '1'='1",
            "https://example.com/../../etc/passwd",
            "data:text/html,<script>alert('XSS')</script>",
        ]

        # Verify none of these URLs are considered valid
        for url in malicious_urls:
            # Use the factory function
            info = create_url_info(url)
            assert not info.is_valid, f"URL should be invalid: {url}"
            assert info.error_message, "Error message should be provided"
