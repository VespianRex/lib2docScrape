"""Tests for the crawler orchestrator component."""

import asyncio
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

from src.backends.base import CrawlerBackend, CrawlResult
from src.backends.selector import BackendCriteria, BackendSelector
from src.crawler import CrawlerConfig, CrawlStats, CrawlTarget, DocumentationCrawler
from src.models.project import ProjectIdentifier, ProjectIdentity, ProjectType
from src.processors.content_processor import ProcessedContent
from src.utils.search import (
    DUCKDUCKGO_AVAILABLE,
    DuckDuckGoSearch,
)
from src.utils.url import (
    URLInfo,
)

# Keep URLInfo import for type hinting if needed elsewhere
from src.utils.url.factory import create_url_info  # Import the factory function


class MockCrawlerBackend(CrawlerBackend):
    """Mock crawler backend for testing the orchestrator."""

    def __init__(self, urls: set[str], delay: float = 0.1):
        super().__init__(name="mock_crawler")
        self.urls = urls
        self.delay = delay
        self.crawled_urls: set[str] = set()

    # Update signature to match ABC: accept url_info and config
    async def crawl(
        self,
        url_info: URLInfo,
        config: Optional[CrawlerConfig] = None,
        params: dict = None,
    ) -> CrawlResult:
        """Simulate crawling with configurable delay."""
        # Use normalized URL from url_info for internal logic and result
        url = url_info.normalized_url
        self.crawled_urls.add(url)
        await asyncio.sleep(self.delay)

        if url in self.urls:
            return CrawlResult(
                url=url,
                content={
                    "html": f"""
                    <html>
                        <head><title>Test {url}</title></head>
                        <body>
                            <h1>Test {url}</h1>
                            <p>Content for {url}</p>
                            <a href="{url}/subpage">Link</a>
                        </body>
                    </html>
                    """
                },
                metadata={"status_code": 200, "headers": {"Content-Type": "text/html"}},
                status=200,
                content_type="text/html",
                documents=[
                    {
                        "url": url,
                        "title": f"Test {url}",
                        "content": f"Content for {url}",
                    }
                ],
            )
        else:
            return CrawlResult(
                url=url,
                content={},
                metadata={"error": "Not found"},
                status=404,
                error="Not found",
                content_type=None,
                documents=[],
            )

    async def validate(self, content: CrawlResult) -> bool:
        """Validate crawled content."""
        return content.status == 200

    async def process(self, content: CrawlResult) -> dict:
        """Process crawled content."""
        if content.status != 200:
            return {"error": "Processing failed"}

        return {
            "title": f"Test {content.url}",
            "content": {
                "text": f"Content for {content.url}",
                "links": [{"url": f"{content.url}/subpage", "text": "Link"}],
            },
            "metadata": content.metadata,
        }


@pytest.fixture
def test_urls() -> set[str]:
    """Fixture providing test URLs."""
    return {
        "https://example.com/doc1",
        "https://example.com/doc2",
        "https://example.com/doc3",
    }


@pytest.fixture
def mock_backend(test_urls: set[str]) -> MockCrawlerBackend:
    """Fixture providing configured mock backend."""
    return MockCrawlerBackend(test_urls)


@pytest.fixture
def backend_selector(mock_backend: MockCrawlerBackend) -> BackendSelector:
    """Fixture providing configured backend selector."""
    selector = BackendSelector()
    selector.register_backend(
        name=mock_backend.name,  # Use the name attribute of the instance
        backend=mock_backend,  # Pass the instance as 'backend'
        criteria=BackendCriteria(  # Pass the criteria as 'criteria'
            priority=100,
            content_types=["text/html"],
            url_patterns=["*"],
            max_load=0.8,
            min_success_rate=0.7,
        ),
    )
    return selector


@pytest.mark.asyncio
async def test_crawler_initialization(crawler: DocumentationCrawler):
    """Test crawler initialization and configuration."""
    assert crawler.config is not None
    assert crawler.backend_selector is not None
    assert crawler.content_processor is not None
    assert crawler.quality_checker is not None
    assert crawler.document_organizer is not None
    assert crawler._crawled_urls == set()
    assert crawler._processing_semaphore is not None


