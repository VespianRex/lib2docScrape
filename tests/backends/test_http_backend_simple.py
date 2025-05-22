"""Simple tests for the HTTP backend."""

import pytest
from unittest.mock import MagicMock, AsyncMock

from src.backends.http_backend import HTTPBackend, HTTPBackendConfig
from src.backends.base import CrawlResult


@pytest.fixture
def http_config():
    """Create an HTTPBackendConfig instance for testing."""
    return HTTPBackendConfig(
        timeout=10.0,
        verify_ssl=True,
        follow_redirects=True,
        headers={"User-Agent": "TestAgent/1.0"}
    )


@pytest.fixture
def http_backend(http_config):
    """Create an HTTPBackend instance for testing."""
    return HTTPBackend(config=http_config)


@pytest.mark.asyncio
async def test_validate_valid_content(http_backend):
    """Test validating valid content."""
    valid_content = CrawlResult(
        url="https://example.com",
        content={"html": "<html></html>"},
        metadata={},
        status=200
    )
    assert await http_backend.validate(valid_content) is True


@pytest.mark.asyncio
async def test_validate_invalid_content_status(http_backend):
    """Test validating content with invalid status."""
    invalid_content = CrawlResult(
        url="https://example.com",
        content={"html": "<html></html>"},
        metadata={},
        status=404
    )
    assert await http_backend.validate(invalid_content) is False


@pytest.mark.asyncio
async def test_validate_invalid_content_no_html(http_backend):
    """Test validating content with no HTML."""
    invalid_content = CrawlResult(
        url="https://example.com",
        content={},
        metadata={},
        status=200
    )
    assert await http_backend.validate(invalid_content) is False


@pytest.mark.asyncio
async def test_validate_none_content(http_backend):
    """Test validating None content."""
    assert await http_backend.validate(None) is False


@pytest.mark.asyncio
async def test_process_valid_content(http_backend):
    """Test processing valid content."""
    valid_content = CrawlResult(
        url="https://example.com",
        content={"html": "<html></html>"},
        metadata={"content-type": "text/html"},
        status=200
    )
    processed = await http_backend.process(valid_content)
    assert processed["url"] == valid_content.url
    assert processed["html"] == valid_content.content["html"]
    assert processed["metadata"] == valid_content.metadata


@pytest.mark.asyncio
async def test_process_invalid_content(http_backend):
    """Test processing invalid content."""
    invalid_content = CrawlResult(
        url="https://example.com",
        content={},
        metadata={},
        status=404
    )
    processed = await http_backend.process(invalid_content)
    assert processed == {}


@pytest.mark.asyncio
async def test_close(http_backend):
    """Test closing the session."""
    # Create a mock session
    mock_session = AsyncMock()
    http_backend.session = mock_session
    
    # Call the method
    await http_backend.close()
    
    # Verify the session was closed
    mock_session.close.assert_called_once()
    assert http_backend.session is None
