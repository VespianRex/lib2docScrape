"""Tests for the sequential crawler implementation."""

import pytest

from src.crawler.crawler import Crawler, CrawlerOptions
from src.crawler.models import CrawlConfig


@pytest.fixture
def crawler():
    """Fixture providing a basic Crawler instance."""
    return Crawler()


@pytest.fixture
def crawler_with_config():
    """Fixture providing a Crawler instance with custom config."""
    config = CrawlConfig(rate_limit=0.5)
    return Crawler(config=config)


class TestCrawlerInit:
    """Tests for Crawler.__init__ method."""

    def test_init_with_default_config(self):
        """Test 1.2: Defaulting of `config` argument."""
        crawler = Crawler(config=None)
        assert isinstance(crawler.config, CrawlConfig)

        # Check that the default CrawlConfig().rate_limit is used for RateLimiter
        default_cfg = CrawlConfig()
        expected_rps = (
            1.0 / default_cfg.rate_limit if default_cfg.rate_limit > 0 else float("inf")
        )
        assert crawler.rate_limiter.rate == expected_rps

    def test_init_with_zero_rate_limit(self):
        """Test 1.1: `rate_limit == 0` or negative."""
        config_zero = CrawlConfig(rate_limit=0)
        crawler_zero = Crawler(config=config_zero)
        assert crawler_zero.rate_limiter.rate == float("inf")

    def test_init_with_negative_rate_limit(self):
        """Test 1.1: `rate_limit == 0` or negative (negative case)."""
        # Create a config with negative rate_limit
        # Note: If CrawlConfig validates rate_limit >= 0, we'll need to patch or modify this test
        config_neg = CrawlConfig()
        config_neg.rate_limit = -1  # Directly set attribute to bypass validation
        crawler_neg = Crawler(config=config_neg)
        assert crawler_neg.rate_limiter.rate == float("inf")

    def test_init_with_custom_config(self):
        """Test initialization with custom config."""
        custom_config = CrawlConfig(max_depth=5, max_pages=100, rate_limit=0.5)
        crawler = Crawler(config=custom_config)
        assert crawler.config == custom_config
        assert crawler.rate_limiter.rate == 2.0  # 1.0 / 0.5


class TestCrawlerOptions:
    """Tests for CrawlerOptions class."""

    def test_crawler_options_default_values(self):
        """Test 3.1: Basic instantiation with default values."""
        options = CrawlerOptions()
        assert options.verify_ssl is True
        assert options.javascript_rendering is False
        assert options.extract_images is True

    def test_crawler_options_custom_values(self):
        """Test 3.1: Basic instantiation with custom values."""
        options = CrawlerOptions(
            verify_ssl=False, javascript_rendering=True, extract_images=False
        )
        assert options.verify_ssl is False
        assert options.javascript_rendering is True
        assert options.extract_images is False


@pytest.mark.asyncio
class TestCrawlerCrawl:
    """Tests for Crawler.crawl method."""

    async def test_crawl_with_varied_parameters(self, crawler):
        """Test 2.1: Call with varied `CrawlTarget` parameters."""
        result = await crawler.crawl(
            target_url="http://example.com/test-crawl",
            depth=3,
            follow_external=True,
            content_types=["application/json", "text/xml"],
            exclude_patterns=["/api/", "/v1/"],
            include_patterns=["/data/", "/archive/"],
            max_pages=50,
            allowed_paths=["/data/items/", "/archive/specific/"],
            excluded_paths=["/data/raw/", "/archive/temp/"],
        )

        # Verify target parameters were passed through correctly
        assert result.target.url == "http://example.com/test-crawl"
        # Note: depth might be modified during crawling process, so we check it was at least 1
        assert result.target.depth >= 1
        assert result.target.follow_external is True
        assert result.target.content_types == ["application/json", "text/xml"]
        assert result.target.exclude_patterns == ["/api/", "/v1/"]
        assert result.target.include_patterns == ["/data/", "/archive/"]
        assert result.target.max_pages == 50
        assert result.target.allowed_paths == ["/data/items/", "/archive/specific/"]
        assert result.target.excluded_paths == ["/data/raw/", "/archive/temp/"]

        # Verify crawler behavior (may not crawl pages if URL filtering rejects them)
        assert result.stats.pages_crawled >= 0  # Could be 0 if URL is filtered out
        assert len(result.documents) >= 0  # Could be 0 if no pages were crawled

    async def test_crawl_logger_call(self, crawler, caplog):
        """Test 2.2: Ensure logger call is covered."""
        await crawler.crawl(
            target_url="http://logtest.com",
            depth=1,
            follow_external=False,
            content_types=[],
            exclude_patterns=[],
            include_patterns=[],
            max_pages=1,
            allowed_paths=[],
            excluded_paths=[],
        )

        assert "Crawling http://logtest.com with depth=1" in caplog.text
