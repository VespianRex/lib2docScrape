import asyncio
import logging  # Import logging
from typing import Any, Optional  # Add Optional, Union, Dict, Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio  # Add this import

from src.backends.base import CrawlerBackend

# Use CrawlerConfig
from src.backends.base import CrawlResult as BackendCrawlResult  # Import for mock
from src.crawler import (
    CrawlerConfig,
    CrawlResult,
    CrawlTarget,
    DocumentationCrawler,
)
from src.processors.content_processor import (
    ContentProcessor,
    ProcessedContent,
)

# Import necessary types for QualityIssue
from src.processors.quality_checker import IssueLevel, IssueType, QualityIssue

# Import for mock
from src.utils.url import URLInfo  # Corrected import path

TEST_URL = "http://example.com"


# Mock asyncio.sleep globally to make all tests run faster
@pytest.fixture(autouse=True)
async def mock_asyncio_sleep():
    """Mock asyncio.sleep to return immediately for faster tests."""

    async def fast_sleep(delay, *args, **kwargs):
        pass  # Don't sleep at all - just return immediately

    with patch.object(asyncio, "sleep", fast_sleep):
        yield


@pytest.fixture
def mock_backend():
    backend = AsyncMock(spec=CrawlerBackend)  # Use spec for better mocking
    backend.name = "mock_test_backend"

    async def crawl_side_effect(
        url_info: URLInfo,
        config: Optional[CrawlerConfig] = None,
        params: Optional[dict[str, Any]] = None,
    ):
        normalized_url = url_info.normalized_url
        if normalized_url == TEST_URL:
            return BackendCrawlResult(
                url=TEST_URL,
                content={
                    "html": f"<html><head><title>Advanced Test for {TEST_URL}</title></head><body>Mock content for {TEST_URL}. <a href='/advanced_link'>Link</a></body></html>"
                },
                metadata={"status_code": 200, "headers": {"content-type": "text/html"}},
                status=200,
            )
        elif normalized_url == f"{TEST_URL}/advanced_link":
            return BackendCrawlResult(
                url=f"{TEST_URL}/advanced_link",
                content={
                    "html": "<html><head><title>Advanced Test for advanced_link</title></head><body>Mock content for advanced_link.</body></html>"
                },
                metadata={"status_code": 200, "headers": {"content-type": "text/html"}},
                status=200,
            )
        # Default for http://nonexistent.com or other unexpected URLs in this test file's context
        return BackendCrawlResult(
            url=normalized_url,
            content={},
            metadata={},
            status=404,
            error="Not Found by mock_backend",
        )

    backend.crawl = AsyncMock(side_effect=crawl_side_effect)
    backend.process = AsyncMock(
        return_value={"processed": True}
    )  # Kept for completeness if used elsewhere
    # Add mock for get_metrics to avoid TypeError during selection
    backend.get_metrics = Mock(
        return_value={"success_rate": 1.0, "pages_crawled": 0, "errors": 0}
    )
    return backend


@pytest.fixture
def mock_content_processor():
    # Mock the process method to return a ProcessedContent object
    mock_processed = ProcessedContent(
        content={
            "formatted_content": "Processed content",
            "structure": [],
        },  # Ensure structure key exists
        metadata={"title": "Mock Title"},
        assets={"images": [], "stylesheets": [], "scripts": [], "media": []},
        headings=[],
        structure=[],  # Add top-level structure
        title="Mock Title",
    )
    processor = AsyncMock(spec=ContentProcessor)
    processor.process = AsyncMock(return_value=mock_processed)
    return processor


@pytest.fixture
def mock_quality_checker():
    checker = AsyncMock()
    # Mock check_quality to return a list with a QualityIssue instance
    # Use a valid IssueType, e.g., GENERAL
    mock_issue = QualityIssue(
        type=IssueType.GENERAL,  # Corrected: Use a valid IssueType member
        level=IssueLevel.WARNING,
        message="Low content quality",
        location="body",
    )
    # Default return value for the fixture
    checker.check_quality = AsyncMock(
        return_value=([mock_issue], {"quality_score": 0.5})
    )
    return checker


@pytest.fixture
def mock_document_organizer():
    organizer = AsyncMock()
    # Mock add_document instead of organize
    organizer.add_document = AsyncMock(return_value="mock_doc_id")
    return organizer


