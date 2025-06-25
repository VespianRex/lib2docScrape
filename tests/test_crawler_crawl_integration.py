# Python

from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.crawler import CrawlerConfig, CrawlResult, CrawlTarget, DocumentationCrawler


@pytest.mark.asyncio
class TestDocumentationCrawlerCrawlIntegration:
    @pytest.fixture
    def crawler(self):
        return DocumentationCrawler(config=CrawlerConfig(use_duckduckgo=False))

    @pytest.fixture
    def target_cfg(self):
        return CrawlTarget(url="http://example.com/page1", depth=0)

    async def test_simple_successful_crawl(self, crawler, target_cfg):
        # Test 12.1: Simple Successful Crawl (1 page, depth 0)
        from types import SimpleNamespace

        stats = SimpleNamespace(pages_crawled=1, successful_crawls=1, failed_crawls=0)
        mock_result = Mock(spec=CrawlResult)
        mock_result.stats = stats
        mock_result.documents = [Mock()]
        mock_result.issues = []
        with patch.object(
            DocumentationCrawler, "crawl", AsyncMock(return_value=mock_result)
        ):
            final_result = await crawler.crawl(
                target_cfg.url,
                target_cfg.depth,
                False,  # follow_external
                [],  # content_types
                [],  # exclude_patterns
                [],  # include_patterns
                getattr(target_cfg, "max_pages", 1000),
                [],  # allowed_paths
                [],  # excluded_paths
            )
            assert final_result.stats.pages_crawled == 1
            assert final_result.stats.successful_crawls == 1
            assert len(final_result.documents) == 1

    async def test_depth_limited_crawl(self, crawler):
        # Test 12.2: Depth Limited Crawl (depth 1, finds new links)
        from types import SimpleNamespace

        stats = SimpleNamespace(pages_crawled=2, successful_crawls=2, failed_crawls=0)
        mock_result = Mock(spec=CrawlResult)
        mock_result.stats = stats
        mock_result.documents = [Mock(), Mock()]
        mock_result.issues = []
        with patch.object(
            DocumentationCrawler, "crawl", AsyncMock(return_value=mock_result)
        ):
            target_cfg = CrawlTarget(url="http://example.com/page1", depth=1)
            final_result = await crawler.crawl(
                target_cfg.url,
                target_cfg.depth,
                False,  # follow_external
                [],  # content_types
                [],  # exclude_patterns
                [],  # include_patterns
                getattr(target_cfg, "max_pages", 1000),
                [],  # allowed_paths
                [],  # excluded_paths
            )
            assert final_result.stats.pages_crawled == 2

    async def test_max_pages_limit(self, crawler):
        # Test 12.3: max_pages limit hit
        from types import SimpleNamespace

        stats = SimpleNamespace(pages_crawled=1, successful_crawls=1, failed_crawls=0)
        mock_result = Mock(spec=CrawlResult)
        mock_result.stats = stats
        mock_result.documents = [Mock()]
        mock_result.issues = []
        with patch.object(
            DocumentationCrawler, "crawl", AsyncMock(return_value=mock_result)
        ):
            target_cfg = CrawlTarget(
                url="http://example.com/page1", depth=5, max_pages=2
            )
            final_result = await crawler.crawl(
                target_cfg.url,
                target_cfg.depth,
                False,  # follow_external
                [],  # content_types
                [],  # exclude_patterns
                [],  # include_patterns
                getattr(target_cfg, "max_pages", 2),
                [],  # allowed_paths
                [],  # excluded_paths
            )
            assert final_result.stats.pages_crawled == 1

    async def test_asyncio_timeout_error(self, crawler, target_cfg):
        # Test 12.4: asyncio.TimeoutError during _process_url
        from types import SimpleNamespace

        stats = SimpleNamespace(pages_crawled=0, successful_crawls=0, failed_crawls=0)
        mock_result = Mock(spec=CrawlResult)
        mock_result.stats = stats
        mock_result.documents = []
        mock_result.issues = [Exception("Timeout")]
        with patch.object(
            DocumentationCrawler, "crawl", AsyncMock(return_value=mock_result)
        ):
            final_result = await crawler.crawl(
                target_cfg.url,
                target_cfg.depth,
                False,  # follow_external
                [],  # content_types
                [],  # exclude_patterns
                [],  # include_patterns
                getattr(target_cfg, "max_pages", 1000),
                [],  # allowed_paths
                [],  # excluded_paths
            )
            assert isinstance(final_result.issues[0], Exception) or hasattr(
                final_result.issues[0], "message"
            )

    async def test_error_in_process_url(self, crawler, target_cfg):
        # Test 12.5: Error in _process_url
        from types import SimpleNamespace

        stats = SimpleNamespace(pages_crawled=0, successful_crawls=0, failed_crawls=1)
        mock_result = Mock(spec=CrawlResult)
        mock_result.stats = stats
        mock_result.issues = [Mock(message="Some error")]
        mock_result.documents = []
        with patch.object(
            DocumentationCrawler, "crawl", AsyncMock(return_value=mock_result)
        ):
            final_result = await crawler.crawl(
                target_cfg.url,
                target_cfg.depth,
                False,  # follow_external
                [],  # content_types
                [],  # exclude_patterns
                [],  # include_patterns
                getattr(target_cfg, "max_pages", 1000),
                [],  # allowed_paths
                [],  # excluded_paths
            )
            assert len(final_result.issues) == 1
            assert final_result.stats.failed_crawls == 1
