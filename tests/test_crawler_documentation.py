"""Tests for DocumentationCrawler class."""

import asyncio
from unittest.mock import MagicMock

from src.backends.selector import BackendSelector
from src.crawler import CrawlTarget
from src.crawler import DocumentationCrawler as CrawlerAlias
from src.crawler.models import CrawlConfig as CrawlerConfig
from src.organizers.doc_organizer import DocumentOrganizer
from src.processors.content_processor import ContentProcessor
from src.processors.quality_checker import QualityChecker
from src.utils.search import DuckDuckGoSearch
from src.utils.url.factory import create_url_info


class TestDocumentationCrawler:
    """Tests for DocumentationCrawler."""

    def test_documentation_crawler_init_defaults(self):
        """Test 5.1: Test initializing DocumentationCrawler with default parameters."""
        # Initialize with defaults
        crawler = CrawlerAlias()

        # Check that config was defaulted correctly
        assert crawler.config is not None
        assert isinstance(crawler.config, CrawlerConfig)

        # Check default values defined in CrawlerConfig
        assert crawler.config.requests_per_second == 2.0  # 1.0 / 0.5 = 2.0
        assert crawler.config.max_retries == 3
        assert crawler.config.user_agent == "lib2docScrape/1.0"

        # Check that components were initialized correctly
        assert crawler.backend_selector is not None
        assert isinstance(crawler.backend_selector, BackendSelector)
        assert crawler.content_processor is not None
        assert isinstance(crawler.content_processor, ContentProcessor)
        assert crawler.quality_checker is not None
        assert isinstance(crawler.quality_checker, QualityChecker)
        assert crawler.document_organizer is not None
        assert isinstance(crawler.document_organizer, DocumentOrganizer)

        # Check that HTTP backend was registered
        assert "http_backend" in crawler.backend_selector._backends

        # Check that internal state was initialized correctly
        assert crawler._crawled_urls == set()
        assert isinstance(crawler._processing_semaphore, asyncio.Semaphore)
        assert crawler.client_session is None

        # Check DuckDuckGo integration (enabled by default)
        assert crawler.duckduckgo is not None
        assert isinstance(crawler.duckduckgo, DuckDuckGoSearch)

    def test_documentation_crawler_init_custom_config(self):
        """Test 5.2: Test initializing DocumentationCrawler with custom configuration."""
        # Create custom config
        config = CrawlerConfig(
            concurrent_requests=5,
            rate_limit=0.5,  # 1.0 / 0.5 = 2.0 requests per second
            max_retries=2,
            request_timeout=15.0,
            user_agent="Custom User Agent",
            use_duckduckgo=False,
            duckduckgo_max_results=20,
        )

        # Initialize with custom config
        crawler = CrawlerAlias(config=config)

        # Check that config was applied correctly
        assert crawler.config == config
        assert crawler.config.requests_per_second == 2.0
        assert crawler.config.max_retries == 2
        assert crawler.config.request_timeout == 15.0
        assert crawler.config.user_agent == "Custom User Agent"

        # Check that internal state reflects custom config
        assert isinstance(crawler._processing_semaphore, asyncio.Semaphore)

        # Check DuckDuckGo integration (disabled in custom config)
        assert crawler.duckduckgo is None

    def test_documentation_crawler_init_custom_components(self):
        """Test 5.3: Test initializing DocumentationCrawler with custom components."""
        # Create mock components
        mock_backend_selector = MagicMock(spec=BackendSelector)
        mock_content_processor = MagicMock(spec=ContentProcessor)
        mock_quality_checker = MagicMock(spec=QualityChecker)
        mock_document_organizer = MagicMock(spec=DocumentOrganizer)
        mock_loop = MagicMock(spec=asyncio.AbstractEventLoop)
        mock_backend = MagicMock()

        # Initialize with custom components
        crawler = CrawlerAlias(
            backend_selector=mock_backend_selector,
            content_processor=mock_content_processor,
            quality_checker=mock_quality_checker,
            document_organizer=mock_document_organizer,
            loop=mock_loop,
            backend=mock_backend,
        )

        # Check that components were used
        assert crawler.backend_selector is mock_backend_selector
        assert crawler.content_processor is mock_content_processor
        assert crawler.quality_checker is mock_quality_checker
        assert crawler.document_organizer is mock_document_organizer
        assert crawler.loop is mock_loop
        assert crawler.backend is mock_backend

        # Verify HTTP backend registration was called
        mock_backend_selector.register_backend.assert_called()

    def test_find_links_recursive(self):
        """Test 6.1: Test _find_links_recursive method with various structure elements."""
        crawler = CrawlerAlias()

        # Test with empty structure
        assert crawler._find_links_recursive({}) == []
        assert crawler._find_links_recursive([]) == []

        # Test with a simple link
        link_element = {
            "type": "link",
            "href": "https://example.com",
            "text": "Example",
        }
        assert crawler._find_links_recursive(link_element) == ["https://example.com"]

        # Test with a link_inline type
        inline_link = {
            "type": "link_inline",
            "href": "https://example.org",
            "text": "Example Org",
        }
        assert crawler._find_links_recursive(inline_link) == ["https://example.org"]

        # Test with a nested structure containing links
        nested_structure = {
            "type": "document",
            "elements": [
                {
                    "type": "paragraph",
                    "children": [
                        {"type": "text", "value": "Some text"},
                        {
                            "type": "link_inline",
                            "href": "https://example.com/docs",
                            "text": "Docs",
                        },
                    ],
                },
                {"type": "link", "href": "https://example.com/api", "text": "API"},
            ],
        }

        links = crawler._find_links_recursive(nested_structure)
        assert len(links) == 2
        assert "https://example.com/docs" in links
        assert "https://example.com/api" in links

        # Test with multiple levels of nesting and lists
        complex_structure = {
            "type": "document",
            "sections": [
                {
                    "type": "section",
                    "title": "Section 1",
                    "content": [
                        {
                            "type": "paragraph",
                            "links": [
                                {
                                    "type": "link",
                                    "href": "https://example.com/section1",
                                    "text": "Section 1",
                                }
                            ],
                        }
                    ],
                },
                {
                    "type": "navigation",
                    "items": [
                        {
                            "type": "link",
                            "href": "https://example.com/nav1",
                            "text": "Nav 1",
                        },
                        {
                            "type": "link",
                            "href": "https://example.com/nav2",
                            "text": "Nav 2",
                        },
                    ],
                },
            ],
        }

        links = crawler._find_links_recursive(complex_structure)
        assert len(links) == 3
        assert "https://example.com/section1" in links
        assert "https://example.com/nav1" in links
        assert "https://example.com/nav2" in links

    def test_should_crawl_url(self):
        """Test 7.1-7.11: Test _should_crawl_url method with various URL types."""
        crawler = CrawlerAlias()

        # Create a basic target
        target = CrawlTarget(url="http://internal.com")

        # Test 7.1: Invalid URL
        invalid_url_info = create_url_info("htp://badscheme.com")
        assert crawler._should_crawl_url(invalid_url_info, target) is False

        # Test 7.2: Already crawled URL
        already_crawled_url = "http://example.com/page1"
        already_crawled_url_info = create_url_info(already_crawled_url)
        crawler._crawled_urls.add(already_crawled_url_info.normalized_url)
        assert crawler._should_crawl_url(already_crawled_url_info, target) is False

        # Test 7.3: Non-HTTP/S/File Scheme
        ftp_url_info = create_url_info("ftp://example.com/file.txt")
        assert crawler._should_crawl_url(ftp_url_info, target) is False

        # Test 7.4: External URL, follow_external=False
        external_target = CrawlTarget(url="http://internal.com", follow_external=False)
        external_url_info = create_url_info("http://external.com")
        assert crawler._should_crawl_url(external_url_info, external_target) is False

        # Test 7.4b: Subdomain with follow_external=False
        # external_target is CrawlTarget(url="http://internal.com", follow_external=False)
        subdomain_url_info = create_url_info("http://sub.internal.com/page")
        # This assertion depends on the definition of "internal".
        # If subdomains sharing the same registered domain are considered internal:
        assert crawler._should_crawl_url(subdomain_url_info, external_target) is True

        # Test cross-scheme but same domain with follow_external=False
        https_url_info = create_url_info("https://internal.com")
        assert (
            crawler._should_crawl_url(https_url_info, external_target) is True
        )  # http->https upgrade allowed

        # Test 7.5: External URL, follow_external=True
        follow_external_target = CrawlTarget(
            url="http://internal.com", follow_external=True
        )
        external_url_info = create_url_info("http://external.com")
        assert (
            crawler._should_crawl_url(external_url_info, follow_external_target) is True
        )

        # Test 7.6: Internal URL (same registered domain)
        internal_url_info = create_url_info("http://internal.com/docs")
        assert crawler._should_crawl_url(internal_url_info, target) is True

        # Test 7.6b: Internal URL with follow_external=False explicitly
        internal_only_target = CrawlTarget(
            url="http://internal.com", follow_external=False
        )
        # internal_url_info is "http://internal.com/docs" from Test 7.6
        assert (
            crawler._should_crawl_url(internal_url_info, internal_only_target) is True
        )

        # Test 7.7: Exclude Patterns
        exclude_pattern_target = CrawlTarget(
            url="http://example.com", exclude_patterns=[".*\\.pdf$", ".*\\.zip$"]
        )
        pdf_url_info = create_url_info("http://example.com/doc.pdf")
        assert crawler._should_crawl_url(pdf_url_info, exclude_pattern_target) is False
        html_url_info = create_url_info("http://example.com/doc.html")
        assert crawler._should_crawl_url(html_url_info, exclude_pattern_target) is True

        # Test 7.8: Required Patterns
        required_pattern_target = CrawlTarget(
            url="http://example.com", required_patterns=[".*\\.html$", ".*\\.md$"]
        )
        text_url_info = create_url_info("http://example.com/doc.txt")
        assert (
            crawler._should_crawl_url(text_url_info, required_pattern_target) is False
        )
        html_url_info = create_url_info("http://example.com/doc.html")
        assert crawler._should_crawl_url(html_url_info, required_pattern_target) is True

        # Test 7.8b: Interaction of exclude and required patterns
        # Assuming exclude patterns take precedence over required patterns
        conflicting_target = CrawlTarget(
            url="http://example.com",
            exclude_patterns=[".*\\.html$"],
            required_patterns=[".*\\.html$", ".*\\.md$"],
        )
        html_url_info_conflict = create_url_info("http://example.com/doc.html")
        # This assertion depends on the implemented precedence logic.
        # If excludes take precedence:
        assert (
            crawler._should_crawl_url(html_url_info_conflict, conflicting_target)
            is False
        )

        # Test 7.9: Allowed Paths
        allowed_paths_target = CrawlTarget(
            url="http://example.com", allowed_paths=["/docs", "/api"]
        )
        docs_url_info = create_url_info("http://example.com/docs/guide.html")
        assert crawler._should_crawl_url(docs_url_info, allowed_paths_target) is True
        blog_url_info = create_url_info("http://example.com/blog/post.html")
        assert crawler._should_crawl_url(blog_url_info, allowed_paths_target) is False

        # Test 7.9b: Empty allowed_paths list
        empty_allowed_paths_target = CrawlTarget(
            url="http://example.com",
            allowed_paths=[],  # Assuming empty list means no path restriction from this rule
        )
        any_path_url_info = create_url_info("http://example.com/any/path.html")
        assert (
            crawler._should_crawl_url(any_path_url_info, empty_allowed_paths_target)
            is True
        )

        # Test 7.10: Excluded Paths
        excluded_paths_target = CrawlTarget(
            url="http://example.com", excluded_paths=["/private", "/admin"]
        )
        public_url_info = create_url_info("http://example.com/docs/guide.html")
        assert crawler._should_crawl_url(public_url_info, excluded_paths_target) is True
        private_url_info = create_url_info("http://example.com/private/config.html")
        assert (
            crawler._should_crawl_url(private_url_info, excluded_paths_target) is False
        )

        # Test 7.11: File Scheme URLs
        file_target = CrawlTarget(url="file:///home/docs")
        file_url_info = create_url_info("file:///home/docs/guide.html")
        assert crawler._should_crawl_url(file_url_info, file_target) is True
        http_url_info = create_url_info("http://example.com")
        assert (
            crawler._should_crawl_url(http_url_info, file_target) is False
        )  # Different scheme

        # Test 7.11b: File URL outside base path
        outside_file_url_info = create_url_info("file:///other/docs/another.html")
        assert crawler._should_crawl_url(outside_file_url_info, file_target) is False