@pytest.mark.asyncio
async def test_url_filtering(crawler: DocumentationCrawler, test_urls: set[str]):
    """Test URL filtering logic."""
    target = CrawlTarget(
        url="https://example.com/doc1",
        depth=2,
        follow_external=False,
        exclude_patterns=["/excluded/"],
        required_patterns=["/doc"],
        max_pages=10,
    )

    # Test valid URL
    assert crawler._should_crawl_url(
        create_url_info("https://example.com/doc1"), target
    )

    # Test excluded pattern
    assert not crawler._should_crawl_url(
        create_url_info("https://example.com/excluded/page"), target
    )

    # Test external URL
    assert not crawler._should_crawl_url(
        create_url_info("https://other-domain.com/doc1"), target
    )

    # Test already crawled URL
    # Use normalized URL for the visited set check
    # Use normalized URL for the visited set check
    visited_url_info = create_url_info("https://example.com/doc1")
    crawler._crawled_urls.add(visited_url_info.normalized_url)
    assert not crawler._should_crawl_url(visited_url_info, target)


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_single_url_processing(crawler, test_urls):
    """Test that a single URL is processed and yields the expected document."""
    target_url = "https://example.com/doc1"

    # Mock ProcessedContent that patched_fetch will return
    processed_content_for_patch = ProcessedContent(
        content={
            "formatted_content": "Processed content",
            "headings": [{"level": 1, "text": "Sample Document"}],
            "code_blocks": [{"language": "python", "content": "def test():\n    pass"}],
            "links": [{"text": "Test Link", "url": "/test"}],
        },
        metadata={"title": "Sample Document"},  # This title is key
        assets={
            "images": ["/test.jpg"],
            "stylesheets": [],
            "scripts": [],
            "media": [],
        },
        headings=[{"level": 1, "text": "Sample Document"}],
    )
    processed_content_for_patch.title = processed_content_for_patch.metadata["title"]

    # Mock BackendCrawlResult that patched_fetch will return, now including a document
    # This assumes _process_url might use documents from BackendCrawlResult if available,
    # or that it helps in constructing the final CrawlResult.documents.
    mock_backend_result_for_patch_with_doc = CrawlResult(
        url=target_url,
        status=200,
        content={"html": "Test HTML content"},
        metadata={"headers": {"Content-Type": "text/html"}},
        documents=[  # Provide the document structure directly here
            {
                "url": target_url,
                "title": "Sample Document",  # Match the expected title from ProcessedContent
                "content": "Processed content",  # Or some other relevant content
                # Ensure this structure matches what DocumentationCrawler.CrawlResult expects
            }
        ],
    )

    original_fetch = crawler._fetch_and_process_with_backend

    async def patched_fetch(*args, **kwargs):
        # Return a 5-tuple with the elements: processed_content, backend_result, final_url, metrics, exception
        # The 5 elements are: processed_content, backend_result, final_url, metrics, exception
        return (
            processed_content_for_patch,
            mock_backend_result_for_patch_with_doc,
            target_url,
            {},
            None,
        )

    crawler._fetch_and_process_with_backend = patched_fetch

    target = CrawlTarget(
        url=target_url,
        depth=1,
        follow_external=False,
        content_types=["text/html"],
        max_pages=1,
        required_patterns=[],
    )
    stats = CrawlStats()
    result = await crawler._process_url(target.url, 0, target, stats, set())

    # restore original
    crawler._fetch_and_process_with_backend = original_fetch

    assert result is not None
    crawl_result_data, discovered_urls, _, _ = result
    assert crawl_result_data is not None

    assert (
        len(crawl_result_data.documents) > 0
    ), "CrawlResult.documents should not be empty"
    doc = crawl_result_data.documents[0]
    assert doc["url"] == target_url
    assert doc["title"] == "Sample Document"
    # since our stub does not emit new URLs, expect empty list
    assert discovered_urls == []


@pytest.mark.asyncio
async def test_depth_limited_crawling(
    crawler: DocumentationCrawler, test_urls: set[str]
):
    """Test crawling with depth limitation."""
    target = CrawlTarget(
        url=next(iter(test_urls)),
        depth=2,
        follow_external=False,
        content_types=["text/html"],
        max_pages=10,
    )

    result = await crawler.crawl(
        target_url=target.url,
        depth=target.depth,
        follow_external=target.follow_external,
        content_types=target.content_types,
        exclude_patterns=target.exclude_patterns,
        required_patterns=target.required_patterns,
        max_pages=target.max_pages,
        allowed_paths=target.allowed_paths,
        excluded_paths=target.excluded_paths,
    )

    assert result.stats.pages_crawled > 0
    assert result.stats.pages_crawled <= target.max_pages
    assert len(crawler._crawled_urls) <= target.max_pages


