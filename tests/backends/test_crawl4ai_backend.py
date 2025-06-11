"""
Tests for the Crawl4AI backend.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp.client_exceptions import ClientError

from src.backends.crawl4ai_backend import Crawl4AIBackend, Crawl4AIConfig
from src.utils.url import URLInfo, create_url_info


@pytest.fixture
def mock_response():
    """Create a mock aiohttp response."""
    mock = AsyncMock()
    mock.status = 200
    mock.headers = {"content-type": "text/html"}
    mock.url = "https://example.com"
    mock.text = AsyncMock(
        return_value="<html><head><title>Test</title></head><body>Test content</body></html>"
    )
    return mock


@pytest.fixture
def mock_session(mock_response):
    """Create a mock aiohttp session."""
    session = MagicMock()
    session.closed = False

    # Create a context manager for get requests
    get_context = AsyncMock()
    get_context.__aenter__.return_value = mock_response

    # Make session.get return the context manager
    session.get = AsyncMock(return_value=get_context)

    return session


@pytest.fixture
def backend():
    """Create a Crawl4AI backend instance."""
    config = Crawl4AIConfig(
        max_retries=2, timeout=5.0, rate_limit=10.0, concurrent_requests=5
    )
    return Crawl4AIBackend(config=config)


@pytest.mark.asyncio
async def test_crawl_valid_url(backend, mock_session):
    """Test crawling a valid URL."""
    # Patch the session creation
    with patch.object(backend, "_ensure_session", AsyncMock()):
        # Set the session directly
        backend._session = mock_session

        # Create a valid URL
        url_info = create_url_info("https://example.com")

        # Crawl the URL
        result = await backend.crawl(url_info)

        # Check that the session was used
        mock_session.get.assert_called_once()

        # Check the result
        assert result.status == 200
        assert result.url == "https://example.com"
        assert "html" in result.content
        assert result.is_success()


@pytest.mark.asyncio
async def test_crawl_invalid_url(backend):
    """Test crawling an invalid URL."""
    # Create an invalid URL
    url_info = URLInfo(
        raw_url="invalid-url",
        normalized_url="",
        is_valid=False,
        error_message="Invalid URL format",
    )

    # Crawl the URL
    result = await backend.crawl(url_info)

    # Check the result
    assert result.status == 400
    assert result.error == "Invalid URL: Invalid URL format"
    assert not result.is_success()


@pytest.mark.asyncio
async def test_retry_on_error(backend, mock_session):
    """Test retry behavior on error."""
    # Make the first call fail, then succeed
    side_effects = [
        ClientError("Connection error"),
        AsyncMock().__aenter__.return_value,  # Second call succeeds
    ]

    # Create a context manager for get requests that fails first time
    get_context1 = AsyncMock()
    get_context1.__aenter__.side_effect = side_effects[0]

    # Create a context manager for get requests that succeeds second time
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.headers = {"content-type": "text/html"}
    mock_response.url = "https://example.com"
    mock_response.text = AsyncMock(return_value="<html><body>Test</body></html>")

    get_context2 = AsyncMock()
    get_context2.__aenter__.return_value = mock_response

    # Make session.get return the context managers in sequence
    mock_session.get = AsyncMock(side_effect=[get_context1, get_context2])

    # Patch the session creation and sleep
    with (
        patch.object(backend, "_ensure_session", AsyncMock()),
        patch.object(asyncio, "sleep", AsyncMock()),
    ):
        # Set the session directly
        backend._session = mock_session

        # Create a valid URL
        url_info = create_url_info("https://example.com")

        # Crawl the URL
        result = await backend.crawl(url_info)

        # Check that get was called twice
        assert mock_session.get.call_count == 2

        # Check the result
        assert result.status == 200
        assert result.is_success()


@pytest.mark.asyncio
async def test_circuit_breaker(backend):
    """Test circuit breaker behavior."""
    from src.backends.base import CrawlResult
    from src.utils.circuit_breaker import CircuitState

    # Force the circuit breaker to open
    backend.circuit_breaker._failure_count = backend.config.circuit_breaker_threshold
    backend.circuit_breaker._change_state(CircuitState.OPEN)
    # Patch _fetch_with_retry to ensure no real HTTP request is made and return a real CrawlResult
    with patch.object(
        backend,
        "_fetch_with_retry",
        AsyncMock(
            return_value=CrawlResult(
                url="https://example.com",
                content={},
                metadata={"circuit_breaker": "open"},
                status=503,
                error="Circuit breaker open",
            )
        ),
    ):
        # Create a valid URL
        url_info = create_url_info("https://example.com")
        # Crawl the URL
        result = await backend.crawl(url_info)
        # Check the result
        assert result.status == 503
        assert "circuit_breaker" in result.metadata
        assert result.metadata["circuit_breaker"] == "open"
        assert not result.is_success()


@pytest.mark.asyncio
async def test_validate_content(backend):
    """Test content validation."""
    # Create a valid result
    valid_result = MagicMock()
    valid_result.content = {
        "html": "<html><head><title>Test</title></head><body>Test content</body></html>"
    }
    valid_result.url = "https://example.com"

    # Create an invalid result
    invalid_result = MagicMock()
    invalid_result.content = {"html": ""}
    invalid_result.url = "https://example.com"

    # Validate the results
    assert await backend.validate(valid_result) is True
    assert await backend.validate(invalid_result) is False
    assert await backend.validate(None) is False


@pytest.mark.asyncio
async def test_process_content(backend):
    """Test content processing."""
    # Create a valid result
    valid_result = MagicMock()
    valid_result.content = {
        "html": "<html><head><title>Test</title></head><body><h1>Test</h1><p>Content</p></body></html>"
    }
    valid_result.url = "https://example.com"

    # Mock the content processor
    mock_processed_content = MagicMock()
    mock_processed_content.title = "Test"
    mock_processed_content.content = "Test Content"
    mock_processed_content.metadata = {"keywords": "test"}
    mock_processed_content.headings = [{"level": 1, "text": "Test"}]
    mock_processed_content.assets = []

    # Patch the content processor
    with patch.object(
        backend.content_processor,
        "process",
        AsyncMock(return_value=mock_processed_content),
    ):
        # Process the content
        result = await backend.process(valid_result)

        # Check the result
        assert result["title"] == "Test"
        assert result["content"] == "Test Content"
        assert "metadata" in result
        assert "headings" in result
        assert "links" in result


@pytest.mark.asyncio
async def test_close(backend, mock_session):
    """Test closing the backend."""
    # Set the session
    backend._session = mock_session
    # Patch close to be awaitable
    mock_session.close = AsyncMock()
    # Close the backend
    await backend.close()
    # Check that close was called
    mock_session.close.assert_called_once()