@pytest.fixture(scope="function")  # Explicitly set scope
def crawler(
    mock_backend, mock_content_processor, mock_quality_checker, mock_document_organizer
):
    from src.backends.selector import BackendCriteria, BackendSelector  # Import here

    # Create a fresh BackendSelector for this crawler instance
    selector_for_advanced_test = BackendSelector()
    selector_for_advanced_test.close_all_backends()  # Clear defaults from this new selector

    # Register the specific mock_backend for this test file
    selector_for_advanced_test.register_backend(
        "mock_test_backend",
        mock_backend,  # This is the AsyncMock from this file's fixture
        BackendCriteria(
            priority=100,
            content_types=["text/html"],
            url_patterns=["*"],
            max_load=0.8,
            min_success_rate=0.7,
        ),
    )

    # Mock DuckDuckGoSearch to prevent actual searches and ensure isolation
    mock_ddg_search = AsyncMock()
    mock_ddg_search.search = AsyncMock(return_value=[])

    crawler_instance = DocumentationCrawler(
        content_processor=mock_content_processor,
        quality_checker=mock_quality_checker,
        document_organizer=mock_document_organizer,
        backend_selector=selector_for_advanced_test,  # Pass the dedicated selector
    )
    crawler_instance.duckduckgo = (
        mock_ddg_search  # Replace the real DDG search with a mock
    )

    # Note: DocumentationCrawler.__init__ will still add its HTTPBackend to this selector_for_advanced_test

    crawler_instance._crawled_urls.clear()  # Clear before yielding
    yield crawler_instance
    # Finalizer: reset state and release resources
    # selector_for_advanced_test is local, no need to clear its backends explicitly here
    # as it will be garbage collected.
    crawler_instance._crawled_urls.clear()  # Clear after test too, just in case


@pytest_asyncio.fixture
async def patched_rate_limiter(crawler):
    async def mock_acquire(*args, **kwargs):
        return 0.0  # Explicitly return float

    with patch.object(crawler.rate_limiter, "acquire", side_effect=mock_acquire):
        yield


@pytest.mark.asyncio
async def test_crawl_target_stability():
    """Check if CrawlTarget instances are stable."""
    url1 = "http://original-url.com"
    ct = CrawlTarget(url=url1)
    original_url_attr = ct.url
    logging.debug(
        f"[test_crawl_target_stability] Initial: id(ct)={id(ct)}, ct.url='{ct.url}', original_url_attr='{original_url_attr}'"
    )

    # Perform some unrelated async operations or pass time
    await asyncio.sleep(0.01)

    logging.debug(
        f"[test_crawl_target_stability] After sleep: id(ct)={id(ct)}, ct.url='{ct.url}', original_url_attr='{original_url_attr}'"
    )
    assert ct.url == url1, "CrawlTarget.url should not change on its own"
    assert (
        ct.url == original_url_attr
    ), "CrawlTarget.url should match initially stored value"


@pytest.mark.asyncio
async def test_crawler_basic_crawl(crawler, patched_rate_limiter):
    """Test basic crawling functionality."""
    from src.crawler import CrawlTarget  # Re-import locally

    target = CrawlTarget(url=TEST_URL, depth=1)  # Ensure depth is set for the test
    logging.debug(
        f"[test_crawler_basic_crawl] Created target id: {id(target)}, url: {target.url}, depth: {target.depth}"
    )
    result = await crawler.crawl(
        target_url=target.url,
        depth=target.depth,
        follow_external=target.follow_external,
        content_types=target.content_types,
        exclude_patterns=target.exclude_patterns,
        include_patterns=target.include_patterns,  # Use include_patterns instead
        max_pages=target.max_pages,
        allowed_paths=target.allowed_paths,
        excluded_paths=target.excluded_paths,
    )

    assert result is not None
    assert isinstance(result, CrawlResult)
    assert result.stats.pages_crawled == 1
    assert result.stats.successful_crawls == 1
    assert result.stats.failed_crawls == 0
    assert len(result.documents) == 1
    assert result.documents[0]["url"] == TEST_URL