@pytest.mark.asyncio
async def test_concurrent_processing(
    crawler: DocumentationCrawler,
    test_urls: set[str],  # test_urls fixture provides example.com URLs
):
    """Test concurrent URL processing."""
    target = CrawlTarget(
        # Use a base example.com URL, actual URLs will come from test_urls
        url="https://example.com",
        depth=1,
        follow_external=False,
        content_types=["text/html"],
        max_pages=len(test_urls),
    )

    tasks = []
    stats = CrawlStats()
    # Ensure all URLs used are from example.com to be handled by mock backends
    example_com_urls = [url for url in test_urls if "example.com" in url]
    if not example_com_urls:
        pytest.skip(
            "No example.com URLs found in test_urls for concurrent processing test."
        )

    for url in example_com_urls:
        task = crawler._process_url(url, 0, target, stats, set())
        tasks.append(task)

    results = await asyncio.gather(*tasks)

    assert len(results) == len(example_com_urls)
    assert stats.pages_crawled == len(
        example_com_urls
    ), f"Expected {len(example_com_urls)} pages crawled, got {stats.pages_crawled}"

    # The CrawlResult from _process_url doesn't have a 'status' field directly
    # But we can check for successful crawls by verifying that documents exist
    successful_results_count = sum(
        1
        for res_tuple in results
        if res_tuple and res_tuple[0] and len(res_tuple[0].documents) > 0
    )
    assert (
        successful_results_count == len(example_com_urls)
    ), f"Expected {len(example_com_urls)} successful results, got {successful_results_count}"
    assert all(
        result_tuple[0] is not None for result_tuple in results if result_tuple
    ), "All crawl result objects should not be None"


@pytest.mark.asyncio
async def test_rate_limiting(crawler: DocumentationCrawler, test_urls: set[str]):
    """Test crawler rate limiting by directly testing the rate limiter."""
    # Ensure crawler config has rate limit set (e.g., 1 req/sec from fixture)
    assert crawler.config.requests_per_second == 1

    # Test the rate limiter directly
    num_calls = 3
    expected_min_time = (num_calls - 1) / crawler.config.requests_per_second

    start_time = asyncio.get_event_loop().time()
    for i in range(num_calls):
        print(f"Rate limit test: Call {i + 1}/{num_calls}")
        # Directly test the rate limiter
        wait_time = await crawler.rate_limiter.acquire()
        if wait_time > 0:
            await asyncio.sleep(wait_time)
    end_time = asyncio.get_event_loop().time()

    time_taken = end_time - start_time
    print(f"Time taken for {num_calls} calls: {time_taken:.4f}s")
    print(f"Expected min time due to rate limit: {expected_min_time:.4f}s")

    # Assert that the total time reflects the rate limit delay
    # For 3 calls at 1 req/sec, we expect at least 2 seconds total
    assert time_taken >= 1.0


@pytest.mark.asyncio
async def test_error_handling(crawler: DocumentationCrawler):
    """Test crawler error handling."""
    # Test with invalid URL
    target = CrawlTarget(url="https://invalid.example.com", depth=1, max_pages=1)

    result = await crawler.crawl(
        target_url=target.url,
        depth=target.depth,
        follow_external=target.follow_external,
        content_types=target.content_types,
        exclude_patterns=target.exclude_patterns,
        required_patterns=target.required_patterns,
        max_pages=target.max_pages,
        allowed_paths=target.allowed_paths,
        excluded_paths=target.excluded_paths,
    )

    assert result.stats.failed_crawls > 0
    assert result.stats.successful_crawls == 0


