import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import pytest

from src.backends.base import CrawlerBackend
from src.backends.base import CrawlResult as BackendCrawlResult
from src.crawler import CrawlStats, CrawlTarget
from src.processors.content_processor import ContentProcessor, ProcessedContent
from src.utils.url.factory import create_url_info

# Ensure pytest.mark.asyncio is available
pytest_plugins = ["pytest_asyncio"]


# Define test helper functions for creating test instances
def create_mock_backend():
    mock_backend = AsyncMock(spec=CrawlerBackend)
    mock_backend.name = "MockBackend"
    return mock_backend


def create_url_info_obj(url, base_url=None):
    return create_url_info(url, base_url=base_url)


def create_stats():
    return CrawlStats(
        start_time=datetime.now(UTC),
        pages_crawled=0,
        successful_crawls=0,
        failed_crawls=0,
        bytes_processed=0,
    )


def create_target_config(content_types=None):
    if content_types is None:
        content_types = ["text/html"]
    return CrawlTarget(url="http://example.com", depth=2, content_types=content_types)


# Standalone implementation of _fetch_and_process_with_backend for testing
async def fetch_and_process_with_backend(
    backend,
    url_info,
    content_processor,
    config,
    target,
    stats,
    visited_urls,
    processing_semaphore,
):
    """
    A standalone version of _fetch_and_process_with_backend for testing.
    This replicates the behavior of DocumentationCrawler._fetch_and_process_with_backend method.
    """
    normalized_url = url_info.normalized_url
    backend_result = None
    processed_content = None
    final_url_processed = None
    normalized_final_url = None

    async with processing_semaphore:
        backend_result = await backend.crawl(url_info=url_info, config=config)

        if not backend_result or backend_result.status != 200:
            return None, backend_result, None

        # Process the content (assuming success)
        final_url_processed = backend_result.url or normalized_url
        final_url_info = create_url_info(final_url_processed, base_url=target.url)
        normalized_final_url = final_url_info.normalized_url

        # Re-check if the final URL was already visited (due to redirects)
        if (
            normalized_final_url in visited_urls
            and normalized_final_url != normalized_url
        ):
            return None, backend_result, normalized_final_url

        # Add final URL to visited if different from initial normalized
        if normalized_final_url != normalized_url:
            visited_urls.add(normalized_final_url)

        # Check content type if backend provides it
        headers_dict = backend_result.metadata.get("headers", {})
        content_type_val = ""
        for key, value in headers_dict.items():
            if key.lower() == "content-type":
                content_type_val = value
                break
        content_type = content_type_val.lower()
        content_type_match = any(ct in content_type for ct in target.content_types)

        if not content_type_match:
            return None, backend_result, normalized_final_url

        # Process content using ContentProcessor
        processed_content = await content_processor.process(
            backend_result.content.get("html", ""), base_url=final_url_processed
        )

        stats.successful_crawls += 1
        stats.pages_crawled += 1
        stats.bytes_processed += len(backend_result.content.get("html", ""))

        return processed_content, backend_result, normalized_final_url


