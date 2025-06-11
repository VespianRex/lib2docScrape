from unittest.mock import (
    AsyncMock,
    MagicMock,
)

import pytest

# Added MagicMock back for the spec in one test
from pytest_mock import MockerFixture

from src.backends.base import CrawlResult  # Changed BackendCrawlResult to CrawlResult
from src.backends.scrapy_backend import ScrapyBackend, ScrapyConfig
from src.crawler import CrawlerConfig
from src.utils.url.factory import create_url_info
from src.utils.url.info import URLInfo  # Added for mock_url_info spec


@pytest.fixture
def mock_aiohttp_session():
    """
    Fixture to create a mock aiohttp session and response.

    Returns:
        Tuple[MagicMock, AsyncMock]: A mock session and a mock response
    """

    def _create_mock_session(response_body="", status=200, content_type="text/html"):
        # Create mock response
        mock_response = AsyncMock()
        mock_response.status = status
        mock_response.headers = {"Content-Type": content_type}
        mock_response.text = AsyncMock(return_value=response_body)

        # Create mock context manager for session.get()
        mock_cm = AsyncMock()
        mock_cm.__aenter__.return_value = mock_response
        mock_cm.__aexit__.return_value = None

        # Create mock session
        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_cm)

        return mock_session, mock_response

    return _create_mock_session


@pytest.mark.asyncio
async def test_scrapy_backend_crawl_success(mocker: MockerFixture):
    target_url = "http://example.com"
    html_content = "<html><body>Test content</body></html>"

    # 1. Mock the response object that session.get().__aenter__() will return
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.headers = {"Content-Type": "text/html"}
    mock_response.text = AsyncMock(
        return_value=html_content
    )  # .text() is an async method

    # 2. Mock the async context manager returned by session.get()
    mock_session_get_cm = AsyncMock()
    mock_session_get_cm.__aenter__.return_value = mock_response
    # __aexit__ is also needed for the context manager protocol
    mock_session_get_cm.__aexit__.return_value = None

    # 3. Mock the session instance and its get() method
    mock_session_instance = AsyncMock()
    # .get() should return the async context manager mock
    mock_session_instance.get = MagicMock(return_value=mock_session_get_cm)  # Corrected

    # 4. Patch aiohttp.ClientSession in the scrapy_backend module's scope
    # This ensures that when ScrapyBackend instantiates a ClientSession, it gets our mock_session_instance.
    mocker.patch(
        "src.backends.scrapy_backend.aiohttp.ClientSession",
        return_value=mock_session_instance,
    )

    # Instantiate the backend
    backend = ScrapyBackend(config=ScrapyConfig())

    # Mock _notify_progress to prevent actual logging/side-effects and allow verification
    mocker.patch.object(backend, "_notify_progress", AsyncMock())

    # Prepare inputs for the crawl method
    url_info = create_url_info(url=target_url)
    crawler_config = CrawlerConfig()

    # Call the method under test
    result: CrawlResult = await backend.crawl(
        url_info, crawler_config
    )  # Changed BackendCrawlResult to CrawlResult

    # Assertions
    assert result is not None
    assert result.url == target_url
    assert result.status == 200
    assert result.content is not None
    assert "html" in result.content
    assert result.content["html"] == html_content
    assert result.error is None

    # Verify mocks
    mock_session_instance.get.assert_called_once_with(target_url)

    backend._notify_progress.assert_any_call(target_url, 0, "Started")
    backend._notify_progress.assert_any_call(target_url, 0, "Completed")

    mock_response.text.assert_called_once()


# Add a new test for failure cases, e.g., HTTP error
@pytest.mark.asyncio
async def test_scrapy_backend_crawl_http_error(mocker: MockerFixture):
    target_url = "http://example.com/notfound"

    mock_response = AsyncMock()
    mock_response.status = 404
    mock_response.headers = {"Content-Type": "text/html"}
    mock_response.text = AsyncMock(return_value="Not Found")

    mock_session_get_cm = AsyncMock()
    mock_session_get_cm.__aenter__.return_value = mock_response
    mock_session_get_cm.__aexit__.return_value = None

    mock_session_instance = AsyncMock()
    mock_session_instance.get = MagicMock(return_value=mock_session_get_cm)  # Corrected

    mocker.patch(
        "src.backends.scrapy_backend.aiohttp.ClientSession",
        return_value=mock_session_instance,
    )

    backend = ScrapyBackend(config=ScrapyConfig())
    mocker.patch.object(backend, "_notify_progress", AsyncMock())

    url_info = create_url_info(url=target_url)
    crawler_config = CrawlerConfig()

    result: CrawlResult = await backend.crawl(
        url_info, crawler_config
    )  # Changed BackendCrawlResult to CrawlResult

    assert result is not None
    assert result.url == target_url
    assert result.status == 404
    assert result.content is not None  # Content should still be there
    assert result.content["html"] == "Not Found"
    assert (
        result.error is None
    )  # ScrapyBackend currently sets error to None if response is received

    mock_session_instance.get.assert_called_once_with(target_url)
    backend._notify_progress.assert_any_call(target_url, 0, "Started")
    backend._notify_progress.assert_any_call(target_url, 0, "Failed: 404")
    mock_response.text.assert_called_once()