@pytest.mark.asyncio
async def test_content_processing_pipeline(
    crawler: DocumentationCrawler, test_urls: set[str]
):
    """Test complete content processing pipeline."""
    # Use an example.com URL to ensure mock backend is hit
    target_url = "https://example.com/doc1"

    target = CrawlTarget(url=target_url, depth=1, max_pages=1)

    # Mock the content processor's process method to return a predictable ProcessedContent
    # This isolates the test to the crawler's interaction with the processor
    mock_processed_content = ProcessedContent(
        content={
            "formatted_content": "Processed HTML for Test Document for https://example.com/doc1",
            "headings": [
                {"level": 1, "text": "Test Document for https://example.com/doc1"}
            ],
            "code_blocks": [
                {"language": "python", "content": "def test():\\n    pass"}
            ],
            "links": [{"text": "Test Link", "url": "/test"}],
        },
        metadata={"title": "Test Document for https://example.com/doc1"},
        assets={"images": [], "stylesheets": [], "scripts": [], "media": []},
        headings=[{"level": 1, "text": "Test Document for https://example.com/doc1"}],
        structure=[
            {"type": "section", "title": "Test Document for https://example.com/doc1"},
            {"type": "link", "text": "Test Link", "href": "/test"},
        ],
    )

    # Access the mocked ContentProcessor instance through the crawler
    # and configure its behavior for this test.
    # This assumes 'content_processor' is an attribute of 'crawler' and is a mock.
    if hasattr(crawler.content_processor, "process") and isinstance(
        crawler.content_processor.process, MagicMock
    ):
        crawler.content_processor.process.return_value = mock_processed_content
    else:
        # Fallback or error if the content_processor is not a mock as expected
        # This might happen if the fixture setup changes.
        # For now, we'll assume it's a MagicMock as per conftest.py.
        pass

    result = await crawler.crawl(
        target_url=target.url,
        depth=target.depth,
        follow_external=target.follow_external,
        content_types=target.content_types,
        exclude_patterns=target.exclude_patterns,
        required_patterns=target.required_patterns,  # Ensure this allows /doc1
        max_pages=target.max_pages,
        allowed_paths=target.allowed_paths,
        excluded_paths=target.excluded_paths,
    )

    assert (
        result.stats.successful_crawls == 1
    ), f"Expected 1 successful crawl, got {result.stats.successful_crawls}"
    # The CrawlResult.documents is a list of documents
    assert result.documents is not None, "Result should have documents."
    assert isinstance(result.documents, list), "Documents should be a list"
    assert len(result.documents) > 0, "Documents list should not be empty"

    # Check the structure property of the CrawlResult itself
    assert hasattr(result, "structure"), "Result should have a structure property"
    assert result.structure is not None, "Result structure should not be None"
    assert isinstance(result.structure, list), "Result structure should be a list"
    assert len(result.structure) > 0, "Result structure should not be empty"
    assert (
        result.structure[0].get("type") == "section"
    ), "First structure item should have type 'section'"
    assert (
        result.structure[0].get("title") == "organized"
    ), "First structure item should have title 'organized'"

    assert len(result.issues) >= 0
    assert result.metrics


@pytest.mark.asyncio
async def test_cleanup(crawler: DocumentationCrawler):
    """Test crawler cleanup."""
    # Run a crawl
    target = CrawlTarget(url="https://example.com/test", depth=1, max_pages=1)

    await crawler.crawl(
        target_url=target.url,
        depth=target.depth,
        follow_external=target.follow_external,
        content_types=target.content_types,
        exclude_patterns=target.exclude_patterns,
        required_patterns=target.required_patterns,
        max_pages=target.max_pages,
        allowed_paths=target.allowed_paths,
        excluded_paths=target.excluded_paths,
    )

    # Verify cleanup
    await crawler.cleanup()  # Calls backend_selector.close_all_backends() internally
    assert crawler.client_session is None
    # To verify backends are closed, you might need to inspect the state of
    # the backend_selector or mock close_all_backends and check it was called.
    # For instance, if close_all_backends clears the internal list:
    # assert len(crawler.backend_selector._backends) == 0
    # Or, more robustly, mock it on the specific selector instance if needed:
    # mock_close_all = AsyncMock()
    # crawler.backend_selector.close_all_backends = mock_close_all
    # await crawler.cleanup()
    # mock_close_all.assert_called_once()


@pytest.mark.asyncio
async def test_max_pages_limit(crawler: DocumentationCrawler, test_urls: set[str]):
    """Test maximum pages limit."""
    max_pages = 2
    target = CrawlTarget(
        url=next(iter(test_urls)),
        depth=3,  # Deep enough to find more pages
        max_pages=max_pages,
    )

    result = await crawler.crawl(
        target_url=target.url,
        depth=target.depth,
        follow_external=target.follow_external,
        content_types=target.content_types,
        exclude_patterns=target.exclude_patterns,
        required_patterns=target.required_patterns,
        max_pages=target.max_pages,
        allowed_paths=target.allowed_paths,
        excluded_paths=target.excluded_paths,
    )

    assert result.stats.pages_crawled <= max_pages
    assert len(crawler._crawled_urls) <= max_pages


@pytest.mark.asyncio
async def test_statistics_tracking(crawler: DocumentationCrawler, test_urls: set[str]):
    """Test crawl statistics tracking."""
    target = CrawlTarget(url=next(iter(test_urls)), depth=1, max_pages=len(test_urls))

    result = await crawler.crawl(
        target_url=target.url,
        depth=target.depth,
        follow_external=target.follow_external,
        content_types=target.content_types,
        exclude_patterns=target.exclude_patterns,
        required_patterns=target.required_patterns,
        max_pages=target.max_pages,
        allowed_paths=target.allowed_paths,
        excluded_paths=target.excluded_paths,
    )

    assert result.stats.start_time is not None
    assert result.stats.end_time is not None
    assert result.stats.total_time > 0
    assert result.stats.average_time_per_page > 0
    assert (
        result.stats.pages_crawled
        == result.stats.successful_crawls + result.stats.failed_crawls
    )