@pytest.mark.asyncio
async def test_crawler_failed_crawl(crawler, mock_backend):
    """Test handling of failed crawls."""
    mock_backend.crawl.side_effect = None  # Clear side_effect
    # Use BackendCrawlResult for failure case as well
    mock_backend.crawl.return_value = BackendCrawlResult(
        url="http://nonexistent.com",
        content={},
        metadata={},
        status=404,
        error="Not Found",
    )

    from src.crawler import CrawlTarget  # Re-import locally

    target = CrawlTarget(url="http://nonexistent.com", depth=0)  # Ensure depth is set
    logging.debug(
        f"[test_crawler_failed_crawl] Created target id: {id(target)}, url: {target.url}, depth: {target.depth}"
    )
    result = await crawler.crawl(
        target_url=target.url,
        depth=target.depth,
        follow_external=target.follow_external,
        content_types=target.content_types,
        exclude_patterns=target.exclude_patterns,
        include_patterns=target.include_patterns,  # Use include_patterns instead
        max_pages=target.max_pages,
        allowed_paths=target.allowed_paths,
        excluded_paths=target.excluded_paths,
    )

    assert result is not None
    assert (
        result.stats.pages_crawled == 1
    )  # URL is added to visited_urls even if crawl fails
    assert result.stats.failed_crawls == 1
    assert result.stats.successful_crawls == 0
    assert len(result.documents) == 0
    assert len(result.issues) == 1
    assert "Not Found" in result.issues[0].message  # Check specific error message


