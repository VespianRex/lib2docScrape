"""Tests for crawler configuration and initialization."""

from datetime import timedelta
from unittest.mock import AsyncMock

import pytest

from src.crawler import (
    CrawlerConfig,
    CrawlerOrganizationConfig,
    CrawlerQualityCheckConfig,
    CrawlStats,
    CrawlTarget,
    DocumentationCrawler,
)
from src.organizers.doc_organizer import DocumentOrganizer
from src.processors.content_processor import ContentProcessor
from src.processors.quality_checker import QualityChecker


def test_crawler_config_defaults():
    """Test default values for CrawlerConfig."""
    config = CrawlerConfig()
    assert config.max_retries == 3
    assert config.retry_delay == 1.0
    assert config.timeout == 30.0
    assert config.max_async_tasks == 10
    assert config.quality_config is not None
    assert config.organization_config is not None


def test_crawler_config_custom():
    """Test custom values for CrawlerConfig."""
    config = CrawlerConfig(
        max_retries=5,
        retry_delay=2.0,
        timeout=60.0,
        max_async_tasks=20,
        quality_config=CrawlerQualityCheckConfig(
            min_quality_score=0.8, ignore_low_quality=True
        ),
        organization_config=CrawlerOrganizationConfig(
            skip_organization=True, organization_delay=1.0
        ),
    )
    assert config.max_retries == 5
    assert config.retry_delay == 2.0
    assert config.timeout == 60.0
    assert config.max_async_tasks == 20
    assert config.quality_config.min_quality_score == 0.8
    assert config.quality_config.ignore_low_quality is True
    assert config.organization_config.skip_organization is True
    assert config.organization_config.organization_delay == 1.0


def test_crawler_config_validation():
    """Test validation of CrawlerConfig values."""
    with pytest.raises(ValueError):
        CrawlerConfig(max_retries=-1)

    with pytest.raises(ValueError):
        CrawlerConfig(retry_delay=-1.0)

    with pytest.raises(ValueError):
        CrawlerConfig(timeout=0.0)

    with pytest.raises(ValueError):
        CrawlerConfig(max_async_tasks=0)


def test_crawl_target_defaults():
    """Test default values for CrawlTarget."""
    target = CrawlTarget()
    assert isinstance(target.url, str)
    assert target.depth == 1
    assert target.follow_external is False
    assert isinstance(target.content_types, list)
    assert isinstance(target.exclude_patterns, list)
    assert isinstance(target.required_patterns, list)
    assert target.max_pages == 1000
    assert isinstance(target.allowed_paths, list)
    assert isinstance(target.excluded_paths, list)


def test_crawl_target_custom():
    """Test custom values for CrawlTarget."""
    target = CrawlTarget(
        url="https://test.com",
        depth=3,
        follow_external=True,
        content_types=["text/html", "text/plain"],
        exclude_patterns=[r"\\.pdf$"],
        required_patterns=[r"^/docs/"],
        max_pages=100,
        allowed_paths=["/docs", "/api"],
        excluded_paths=["/private"],
    )
    assert target.url == "https://test.com"
    assert target.depth == 3
    assert target.follow_external is True
    assert "text/html" in target.content_types
    assert "text/plain" in target.content_types
    assert r"\\.pdf$" in target.exclude_patterns
    assert r"^/docs/" in target.required_patterns
    assert target.max_pages == 100
    assert "/docs" in target.allowed_paths
    assert "/api" in target.allowed_paths
    assert "/private" in target.excluded_paths


def test_crawl_target_validation():
    """Test validation of CrawlTarget values."""
    with pytest.raises(ValueError):
        CrawlTarget(depth=-1)

    with pytest.raises(ValueError):
        CrawlTarget(url="invalid-url")

    with pytest.raises(ValueError):
        CrawlTarget(max_pages=-1)


def test_crawl_stats_tracking():
    """Test CrawlStats tracking functionality."""
    stats = CrawlStats()
    assert stats.start_time is not None
    assert stats.end_time is None

    # Test updating stats
    stats.pages_crawled = 5
    stats.errors = 2
    stats.quality_issues = 3
    stats.end_time = stats.start_time + timedelta(seconds=10)

    assert stats.pages_crawled == 5
    assert stats.errors == 2
    assert stats.quality_issues == 3
    assert isinstance(stats.duration, timedelta)
    assert stats.duration.total_seconds() == 10


def test_crawler_initialization():
    """Test DocumentationCrawler initialization."""
    mock_quality_checker = AsyncMock(spec=QualityChecker)
    mock_doc_organizer = AsyncMock(spec=DocumentOrganizer)
    mock_content_processor = AsyncMock(spec=ContentProcessor)

    crawler = DocumentationCrawler(
        quality_checker=mock_quality_checker,
        document_organizer=mock_doc_organizer,
        content_processor=mock_content_processor,
    )

    assert crawler.quality_checker == mock_quality_checker
    assert crawler.document_organizer == mock_doc_organizer
    assert crawler.content_processor == mock_content_processor
    assert crawler.active_tasks == 0
    assert crawler.crawled_urls == set()


def test_crawler_custom_initialization():
    """Test DocumentationCrawler initialization with custom config."""
    mock_quality_checker = AsyncMock(spec=QualityChecker)
    mock_doc_organizer = AsyncMock(spec=DocumentOrganizer)
    mock_content_processor = AsyncMock(spec=ContentProcessor)

    config = CrawlerConfig(
        max_retries=5, retry_delay=2.0, timeout=60.0, max_async_tasks=20
    )

    crawler = DocumentationCrawler(
        quality_checker=mock_quality_checker,
        document_organizer=mock_doc_organizer,
        content_processor=mock_content_processor,
        config=config,
    )

    assert crawler.config == config
    assert crawler.quality_checker == mock_quality_checker
    assert crawler.document_organizer == mock_doc_organizer
    assert crawler.content_processor == mock_content_processor


@pytest.mark.asyncio
async def test_crawler_cleanup():
    """Test that crawler properly cleans up resources."""
    mock_quality_checker = AsyncMock(spec=QualityChecker)
    mock_doc_organizer = AsyncMock(spec=DocumentOrganizer)
    mock_content_processor = AsyncMock(spec=ContentProcessor)

    # Add cleanup methods to mocks
    mock_quality_checker.cleanup = AsyncMock()
    mock_doc_organizer.cleanup = AsyncMock()
    mock_content_processor.cleanup = AsyncMock()

    crawler = DocumentationCrawler(
        quality_checker=mock_quality_checker,
        document_organizer=mock_doc_organizer,
        content_processor=mock_content_processor,
    )

    # Simulate some crawling activity
    crawler.crawled_urls.add("https://test.com")
    crawler.active_tasks = 5

    # Clean up
    await crawler.cleanup()

    assert len(crawler.crawled_urls) == 0
    assert crawler.active_tasks == 0
    mock_quality_checker.cleanup.assert_called_once()
    mock_doc_organizer.cleanup.assert_called_once()
    mock_content_processor.cleanup.assert_called_once()