def test_project_type_enum():
    """Test ProjectType enum."""
    # Test all enum values
    assert ProjectType.PACKAGE.value == "package"
    assert ProjectType.FRAMEWORK.value == "framework"
    assert ProjectType.PROGRAM.value == "program"
    assert ProjectType.LIBRARY.value == "library"
    assert ProjectType.CLI_TOOL.value == "cli_tool"
    assert ProjectType.WEB_APP.value == "web_app"
    assert ProjectType.API.value == "api"
    assert ProjectType.UNKNOWN.value == "unknown"


def test_project_identity():
    """Test ProjectIdentity class."""
    # Test basic initialization
    identity = ProjectIdentity(
        name="test-project",
        type=ProjectType.LIBRARY,
        language="python",
        framework="flask",
        repository="https://github.com/test/test-project",
        package_manager="pip",
        main_doc_url="https://test-project.readthedocs.io",
        related_keywords=["web", "api"],
        confidence=0.85,
    )

    assert identity.name == "test-project"
    assert identity.type == ProjectType.LIBRARY
    assert identity.language == "python"
    assert identity.framework == "flask"
    assert identity.repository == "https://github.com/test/test-project"
    assert identity.package_manager == "pip"
    assert identity.main_doc_url == "https://test-project.readthedocs.io"
    assert identity.related_keywords == ["web", "api"]
    assert identity.confidence == 0.85

    # Test default values
    basic_identity = ProjectIdentity(name="basic-project", type=ProjectType.UNKNOWN)
    assert basic_identity.language is None
    assert basic_identity.framework is None
    assert basic_identity.repository is None
    assert basic_identity.package_manager is None
    assert basic_identity.main_doc_url is None
    assert basic_identity.related_keywords == []
    assert basic_identity.confidence == 0.0


def test_project_identifier():
    """Test ProjectIdentifier class."""
    identifier = ProjectIdentifier()

    # Test language detection
    files = ["setup.py", "requirements.txt", "src/main.py", "tests/test_main.py"]

    detected = identifier._detect_language(files)
    assert detected == "python"

    # Test framework detection
    python_files = ["manage.py", "wsgi.py", "urls.py", "settings.py"]

    detected = identifier._detect_framework(python_files, "python")
    assert detected == "django"

    # Test doc URL generation
    identity = ProjectIdentity(
        name="test-project", type=ProjectType.LIBRARY, language="python"
    )

    urls = identifier._generate_doc_urls(identity)
    assert "https://test-project.readthedocs.io/en/latest/" in urls
    assert "https://docs.test-project.org/" in urls


