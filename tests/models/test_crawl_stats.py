"""Tests for CrawlStats model."""

from datetime import UTC, datetime, timedelta

from src.crawler.models import CrawlStats


def test_crawl_stats_default_instantiation():
    """Test default instantiation of CrawlStats model."""
    stats = CrawlStats()

    # Check default values
    assert isinstance(stats.start_time, datetime)
    assert stats.end_time is None
    assert stats.pages_crawled == 0
    assert stats.successful_crawls == 0
    assert stats.failed_crawls == 0
    assert stats.total_time == 0.0
    assert stats.average_time_per_page == 0.0
    assert stats.quality_issues == 0
    assert stats.bytes_processed == 0


def test_crawl_stats_custom_values():
    """Test setting and getting custom values for CrawlStats model."""
    # Set up a custom start time for testing
    start_time = datetime.now(UTC) - timedelta(hours=1)

    # Create stats with custom start time
    stats = CrawlStats(start_time=start_time)
    assert stats.start_time == start_time

    # Modify values
    stats.pages_crawled = 10
    stats.successful_crawls = 8
    stats.failed_crawls = 2
    stats.total_time = 60.0
    stats.quality_issues = 3
    stats.bytes_processed = 1024

    # Verify changes
    assert stats.pages_crawled == 10
    assert stats.successful_crawls == 8
    assert stats.failed_crawls == 2
    assert stats.total_time == 60.0
    assert stats.quality_issues == 3
    assert stats.bytes_processed == 1024

    # Set end time and check average time calculation
    end_time = datetime.now(UTC)
    stats.end_time = end_time
    stats.average_time_per_page = stats.total_time / stats.pages_crawled

    assert stats.end_time == end_time
    assert stats.average_time_per_page == 6.0  # 60.0 / 10
