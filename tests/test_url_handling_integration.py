import pytest
from unittest.mock import AsyncMock, patch # Import patch and AsyncMock
from unittest.mock import AsyncMock, patch # Import patch and AsyncMock
from src.utils.url import URLInfo, URLType # Use the modular implementation directly
from src.crawler import DocumentationCrawler, CrawlerConfig, CrawlTarget  # Import CrawlTarget

class TestURLIntegration:
    """Test integration of the new URLInfo implementation with other components."""
    
    @pytest.mark.asyncio # Mark test as async
    @patch('aiohttp.ClientSession.get', new_callable=AsyncMock) # Patch the correct async method
    async def test_crawler_url_handling(self, mock_get, mocker): # Add mock_get parameter
        """Test that the crawler properly works with the new URLInfo implementation."""

        # Configure the mock aiohttp response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.url = "https://example.com" # Set a URL for the response mock
        mock_response.text.return_value = '<html><head><title>Test</title></head><body><a href="/page1">Link 1</a></body></html>'
        mock_response.headers = {'content-type': 'text/html'}
        # Make the mock response usable as an async context manager
        mock_response.__aenter__.return_value = mock_response
        mock_response.__aexit__.return_value = None
        mock_get.return_value = mock_response # Set the return value for session.get

        # Create a crawler instance with a starting URL and basic config
        # Use a config that selects the default backend (crawl4ai) which uses aiohttp
        config = CrawlerConfig()
        crawler = DocumentationCrawler(config=config) # Pass config

        # Start the crawl process (assuming crawl method exists and uses the backend)
        target_url = "https://example.com"
        crawl_target = CrawlTarget(url=target_url) # Create CrawlTarget object
        crawl_result = await crawler.crawl(crawl_target) # Pass the CrawlTarget object and capture result

        # Verify crawler initialized correctly with our URLInfo (base_url is set during crawl)
        # Base URL is set internally, check if it was set correctly after crawl
        # Base URL is handled internally by URLInfo and during processing,
        # not stored directly on the crawler instance. Removed assertions for crawler.base_url.

        # Verify that the mock HTTP request was made
        mock_get.assert_called_once()
        # Check the URL passed to the mock_get call
        call_args, call_kwargs = mock_get.call_args
        assert call_args[0] == target_url # Check the URL argument

        # Check results from the returned CrawlResult object
        assert crawl_result is not None
        assert crawl_result.stats.successful_crawls == 1
        assert len(crawl_result.documents) == 1
        document = crawl_result.documents[0]
        assert document['url'] == target_url
        # Check status from the document metadata if available, or assume 200 if processed
        # assert document['metadata'].get('status_code', 200) == 200 # Assuming status is in metadata
        assert "Link 1" in document['content'].get("formatted_content", "")

        # Cleanup crawler resources if necessary (e.g., close session)
        await crawler.cleanup() # Use the correct cleanup method name
    
    def test_url_type_classification(self):
        """Test URL type classification in a real-world scenario."""
        base_url = "https://example.com/docs/index.html"
        
        # Internal URLs (same domain)
        internal_urls = [
            "https://example.com/about",
            "/contact",  # Relative URL
            "page.html",  # Relative URL
            "https://example.com/docs/api?version=2"
        ]
        
        # External URLs (different domain)
        external_urls = [
            "https://github.com",
            "https://api.example.org",
            "http://example.com"  # Different scheme
        ]
        
        # Verify internal URL classification
        for url in internal_urls:
            info = URLInfo(url, base_url=base_url)
            assert info.url_type == URLType.INTERNAL, f"Expected {url} to be internal"
        
        # Verify external URL classification
        for url in external_urls:
            info = URLInfo(url, base_url=base_url)
            assert info.url_type == URLType.EXTERNAL, f"Expected {url} to be external"
    
    def test_url_security_validation(self):
        """Test security validation in an integration context."""
        # Create a set of potentially malicious URLs
        malicious_urls = [
            "javascript:alert('XSS')",
            "https://example.com/<script>alert('XSS')</script>",
            "https://example.com/page?id=1' OR '1'='1",
            "https://example.com/../../etc/passwd",
            "data:text/html,<script>alert('XSS')</script>"
        ]
        
        # Verify none of these URLs are considered valid
        for url in malicious_urls:
            info = URLInfo(url)
            assert not info.is_valid, f"URL should be invalid: {url}"
            assert info.error_message, "Error message should be provided"