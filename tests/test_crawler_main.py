"""Tests for the main src/crawler.py module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from src.backends.base import CrawlerBackend, CrawlResult
from src.backends.selector import BackendCriteria, BackendSelector
from src.crawler import (
    CrawlerConfig,
    CrawlStats,
    CrawlTarget,
    DocumentationCrawler,
)
from src.crawler import (
    CrawlResult as OrchestratorResult,
)
from src.models.project import ProjectIdentity, ProjectType
from src.processors.content_processor import ProcessedContent
from src.utils.url.factory import create_url_info


class MockCrawlerBackend(CrawlerBackend):
    """Mock crawler backend for testing."""

    def __init__(self, name="mock_backend"):
        super().__init__(name=name)
        self.crawl_called = False
        self.validate_called = False
        self.process_called = False

    async def crawl(self, url_info, **kwargs):
        """Mock crawl method."""
        self.crawl_called = True
        normalized_url = url_info.normalized_url
        return CrawlResult(
            url=normalized_url,
            content={
                "html": "<html><body><h1>Test Document</h1><p>Test content</p><a href='/test'>Test Link</a></body></html>"
            },
            metadata={"status_code": 200, "headers": {"Content-Type": "text/html"}},
            status=200,
            content_type="text/html",
        )

    async def validate(self, _):
        """Mock validate method."""
        self.validate_called = True
        return True

    async def process(self, content):
        """Mock process method."""
        self.process_called = True
        return {"title": "Test Document", "content": "Test content", "url": content.url}


@pytest.fixture
def mock_backend():
    """Fixture providing a mock backend."""
    return MockCrawlerBackend()


@pytest.fixture
def crawler_config():
    """Fixture providing a crawler configuration."""
    return CrawlerConfig(
        concurrent_requests=5,
        rate_limit=0.1,  # This gives requests_per_second=10.0 (1/0.1)
        max_retries=2,
        request_timeout=10.0,
        follow_redirects=True,
        verify_ssl=True,
        user_agent="Test User Agent",
        use_duckduckgo=False,
    )


@pytest.fixture
def mock_content_processor():
    """Fixture providing a mock content processor."""
    processor = AsyncMock()
    processed_content = ProcessedContent(
        content={
            "formatted_content": "Processed content",
            "headings": [{"level": 1, "text": "Test Document"}],
            "code_blocks": [{"language": "python", "content": "def test():\n    pass"}],
            "links": [{"text": "Test Link", "url": "/test"}],
        },
        metadata={"title": "Test Document"},
        assets={"images": [], "stylesheets": [], "scripts": [], "media": []},
        headings=[{"level": 1, "text": "Test Document"}],
        structure=[
            {"type": "section", "title": "Test Document"},
            {"type": "link", "text": "Test Link", "href": "/test"},
        ],
    )
    # Add title attribute to match crawler expectations
    processed_content.title = "Test Document"
    processor.process.return_value = processed_content
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
    organizer.organize = AsyncMock(
        return_value={
            "structure": [{"type": "section", "title": "organized"}],
            "summary": "summary",
        }
    )
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
    selector = BackendSelector()
    selector.register_backend(
        name=mock_backend.name,
        backend=mock_backend,
        criteria=BackendCriteria(
            priority=100, content_types=["text/html"], url_patterns=["*"]
        ),
    )

    crawler_instance = DocumentationCrawler(
        config=crawler_config,
        backend_selector=selector,
        content_processor=mock_content_processor,
        quality_checker=mock_quality_checker,
        document_organizer=mock_document_organizer,
    )

    yield crawler_instance
    # No cleanup needed for this test


@pytest.mark.asyncio
async def test_crawler_initialization(crawler_config):
    """Test crawler initialization with custom config."""
    crawler = DocumentationCrawler(config=crawler_config)

    assert crawler.config == crawler_config
    assert crawler.config.concurrent_requests == 5
    assert crawler.config.requests_per_second == 10.0
    assert crawler.config.max_retries == 2
    assert crawler.config.user_agent == "Test User Agent"
    assert crawler.backend_selector is not None
    assert crawler.content_processor is not None
    assert crawler.quality_checker is not None
    assert crawler.document_organizer is not None
    assert crawler._crawled_urls == set()
    assert crawler._processing_semaphore is not None
    assert crawler.duckduckgo is None  # use_duckduckgo=False in config


@pytest.mark.asyncio
async def test_crawler_with_direct_backend(crawler_config, mock_backend):
    """Test crawler initialization with direct backend."""
    crawler = DocumentationCrawler(config=crawler_config, backend=mock_backend)

    assert crawler.direct_backend == mock_backend
    assert crawler.backend == mock_backend


@pytest.mark.asyncio
async def test_find_links_recursive():
    """Test _find_links_recursive method."""
    crawler = DocumentationCrawler(config=CrawlerConfig(use_duckduckgo=False))

    # Test with a dictionary containing a link
    structure_dict = {
        "type": "link",
        "href": "https://example.com/page1",
        "text": "Link 1",
    }
    links = crawler._find_links_recursive(structure_dict)
    assert links == ["https://example.com/page1"]

    # Test with a nested dictionary
    nested_dict = {
        "type": "section",
        "title": "Section 1",
        "children": [
            {"type": "link", "href": "https://example.com/page2", "text": "Link 2"}
        ],
    }
    links = crawler._find_links_recursive(nested_dict)
    assert links == ["https://example.com/page2"]

    # Test with a list
    structure_list = [
        {"type": "link", "href": "https://example.com/page3", "text": "Link 3"},
        {"type": "link", "href": "https://example.com/page4", "text": "Link 4"},
    ]
    links = crawler._find_links_recursive(structure_list)
    assert sorted(links) == sorted(
        ["https://example.com/page3", "https://example.com/page4"]
    )


@pytest.mark.asyncio
async def test_should_crawl_url():
    """Test _should_crawl_url method."""
    crawler = DocumentationCrawler(config=CrawlerConfig(use_duckduckgo=False))

    # Create a target with specific rules
    target = CrawlTarget(
        url="https://example.com/docs",
        depth=2,
        follow_external=False,
        exclude_patterns=["/excluded/"],
        required_patterns=["/docs"],
        max_pages=10,
    )

    # Test valid URL
    url_info = create_url_info("https://example.com/docs/page1")
    assert crawler._should_crawl_url(url_info, target) is True

    # Test excluded pattern
    url_info = create_url_info("https://example.com/excluded/page")
    assert crawler._should_crawl_url(url_info, target) is False

    # Test missing required pattern
    url_info = create_url_info("https://example.com/api/page")
    assert crawler._should_crawl_url(url_info, target) is False

    # Test external URL
    url_info = create_url_info("https://other-domain.com/docs/page")
    assert crawler._should_crawl_url(url_info, target) is False

    # Test already crawled URL
    url_info = create_url_info("https://example.com/docs/already-crawled")
    crawler._crawled_urls.add(url_info.normalized_url)
    assert crawler._should_crawl_url(url_info, target) is False

    # Test non-HTTP URL
    url_info = create_url_info("ftp://example.com/docs/page")
    assert crawler._should_crawl_url(url_info, target) is False

    # Test with allowed paths
    target_with_paths = CrawlTarget(
        url="https://example.com/docs",
        depth=2,
        follow_external=False,
        allowed_paths=["/docs/api/", "/docs/guide/"],
        excluded_paths=["/docs/api/private/"],
    )

    # Test allowed path
    url_info = create_url_info("https://example.com/docs/api/public")
    assert crawler._should_crawl_url(url_info, target_with_paths) is True

    # Test not in allowed paths
    url_info = create_url_info("https://example.com/docs/other")
    assert crawler._should_crawl_url(url_info, target_with_paths) is False

    # Test excluded path
    url_info = create_url_info("https://example.com/docs/api/private/secret")
    assert crawler._should_crawl_url(url_info, target_with_paths) is False


@pytest.mark.asyncio
async def test_fetch_and_process_with_backend(crawler, mock_backend):
    """Test _fetch_and_process_with_backend method."""
    # Create a target
    target = CrawlTarget(
        url="https://example.com/docs", depth=2, content_types=["text/html"]
    )

    # Create stats
    stats = CrawlStats()

    # Create URL info
    url_info = create_url_info("https://example.com/docs/page1")

    # Create visited URLs set
    visited_urls = set()

    # First get the backend result
    backend_result_for_test = await mock_backend.crawl(url_info)

    # Call the method
    (
        processed_content,
        backend_result,
        final_url,
        quality_metrics,
        exception,
    ) = await crawler._fetch_and_process_with_backend(
        mock_backend, url_info, target, stats, visited_urls, backend_result_for_test
    )

    # Verify results
    assert processed_content is not None
    assert backend_result is not None
    assert final_url is not None
    assert stats.successful_crawls == 1
    assert stats.pages_crawled == 1
    assert stats.bytes_processed > 0

    # Test with already visited URL (redirect case)
    # Mock a backend that returns a different URL than requested
    redirect_backend = MockCrawlerBackend(name="redirect_backend")

    # Patch the crawl method to return a different URL
    original_crawl = redirect_backend.crawl

    async def patched_crawl(url_info, config=None, params=None):
        result = await original_crawl(url_info)
        # Change the URL to simulate a redirect
        result.url = "https://example.com/docs/redirected"
        return result

    redirect_backend.crawl = patched_crawl

    # Add the redirected URL to visited_urls
    redirected_url_info = create_url_info("https://example.com/docs/redirected")
    visited_urls.add(redirected_url_info.normalized_url)

    # Get backend result for redirect test
    redirect_backend_result = await redirect_backend.crawl(url_info)

    # Call the method with the redirect backend
    (
        processed_content,
        backend_result,
        final_url,
        quality_metrics,
        exception,
    ) = await crawler._fetch_and_process_with_backend(
        redirect_backend, url_info, target, stats, visited_urls, redirect_backend_result
    )

    # Verify results - should be None for processed_content due to redirect to already visited URL
    assert processed_content is None
    assert backend_result is not None
    assert final_url == redirected_url_info.normalized_url

    # Test with non-matching content type
    content_type_backend = MockCrawlerBackend(name="content_type_backend")

    # Patch the crawl method to return a different content type
    async def content_type_crawl(url_info, config=None, params=None):
        result = await original_crawl(url_info)
        # Change the content type to non-matching
        result.metadata["headers"]["Content-Type"] = "application/json"
        return result

    content_type_backend.crawl = content_type_crawl

    # Get backend result for content type test
    content_type_backend_result = await content_type_backend.crawl(url_info)

    # Call the method with the content type backend
    (
        processed_content,
        backend_result,
        final_url,
        quality_metrics,
        exception,
    ) = await crawler._fetch_and_process_with_backend(
        content_type_backend,
        url_info,
        target,
        stats,
        visited_urls,
        content_type_backend_result,
    )

    # Verify results - should be None for processed_content due to content type mismatch
    assert processed_content is None
    assert backend_result is not None
    assert final_url is not None


@pytest.mark.asyncio
async def test_process_url_success(crawler):
    """Test _process_url method with successful processing."""
    # Create a target
    target = CrawlTarget(
        url="https://example.com/docs", depth=2, content_types=["text/html"]
    )

    # Create stats
    stats = CrawlStats()

    # Create visited URLs set
    visited_urls = set()

    # Call the method
    result_data, new_links, metrics, error = await crawler._process_url(
        "https://example.com/docs/page1", 0, target, stats, visited_urls
    )

    # Verify results
    assert result_data is not None
    assert len(result_data.documents) == 1
    assert result_data.documents[0]["url"] == "https://example.com/docs/page1"
    assert result_data.documents[0]["title"] == "Test Document"
    assert len(new_links) > 0  # Should have found links
    # Check that metrics are in the expected nested format
    assert "https://example.com/docs/page1" in metrics
    assert "score" in metrics["https://example.com/docs/page1"]
    assert metrics["https://example.com/docs/page1"]["score"] == 0.9
    assert stats.successful_crawls == 1
    assert stats.pages_crawled == 1

    # Verify URL was added to visited_urls
    assert "https://example.com/docs/page1" in visited_urls


@pytest.mark.asyncio
async def test_process_url_max_pages_limit(crawler):
    """Test _process_url method with max_pages limit reached."""
    # Create a target with max_pages=1
    target = CrawlTarget(
        url="https://example.com/docs",
        depth=2,
        content_types=["text/html"],
        max_pages=1,
    )

    # Create stats
    stats = CrawlStats()

    # Create visited URLs set with one URL already visited
    visited_urls = {"https://example.com/docs/already-visited"}

    # Call the method
    result_data, new_links, metrics, error = await crawler._process_url(
        "https://example.com/docs/page1", 0, target, stats, visited_urls
    )

    # Verify results - should return None due to max_pages limit
    assert result_data is None
    assert new_links == []
    assert metrics == {}


@pytest.mark.asyncio
async def test_process_url_already_visited(crawler):
    """Test _process_url method with already visited URL."""
    # Create a target
    target = CrawlTarget(
        url="https://example.com/docs", depth=2, content_types=["text/html"]
    )

    # Create stats
    stats = CrawlStats()

    # Create visited URLs set with the URL already visited
    url_info = create_url_info("https://example.com/docs/page1")
    visited_urls = {url_info.normalized_url}

    # Call the method
    result_data, new_links, metrics, error = await crawler._process_url(
        "https://example.com/docs/page1", 0, target, stats, visited_urls
    )

    # Verify results - should return None due to already visited URL
    assert result_data is None
    assert new_links == []
    assert metrics == {}


@pytest.mark.asyncio
async def test_initialize_crawl_queue():
    """Test _initialize_crawl_queue method with URL."""
    crawler = DocumentationCrawler(config=CrawlerConfig(use_duckduckgo=False))

    # Create a target with a URL
    target = CrawlTarget(
        url="https://example.com/docs", depth=2, content_types=["text/html"]
    )

    # Call the method
    queue, start_url = await crawler._initialize_crawl_queue(target)

    # Verify results
    assert len(queue) == 1
    assert queue[0] == ("https://example.com/docs", 0)
    assert start_url == "https://example.com/docs"


@pytest.mark.asyncio
@patch("src.utils.project_identifier.ProjectIdentifier.discover_doc_url")
async def test_initialize_crawl_queue_with_package(mock_discover_doc_url):
    """Test _initialize_crawl_queue method with package name."""
    # Mock the discover_doc_url method to return a URL
    mock_discover_doc_url.return_value = "https://docs.example-package.org"

    crawler = DocumentationCrawler(config=CrawlerConfig(use_duckduckgo=False))

    # Create a target with a package name
    target = CrawlTarget(url="example-package", depth=2, content_types=["text/html"])

    # Call the method
    queue, start_url = await crawler._initialize_crawl_queue(target)

    # Verify results
    assert len(queue) == 1
    assert queue[0] == ("https://docs.example-package.org", 0)
    assert start_url == "https://docs.example-package.org"

    # Verify the discover_doc_url method was called with the package name
    mock_discover_doc_url.assert_called_once_with("example-package")


@pytest.mark.asyncio
@patch("src.utils.project_identifier.ProjectIdentifier.discover_doc_url")
async def test_initialize_crawl_queue_with_package_discovery_failure(
    mock_discover_doc_url,
):
    """Test _initialize_crawl_queue method with package name that fails discovery."""
    # Mock the discover_doc_url method to return None
    mock_discover_doc_url.return_value = None

    crawler = DocumentationCrawler(config=CrawlerConfig(use_duckduckgo=False))

    # Create a target with a package name
    target = CrawlTarget(url="unknown-package", depth=2, content_types=["text/html"])

    # Call the method - should raise ValueError
    with pytest.raises(ValueError):
        await crawler._initialize_crawl_queue(target)


def test_generate_search_queries():
    """Test _generate_search_queries method."""
    crawler = DocumentationCrawler(config=CrawlerConfig(use_duckduckgo=False))

    # Test with library type and version
    identity = ProjectIdentity(
        name="example-lib", type=ProjectType.LIBRARY, version="1.2.3"
    )

    queries = crawler._generate_search_queries("https://example.com/docs", identity)
    assert "example-lib 1.2.3 documentation" in queries
    assert "example-lib 1.2 documentation" in queries
    assert "example-lib documentation" in queries

    # Test with library type without version
    identity = ProjectIdentity(name="example-lib", type=ProjectType.LIBRARY)

    queries = crawler._generate_search_queries("https://example.com/docs", identity)
    assert "example-lib documentation" in queries

    # Test with non-library type
    identity = ProjectIdentity(
        name="example-framework", type=ProjectType.FRAMEWORK, version="2.0"
    )

    queries = crawler._generate_search_queries("https://example.com/docs", identity)
    assert "example-framework 2.0 documentation" in queries
    assert "example-framework documentation" in queries

    # Test with unknown name
    identity = ProjectIdentity(name="unknown", type=ProjectType.UNKNOWN)

    queries = crawler._generate_search_queries("https://example.com/docs", identity)
    assert "example.com documentation" in queries


@pytest.mark.asyncio
async def test_crawl_basic(crawler):
    """Test the main crawl method with basic configuration."""
    # Call the crawl method
    result = await crawler.crawl(
        target_url="https://example.com/docs",
        depth=1,
        follow_external=False,
        content_types=["text/html"],
        exclude_patterns=[],
        required_patterns=[],
        max_pages=1,
        allowed_paths=[],
        excluded_paths=[],
    )

    # Verify results
    assert result is not None
    assert isinstance(result, OrchestratorResult)
    assert result.stats.pages_crawled == 1
    assert result.stats.successful_crawls == 1
    assert result.stats.failed_crawls == 0
    assert len(result.documents) == 1
    assert result.documents[0]["title"] == "Test Document"
    assert len(result.crawled_urls) == 1
    assert "https://example.com/docs" in result.crawled_urls


@pytest.mark.asyncio
async def test_crawl_with_depth(crawler):
    """Test the crawl method with depth > 1."""
    # Call the crawl method with depth=2
    result = await crawler.crawl(
        target_url="https://example.com/docs",
        depth=2,
        follow_external=False,
        content_types=["text/html"],
        exclude_patterns=[],
        required_patterns=[],
        max_pages=5,  # Allow multiple pages
        allowed_paths=[],
        excluded_paths=[],
    )

    # Verify results
    assert result is not None
    assert result.stats.pages_crawled > 1  # Should crawl more than just the initial URL
    assert len(result.documents) > 1
    assert len(result.crawled_urls) > 1


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
        required_patterns=[],
        max_pages=1,
        allowed_paths=[],
        excluded_paths=[],
    )

    # Verify results
    assert result is not None
    assert result.stats.pages_crawled == 1

    # Verify the identify_from_url method was called
    mock_identify_from_url.assert_called_once_with("https://example.com/docs")


@pytest.mark.asyncio
@patch("src.utils.search.DuckDuckGoSearch.search")
async def test_crawl_with_duckduckgo(mock_ddg_search):
    """Test the crawl method with DuckDuckGo search."""
    # Mock the DuckDuckGo search method
    mock_ddg_search.return_value = [
        {
            "title": "Example Docs",
            "url": "https://example.com/docs/guide",
            "description": "Guide",
        },
        {
            "title": "Example API",
            "url": "https://example.com/docs/api",
            "description": "API",
        },
    ]

    # Create a crawler with DuckDuckGo enabled but mocked
    config = CrawlerConfig(use_duckduckgo=True)
    crawler = DocumentationCrawler(config=config)

    # Patch the _process_url method to avoid actual processing
    crawler._process_url = AsyncMock(return_value=(None, [], {}, None))

    # Call the crawl method
    await crawler.crawl(
        target_url="https://example.com/docs",
        depth=1,
        follow_external=False,
        content_types=["text/html"],
        exclude_patterns=[],
        required_patterns=[],
        max_pages=5,
        allowed_paths=[],
        excluded_paths=[],
    )

    # Verify the DuckDuckGo search method was called (on the patched mock)
    assert mock_ddg_search.called

    # Clean up
    await crawler.cleanup()


# Removed test_cleanup as it's not applicable for this implementation