@pytest.mark.asyncio
async def test_crawler_retry_mechanism(crawler, mock_backend):
    """Test the retry mechanism for failed requests - OPTIMIZED."""
    # Make the first two attempts fail, third succeeds
    success_result = BackendCrawlResult(
        status=200,
        url=TEST_URL,
        content={"html": "<html>Success</html>"},
        metadata={"headers": {"content-type": "text/html"}},
    )

    # Use side_effect for this specific test
    mock_backend.crawl.side_effect = [
        Exception("Network error"),
        Exception("Timeout"),
        success_result,
    ]

    # Patch the retry delay function to avoid real sleeps
    with patch(
        "src.crawler.crawler.asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep:
        # Configure crawler to use minimal retry delays
        original_config = crawler.config
        crawler.config = CrawlerConfig(
            max_retries=3,
            retry_delay=0.01,  # Minimal delay
            max_retry_delay=0.05,  # Minimal max delay
            retry_backoff_factor=1.0,  # No exponential increase
        )

        try:
            target = CrawlTarget(url=TEST_URL, depth=0)
            result = await crawler.crawl(
                target_url=target.url,
                depth=target.depth,
                follow_external=target.follow_external,
                content_types=target.content_types,
                exclude_patterns=target.exclude_patterns,
                include_patterns=target.include_patterns,
                max_pages=target.max_pages,
                allowed_paths=target.allowed_paths,
                excluded_paths=target.excluded_paths,
            )

            # Verify the test worked as expected
            assert result is not None
            assert result.stats.successful_crawls == 1
            assert mock_backend.crawl.call_count == 3

            # Verify sleep was called for retries but didn't actually sleep
            assert mock_sleep.call_count == 2  # Called twice for the two retries

        finally:
            # Restore original config
            crawler.config = original_config
            # Reset side_effect
            mock_backend.crawl.side_effect = None


@pytest.mark.asyncio
@pytest.mark.skip(reason="Rate limiter timing is difficult to test reliably with mocks")
async def test_crawler_rate_limiting(crawler):
    """Test rate limiting functionality."""
    target = CrawlTarget(
        url=TEST_URL, depth=0, max_pages=1
    )  # Ensure depth and max_pages
    start_time = asyncio.get_event_loop().time()

    # Crawl multiple times
    for _ in range(3):
        crawler._crawled_urls.clear()  # Clear crawled URLs to ensure rate limiter is hit
        await crawler.crawl(
            target_url=target.url,
            depth=target.depth,
            follow_external=target.follow_external,
            content_types=target.content_types,
            exclude_patterns=target.exclude_patterns,
            include_patterns=target.include_patterns,  # Use include_patterns instead
            max_pages=target.max_pages,
            allowed_paths=target.allowed_paths,
            excluded_paths=target.excluded_paths,
        )

    end_time = asyncio.get_event_loop().time()
    time_taken = end_time - start_time

    # With default rate limiting (1 request per second)
    # 3 requests should take at least 2 seconds
    # Assert that the total time reflects *some* delay from the rate limit.
    # For 3 calls at 1 req/sec, the delay between call 1 and 2 should be ~1s.
    assert time_taken >= 1.0  # Correct assertion for token bucket


@pytest.mark.asyncio
async def test_crawler_content_processing(crawler, mock_content_processor):
    """Test content processing pipeline."""
    target = CrawlTarget(url=TEST_URL, depth=1)  # Ensure depth
    # Ensure mock backend returns the expected URL for this test
    mock_backend = crawler.backend_selector._backends["mock_test_backend"]
    mock_backend.crawl.side_effect = (
        None  # Clear potential side effects from other tests
    )
    mock_backend.crawl.return_value = BackendCrawlResult(
        url=TEST_URL,
        content={
            "html": "<html><head><title>Advanced Test for http://example.com</title></head><body>Mock content for http://example.com. <a href='/advanced_link'>Link</a></body></html>"
        },
        metadata={"status_code": 200, "headers": {"content-type": "text/html"}},
        status=200,
    )

    await crawler.crawl(
        target_url=target.url,
        depth=target.depth,
        follow_external=target.follow_external,
        content_types=target.content_types,
        exclude_patterns=target.exclude_patterns,
        include_patterns=target.include_patterns,  # Use include_patterns instead
        max_pages=target.max_pages,
        allowed_paths=target.allowed_paths,
        excluded_paths=target.excluded_paths,
    )

    # Verify content processor was called with correct input
    mock_content_processor.process.assert_called_once()
    call_args = mock_content_processor.process.call_args[0][0]
    assert isinstance(call_args, str)
    assert (
        "Mock content for http://example.com." in call_args
    )  # Check for actual mock content substring


@pytest.mark.asyncio
async def test_crawler_quality_checking(crawler, mock_quality_checker):
    """Test quality checking functionality."""
    target = CrawlTarget(url=TEST_URL, depth=0)  # Ensure depth
    # Mock check_quality to return a list with a QualityIssue instance
    mock_issue = QualityIssue(
        type=IssueType.GENERAL,  # Corrected: Use a valid IssueType member
        level=IssueLevel.WARNING,
        message="Low content quality",
        location="body",
    )
    # Set the return value for this specific test run
    mock_quality_checker.check_quality.return_value = (
        [mock_issue],
        {"quality_score": 0.5},
    )

    result = await crawler.crawl(
        target_url=target.url,
        depth=target.depth,
        follow_external=target.follow_external,
        content_types=target.content_types,
        exclude_patterns=target.exclude_patterns,
        include_patterns=target.include_patterns,  # Use include_patterns instead
        max_pages=target.max_pages,
        allowed_paths=target.allowed_paths,
        excluded_paths=target.excluded_paths,
    )

    # Assert that the issue from the quality checker is present in the results
    # The crawler adds issues returned by the quality checker.
    assert len(result.issues) == 1
    assert result.issues[0].message == "Low content quality"
    # The crawler converts enum types to strings, so compare with string value
    assert result.issues[0].type == IssueType.GENERAL.value
    # Check metrics are included, accessing via the URL key
    assert result.metrics[target.url]["quality_score"] == 0.5


@pytest.mark.asyncio
async def test_crawler_resource_cleanup(crawler):
    """Test proper cleanup of resources."""
    target = CrawlTarget(url=TEST_URL, depth=0)  # Ensure depth
    await crawler.crawl(
        target_url=target.url,
        depth=target.depth,
        follow_external=target.follow_external,
        content_types=target.content_types,
        exclude_patterns=target.exclude_patterns,
        include_patterns=target.include_patterns,  # Use include_patterns instead
        max_pages=target.max_pages,
        allowed_paths=target.allowed_paths,
        excluded_paths=target.excluded_paths,
    )

    # Test cleanup
    await crawler.cleanup()

    # Verify all cleanup methods were called
    assert crawler.client_session is None
    # Add more cleanup verifications as needed


@pytest.mark.asyncio
async def test_crawler_concurrent_requests(
    crawler, mock_backend
):  # Pass mock_backend here
    """Test handling of concurrent requests."""

    # Use the side_effect function from the fixture for dynamic responses
    async def mock_crawl_side_effect(
        url_info: URLInfo, config: Optional[CrawlerConfig] = None
    ):
        url = url_info.normalized_url
        return BackendCrawlResult(
            url=url,
            content={"html": f"<html><body>Content for {url}</body></html>"},
            metadata={"status_code": 200, "headers": {"content-type": "text/html"}},
            status=200,
        )

    mock_backend.crawl.side_effect = (
        mock_crawl_side_effect  # Set side_effect for this test
    )

    targets = [
        CrawlTarget(url=f"http://example{i}.com", depth=0)  # Ensure depth
        for i in range(5)
    ]

    # Process multiple targets concurrently
    tasks = [
        crawler.crawl(
            target_url=t.url,
            depth=t.depth,
            follow_external=t.follow_external,
            content_types=t.content_types,
            exclude_patterns=t.exclude_patterns,
            include_patterns=t.include_patterns,  # Use include_patterns instead
            max_pages=t.max_pages,
            allowed_paths=t.allowed_paths,
            excluded_paths=t.excluded_paths,
        )
        for t in targets
    ]
    results = await asyncio.gather(*tasks)

    assert len(results) == 5
    assert all(isinstance(r, CrawlResult) for r in results)
    assert sum(r.stats.successful_crawls for r in results) == 5
    # Reset side_effect after test
    mock_backend.crawl.side_effect = None


@pytest.mark.asyncio
async def test_crawler_url_normalization(crawler, mock_backend):  # Pass mock_backend
    """Test URL normalization during crawling."""

    async def mock_crawl_side_effect(
        url_info: URLInfo, config: Optional[CrawlerConfig] = None
    ):
        url = url_info.normalized_url
        return BackendCrawlResult(
            url=url,
            content={"html": f"<html><body>Content for {url}</body></html>"},
            metadata={"status_code": 200, "headers": {"content-type": "text/html"}},
            status=200,
        )

    mock_backend.crawl.side_effect = (
        mock_crawl_side_effect  # Set side_effect for this test
    )

    # Temporarily disable quality checker for this test
    original_qc_return_value = crawler.quality_checker.check_quality.return_value
    crawler.quality_checker.check_quality.return_value = ([], {})

    test_urls = [
        (
            "http://EXAMPLE.com",
            "http://example.com",
        ),  # Reverted: No trailing slash expected for root
        ("http://example.com/path//to/page", "http://example.com/path/to/page"),
        # Removed path traversal case as it's now caught by validation before normalization test here
        # ("http://example.com/./path/../page", "http://example.com/page"),
    ]

    try:
        for input_url, expected_url in test_urls:
            target = CrawlTarget(url=input_url, depth=0)  # Ensure depth
            crawler._crawled_urls.clear()
            result = await crawler.crawl(
                target_url=target.url,
                depth=target.depth,
                follow_external=target.follow_external,
                content_types=target.content_types,
                exclude_patterns=target.exclude_patterns,
                include_patterns=target.include_patterns,  # Use include_patterns instead
                max_pages=target.max_pages,
                allowed_paths=target.allowed_paths,
                excluded_paths=target.excluded_paths,
            )

            # Expect success and check normalized URL in the result document
            assert (
                not result.issues
            ), f"Expected no issues for {input_url}, but got: {result.issues}"
            assert (
                result.documents
            ), f"Expected documents for {input_url}, but got none."
            assert (
                len(result.documents) == 1
            ), f"Expected 1 document for {input_url}, got {len(result.documents)}"
            assert (
                result.documents[0]["url"] == expected_url
            ), f"URL mismatch for {input_url}. Expected: {expected_url}, Got: {result.documents[0]['url']}"
    finally:
        mock_backend.crawl.side_effect = None
        crawler.quality_checker.check_quality.return_value = original_qc_return_value


@pytest.mark.parametrize(
    "error, expected_message",
    [
        (Exception("Network error"), "Network error"),
        (ValueError("Invalid response"), "Invalid response"),
        (asyncio.TimeoutError(), "Timeout"),
        (ConnectionError("Connection failed"), "Connection failed"),
    ],
)
@pytest.mark.asyncio
async def test_crawler_error_handling(crawler, mock_backend, error, expected_message):
    """Test various error scenarios - OPTIMIZED."""
    # Set up the mock to return the error
    mock_backend.crawl.side_effect = [error] * crawler.config.max_retries
    crawler._crawled_urls.clear()  # Clear crawled URLs for each test case

    # Patch the retry delay function to avoid real sleeps
    with patch(
        "src.crawler.crawler.asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep:
        # Configure crawler to use minimal retry delays
        original_config = crawler.config
        crawler.config = CrawlerConfig(
            max_retries=2,  # Reduce retries for faster tests
            retry_delay=0.01,  # Minimal delay
            max_retry_delay=0.01,  # Minimal max delay
            retry_backoff_factor=1.0,  # No exponential increase
        )

        try:
            target = CrawlTarget(url=TEST_URL, depth=0)
            result = await crawler.crawl(
                target_url=target.url,
                depth=target.depth,
                follow_external=target.follow_external,
                content_types=target.content_types,
                exclude_patterns=target.exclude_patterns,
                include_patterns=target.include_patterns,
                max_pages=target.max_pages,
                allowed_paths=target.allowed_paths,
                excluded_paths=target.excluded_paths,
            )

            # Verify the expected error was captured
            assert len(result.issues) == 1
            assert (
                expected_message in result.issues[0].message
            ), f"Expected '{expected_message}' in issue message, but got '{result.issues[0].message}'"

            # Verify sleep was called for retries but didn't actually sleep
            assert mock_sleep.call_count > 0

        finally:
            # Restore original config
            crawler.config = original_config
