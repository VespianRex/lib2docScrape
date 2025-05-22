"""
Tests for the Lightpanda backend.
"""
import asyncio
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.backends.lightpanda_backend import LightpandaBackend, LightpandaConfig
from src.utils.url.info import URLInfo
from src.backends.base import CrawlResult

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
        screenshots=False
    )

@pytest.fixture
def mock_ws():
    """Create a mock WebSocket connection."""
    ws = AsyncMock()
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
async def test_browser_start_failure(mock_popen, mock_client_session, url_info, lightpanda_config):
    """Test handling of browser start failure."""
    # Mock subprocess.Popen to return a process
    mock_process = MagicMock()
    mock_popen.return_value = mock_process
    
    # Mock ClientSession to raise an exception
    mock_client_session.side_effect = Exception("Failed to connect")
    
    backend = LightpandaBackend(config=lightpanda_config)
    
    # Patch _is_in_path to return True
    with patch.object(backend, "_is_in_path", return_value=True):
        result = await backend.crawl(url_info)
    
    assert result.status == 500
    assert "error" in result.metadata
    assert "Failed to start" in result.error or "Failed to connect" in result.error

@pytest.mark.asyncio
@patch("src.backends.lightpanda_backend.aiohttp.ClientSession")
@patch("src.backends.lightpanda_backend.subprocess.Popen")
async def test_successful_crawl(mock_popen, mock_client_session, url_info, lightpanda_config, mock_session, mock_ws):
    """Test successful crawling of a URL."""
    # Mock subprocess.Popen to return a process
    mock_process = MagicMock()
    mock_popen.return_value = mock_process
    
    # Mock ClientSession to return our mock session
    mock_client_session.return_value = mock_session
    
    # Mock the response from /json/version
    mock_version_response = AsyncMock()
    mock_version_response.status = 200
    mock_version_response.json = AsyncMock(return_value={"webSocketDebuggerUrl": "ws://localhost:9222/devtools/browser/123"})
    mock_session.get.return_value.__aenter__.return_value = mock_version_response
    
    # Mock WebSocket responses
    async def mock_ws_iter():
        # Response for Target.createBrowserContext
        yield MagicMock(type=mock_ws.TEXT, data='{"id": 1, "result": {"browserContextId": "1"}}')
        # Response for Target.createTarget
        yield MagicMock(type=mock_ws.TEXT, data='{"id": 2, "result": {"targetId": "2"}}')
        # Response for Target.attachToTarget
        yield MagicMock(type=mock_ws.TEXT, data='{"id": 3, "result": {"sessionId": "3"}}')
        # Response for Emulation.setDeviceMetricsOverride
        yield MagicMock(type=mock_ws.TEXT, data='{"id": 4, "result": {}}')
        # Response for Network.setUserAgentOverride
        yield MagicMock(type=mock_ws.TEXT, data='{"id": 5, "result": {}}')
        # Response for Page.navigate
        yield MagicMock(type=mock_ws.TEXT, data='{"id": 6, "result": {}}')
        # Response for Runtime.evaluate
        yield MagicMock(type=mock_ws.TEXT, data='{"id": 7, "result": {"result": {"value": "<html><body>Test</body></html>"}}}')
        # Response for Target.closeTarget
        yield MagicMock(type=mock_ws.TEXT, data='{"id": 8, "result": {}}')
    
    mock_ws.__aiter__.return_value = mock_ws_iter()
    
    backend = LightpandaBackend(config=lightpanda_config)
    
    # Patch _is_in_path to return True
    with patch.object(backend, "_is_in_path", return_value=True):
        # Patch ContentProcessor.process to return a simple result
        with patch("src.processors.content_processor.ContentProcessor.process") as mock_process:
            from src.processors.content.models import ProcessedContent
            mock_process.return_value = ProcessedContent(
                title="Test Page",
                content={"formatted_content": "Test content"},
                metadata={"description": "Test description"},
                headings=[{"level": 1, "text": "Test Heading"}],
                structure=[{"type": "heading", "text": "Test Heading"}]
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
        content={"html": "<html><head><title>Valid Page</title></head><body>This is a valid page with enough content to pass validation.</body></html>"},
        metadata={},
        status=200
    )
    assert await backend.validate(valid_content) is True
    
    # Invalid content (too short)
    short_content = CrawlResult(
        url="https://example.com",
        content={"html": "<html></html>"},
        metadata={},
        status=200
    )
    assert await backend.validate(short_content) is False
    
    # Invalid content (error page)
    error_content = CrawlResult(
        url="https://example.com",
        content={"html": "<html><head><title>404 Not Found</title></head><body>Page not found</body></html>"},
        metadata={},
        status=200
    )
    assert await backend.validate(error_content) is False