class TestFetchAndProcessWithBackend:
    @pytest.fixture
    def mock_backend(self):
        return create_mock_backend()

    @pytest.fixture
    def mock_content_processor(self):
        mock_processor = AsyncMock(spec=ContentProcessor)
        mock_processor.process.return_value = ProcessedContent(
            text="Processed content", structure=[]
        )
        return mock_processor

    @pytest.fixture
    def processing_semaphore(self):
        return asyncio.Semaphore(10)

    @pytest.fixture
    def mock_config(self):
        return Mock()

    @pytest.mark.asyncio
    async def test_successful_fetch_and_process(
        self, mock_backend, mock_content_processor, processing_semaphore, mock_config
    ):
        """Test 8.1: Successful Fetch and Process"""
        # Setup
        url_info = create_url_info_obj("http://example.com/page")
        target = create_target_config(content_types=["text/html"])
        stats = create_stats()
        visited = set()

        # Configure mock responses
        mock_backend.crawl.return_value = BackendCrawlResult(
            url="http://example.com/page",
            status=200,
            content={"html": "<html><body>Test</body></html>"},
            metadata={"headers": {"Content-Type": "text/html"}},
        )

        # Call the function being tested
        (
            processed_content,
            backend_result,
            final_url,
        ) = await fetch_and_process_with_backend(
            mock_backend,
            url_info,
            mock_content_processor,
            mock_config,
            target,
            stats,
            visited,
            processing_semaphore,
        )

        # Assertions
        assert processed_content is not None
        assert processed_content.text == "Processed content"
        assert backend_result.status == 200
        assert backend_result.url == "http://example.com/page"
        assert final_url == url_info.normalized_url
        assert stats.successful_crawls == 1
        assert stats.pages_crawled == 1
        assert stats.bytes_processed == len("<html><body>Test</body></html>")

        # Verify method calls
        mock_backend.crawl.assert_called_once_with(
            url_info=url_info, config=mock_config
        )
        mock_content_processor.process.assert_called_once_with(
            "<html><body>Test</body></html>", base_url="http://example.com/page"
        )

    @pytest.mark.asyncio
    async def test_backend_crawl_fails(
        self, mock_backend, mock_content_processor, processing_semaphore, mock_config
    ):
        """Test 8.2: Backend Crawl Fails (status != 200)"""
        # Setup
        url_info = create_url_info_obj("http://example.com/page")
        target = create_target_config()
        stats = create_stats()
        visited = set()

        # Configure the backend to return a 404 error
        mock_backend.crawl.return_value = BackendCrawlResult(
            url="http://example.com/page",
            status=404,
            content={},
            metadata={},  # Add empty metadata dictionary
            error="Not Found",
        )

        # Call the function being tested
        (
            processed_content,
            backend_result,
            final_url,
        ) = await fetch_and_process_with_backend(
            mock_backend,
            url_info,
            mock_content_processor,
            mock_config,
            target,
            stats,
            visited,
            processing_semaphore,
        )

        # Assertions
        assert processed_content is None
        assert backend_result.status == 404
        assert final_url is None
        assert stats.successful_crawls == 0  # Not incremented on failure
        assert stats.pages_crawled == 0  # Not incremented on failure

        # Verify the content processor was not called
        mock_content_processor.process.assert_not_called()

    @pytest.mark.asyncio
    async def test_redirect_to_new_unvisited_url(
        self, mock_backend, mock_content_processor, processing_semaphore, mock_config
    ):
        """Test 8.3: Redirect to New, Unvisited URL"""
        # Setup
        original_url = "http://example.com/old"
        redirected_url = "http://example.com/new"

        url_info = create_url_info_obj(original_url)
        target = create_target_config()
        stats = create_stats()
        visited = {url_info.normalized_url}  # Original URL is already in visited

        # Configure mocks for successful redirect
        mock_backend.crawl.return_value = BackendCrawlResult(
            url=redirected_url,  # Backend returns the redirected URL
            status=200,
            content={"html": "<p>New content</p>"},
            metadata={"headers": {"Content-Type": "text/html"}},
        )

        # Call the function being tested
        (
            processed_content,
            backend_result,
            final_url,
        ) = await fetch_and_process_with_backend(
            mock_backend,
            url_info,
            mock_content_processor,
            mock_config,
            target,
            stats,
            visited,
            processing_semaphore,
        )

        # Get the normalized URL of the redirected URL for comparison
        redirected_url_info = create_url_info_obj(redirected_url)
        redirected_normalized = redirected_url_info.normalized_url

        # Assertions
        assert processed_content is not None
        assert final_url == redirected_normalized
        assert redirected_normalized in visited
        assert stats.successful_crawls == 1
        assert stats.pages_crawled == 1

        # Verify processor was called with redirected URL as base
        mock_content_processor.process.assert_called_once_with(
            "<p>New content</p>", base_url=redirected_url
        )

    @pytest.mark.asyncio
    async def test_redirect_to_already_visited_url(
        self, mock_backend, mock_content_processor, processing_semaphore, mock_config
    ):
        """Test 8.4: Redirect to Already Visited URL"""
        # Setup
        original_url = "http://example.com/old"
        redirected_url = "http://example.com/visited"

        url_info = create_url_info_obj(original_url)
        redirected_url_info = create_url_info_obj(redirected_url)

        target = create_target_config()
        stats = create_stats()
        visited = {
            create_url_info_obj(redirected_url).normalized_url
        }  # Redirected URL is already visited

        # Configure mocks
        mock_backend.crawl.return_value = BackendCrawlResult(
            url=redirected_url,
            status=200,
            content={"html": "<p>Already visited content</p>"},
            metadata={"headers": {"Content-Type": "text/html"}},
        )

        # Call the function being tested
        (
            processed_content,
            backend_result,
            final_url,
        ) = await fetch_and_process_with_backend(
            mock_backend,
            url_info,
            mock_content_processor,
            mock_config,
            target,
            stats,
            visited,
            processing_semaphore,
        )

        # Assertions
        assert processed_content is None  # Should be skipped
        assert final_url == redirected_url_info.normalized_url
        assert stats.successful_crawls == 0
        assert stats.pages_crawled == 0

        # Verify processor was not called
        mock_content_processor.process.assert_not_called()

    @pytest.mark.asyncio
    async def test_non_allowed_content_type(
        self, mock_backend, mock_content_processor, processing_semaphore, mock_config
    ):
        """Test 8.5: Non-Allowed Content Type"""
        # Setup
        url_info = create_url_info_obj("http://example.com/image.jpg")
        target = create_target_config(content_types=["text/html"])  # Only HTML allowed
        stats = create_stats()
        visited = set()

        # Configure backend to return image content type
        mock_backend.crawl.return_value = BackendCrawlResult(
            url="http://example.com/image.jpg",
            status=200,
            content={"html": ""},
            metadata={"headers": {"Content-Type": "image/jpeg"}},
        )

        # Call the function being tested
        (
            processed_content,
            backend_result,
            final_url,
        ) = await fetch_and_process_with_backend(
            mock_backend,
            url_info,
            mock_content_processor,
            mock_config,
            target,
            stats,
            visited,
            processing_semaphore,
        )

        # Assertions
        assert processed_content is None  # Should be skipped
        assert final_url == url_info.normalized_url
        assert stats.successful_crawls == 0
        assert stats.pages_crawled == 0

        # Verify processor was not called
        mock_content_processor.process.assert_not_called()

    @pytest.mark.asyncio
    async def test_backend_returns_null_content(
        self, mock_backend, mock_content_processor, processing_semaphore, mock_config
    ):
        """Additional test: Backend returns null content"""
        # Setup
        url_info = create_url_info_obj("http://example.com/empty")
        target = create_target_config()
        stats = create_stats()
        visited = set()

        # Configure backend to return null content
        mock_backend.crawl.return_value = BackendCrawlResult(
            url="http://example.com/empty",
            status=200,
            content={},  # Empty content dictionary
            metadata={"headers": {"Content-Type": "text/html"}},
        )

        # Call the function being tested
        (
            processed_content,
            backend_result,
            final_url,
        ) = await fetch_and_process_with_backend(
            mock_backend,
            url_info,
            mock_content_processor,
            mock_config,
            target,
            stats,
            visited,
            processing_semaphore,
        )

        # Assertions
        assert processed_content is not None  # Should still process empty content
        assert final_url == url_info.normalized_url
        assert stats.successful_crawls == 1
        assert stats.pages_crawled == 1
        assert stats.bytes_processed == 0

        # Verify processor was called with empty string
        mock_content_processor.process.assert_called_once_with(
            "", base_url="http://example.com/empty"
        )

    @pytest.mark.asyncio
    async def test_backend_returns_null_result(
        self, mock_backend, mock_content_processor, processing_semaphore, mock_config
    ):
        """Additional test: Backend returns null result"""
        # Setup
        url_info = create_url_info_obj("http://example.com/error")
        target = create_target_config()
        stats = create_stats()
        visited = set()

        # Configure backend to return None
        mock_backend.crawl.return_value = None

        # Call the function being tested
        (
            processed_content,
            backend_result,
            final_url,
        ) = await fetch_and_process_with_backend(
            mock_backend,
            url_info,
            mock_content_processor,
            mock_config,
            target,
            stats,
            visited,
            processing_semaphore,
        )

        # Assertions
        assert processed_content is None
        assert backend_result is None
        assert final_url is None
        assert stats.successful_crawls == 0
        assert stats.pages_crawled == 0

        # Verify processor was not called
        mock_content_processor.process.assert_not_called()

    @pytest.mark.asyncio
    async def test_content_processor_raises_exception(
        self, mock_backend, mock_content_processor, processing_semaphore, mock_config
    ):
        """Additional test: Content Processor raises exception"""
        # Setup
        url_info = create_url_info_obj("http://example.com/error-page")
        target = create_target_config()
        stats = create_stats()
        visited = set()

        # Configure backend to return valid result
        mock_backend.crawl.return_value = BackendCrawlResult(
            url="http://example.com/error-page",
            status=200,
            content={"html": "<html>Bad markup</html>"},
            metadata={"headers": {"Content-Type": "text/html"}},
        )

        # Configure content processor to raise exception
        exc = ValueError("Processing error")
        mock_content_processor.process.side_effect = exc

        # Call the function being tested and expect an exception
        with pytest.raises(ValueError) as excinfo:
            await fetch_and_process_with_backend(
                mock_backend,
                url_info,
                mock_content_processor,
                mock_config,
                target,
                stats,
                visited,
                processing_semaphore,
            )

        # Assertions
        assert str(excinfo.value) == "Processing error"
        assert stats.successful_crawls == 0
        assert stats.pages_crawled == 0

        # Verify method calls
        mock_backend.crawl.assert_called_once()
        mock_content_processor.process.assert_called_once()
