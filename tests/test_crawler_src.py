"""Tests for the DocumentationCrawler class from src.crawler."""

from unittest.mock import Mock

import pytest

from src.crawler.crawler import Crawler as DocumentationCrawler
from src.crawler.models import CrawlTarget
from src.utils.url.factory import create_url_info

# Enable asyncio support
pytest_plugins = ["pytest_asyncio"]


class TestCrawlerSrc:
    """Test class for testing DocumentationCrawler functionality."""

    @pytest.fixture
    def setup_crawler(self):
        """Set up crawler with mocks."""
        crawler = DocumentationCrawler(content_processor=Mock(), quality_checker=Mock())
        return crawler

    def test_find_links_recursive(self, setup_crawler):
        """Test find_links_recursive method."""
        crawler = setup_crawler

        # Test case with empty structure
        structure = []
        links = crawler._find_links_recursive(structure)
        assert links == []

        # Test case with structure containing links
        structure = [
            {"type": "link", "url": "/api", "text": "API"},
            {
                "type": "section",
                "children": [{"type": "link", "url": "/docs", "text": "Docs"}],
            },
            {"type": "text", "content": "Some text"},
        ]

        links = crawler._find_links_recursive(structure)
        assert set(links) == {"/api", "/docs"}

        # Test case with absolute URLs
        structure = [
            {"type": "link", "url": "https://external.com/api", "text": "External API"}
        ]

        links = crawler._find_links_recursive(structure)
        assert links == ["https://external.com/api"]

        # Test case with nested sections
        structure = [
            {
                "type": "section",
                "children": [
                    {
                        "type": "section",
                        "children": [
                            {"type": "link", "url": "/deep", "text": "Deep Link"}
                        ],
                    }
                ],
            }
        ]

        links = crawler._find_links_recursive(structure)
        assert len(links) == 1
        assert "/deep" in links

    def test_should_crawl_url(self, setup_crawler):
        """Test _should_crawl_url method with various URL types."""
        crawler = setup_crawler

        # Create a basic target
        target = CrawlTarget(url="http://internal.com")

        # Test: Invalid URL
        invalid_url_info = create_url_info("htp://badscheme.com")
        assert not crawler._should_crawl_url(invalid_url_info, target)

        # Test: Excluded pattern
        target.exclude_patterns = ["/admin/"]
        admin_url = create_url_info("http://internal.com/admin/settings")
        assert not crawler._should_crawl_url(admin_url, target)

        # Test: Required pattern match
        target.exclude_patterns = []
        target.required_patterns = ["/docs/"]
        docs_url = create_url_info("http://internal.com/docs/api")
        not_docs_url = create_url_info("http://internal.com/api")
        assert crawler._should_crawl_url(docs_url, target)
        assert not crawler._should_crawl_url(not_docs_url, target)

        # Test: External URL with follow_external=False
        target.required_patterns = []
        target.follow_external = False
        external_url = create_url_info("http://external.com/page")
        assert not crawler._should_crawl_url(external_url, target)

        # Test: External URL with follow_external=True
        target.follow_external = True
        assert crawler._should_crawl_url(external_url, target)
