"""Tests for the main crawler.py module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from src.backends.base import CrawlResult as BackendCrawlResult
from src.crawler import CrawlerConfig, CrawlResult, DocumentationCrawler
from src.models.project import ProjectIdentity, ProjectType


class MockBackend:
    """Mock backend for testing."""

    def __init__(self, name="mock_backend"):
        self.name = name
        self.crawl_called = False

    async def crawl(self, url_info, **_):
        """Mock crawl method."""
        self.crawl_called = True
        return BackendCrawlResult(
            url=url_info.normalized_url,
            content={
                "html": "<html><head><title>Test Document</title></head><body>Test content</body></html>"
            },
            status=200,
            content_type="text/html",
            metadata={},
            documents=[
                {
                    "url": url_info.normalized_url,
                    "title": "Test Document",
                    "content": "Test content",
                }
            ],
        )


@pytest.fixture
def crawler_config():
    """Fixture providing a crawler configuration."""
    return CrawlerConfig(
        max_depth=2,
        max_pages=10,
        follow_external=False,
        content_types=["text/html"],
        exclude_patterns=[],
        include_patterns=[],
        rate_limit=0.1,
        timeout=10,
        retry_count=2,
        user_agent="Test User Agent",
    )


@pytest.fixture
def mock_backend():
    """Fixture providing a mock backend."""
    return MockBackend()


@pytest.fixture
def mock_content_processor():
    """Fixture providing a mock content processor."""
    processor = AsyncMock()
    processor.process.return_value = {
        "title": "Test Document",
        "content": "Processed content",
        "headings": [{"level": 1, "text": "Test Document"}],
        "links": [{"text": "Test Link", "url": "/test"}],
    }
    return processor


@pytest.fixture
def mock_quality_checker():
    """Fixture providing a mock quality checker."""
    checker = AsyncMock()
    checker.check_quality.return_value = ([], {"score": 0.9})
    return checker


@pytest.fixture
def mock_document_organizer():
    """Fixture providing a mock document organizer."""
    organizer = MagicMock()
    organizer.add_document.return_value = "doc_id_1"
    organizer.organize.return_value = {
        "structure": [{"type": "section", "title": "organized"}],
        "summary": "summary",
    }
    return organizer


@pytest_asyncio.fixture
async def crawler(
    crawler_config,
    mock_backend,
    mock_content_processor,
    mock_quality_checker,
    mock_document_organizer,
):
    """Fixture providing a DocumentationCrawler instance."""
    crawler_instance = DocumentationCrawler(
        config=crawler_config,
        backend=mock_backend,
        content_processor=mock_content_processor,
        quality_checker=mock_quality_checker,
        document_organizer=mock_document_organizer,
    )

    yield crawler_instance


@pytest.mark.asyncio
async def test_crawler_initialization(crawler_config):
    """Test crawler initialization with custom config."""
    crawler = DocumentationCrawler(config=crawler_config)

    assert crawler.config == crawler_config
    assert crawler.config.max_depth == 2
    assert crawler.config.max_pages == 10
    assert crawler.config.retry_count == 2
    assert crawler.config.user_agent == "Test User Agent"


@pytest.mark.asyncio
async def test_crawler_with_direct_backend(crawler_config, mock_backend):
    """Test crawler initialization with direct backend."""
    crawler = DocumentationCrawler(config=crawler_config, backend=mock_backend)

    assert crawler.backend == mock_backend


@pytest.mark.asyncio
@patch("src.crawler.crawler.DuckDuckGoSearch")
async def test_crawler_with_duckduckgo(mock_ddg_class):
    """Test crawler initialization with DuckDuckGo enabled."""
    # Create config with DuckDuckGo enabled
    config = CrawlerConfig(max_depth=2, max_pages=10, use_duckduckgo=True)

    # Create crawler with DuckDuckGo enabled
    DocumentationCrawler(config=config)

    # Verify DuckDuckGo was initialized
    mock_ddg_class.assert_called_once()


@pytest.mark.asyncio
async def test_crawl_basic(crawler, mock_backend):
    """Test the main crawl method with basic configuration."""
    # Call the crawl method
    result = await crawler.crawl(
        target_url="https://example.com/docs",
        depth=1,
        follow_external=False,
        content_types=["text/html"],
        exclude_patterns=[],
        include_patterns=[],
        max_pages=1,
    )

    # Verify results
    assert result is not None
    assert isinstance(result, CrawlResult)
    assert len(result.documents) == 1
    assert result.documents[0]["title"] == "Test Document"
    assert len(result.crawled_urls) == 1
    assert "https://example.com/docs" in result.crawled_urls

    # Verify backend was called
    assert mock_backend.crawl_called is True


@pytest.mark.asyncio
@patch("src.utils.project_identifier.ProjectIdentifier.identify_from_url")
async def test_crawl_with_project_identification(mock_identify_from_url, crawler):
    """Test the crawl method with project identification."""
    # Mock the identify_from_url method
    mock_identify_from_url.return_value = ProjectIdentity(
        name="example-project", type=ProjectType.LIBRARY, version="1.0.0"
    )

    # Call the crawl method
    result = await crawler.crawl(
        target_url="https://example.com/docs",
        depth=1,
        follow_external=False,
        content_types=["text/html"],
        exclude_patterns=[],
        include_patterns=[],
        max_pages=1,
    )

    # Verify results
    assert result is not None
    assert result.project_identity is not None
    assert result.project_identity.name == "example-project"
    assert result.project_identity.type == ProjectType.LIBRARY
    assert result.project_identity.version == "1.0.0"

    # Verify the identify_from_url method was called
    mock_identify_from_url.assert_called_once_with("https://example.com/docs")