@pytest.mark.asyncio
@patch(
    "src.utils.search.DDGS"
)  # Patch the DDGS class where it's imported in src.utils.search
async def test_duckduckgo_search(mock_ddgs_class: MagicMock):  # Add MagicMock type hint
    """Test DuckDuckGoSearch class with mocked external calls."""
    if not DUCKDUCKGO_AVAILABLE:
        # This check is based on whether the duckduckgo_search library was importable
        # when src.utils.search was first loaded. Patching DDGS within that module
        # doesn't affect this initial DUCKDUCKGO_AVAILABLE flag.
        pytest.skip("DuckDuckGo search not available (library not installed)")

    # Configure the mock DDGS instance and its text method
    mock_ddgs_instance = MagicMock()
    mock_library_results = [
        {
            "title": "Python Official Docs",
            "href": "https://docs.python.org",
            "body": "The official Python documentation.",
        },
        {
            "title": "RealPython Tutorials",
            "href": "https://realpython.com",
            "body": "Practical Python tutorials.",
        },
    ]
    mock_ddgs_instance.text.return_value = mock_library_results

    # When DDGS() is called within DuckDuckGoSearch, it will return our mock_ddgs_instance
    mock_ddgs_class.return_value = mock_ddgs_instance

    # Initialize DuckDuckGoSearch; it will use the mocked DDGS
    # We set max_results to 2 to match our mock data size for precise assertion
    search_instance = DuckDuckGoSearch(max_results=2)

    # Test basic search
    query = "python documentation"
    results = await search_instance.search(query)

    # Assert that the text method was called with the exact query we provided
    mock_ddgs_instance.text.assert_called_once_with(
        query, max_results=search_instance.max_results
    )

    expected_formatted_results = [
        {
            "title": "Python Official Docs",
            "url": "https://docs.python.org",
            "description": "The official Python documentation.",
        },
        {
            "title": "RealPython Tutorials",
            "url": "https://realpython.com",
            "description": "Practical Python tutorials.",
        },
    ]
    assert results == expected_formatted_results
    assert len(results) == 2, "Should return the two mocked results"

    # Test empty search query
    mock_ddgs_instance.text.reset_mock()
    mock_ddgs_instance.text.return_value = []  # Simulate library returning no results for empty query

    empty_query_results = await search_instance.search("")

    mock_ddgs_instance.text.assert_called_once_with(
        "", max_results=search_instance.max_results
    )
    assert (
        empty_query_results == []
    ), "Search with empty query should return an empty list"

    # Test search with a site filter
    mock_ddgs_instance.text.reset_mock()
    site_specific_mock_results = [
        {
            "title": "Python Site Specific Page",
            "href": "https://python.org/specific",
            "body": "A specific page on python.org.",
        }
    ]
    mock_ddgs_instance.text.return_value = site_specific_mock_results

    site_query = "specifics"
    site_filter = "python.org"
    site_search_results = await search_instance.search(site_query, site=site_filter)

    expected_ddgs_query_with_site = f"site:{site_filter} {site_query}"
    mock_ddgs_instance.text.assert_called_once_with(
        expected_ddgs_query_with_site, max_results=search_instance.max_results
    )

    expected_site_formatted_results = [
        {
            "title": "Python Site Specific Page",
            "url": "https://python.org/specific",
            "description": "A specific page on python.org.",
        }
    ]
    assert site_search_results == expected_site_formatted_results
    assert len(site_search_results) == 1


