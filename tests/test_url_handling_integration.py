import pytest
from unittest.mock import AsyncMock, MagicMock
from pytest_mock import MockerFixture
from src.utils.url.factory import create_url_info # Import the factory function
from src.utils.url import URLInfo, URLType # Use the modular implementation directly
from src.crawler import DocumentationCrawler, CrawlerConfig, CrawlTarget  # Import CrawlTarget
from src.backends.http_backend import HTTPBackend # Import HTTPBackend
from src.backends.base import CrawlResult  # Import CrawlResult

class TestURLIntegration:
    """Test integration of the new URLInfo implementation with other components."""

    @pytest.mark.asyncio # Mark test as async
    async def test_crawler_url_handling(self, mocker: MockerFixture):
        """Test that the crawler properly works with the new URLInfo implementation."""
        
        # Create our own mock session directly
        html_content = '<html><head><title>Test</title></head><body><a href="/page1">Link 1</a></body></html>'
        
        # Create mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {"content-type": "text/html"}
        mock_response.text = AsyncMock(return_value=html_content)
        # Set the URL explicitly rather than letting it be an AsyncMock
        mock_response.url = "https://example.com"
        
        # Create async context manager
        class AsyncContextManagerMock:
            async def __aenter__(self):
                return mock_response
                
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None
                
        # Create session mock
        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=AsyncContextManagerMock())
        mock_session.close = AsyncMock()
        
        # No need to patch ClientSession anymore as we're directly setting the session on the HTTPBackend

        # Create a crawler instance with a starting URL and basic config
        # Use a config that selects the default backend (crawl4ai) which uses aiohttp
        config = CrawlerConfig()
        
        # Create our own backend selector with explicit wildcard pattern for our test URL
        from src.backends.selector import BackendSelector, BackendCriteria
        from src.backends.http_backend import HTTPBackendConfig, HTTPBackend
        
        # Create a fresh backend selector
        backend_selector = BackendSelector()
        
        # Create HTTP backend with our mock session
        http_backend = HTTPBackend(HTTPBackendConfig())
        
        # Set the session directly to our mock (instead of letting it create one)
        http_backend.session = mock_session
        # Also patch the crawl method to ensure our mock is used
        http_backend.crawl = AsyncMock(return_value=CrawlResult(
            url="https://example.com",
            content={"html": html_content},
            metadata={"status": 200, "content-type": "text/html"},
            status=200
        ))
        # Also patch the crawl method to ensure our mock is used
        http_backend.crawl = AsyncMock(return_value=CrawlResult(
            url="https://example.com",
            content={"html": html_content},
            metadata={"status": 200, "content-type": "text/html"},
            status=200
        ))
        
        # Register the backend with wildcard criteria to ensure it matches our URL
        backend_selector.register_backend(
            "http_backend",
            http_backend,
            BackendCriteria(
                priority=100,
                content_types=["text/html"],
                url_patterns=["*"],  # Match all URLs
                max_load=0.8,
                min_success_rate=0.7
            )
        )
        
        # Create crawler with our customized backend selector
        crawler = DocumentationCrawler(
            config=config,
            backend_selector=backend_selector
        )

        # Start the crawl process (assuming crawl method exists and uses the backend)
        target_url = "https://example.com"
        crawl_target = CrawlTarget(url=target_url) # Create CrawlTarget object
        crawl_result = await crawler.crawl(
            target_url=crawl_target.url,
            depth=crawl_target.depth,
            follow_external=crawl_target.follow_external,
            content_types=crawl_target.content_types,
            exclude_patterns=crawl_target.exclude_patterns,
            required_patterns=crawl_target.required_patterns,
            max_pages=crawl_target.max_pages,
            allowed_paths=crawl_target.allowed_paths,
            excluded_paths=crawl_target.excluded_paths
        ) # Pass the CrawlTarget object and capture result

        # Verify that the mock HTTP request was made via the session instance
        mock_session.get.assert_called_once()
        call_args, call_kwargs = mock_session.get.call_args
        # The crawler normalizes the URL before fetching, so compare against the normalized version
        expected_normalized_url = "https://example.com" # Root path normalization removes trailing slash
        assert call_args[0] == expected_normalized_url # Check the URL argument

        # Check results from the returned CrawlResult object
        assert crawl_result is not None
        assert crawl_result.stats.successful_crawls == 1
        assert len(crawl_result.documents) == 1
        document = crawl_result.documents[0]
        # The document URL should store the normalized URL
        assert document['url'] == expected_normalized_url # Compare against corrected normalized URL
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
            "data:text/html,<script>alert('XSS')</script>"
        ]

        # Verify none of these URLs are considered valid
        for url in malicious_urls:
            # Use the factory function
            info = create_url_info(url)
            assert not info.is_valid, f"URL should be invalid: {url}"
            assert info.error_message, "Error message should be provided"