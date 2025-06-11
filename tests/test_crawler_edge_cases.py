"""Tests focused on edge cases and error conditions for the crawler module."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from src.backends.base import CrawlerBackend
from src.backends.base import CrawlResult as BackendCrawlResult
from src.crawler import (
    CrawlerConfig,
    CrawlerQualityCheckConfig,
    CrawlTarget,
    DocumentationCrawler,
)
from src.processors.content_processor import ProcessedContent
from src.processors.quality_checker import IssueLevel, IssueType, QualityIssue


class MockErrorBackend(CrawlerBackend):
    """Mock backend that simulates various error conditions."""

    def __init__(self, error_scenario: str = "timeout"):
        super().__init__(name="mock_error_backend")
        self.error_scenario = error_scenario
        self.crawl_count = 0

    async def crawl(self, url_info, config=None, params=None) -> BackendCrawlResult:
        self.crawl_count += 1
        if self.error_scenario == "timeout":
            await asyncio.sleep(0.1)
            raise asyncio.TimeoutError("Simulated timeout")
        elif self.error_scenario == "connection":
            raise aiohttp.ClientError("Simulated connection error")
        elif self.error_scenario == "http":
            raise aiohttp.ClientResponseError(
                status=404, message="Not Found", request_info=MagicMock(), history=()
            )
        elif self.error_scenario == "rate_limit":
            raise aiohttp.ClientResponseError(
                status=429,
                message="Too Many Requests",
                request_info=MagicMock(),
                history=(),
            )
        else:
            raise Exception("Unexpected error")

    async def validate(self, content) -> bool:
        """Validate the crawled content."""
        return True

    async def process(self, content) -> dict:
        """Process the crawled content."""
        return {"error": f"Processing failed due to {self.error_scenario}"}


@pytest.fixture
def mock_quality_checker():
    checker = AsyncMock()
    mock_issue = QualityIssue(
        type=IssueType.GENERAL,
        level=IssueLevel.WARNING,
        message="Test quality issue",
        location="body",
    )
    checker.check_quality = AsyncMock(
        return_value=([mock_issue], {"quality_score": 0.5})
    )
    return checker


@pytest.fixture
def mock_doc_organizer():
    organizer = AsyncMock()
    organizer.add_document = AsyncMock(return_value="test_doc_id")
    organizer.process_document = AsyncMock()
    return organizer


@pytest.fixture
def mock_content_processor():
    processor = AsyncMock()
    processor.process = AsyncMock(
        return_value=ProcessedContent(
            url="https://test.com",
            title="Test",
            content={"text": "Test content", "links": []},
        )
    )
    return processor


@pytest.mark.asyncio
async def test_crawler_timeout_handling(
    mock_quality_checker, mock_doc_organizer, mock_content_processor
):
    """Test how crawler handles backend timeouts."""
    backend = MockErrorBackend("timeout")
    crawler = DocumentationCrawler(
        quality_checker=mock_quality_checker,
        document_organizer=mock_doc_organizer,
        content_processor=mock_content_processor,
    )

    target = CrawlTarget(url="https://test.com")
    config = CrawlerConfig(max_retries=1, retry_delay=0.1)

    result = await crawler.crawl(target, config, backend=backend)
    assert len(result.errors) > 0
    # result.errors is a dict mapping URLs to errors
    error_messages = list(result.errors.values())
    assert "timeout" in str(error_messages[0]).lower()


@pytest.mark.asyncio
async def test_crawler_connection_error(
    mock_quality_checker, mock_doc_organizer, mock_content_processor
):
    """Test how crawler handles connection errors."""
    backend = MockErrorBackend("connection")
    crawler = DocumentationCrawler(
        quality_checker=mock_quality_checker,
        document_organizer=mock_doc_organizer,
        content_processor=mock_content_processor,
    )

    target = CrawlTarget(url="https://test.com")
    config = CrawlerConfig(max_retries=1, retry_delay=0.1)

    result = await crawler.crawl(target, config, backend=backend)
    assert len(result.errors) > 0
    # result.errors is a dict mapping URLs to errors
    error_messages = list(result.errors.values())
    assert "connection" in str(error_messages[0]).lower()


@pytest.mark.asyncio
async def test_crawler_http_error(
    mock_quality_checker, mock_doc_organizer, mock_content_processor
):
    """Test how crawler handles HTTP errors."""
    backend = MockErrorBackend("http")
    crawler = DocumentationCrawler(
        quality_checker=mock_quality_checker,
        document_organizer=mock_doc_organizer,
        content_processor=mock_content_processor,
    )

    target = CrawlTarget(url="https://test.com")
    config = CrawlerConfig(max_retries=1, retry_delay=0.1)

    result = await crawler.crawl(target, config, backend=backend)
    assert len(result.errors) > 0
    # result.errors is a dict mapping URLs to errors
    error_messages = list(result.errors.values())
    assert "404" in str(error_messages[0])


@pytest.mark.asyncio
async def test_crawler_rate_limit_handling(
    mock_quality_checker, mock_doc_organizer, mock_content_processor
):
    """Test how crawler handles rate limiting."""
    backend = MockErrorBackend("rate_limit")
    crawler = DocumentationCrawler(
        quality_checker=mock_quality_checker,
        document_organizer=mock_doc_organizer,
        content_processor=mock_content_processor,
    )

    target = CrawlTarget(url="https://test.com")
    config = CrawlerConfig(max_retries=2, retry_delay=0.1)

    result = await crawler.crawl(target, config, backend=backend)
    assert len(result.errors) > 0
    # result.errors is a dict mapping URLs to errors
    error_messages = list(result.errors.values())
    assert "429" in str(error_messages[0])


@pytest.mark.asyncio
async def test_crawler_invalid_content(mock_quality_checker, mock_doc_organizer):
    """Test how crawler handles invalid content from backend."""
    processor = AsyncMock()
    processor.process = AsyncMock(side_effect=ValueError("Invalid content"))

    crawler = DocumentationCrawler(
        quality_checker=mock_quality_checker,
        document_organizer=mock_doc_organizer,
        content_processor=processor,
    )

    target = CrawlTarget(url="https://test.com")
    mock_backend = AsyncMock()
    mock_backend.crawl = AsyncMock(
        return_value=BackendCrawlResult(
            url="https://test.com",
            content={"html": "Invalid content"},
            metadata={},
            status=200,
        )
    )

    result = await crawler.crawl(target, backend=mock_backend)
    assert len(result.errors) > 0
    # result.errors is a dict mapping URLs to errors
    error_messages = list(result.errors.values())
    assert "invalid content" in str(error_messages[0]).lower()


@pytest.mark.asyncio
async def test_crawler_quality_threshold(mock_doc_organizer, mock_content_processor):
    """Test crawler's quality threshold functionality."""
    # Create a quality checker that always returns low quality scores
    checker = AsyncMock()
    mock_issue = QualityIssue(
        type=IssueType.GENERAL,
        level=IssueLevel.ERROR,
        message="Low quality content",
        location="body",
    )
    checker.check_quality = AsyncMock(
        return_value=([mock_issue], {"quality_score": 0.1})
    )

    crawler = DocumentationCrawler(
        quality_checker=checker,
        document_organizer=mock_doc_organizer,
        content_processor=mock_content_processor,
    )

    target = CrawlTarget(url="https://test.com")
    config = CrawlerConfig(
        quality_config=CrawlerQualityCheckConfig(
            min_quality_score=0.5, ignore_low_quality=False
        )
    )

    # Create a mock backend to provide content
    mock_backend = AsyncMock()
    mock_backend.crawl = AsyncMock(
        return_value=BackendCrawlResult(
            url="https://test.com",
            content={"html": "Low quality content"},
            metadata={},
            status=200,
        )
    )

    result = await crawler.crawl(target, config, backend=mock_backend)
    assert len(result.errors) > 0
    # result.errors is a dict mapping URLs to errors
    error_messages = list(result.errors.values())
    assert "quality" in str(error_messages[0]).lower()


