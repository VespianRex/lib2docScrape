"""Tests for focusing on src/crawler.py."""

from unittest.mock import MagicMock, patch

import pytest

# Import the actual module we want to test
import src.crawler


def test_crawler_module_imports():
    """Test core imports of the crawler module."""
    # Test that the module has the expected attributes
    assert hasattr(src.crawler, "CrawlerConfig")
    assert hasattr(src.crawler, "DocumentationCrawler")
    assert hasattr(src.crawler, "CrawlTarget")


@pytest.mark.asyncio
async def test_crawler_basic_initialization():
    """Test basic crawler initialization."""
    config = src.crawler.CrawlerConfig(max_depth=2, max_pages=100)

    with patch("src.crawler.BackendSelector") as mock_selector:
        with patch("src.crawler.DocumentOrganizer") as mock_organizer:
            with patch("src.crawler.ContentProcessor") as mock_processor:
                # Setup mock returns
                mock_selector.return_value = MagicMock()
                mock_organizer.return_value = MagicMock()
                mock_processor.return_value = MagicMock()

                # Initialize crawler
                crawler = src.crawler.DocumentationCrawler(config)

                # Check basics
                assert crawler.config.max_depth == 2
                assert crawler.config.max_pages == 100
                assert crawler.visited_urls == set()
                assert crawler.crawl_queue == []


@pytest.mark.asyncio
async def test_crawler_add_target():
    """Test adding a target to the crawler."""
    config = src.crawler.CrawlerConfig(max_depth=2, max_pages=100)

    with patch("src.crawler.BackendSelector") as mock_selector:
        with patch("src.crawler.DocumentOrganizer") as mock_organizer:
            with patch("src.crawler.ContentProcessor") as mock_processor:
                # Setup mock returns
                mock_selector.return_value = MagicMock()
                mock_organizer.return_value = MagicMock()
                mock_processor.return_value = MagicMock()

                # Initialize crawler
                crawler = src.crawler.DocumentationCrawler(config)

                # Add target
                target = src.crawler.CrawlTarget(
                    url="https://example.com/docs", depth=1
                )
                crawler.add_target(target)

                # Check the target was added
                assert len(crawler.crawl_queue) == 1
                assert crawler.crawl_queue[0].url == "https://example.com/docs"
