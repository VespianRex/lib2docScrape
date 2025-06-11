"""
Tests for the Lightpanda backend.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from src.backends.base import CrawlResult
from src.backends.lightpanda_backend import LightpandaBackend, LightpandaConfig
from src.processors.content.models import ProcessedContent
from src.utils.url.info import URLInfo


@pytest.fixture
def url_info():
    """Create a valid URLInfo object for testing."""
    url_info = MagicMock(spec=URLInfo)
    url_info.is_valid = True
    url_info.normalized_url = "https://example.com"
    url_info.raw_url = "https://example.com"
    url_info.error_message = None
    return url_info


@pytest.fixture
def invalid_url_info():
    """Create an invalid URLInfo object for testing."""
    url_info = MagicMock(spec=URLInfo)
    url_info.is_valid = False
    url_info.normalized_url = ""
    url_info.raw_url = "invalid://example.com"
    url_info.error_message = "Invalid URL scheme"
    return url_info


@pytest.fixture
def lightpanda_config():
    """Create a LightpandaConfig for testing."""
    return LightpandaConfig(
        executable_path="lightpanda",
        host="127.0.0.1",
        port=9222,
        timeout=1.0,
        max_retries=1,
        wait_for_load=True,
        wait_time=0.1,
        javascript_enabled=True,
        screenshots=False,
    )


@pytest.fixture
def mock_ws():
    """Create a mock WebSocket connection."""
    ws = AsyncMock()
    ws.TEXT = aiohttp.WSMsgType.TEXT
    ws.send_json = AsyncMock()
    ws.close = AsyncMock()
    return ws


@pytest.fixture
def mock_session(mock_ws):
    """Create a mock aiohttp ClientSession."""
    session = AsyncMock()
    session.ws_connect = AsyncMock(return_value=mock_ws)
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_process():
    """Create a mock subprocess.Popen instance."""
    process = MagicMock()
    process.terminate = MagicMock()
    process.wait = MagicMock()
    process.kill = MagicMock()
    return process


@pytest.mark.asyncio
async def test_invalid_url(invalid_url_info, lightpanda_config):
    """Test crawling an invalid URL."""
    backend = LightpandaBackend(config=lightpanda_config)
    result = await backend.crawl(invalid_url_info)

    assert result.status == 400
    assert "Invalid URL" in result.error
    assert not result.content


@pytest.mark.asyncio
@patch("src.backends.lightpanda_backend.aiohttp.ClientSession")
@patch("src.backends.lightpanda_backend.subprocess.Popen")
async def test_browser_start_failure(
    mock_popen, mock_client_session, url_info, lightpanda_config
):
    """Test handling of browser start failure."""
    # Mock subprocess.Popen to return a process
    mock_process = MagicMock()
    mock_popen.return_value = mock_process

    # Create a mock for _navigate_with_retry that returns a failure result
    mock_navigate_result = {
        "success": False,
        "error": "Failed to connect",
        "status": 500,
        "content": None,
        "screenshot": None,
    }

    backend = LightpandaBackend(config=lightpanda_config)

    # Patch _navigate_with_retry to return our mock result
    with patch.object(
        backend, "_navigate_with_retry", AsyncMock(return_value=mock_navigate_result)
    ):
        with patch.object(backend, "_is_in_path", return_value=True):
            result = await backend.crawl(url_info)

    assert result.status == 500
    assert "error_details" in result.metadata
    assert "Failed to connect" in result.error


@pytest.mark.asyncio
@patch("src.backends.lightpanda_backend.aiohttp.ClientSession")
@patch("src.backends.lightpanda_backend.subprocess.Popen")
async def test_successful_crawl(
    mock_popen, mock_client_session, url_info, lightpanda_config, mock_session
):
    """Test successful crawling of a URL."""
    # Mock subprocess.Popen to return a process
    mock_process = MagicMock()
    mock_popen.return_value = mock_process

    # Mock ClientSession to return our mock session
    mock_client_session.return_value = mock_session

    # Create a mock for _navigate_with_retry that returns a successful result
    mock_navigate_result = {
        "success": True,
        "status": 200,
        "content": "<html><body>Test</body></html>",
        "screenshot": None,
    }

    backend = LightpandaBackend(config=lightpanda_config)

    # Patch _navigate_with_retry to return our mock result
    with patch.object(
        backend, "_navigate_with_retry", AsyncMock(return_value=mock_navigate_result)
    ):
        with patch.object(backend, "_is_in_path", return_value=True):
            # Patch ContentProcessor.process to return a simple result
            with patch(
                "src.processors.content_processor.ContentProcessor.process"
            ) as mock_process:
                mock_process.return_value = ProcessedContent(
                    title="Test Page",
                    content={"formatted_content": "Test content"},
                    metadata={"description": "Test description"},
                    headings=[{"level": 1, "text": "Test Heading"}],
                    structure=[{"type": "heading", "text": "Test Heading"}],
                )

                result = await backend.crawl(url_info)
                processed = await backend.process(result)

    assert result.status == 200
    assert "html" in result.content
    assert "<html><body>Test</body></html>" == result.content["html"]
    assert "lightpanda" in result.metadata["backend"]

    assert processed["title"] == "Test Page"
    assert "Test content" in str(processed["content"])
    assert processed["metadata"]["description"] == "Test description"
    assert len(processed["headings"]) == 1
    assert processed["headings"][0]["text"] == "Test Heading"


@pytest.mark.asyncio
async def test_validate_content():
    """Test content validation."""
    backend = LightpandaBackend()

    # Valid content
    valid_content = CrawlResult(
        url="https://example.com",
        content={
            "html": "<html><head><title>Valid Page</title></head><body>This is a valid page with enough content to pass validation.</body></html>"
        },
        metadata={},
        status=200,
    )
    assert await backend.validate(valid_content) is True

    # Invalid content (too short)
    short_content = CrawlResult(
        url="https://example.com",
        content={"html": "<html></html>"},
        metadata={},
        status=200,
    )
    assert await backend.validate(short_content) is False

    # Invalid content (error page)
    error_content = CrawlResult(
        url="https://example.com",
        content={
            "html": "<html><head><title>404 Not Found</title></head><body>Page not found</body></html>"
        },
        metadata={},
        status=200,
    )
    assert await backend.validate(error_content) is False


@pytest.mark.asyncio
async def test_close():
    """Test closing the backend resources."""
    backend = LightpandaBackend()

    # Mock the resources
    ws = AsyncMock()
    session = AsyncMock()
    process = MagicMock()

    # Set the mocked resources
    backend._ws = ws
    backend._session = session
    backend._process = process

    # Call close
    await backend.close()

    # Verify resources were closed
    ws.close.assert_called_once()
    session.close.assert_called_once()
    assert backend._ws is None
    assert backend._session is None
    assert backend._process is None