@pytest.mark.asyncio
async def test_scrapy_backend_crawl_exception(mocker: MockerFixture):
    target_url = "http://example.com/exception"

    mock_session_instance = AsyncMock()
    # Simulate a network error or other exception during session.get()
    mock_session_instance.get = MagicMock(
        side_effect=Exception("Network error")
    )  # Corrected

    mocker.patch(
        "src.backends.scrapy_backend.aiohttp.ClientSession",
        return_value=mock_session_instance,
    )

    backend = ScrapyBackend(config=ScrapyConfig())
    mocker.patch.object(backend, "_notify_progress", AsyncMock())

    url_info = create_url_info(url=target_url)
    crawler_config = CrawlerConfig()

    result: CrawlResult = await backend.crawl(
        url_info, crawler_config
    )  # Changed BackendCrawlResult to CrawlResult

    assert result is not None
    assert result.url == target_url
    assert result.status == 0  # Or a specific error status code used by the backend
    assert result.content == {}
    assert result.error == "Error crawling http://example.com/exception: Network error"

    mock_session_instance.get.assert_called_once_with(target_url)
    backend._notify_progress.assert_any_call(target_url, 0, "Started")
    backend._notify_progress.assert_any_call(target_url, 0, "Error: Network error")


@pytest.mark.asyncio
async def test_scrapy_backend_crawl_invalid_url(mocker: MockerFixture):
    backend = ScrapyBackend(config=ScrapyConfig())
    # No need to mock aiohttp calls as it should fail before that

    # Create an invalid URLInfo object
    # Assuming create_url_info sets is_valid to False and provides an error_message
    # For this test, let's manually create one that's invalid
    # invalid_url_info = create_url_info("ftp://invalid_url") # Original attempt

    # To ensure url_info.is_valid is False for the test:
    mock_url_info = mocker.MagicMock(spec=URLInfo)  # Use MagicMock for non-async spec
    mock_url_info.is_valid = False
    mock_url_info.raw_url = "ftp://invalid"
    mock_url_info.normalized_url = "ftp://invalid"  # Though not used if invalid
    # If URLInfo has an error_message attribute that ScrapyBackend uses:
    mock_url_info.error_message = "Mocked invalid URL"

    crawler_config = CrawlerConfig()

    result: CrawlResult = await backend.crawl(
        mock_url_info, crawler_config
    )  # Changed BackendCrawlResult to CrawlResult

    assert result is not None
    assert result.url == "ftp://invalid"  # Uses raw_url from URLInfo
    assert result.status == 400  # Bad Request
    assert result.content == {}
    # Check that the error message from the backend includes the raw_url or a generic invalid message
    assert (
        "Invalid URL provided: ftp://invalid" in result.error
        or "Invalid URL provided" in result.error
    )


@pytest.mark.asyncio
async def test_rate_limiting(mocker: MockerFixture, mock_aiohttp_session):
    """Test that rate limiting in ScrapyBackend works correctly."""
    target_url = "http://example.com/rate_limit_test"
    html_content = "<html><body>Rate limited</body></html>"

    # Create a mock session and response using our fixture
    mock_session, mock_response = mock_aiohttp_session(
        response_body=html_content, status=200, content_type="text/html"
    )

    # Patch the ClientSession class to return our mock
    mocker.patch(
        "src.backends.scrapy_backend.aiohttp.ClientSession", return_value=mock_session
    )

    # Create the backend and patch the progress notification
    backend = ScrapyBackend(config=ScrapyConfig())
    mocker.patch.object(backend, "_notify_progress", AsyncMock())

    # Create test data
    url_info = create_url_info(url=target_url)
    crawler_config = CrawlerConfig()

    # Execute the test
    result: CrawlResult = await backend.crawl(url_info, crawler_config)

    # Verify results
    assert result is not None
    assert result.url == target_url
    assert result.status == 200
    assert result.content is not None
    assert "html" in result.content
    assert result.content["html"] == html_content
    assert result.error is None

    # Verify mocks were called correctly
    mock_session.get.assert_called_once_with(target_url)
    backend._notify_progress.assert_any_call(target_url, 0, "Started")
    backend._notify_progress.assert_any_call(target_url, 0, "Completed")
    mock_response.text.assert_called_once()


@pytest.mark.asyncio
async def test_different_content_types(
    mocker: MockerFixture, mock_aiohttp_session
):  # Use our fixture
    target_url = "http://example.com/content_type_test"
    html_content = "<html><body>Test content</body></html>"

    # First create a mock session for HTML content
    mock_session, mock_html_response = mock_aiohttp_session(
        response_body=html_content, status=200, content_type="text/html"
    )

    # Patch the ClientSession to return our mock session
    mocker.patch(
        "src.backends.scrapy_backend.aiohttp.ClientSession", return_value=mock_session
    )

    backend = ScrapyBackend(config=ScrapyConfig())
    mocker.patch.object(backend, "_notify_progress", AsyncMock())

    url_info = create_url_info(url=target_url)
    crawler_config = CrawlerConfig()

    # First call should process HTML
    result: CrawlResult = await backend.crawl(url_info, crawler_config)

    assert result is not None
    assert result.url == target_url
    assert result.status == 200
    assert result.content is not None
    assert "html" in result.content
    assert result.content["html"] == html_content
    assert result.error is None

    # Verify mocks were called
    mock_session.get.assert_called_once_with(target_url)
    backend._notify_progress.assert_any_call(target_url, 0, "Started")
    backend._notify_progress.assert_any_call(target_url, 0, "Completed")

    mock_html_response.text.assert_called_once()

    # Second call should
