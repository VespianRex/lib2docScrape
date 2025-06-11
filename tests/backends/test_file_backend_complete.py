"""Tests for the file backend module."""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from src.backends.base import CrawlResult
from src.backends.file_backend import FileBackend
from src.utils.url.info import URLInfo


@pytest.fixture
def file_backend():
    """Create a FileBackend instance for testing."""
    return FileBackend()


@pytest.fixture
def temp_html_file():
    """Create a temporary HTML file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".html", mode="w", delete=False) as f:
        f.write("<html><body><h1>Test Content</h1></body></html>")
        file_path = f.name

    yield file_path

    # Clean up
    if os.path.exists(file_path):
        os.unlink(file_path)


@pytest.fixture
def temp_css_file():
    """Create a temporary CSS file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".css", mode="w", delete=False) as f:
        f.write("body { color: red; }")
        file_path = f.name

    yield file_path

    # Clean up
    if os.path.exists(file_path):
        os.unlink(file_path)


@pytest.fixture
def temp_js_file():
    """Create a temporary JavaScript file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".js", mode="w", delete=False) as f:
        f.write("function test() { return true; }")
        file_path = f.name

    yield file_path

    # Clean up
    if os.path.exists(file_path):
        os.unlink(file_path)


class TestFileBackend:
    """Tests for the FileBackend class."""

    def test_initialization(self):
        """Test that FileBackend can be initialized."""
        backend = FileBackend()
        assert backend.name == "file_backend"

    @pytest.mark.asyncio
    async def test_crawl_invalid_url_info(self, file_backend):
        """Test crawling with invalid URLInfo."""
        # Create a mock URLInfo with is_valid=False
        url_info = MagicMock(spec=URLInfo)
        url_info.is_valid = False
        url_info.raw_url = "invalid://url"

        result = await file_backend.crawl(url_info)

        assert result.status == 500
        assert "Invalid URLInfo provided" in result.error
        assert result.url == "invalid://url"

    @pytest.mark.asyncio
    async def test_crawl_none_url_info(self, file_backend):
        """Test crawling with None URLInfo."""
        result = await file_backend.crawl(None)

        assert result.status == 500
        assert "Invalid URLInfo provided" in result.error
        assert result.url == "Unknown URL"

    @pytest.mark.asyncio
    async def test_crawl_non_file_scheme(self, file_backend):
        """Test crawling with non-file scheme URL."""
        # Create a mock URLInfo with http scheme
        url_info = MagicMock(spec=URLInfo)
        url_info.is_valid = True
        url_info.raw_url = "http://example.com"
        url_info.normalized_url = "http://example.com"
        url_info._parsed = MagicMock()
        url_info._parsed.scheme = "http"

        result = await file_backend.crawl(url_info)

        assert result.status == 500
        assert "only supports 'file://' scheme" in result.error
        assert result.url == "http://example.com"

    @pytest.mark.asyncio
    async def test_crawl_file_not_found(self, file_backend):
        """Test crawling a non-existent file."""
        # Create a mock URLInfo for a non-existent file
        url_info = MagicMock(spec=URLInfo)
        url_info.is_valid = True
        url_info.raw_url = "file:///nonexistent/file.html"
        url_info.normalized_url = "file:///nonexistent/file.html"
        url_info._parsed = MagicMock()
        url_info._parsed.scheme = "file"
        url_info._parsed.path = "/nonexistent/file.html"

        result = await file_backend.crawl(url_info)

        assert result.status == 404
        assert "File not found" in result.error
        assert result.url == "file:///nonexistent/file.html"

    @pytest.mark.asyncio
    async def test_crawl_html_file(self, file_backend, temp_html_file):
        """Test crawling an HTML file."""
        file_uri = f"file://{temp_html_file}"

        # Create a mock URLInfo for the HTML file
        url_info = MagicMock(spec=URLInfo)
        url_info.is_valid = True
        url_info.raw_url = file_uri
        url_info.normalized_url = file_uri
        url_info._parsed = MagicMock()
        url_info._parsed.scheme = "file"
        url_info._parsed.path = temp_html_file

        result = await file_backend.crawl(url_info)

        assert result.status == 200
        assert "<h1>Test Content</h1>" in result.content.get("html", "")
        assert result.url == file_uri
        assert result.metadata.get("headers", {}).get("content-type") == "text/html"

    @pytest.mark.asyncio
    async def test_crawl_css_file(self, file_backend, temp_css_file):
        """Test crawling a CSS file."""
        file_uri = f"file://{temp_css_file}"

        # Create a mock URLInfo for the CSS file
        url_info = MagicMock(spec=URLInfo)
        url_info.is_valid = True
        url_info.raw_url = file_uri
        url_info.normalized_url = file_uri
        url_info._parsed = MagicMock()
        url_info._parsed.scheme = "file"
        url_info._parsed.path = temp_css_file

        result = await file_backend.crawl(url_info)

        assert result.status == 200
        assert "body { color: red; }" in result.content.get("html", "")
        assert result.url == file_uri
        assert result.metadata.get("headers", {}).get("content-type") == "text/css"

    @pytest.mark.asyncio
    async def test_crawl_js_file(self, file_backend, temp_js_file):
        """Test crawling a JavaScript file."""
        file_uri = f"file://{temp_js_file}"

        # Create a mock URLInfo for the JS file
        url_info = MagicMock(spec=URLInfo)
        url_info.is_valid = True
        url_info.raw_url = file_uri
        url_info.normalized_url = file_uri
        url_info._parsed = MagicMock()
        url_info._parsed.scheme = "file"
        url_info._parsed.path = temp_js_file

        result = await file_backend.crawl(url_info)

        assert result.status == 200
        assert "function test() { return true; }" in result.content.get("html", "")
        assert result.url == file_uri
        assert (
            result.metadata.get("headers", {}).get("content-type")
            == "application/javascript"
        )

    @pytest.mark.asyncio
    async def test_crawl_file_read_error(self, file_backend, temp_html_file):
        """Test handling of file read errors."""
        file_uri = f"file://{temp_html_file}"

        # Create a mock URLInfo for the HTML file
        url_info = MagicMock(spec=URLInfo)
        url_info.is_valid = True
        url_info.raw_url = file_uri
        url_info.normalized_url = file_uri
        url_info._parsed = MagicMock()
        url_info._parsed.scheme = "file"
        url_info._parsed.path = temp_html_file

        # Mock aiofiles.open to raise an exception
        with patch("aiofiles.open", side_effect=OSError("Mocked file read error")):
            result = await file_backend.crawl(url_info)

            assert result.status == 500
            assert "Error reading file" in result.error
            assert "Mocked file read error" in result.error
            assert result.url == file_uri

    @pytest.mark.asyncio
    async def test_validate_valid_content(self, file_backend):
        """Test validation of valid content."""
        content = CrawlResult(
            url="file:///test.html",
            content={"html": "<html></html>"},
            metadata={},
            status=200,
        )

        is_valid = await file_backend.validate(content)
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_invalid_content(self, file_backend):
        """Test validation of invalid content."""
        # None content
        is_valid = await file_backend.validate(None)
        assert is_valid is False

        # Non-200 status
        content = CrawlResult(
            url="file:///test.html",
            content={"html": "<html></html>"},
            metadata={},
            status=404,
        )
        is_valid = await file_backend.validate(content)
        assert is_valid is False

        # Empty content dictionary
        content = CrawlResult(
            url="file:///test.html", content={}, metadata={}, status=200
        )
        is_valid = await file_backend.validate(content)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_process_valid_content(self, file_backend):
        """Test processing of valid content."""
        content = CrawlResult(
            url="file:///test.html",
            content={"html": "<html><body>Test</body></html>"},
            metadata={"headers": {"content-type": "text/html"}},
            status=200,
        )

        processed = await file_backend.process(content)

        assert processed["url"] == "file:///test.html"
        assert processed["html"] == "<html><body>Test</body></html>"
        assert processed["metadata"] == {"headers": {"content-type": "text/html"}}

    @pytest.mark.asyncio
    async def test_process_invalid_content(self, file_backend):
        """Test processing of invalid content."""
        content = CrawlResult(
            url="file:///test.html", content={}, metadata={}, status=404
        )

        processed = await file_backend.process(content)
        assert processed == {}

    @pytest.mark.asyncio
    async def test_close(self, file_backend):
        """Test close method (should do nothing for file backend)."""
        # Just ensure it doesn't raise an exception
        await file_backend.close()
