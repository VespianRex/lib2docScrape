"""Tests for the http_backend module."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import aiohttp
from aiohttp import ClientResponseError, ClientConnectionError
import asyncio

from src.backends.http_backend import HTTPBackend, HTTPBackendConfig
from src.backends.base import CrawlResult
from src.utils.url.info import URLInfo


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


@pytest.fixture
def mock_url_info():
    """Create a mock URLInfo for testing."""
    url_info = MagicMock(spec=URLInfo)
    url_info.is_valid = True
    url_info.raw_url = "https://example.com"
    url_info.normalized_url = "https://example.com"
    return url_info


@pytest.fixture
def mock_response():
    """Create a mock aiohttp.ClientResponse for testing."""
    response = AsyncMock()
    response.status = 200
    response.headers = {"content-type": "text/html"}
    response.text = AsyncMock(return_value="<html><body><h1>Test Content</h1></body></html>")
    response.url = "https://example.com"
    response.__aenter__.return_value = response
    response.__aexit__.return_value = None
    return response


@pytest.fixture
def mock_session(mock_response):
    """Create a mock aiohttp.ClientSession for testing."""
    session = AsyncMock()
    session.get.return_value = mock_response
    session.close = AsyncMock()
    return session


class TestHTTPBackendConfig:
    """Tests for the HTTPBackendConfig class."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        config = HTTPBackendConfig()
        assert config.timeout == 30.0
        assert config.verify_ssl is True
        assert config.follow_redirects is True
        assert config.headers is None

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        headers = {"User-Agent": "TestAgent/1.0"}
        config = HTTPBackendConfig(
            timeout=10.0,
            verify_ssl=False,
            follow_redirects=False,
            headers=headers
        )
        assert config.timeout == 10.0
        assert config.verify_ssl is False
        assert config.follow_redirects is False
        assert config.headers == headers


class TestHTTPBackend:
    """Tests for the HTTPBackend class."""

    def test_init(self, http_config):
        """Test initialization."""
        backend = HTTPBackend(config=http_config)
        assert backend.name == "http_backend"
        assert backend.config == http_config
        assert backend.session is None

    @pytest.mark.asyncio
    @patch('src.backends.http_backend.aiohttp.ClientSession')
    async def test_crawl_success(self, mock_client_session, http_backend, mock_url_info):
        """Test successful crawling."""
        # Create a mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {"content-type": "text/html"}
        mock_response.text = AsyncMock(return_value="<html><body><h1>Test Content</h1></body></html>")
        mock_response.url = "https://example.com"
        mock_response.__aenter__.return_value = mock_response

        # Create a mock session
        mock_session = AsyncMock()
        mock_session.get.return_value = mock_response
        mock_client_session.return_value = mock_session

        # Call the method
        result = await http_backend.crawl(mock_url_info)

        # Verify the session was created
        mock_client_session.assert_called_once()

        # Verify the get request was made
        mock_session.get.assert_called_once()

        # Verify the result
        assert result.status == 200
        assert "https://example.com" in result.url
        assert "<html><body><h1>Test Content</h1></body></html>" in result.content.get("html", "")
        assert "text/html" in result.metadata.get("content_type", "")

    @pytest.mark.asyncio
    @patch('src.backends.http_backend.aiohttp.ClientSession')
    async def test_crawl_http_error(self, mock_client_session, http_backend, mock_url_info):
        """Test crawling with HTTP error."""
        # Create a ClientResponseError
        error = ClientResponseError(
            request_info=MagicMock(),
            history=(),
            status=404,
            message="Not Found",
            headers={"content-type": "text/plain"}
        )

        # Create a mock session that raises the error
        mock_session = AsyncMock()
        mock_session.get.side_effect = error
        mock_client_session.return_value = mock_session

        # Call the method
        result = await http_backend.crawl(mock_url_info)

        # Verify the result
        assert result.status == 404
        assert result.url == mock_url_info.normalized_url
        assert "HTTP Error: 404 Not Found" in result.error
        assert result.content == {}

    @pytest.mark.asyncio
    @patch('src.backends.http_backend.aiohttp.ClientSession')
    async def test_crawl_timeout(self, mock_client_session, http_backend, mock_url_info):
        """Test crawling with timeout."""
        # Create a mock session that raises a TimeoutError
        mock_session = AsyncMock()
        mock_session.get.side_effect = asyncio.TimeoutError()
        mock_client_session.return_value = mock_session

        # Call the method
        result = await http_backend.crawl(mock_url_info)

        # Verify the result
        assert result.status == 504
        assert result.url == mock_url_info.normalized_url
        assert "Request timed out" in result.error
        assert result.content == {}

    @pytest.mark.asyncio
    @patch('src.backends.http_backend.aiohttp.ClientSession')
    async def test_crawl_connection_error(self, mock_client_session, http_backend, mock_url_info):
        """Test crawling with connection error."""
        # Create a mock session that raises a ClientConnectionError
        mock_session = AsyncMock()
        mock_session.get.side_effect = ClientConnectionError("Connection refused")
        mock_client_session.return_value = mock_session

        # Call the method
        result = await http_backend.crawl(mock_url_info)

        # Verify the result
        assert result.status == 503
        assert result.url == mock_url_info.normalized_url
        assert "Connection Error" in result.error
        assert result.content == {}

    @pytest.mark.asyncio
    @patch('src.backends.http_backend.aiohttp.ClientSession')
    async def test_crawl_unexpected_error(self, mock_client_session, http_backend, mock_url_info):
        """Test crawling with unexpected error."""
        # Create a mock session that raises an unexpected error
        mock_session = AsyncMock()
        mock_session.get.side_effect = Exception("Unexpected error")
        mock_client_session.return_value = mock_session

        # Call the method
        result = await http_backend.crawl(mock_url_info)

        # Verify the result
        assert result.status == 500
        assert result.url == mock_url_info.normalized_url
        assert "Unexpected Error" in result.error
        assert result.content == {}

    @pytest.mark.asyncio
    async def test_validate(self, http_backend):
        """Test validating content."""
        # Valid content
        valid_content = CrawlResult(
            url="https://example.com",
            content={"html": "<html></html>"},
            metadata={},
            status=200
        )
        assert await http_backend.validate(valid_content) is True

        # Invalid content - status not 200
        invalid_status = CrawlResult(
            url="https://example.com",
            content={"html": "<html></html>"},
            metadata={},
            status=404
        )
        assert await http_backend.validate(invalid_status) is False

        # Invalid content - no HTML
        no_html = CrawlResult(
            url="https://example.com",
            content={},
            metadata={},
            status=200
        )
        assert await http_backend.validate(no_html) is False

        # Invalid content - None
        assert await http_backend.validate(None) is False

    @pytest.mark.asyncio
    async def test_process(self, http_backend):
        """Test processing content."""
        # Valid content
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

        # Invalid content
        invalid_content = CrawlResult(
            url="https://example.com",
            content={},
            metadata={},
            status=404
        )
        processed = await http_backend.process(invalid_content)
        assert processed == {}

    @pytest.mark.asyncio
    async def test_close(self, http_backend):
        """Test closing the session."""
        # Create a mock session
        mock_session = AsyncMock()
        mock_session.close = AsyncMock()
        http_backend.session = mock_session

        # Call the method
        await http_backend.close()

        # Verify the session was closed
        mock_session.close.assert_called_once()
        assert http_backend.session is None