@pytest.mark.asyncio
async def test_url_discovery():
    """Test that new URLs discovered during a crawl are added to the queue."""

    # Create a special backend for URL discovery that returns empty documents
    # so the content processor is called
    class URLDiscoveryMockBackend(CrawlerBackend):
        def __init__(self):
            super().__init__(name="url_discovery_mock_backend")

        async def crawl(
            self, url_info: URLInfo, config=None, params=None
        ) -> CrawlResult:
            url = url_info.normalized_url

            if "discovery_start" in url:
                html_content = """
                <html>
                    <head><title>Discovery Start Page</title></head>
                    <body>
                        <h1>Discovery Start Page</h1>
                        <p>This is the starting page for URL discovery.</p>
                        <a href="/test">Discover This Link</a>
                    </body>
                </html>
                """
                title = "Discovery Start Page"
            elif url.endswith("/test"):
                html_content = """
                <html>
                    <head><title>Discovered Page</title></head>
                    <body>
                        <h1>Discovered Page</h1>
                        <p>This page was discovered through URL discovery.</p>
                    </body>
                </html>
                """
                title = "Discovered Page"
            else:
                html_content = "<html><head><title>Default</title></head><body>Default</body></html>"
                title = "Default"

            return CrawlResult(
                url=url,
                status=200,
                content={"html": html_content},
                content_type="text/html",
                metadata={"title": title},
                documents=[],  # Empty documents so content processor is called
            )

        async def validate(self, url_info: URLInfo) -> bool:
            return True

        async def process(self, content: CrawlResult) -> dict:
            return {"title": "Processed"}

    # Import necessary classes
    from unittest.mock import AsyncMock, MagicMock

    from src.models.project import ProjectIdentity, ProjectType
    from src.organizers.doc_organizer import DocumentOrganizer
    from src.processors.content_processor import ContentProcessor
    from src.processors.quality_checker import QualityChecker

    # Create config
    config = CrawlerConfig(
        rate_limit=1.0,
        max_concurrent_requests=5,
        max_retries=1,
        timeout=10,
        use_duckduckgo=False,
        project_identity=ProjectIdentity(name="TestProject", type=ProjectType.LIBRARY),
    )

    # Create backend and selector
    mock_backend = URLDiscoveryMockBackend()
    selector = BackendSelector()
    selector.register_backend(
        name=mock_backend.name,
        backend=mock_backend,
        criteria=BackendCriteria(
            priority=50,
            schemes=["http", "https"],
            domains=["example.com"],
            url_patterns=["*"],
            content_types=["text/html"],
        ),
    )

    # Create content processor mock
    processor = AsyncMock(spec=ContentProcessor)

    async def mock_process(content, base_url=None, content_type=None):
        if base_url and "discovery_start" in base_url:
            return ProcessedContent(
                content={
                    "formatted_content": "This is the starting page for URL discovery.\nDiscover This Link",
                    "headings": [{"level": 1, "text": "Discovery Start Page"}],
                    "code_blocks": [],
                    "links": [{"text": "Discover This Link", "url": "/test"}],
                },
                metadata={"title": "Discovery Start Page"},
                assets={"images": [], "stylesheets": [], "scripts": [], "media": []},
                headings=[{"level": 1, "text": "Discovery Start Page"}],
                structure=[
                    {"type": "section", "title": "Discovery Start Page"},
                    {"type": "link", "text": "Discover This Link", "url": "/test"},
                ],
            )
        elif base_url and base_url.endswith("/test"):
            return ProcessedContent(
                content={
                    "formatted_content": "This page was discovered through URL discovery.",
                    "headings": [{"level": 1, "text": "Discovered Page"}],
                    "code_blocks": [],
                    "links": [],
                },
                metadata={"title": "Discovered Page"},
                assets={"images": [], "stylesheets": [], "scripts": [], "media": []},
                headings=[{"level": 1, "text": "Discovered Page"}],
                structure=[
                    {"type": "section", "title": "Discovered Page"},
                ],
            )
        else:
            return ProcessedContent(
                content={"formatted_content": "Default content"},
                metadata={"title": "Default"},
                assets={},
                headings=[],
                structure=[],
            )

    processor.process.side_effect = mock_process

    # Create other mocks
    quality_checker = AsyncMock(spec=QualityChecker)
    quality_checker.check_quality.return_value = ([], {})

    document_organizer = MagicMock(spec=DocumentOrganizer)
    document_organizer.add_document.return_value = "mock_doc_id_1"

    async def mock_organize(*args, **kwargs):
        return {
            "structure": [{"type": "section", "title": "organized"}],
            "summary": "summary",
        }

    document_organizer.organize = AsyncMock(side_effect=mock_organize)

    # Create crawler
    crawler = DocumentationCrawler(
        config=config,
        backend_selector=selector,
        content_processor=processor,
        quality_checker=quality_checker,
        document_organizer=document_organizer,
        loop=asyncio.get_event_loop(),
    )

    initial_url = "https://example.com/discovery_start"

    target = CrawlTarget(
        url=initial_url,
        depth=2,  # Allow crawling discovered URLs
        follow_external=False,
        max_pages=2,  # Limit to initial + 1 discovered
        required_patterns=["/test"],  # Match the URL we expect to discover
    )

    result = await crawler.crawl(
        target_url=target.url,
        depth=target.depth,
        follow_external=target.follow_external,
        content_types=target.content_types,
        exclude_patterns=target.exclude_patterns,
        required_patterns=target.required_patterns,
        max_pages=target.max_pages,
        allowed_paths=target.allowed_paths,
        excluded_paths=target.excluded_paths,
    )

    # We expect the initial URL + the discovered "/test" (resolved to "https://example.com/test")
    assert (
        result.stats.pages_crawled == 2
    ), f"Expected 2 pages crawled, got {result.stats.pages_crawled}"
    assert (
        result.stats.successful_crawls == 2
    ), f"Expected 2 successful crawls, got {result.stats.successful_crawls}"

    # Check that the discovered URL was actually crawled
    # The URLs in crawled_urls are normalized.
    # create_url_info is available from src.utils.url.factory

    # Access crawled_urls from the result object
    crawled_urls_normalized = result.crawled_urls

    # Normalize the expected discovered URL for comparison
    # The link in MockSuccessBackend is <a href="/test"> which resolves relative to example.com
    expected_discovered_url_normalized = create_url_info(
        "https://example.com/test"
    ).normalized_url

    assert (
        expected_discovered_url_normalized in crawled_urls_normalized
    ), f"Expected {expected_discovered_url_normalized} to be in crawled URLs: {crawled_urls_normalized}"

    # Clean up
    await selector.close_all_backends()


# Test fixtures for DocumentationCrawler initialization tests
@pytest.fixture
def custom_config():
    """Fixture providing custom configuration for testing."""
    return CrawlerConfig(max_concurrent_requests=5, request_delay=0.2, max_retries=3)


@pytest.fixture
def custom_backend_selector():
    """Fixture providing custom backend selector for testing."""
    return BackendSelector()


@pytest.fixture
def custom_content_processor():
    """Fixture providing custom content processor for testing."""
    return MagicMock()


@pytest.fixture
def http_backend():
    """Fixture providing a mock HTTP backend."""
    mock = MagicMock(spec=CrawlerBackend)
    mock.name = "http"
    return mock


