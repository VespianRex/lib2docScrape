"""Tests for the DocumentationCrawler._should_crawl_url method."""

from unittest.mock import Mock

import pytest

from src.crawler.crawler import Crawler as DocumentationCrawler
from src.crawler.models import CrawlTarget
from src.utils.url.factory import create_url_info


class TestShouldCrawlUrl:
    """Tests for the _should_crawl_url method of DocumentationCrawler."""

    @pytest.fixture
    def setup_crawler(self):
        """Set up DocumentationCrawler instance."""
        crawler = DocumentationCrawler(content_processor=Mock(), quality_checker=Mock())
        return crawler

    def test_with_excluded_paths(self, setup_crawler):
        """Test URLs that match excluded paths."""
        crawler = setup_crawler
        target = CrawlTarget(url="http://internal.com")
        target.excluded_paths = ["/admin", "/private"]

        # Should not crawl excluded paths
        admin_url = create_url_info("http://internal.com/admin/settings")
        private_url = create_url_info("http://internal.com/private/data")
        public_url = create_url_info("http://internal.com/public/data")

        assert not crawler._should_crawl_url(admin_url, target)
        assert not crawler._should_crawl_url(private_url, target)
        assert crawler._should_crawl_url(public_url, target)

    def test_with_allowed_paths(self, setup_crawler):
        """Test URLs that match allowed paths."""
        crawler = setup_crawler
        target = CrawlTarget(url="http://internal.com")
        target.allowed_paths = ["/docs", "/api"]

        # Should only crawl allowed paths
        docs_url = create_url_info("http://internal.com/docs/guide")
        api_url = create_url_info("http://internal.com/api/v1")
        other_url = create_url_info("http://internal.com/other/section")

        assert crawler._should_crawl_url(docs_url, target)
        assert crawler._should_crawl_url(api_url, target)
        assert not crawler._should_crawl_url(other_url, target)

    def test_with_content_types(self, setup_crawler):
        """Test URLs with different content types."""
        crawler = setup_crawler
        target = CrawlTarget(url="http://internal.com")
        target.content_types = ["text/html"]

        # Note: _should_crawl_url doesn't actually check content types
        # Content type checking happens in _fetch_and_process_with_backend
        # So both URLs should pass the _should_crawl_url check
        html_url = create_url_info("http://internal.com/page.html")
        pdf_url = create_url_info("http://internal.com/document.pdf")

        # Both should pass _should_crawl_url since it doesn't check content types
        assert crawler._should_crawl_url(html_url, target)
        assert crawler._should_crawl_url(pdf_url, target)

    def test_external_urls(self, setup_crawler):
        """Test handling of external URLs."""
        crawler = setup_crawler
        target = CrawlTarget(url="http://internal.com")

        # Test with follow_external = False
        target.follow_external = False
        internal_url = create_url_info("http://internal.com/page")
        external_url = create_url_info("http://external.com/page")

        assert crawler._should_crawl_url(internal_url, target)
        assert not crawler._should_crawl_url(external_url, target)

        # Test with follow_external = True
        target.follow_external = True
        assert crawler._should_crawl_url(external_url, target)
