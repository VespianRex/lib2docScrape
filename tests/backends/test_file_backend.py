"""Tests for the file_backend module."""

import os
import tempfile
from unittest.mock import MagicMock

import pytest

from src.backends.base import CrawlResult
from src.backends.file_backend import FileBackend
from src.utils.url.info import URLInfo


@pytest.fixture
def temp_html_file():
    """Create a temporary HTML file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as f:
        f.write("<html><body><h1>Test Content</h1></body></html>")
        temp_path = f.name

    yield temp_path

    # Clean up
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_css_file():
    """Create a temporary CSS file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".css", delete=False, mode="w") as f:
        f.write("body { color: red; }")
        temp_path = f.name

    yield temp_path

    # Clean up
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_js_file():
    """Create a temporary JavaScript file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".js", delete=False, mode="w") as f:
        f.write("function test() { return true; }")
        temp_path = f.name

    yield temp_path

    # Clean up
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def file_backend():
    """Create a FileBackend instance for testing."""
    return FileBackend()


@pytest.fixture
def mock_url_info():
    """Create a mock URLInfo for testing."""
    url_info = MagicMock(spec=URLInfo)
    url_info.is_valid = True
    url_info.raw_url = "file:///path/to/file.html"
    url_info.normalized_url = "file:///path/to/file.html"
    url_info._parsed = MagicMock()
    url_info._parsed.scheme = "file"
    url_info._parsed.path = "/path/to/file.html"
    return url_info


class TestFileBackend:
    """Tests for the FileBackend class."""

    def test_init(self):
        """Test initialization."""
        backend = FileBackend()
        assert backend.name == "file_backend"

    @pytest.mark.asyncio
    async def test_crawl_html_file(self, file_backend, temp_html_file, mock_url_info):
        """Test crawling an HTML file."""
        # Update mock URL info to point to the temp file
        mock_url_info.raw_url = f"file://{temp_html_file}"
        mock_url_info.normalized_url = f"file://{temp_html_file}"
        mock_url_info._parsed.path = temp_html_file

        result = await file_backend.crawl(mock_url_info)

        assert result.status == 200
        assert result.url == mock_url_info.normalized_url
        assert "<h1>Test Content</h1>" in result.content.get("html", "")
        assert result.metadata.get("headers", {}).get("content-type") == "text/html"

    @pytest.mark.asyncio
    async def test_crawl_css_file(self, file_backend, temp_css_file, mock_url_info):
        """Test crawling a CSS file."""
        # Update mock URL info to point to the temp file
        mock_url_info.raw_url = f"file://{temp_css_file}"
        mock_url_info.normalized_url = f"file://{temp_css_file}"
        mock_url_info._parsed.path = temp_css_file

        result = await file_backend.crawl(mock_url_info)

        assert result.status == 200
        assert result.url == mock_url_info.normalized_url
        assert "body { color: red; }" in result.content.get("html", "")
        assert result.metadata.get("headers", {}).get("content-type") == "text/css"

    @pytest.mark.asyncio
    async def test_crawl_js_file(self, file_backend, temp_js_file, mock_url_info):
        """Test crawling a JavaScript file."""
        # Update mock URL info to point to the temp file
        mock_url_info.raw_url = f"file://{temp_js_file}"
        mock_url_info.normalized_url = f"file://{temp_js_file}"
        mock_url_info._parsed.path = temp_js_file

        result = await file_backend.crawl(mock_url_info)

        assert result.status == 200
        assert result.url == mock_url_info.normalized_url
        assert "function test() { return true; }" in result.content.get("html", "")
        assert (
            result.metadata.get("headers", {}).get("content-type")
            == "application/javascript"
        )

    @pytest.mark.asyncio
    async def test_crawl_file_not_found(self, file_backend, mock_url_info):
        """Test crawling a file that doesn't exist."""
        # Update mock URL info to point to a non-existent file
        non_existent_file = "/path/to/non_existent_file.html"
        mock_url_info.raw_url = f"file://{non_existent_file}"
        mock_url_info.normalized_url = f"file://{non_existent_file}"
        mock_url_info._parsed.path = non_existent_file

        result = await file_backend.crawl(mock_url_info)

        assert result.status == 404
        assert result.url == mock_url_info.raw_url
        assert "File not found" in result.error

    @pytest.mark.asyncio
    async def test_crawl_invalid_url_info(self, file_backend):
        """Test crawling with invalid URL info."""
        invalid_url_info = MagicMock(spec=URLInfo)
        invalid_url_info.is_valid = False
        invalid_url_info.raw_url = "invalid://url"

        result = await file_backend.crawl(invalid_url_info)

        assert result.status == 500
        assert result.url == invalid_url_info.raw_url
        assert "Invalid URLInfo" in result.error

    @pytest.mark.asyncio
    async def test_crawl_non_file_scheme(self, file_backend, mock_url_info):
        """Test crawling with a non-file scheme."""
        # Update mock URL info to use a non-file scheme
        mock_url_info._parsed.scheme = "http"

        result = await file_backend.crawl(mock_url_info)

        assert result.status == 500
        assert "only supports 'file://' scheme" in result.error

    @pytest.mark.asyncio
    async def test_validate(self, file_backend):
        """Test validating content."""
        # Valid content
        valid_content = CrawlResult(
            url="file:///path/to/file.html",
            content={"html": "<html></html>"},
            metadata={},
            status=200,
        )
        assert await file_backend.validate(valid_content) is True

        # Invalid content
        invalid_content = CrawlResult(
            url="file:///path/to/file.html",
            content={},
            metadata={},
            status=404,
            error="File not found",
        )
        assert await file_backend.validate(invalid_content) is False

    @pytest.mark.asyncio
    async def test_process(self, file_backend):
        """Test processing content."""
        # Valid content
        valid_content = CrawlResult(
            url="file:///path/to/file.html",
            content={"html": "<html></html>"},
            metadata={"content-type": "text/html"},
            status=200,
        )
        processed = await file_backend.process(valid_content)
        assert processed["url"] == valid_content.url
        assert processed["html"] == valid_content.content["html"]
        assert processed["metadata"] == valid_content.metadata

        # Invalid content
        invalid_content = CrawlResult(
            url="file:///path/to/file.html",
            content={},
            metadata={},
            status=404,
            error="File not found",
        )
        processed = await file_backend.process(invalid_content)
        assert processed == {}