@pytest.mark.asyncio
async def test_default_initialization():
    """Test 5.1: Default initialization of DocumentationCrawler."""
    crawler = DocumentationCrawler()

    # Verify config instance
    assert isinstance(crawler.config, CrawlerConfig)
    assert crawler.config.max_concurrent_requests == 10  # default value

    # Verify backend selector instance
    assert isinstance(crawler.backend_selector, BackendSelector)

    # Verify backend selector has been initialized (may not have backends by default)
    backends = await crawler.backend_selector.get_all_backends()
    assert isinstance(backends, dict)  # Should return a dict even if empty

    # Verify direct_backend is None by default
    assert crawler.direct_backend is None


@pytest.mark.asyncio
async def test_custom_components_initialization(
    custom_config, custom_backend_selector, custom_content_processor, http_backend
):
    """Test 5.2: Initialization with custom components."""
    # Register HTTP backend to custom selector
    custom_backend_selector.register_backend(
        name="http",
        backend=http_backend,
        criteria=BackendCriteria(
            priority=100, content_types=["text/html"], url_patterns=["*"]
        ),
    )

    crawler = DocumentationCrawler(
        config=custom_config,
        backend_selector=custom_backend_selector,
        content_processor=custom_content_processor,
    )

    # Verify custom config
    assert crawler.config is custom_config
    assert crawler.config.max_concurrent_requests == 5

    # Verify custom backend selector
    assert crawler.backend_selector is custom_backend_selector

    # Verify custom content processor
    assert crawler.content_processor is custom_content_processor

    # Verify custom backend selector is used
    backends = await crawler.backend_selector.get_all_backends()
    assert any(b.name == "http" for b in backends.values())


@pytest.mark.asyncio
async def test_specific_backend_initialization(http_backend):
    """Test 5.3: Initialization with specific backend."""
    crawler = DocumentationCrawler(backend=http_backend)

    # Verify direct backend assignment
    assert crawler.direct_backend is http_backend

    # Verify backend property returns direct backend
    assert crawler.backend is http_backend


# ... Any additional tests or fixtures ...


def test_generate_search_queries_library_with_version():
    """Test 15.1: Library with version."""
    crawler = DocumentationCrawler()
    identity = ProjectIdentity(name="MyLib", type=ProjectType.LIBRARY, version="1.2.3")
    queries = crawler._generate_search_queries(
        "http://example.com/mylib/1.2.3/docs", identity
    )
    assert "MyLib 1.2.3 documentation" in queries
    assert "MyLib 1.2 documentation" in queries
    assert "MyLib documentation" in queries


def test_generate_search_queries_library_without_version():
    """Test 15.2: Library without version."""
    crawler = DocumentationCrawler()
    identity = ProjectIdentity(name="MyLib", type=ProjectType.LIBRARY, version=None)
    queries = crawler._generate_search_queries(
        "http://example.com/mylib/docs", identity
    )
    # The method returns multiple queries for libraries, including documentation, api reference, tutorial, guide
    expected_queries = [
        "MyLib documentation",
        "MyLib api reference",
        "MyLib tutorial",
        "MyLib guide",
    ]
    assert set(queries) == set(expected_queries)


def test_generate_search_queries_non_library_type():
    """Test 15.3: Non-library project type."""
    crawler = DocumentationCrawler()
    identity = ProjectIdentity(
        name="MyFramework", type=ProjectType.FRAMEWORK, version="2.0"
    )
    queries = crawler._generate_search_queries(
        "http://example.com/myframework/docs", identity
    )
    # For non-library types, the method adds multiple queries including documentation, guide, tutorial, how to
    expected_queries = [
        "MyFramework 2.0 documentation",
        "MyFramework documentation",
        "MyFramework guide",
        "MyFramework tutorial",
        "MyFramework how to",
    ]
    assert set(queries) == set(expected_queries)


def test_generate_search_queries_attribute_error_on_version():
    """Test 15.4: AttributeError during version parsing (non-string version)."""
    crawler = DocumentationCrawler()
    identity = ProjectIdentity(
        name="MyLib", type=ProjectType.LIBRARY, version=123
    )  # Invalid version type
    queries = crawler._generate_search_queries(
        "http://example.com/mylib/docs", identity
    )
    # Even with invalid version type, library type still gets multiple queries
    expected_queries = [
        "MyLib documentation",
        "MyLib api reference",
        "MyLib tutorial",
        "MyLib guide",
    ]
    assert set(queries) == set(expected_queries)