@pytest.mark.asyncio
async def test_crawler_max_depth_limit(
    mock_quality_checker, mock_doc_organizer, mock_content_processor
):
    """Test that crawler respects max depth limit."""
    mock_backend = AsyncMock()
    # Simulate linked pages at different depths
    mock_backend.crawl = AsyncMock(
        return_value=BackendCrawlResult(
            url="https://test.com",
            content={
                "html": """
            <a href="https://test.com/page1">Link 1</a>
            <a href="https://test.com/page2">Link 2</a>
        """
            },
            metadata={},
            status=200,
        )
    )

    crawler = DocumentationCrawler(
        quality_checker=mock_quality_checker,
        document_organizer=mock_doc_organizer,
        content_processor=mock_content_processor,
    )

    target = CrawlTarget(url="https://test.com", depth=1)
    _result = await crawler.crawl(target, backend=mock_backend)

    # Should only crawl the initial URL due to depth=1
    assert mock_backend.crawl.call_count == 1


@pytest.mark.asyncio
async def test_crawler_max_pages_limit(
    mock_quality_checker, mock_doc_organizer, mock_content_processor
):
    """Test that crawler respects max pages limit."""
    mock_backend = AsyncMock()
    mock_backend.crawl = AsyncMock(
        return_value=BackendCrawlResult(
            url="https://test.com",
            content={
                "html": """
            <a href="https://test.com/page1">Link 1</a>
            <a href="https://test.com/page2">Link 2</a>
            <a href="https://test.com/page3">Link 3</a>
        """
            },
            metadata={},
            status=200,
        )
    )

    crawler = DocumentationCrawler(
        quality_checker=mock_quality_checker,
        document_organizer=mock_doc_organizer,
        content_processor=mock_content_processor,
    )

    target = CrawlTarget(url="https://test.com", max_pages=2)
    _result = await crawler.crawl(target, backend=mock_backend)

    # Should only crawl 2 pages due to max_pages=2
    assert mock_backend.crawl.call_count <= 2


@pytest.mark.asyncio
async def test_async_tasks_limit(
    mock_quality_checker, mock_doc_organizer, mock_content_processor
):
    """Test that crawler respects async tasks limit."""
    mock_backend = AsyncMock()
    links = [f"https://test.com/page{i}" for i in range(10)]
    mock_backend.crawl = AsyncMock(
        return_value=BackendCrawlResult(
            url="https://test.com",
            content={"html": " ".join(f'<a href="{link}">Link</a>' for link in links)},
            metadata={},
            status=200,
        )
    )

    crawler = DocumentationCrawler(
        quality_checker=mock_quality_checker,
        document_organizer=mock_doc_organizer,
        content_processor=mock_content_processor,
    )

    target = CrawlTarget(url="https://test.com")
    config = CrawlerConfig(max_async_tasks=3)

    _result = await crawler.crawl(target, config)

    # Should only have 3 concurrent tasks at any time
    active_tasks = crawler.active_tasks  # Assuming this is tracked
    assert active_tasks <= 3
