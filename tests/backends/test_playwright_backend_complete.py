"""Tests for the Playwright backend module."""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.backends.base import CrawlResult
from src.backends.playwright_backend import PlaywrightBackend, PlaywrightConfig
from src.utils.circuit_breaker import CircuitBreaker
from src.utils.retry import ExponentialBackoff
from src.utils.url.info import URLInfo


@pytest.fixture
def playwright_config():
    """Create a PlaywrightConfig instance for testing."""
    return PlaywrightConfig(
        browser_type="chromium",
        headless=True,
        timeout=5.0,
        max_retries=2,
        wait_for_load=True,
        wait_until="networkidle",
        wait_time=1.0,
        javascript_enabled=True,
        user_agent="TestAgent",
        viewport_width=1024,
        viewport_height=768,
        ignore_https_errors=True,
        proxy=None,
        extra_http_headers={"Accept-Language": "en-US"},
        screenshots=True,
        screenshot_path="test_screenshots",
        circuit_breaker_threshold=3,
        circuit_breaker_reset_timeout=30.0,
        rate_limit=5.0,
        concurrent_requests=3,
        extract_links=True,
        extract_images=True,
        extract_metadata=True,
        extract_code_blocks=True,
    )


@pytest.fixture
def playwright_backend(playwright_config):
    """Create a PlaywrightBackend instance for testing."""
    backend = PlaywrightBackend(config=playwright_config)
    return backend


@pytest.fixture
def mock_url_info():
    """Create a mock URLInfo for testing."""
    url_info = MagicMock(spec=URLInfo)
    url_info.is_valid = True
    url_info.raw_url = "https://example.com"
    url_info.normalized_url = "https://example.com"
    url_info.error_message = None
    return url_info


@pytest.fixture
def mock_playwright():
    """Create a mock Playwright instance for testing."""
    playwright = AsyncMock()

    # Mock browser factories
    playwright.chromium = AsyncMock()
    playwright.firefox = AsyncMock()
    playwright.webkit = AsyncMock()

    # Mock browser
    browser = AsyncMock()
    context = AsyncMock()
    page = AsyncMock()
    response = AsyncMock()

    # Set up the mock chain
    playwright.chromium.launch.return_value = browser
    playwright.firefox.launch.return_value = browser
    playwright.webkit.launch.return_value = browser
    browser.new_context.return_value = context
    context.new_page.return_value = page
    page.goto.return_value = response

    # Set up response properties
    response.status = 200
    response.url = "https://example.com"
    response.headers = {"content-type": "text/html"}

    # Set up page properties
    page.content.return_value = """
    <html>
        <head>
            <title>Test Page</title>
            <meta name="description" content="Test description">
        </head>
        <body>
            <h1>Test Content</h1>
            <p>This is a test page.</p>
            <a href="/page1">Page 1</a>
            <a href="https://example.com/page2" title="Page 2">Page 2</a>
        </body>
    </html>
    """

    return playwright


# Mock the async_playwright function
@pytest.fixture
def mock_async_playwright(mock_playwright):
    """Mock the async_playwright function."""
    async_playwright_mock = AsyncMock()
    async_playwright_mock.start.return_value = mock_playwright
    return async_playwright_mock


class TestPlaywrightConfig:
    """Tests for the PlaywrightConfig class."""

    def test_default_initialization(self):
        """Test that PlaywrightConfig can be initialized with default values."""
        config = PlaywrightConfig()
        assert config.browser_type == "chromium"
        assert config.headless is True
        assert config.timeout == 30.0
        assert config.max_retries == 3
        assert config.wait_for_load is True
        assert config.wait_until == "networkidle"
        assert config.wait_time == 2.0
        assert config.javascript_enabled is True
        assert (
            config.user_agent == "Lib2DocScrape/1.0 (Playwright) Documentation Crawler"
        )
        assert config.viewport_width == 1280
        assert config.viewport_height == 800
        assert config.ignore_https_errors is False
        assert config.proxy is None
        assert config.extra_http_headers == {}
        assert config.screenshots is False
        assert config.screenshot_path == "screenshots"
        assert config.circuit_breaker_threshold == 5
        assert config.circuit_breaker_reset_timeout == 60.0
        assert config.rate_limit == 2.0
        assert config.concurrent_requests == 5
        assert config.extract_links is True
        assert config.extract_images is True
        assert config.extract_metadata is True
        assert config.extract_code_blocks is True

    def test_custom_initialization(self, playwright_config):
        """Test that PlaywrightConfig can be initialized with custom values."""
        assert playwright_config.browser_type == "chromium"
        assert playwright_config.headless is True
        assert playwright_config.timeout == 5.0
        assert playwright_config.max_retries == 2
        assert playwright_config.wait_for_load is True
        assert playwright_config.wait_until == "networkidle"
        assert playwright_config.wait_time == 1.0
        assert playwright_config.javascript_enabled is True
        assert playwright_config.user_agent == "TestAgent"
        assert playwright_config.viewport_width == 1024
        assert playwright_config.viewport_height == 768
        assert playwright_config.ignore_https_errors is True
        assert playwright_config.proxy is None
        assert playwright_config.extra_http_headers == {"Accept-Language": "en-US"}
        assert playwright_config.screenshots is True
        assert playwright_config.screenshot_path == "test_screenshots"
        assert playwright_config.circuit_breaker_threshold == 3
        assert playwright_config.circuit_breaker_reset_timeout == 30.0
        assert playwright_config.rate_limit == 5.0
        assert playwright_config.concurrent_requests == 3
        assert playwright_config.extract_links is True
        assert playwright_config.extract_images is True
        assert playwright_config.extract_metadata is True
        assert playwright_config.extract_code_blocks is True


class TestPlaywrightBackend:
    """Tests for the PlaywrightBackend class."""

    def test_initialization(self, playwright_config):
        """Test that PlaywrightBackend can be initialized."""
        backend = PlaywrightBackend(config=playwright_config)
        assert backend.name == "playwright"
        assert backend.config == playwright_config
        assert backend._playwright is None
        assert backend._browser is None
        assert backend._context is None
        assert isinstance(backend._processing_semaphore, asyncio.Semaphore)
        assert isinstance(backend._rate_limiter, asyncio.Lock)
        assert backend._last_request == 0.0
        assert isinstance(backend._crawled_urls, set)
        assert len(backend._crawled_urls) == 0
        assert isinstance(backend.retry_strategy, ExponentialBackoff)
        assert isinstance(backend.circuit_breaker, CircuitBreaker)

    def test_initialization_with_default_config(self):
        """Test that PlaywrightBackend can be initialized with default config."""
        backend = PlaywrightBackend()
        assert backend.name == "playwright"
        assert isinstance(backend.config, PlaywrightConfig)
        assert backend._playwright is None
        assert backend._browser is None

    @pytest.mark.asyncio
    async def test_ensure_browser_playwright_not_available(self, playwright_backend):
        """Test _ensure_browser method when Playwright is not available."""
        with patch("src.backends.playwright_backend.PLAYWRIGHT_AVAILABLE", False):
            with pytest.raises(RuntimeError, match="Playwright is not installed"):
                await playwright_backend._ensure_browser()

    @pytest.mark.asyncio
    async def test_ensure_browser_chromium(
        self, playwright_backend, mock_async_playwright
    ):
        """Test _ensure_browser method with chromium browser."""
        with (
            patch("src.backends.playwright_backend.PLAYWRIGHT_AVAILABLE", True),
            patch(
                "src.backends.playwright_backend.async_playwright",
                return_value=mock_async_playwright,
            ),
        ):
            await playwright_backend._ensure_browser()

            # Verify playwright was started
            mock_async_playwright.start.assert_called_once()

            # Verify chromium browser was launched
            playwright_backend._playwright.chromium.launch.assert_called_once_with(
                headless=True, proxy=None, ignore_https_errors=True
            )

            # Verify browser context was created
            browser = playwright_backend._playwright.chromium.launch.return_value
            browser.new_context.assert_called_once_with(
                viewport={"width": 1024, "height": 768},
                user_agent="TestAgent",
                extra_http_headers={"Accept-Language": "en-US"},
            )

    @pytest.mark.asyncio
    async def test_ensure_browser_firefox(
        self, playwright_backend, mock_async_playwright
    ):
        """Test _ensure_browser method with firefox browser."""
        # Change browser type to firefox
        playwright_backend.config.browser_type = "firefox"

        with (
            patch("src.backends.playwright_backend.PLAYWRIGHT_AVAILABLE", True),
            patch(
                "src.backends.playwright_backend.async_playwright",
                return_value=mock_async_playwright,
            ),
        ):
            await playwright_backend._ensure_browser()

            # Verify firefox browser was launched
            playwright_backend._playwright.firefox.launch.assert_called_once()

    @pytest.mark.asyncio
    async def test_ensure_browser_webkit(
        self, playwright_backend, mock_async_playwright
    ):
        """Test _ensure_browser method with webkit browser."""
        # Change browser type to webkit
        playwright_backend.config.browser_type = "webkit"

        with (
            patch("src.backends.playwright_backend.PLAYWRIGHT_AVAILABLE", True),
            patch(
                "src.backends.playwright_backend.async_playwright",
                return_value=mock_async_playwright,
            ),
        ):
            await playwright_backend._ensure_browser()

            # Verify webkit browser was launched
            playwright_backend._playwright.webkit.launch.assert_called_once()

    @pytest.mark.asyncio
    async def test_ensure_browser_with_proxy(
        self, playwright_backend, mock_async_playwright
    ):
        """Test _ensure_browser method with proxy configuration."""
        # Set proxy
        playwright_backend.config.proxy = "http://proxy.example.com:8080"

        with (
            patch("src.backends.playwright_backend.PLAYWRIGHT_AVAILABLE", True),
            patch(
                "src.backends.playwright_backend.async_playwright",
                return_value=mock_async_playwright,
            ),
        ):
            await playwright_backend._ensure_browser()

            # Verify browser was launched with proxy
            playwright_backend._playwright.chromium.launch.assert_called_once_with(
                headless=True,
                proxy={"server": "http://proxy.example.com:8080"},
                ignore_https_errors=True,
            )

    @pytest.mark.asyncio
    async def test_ensure_browser_exception(
        self, playwright_backend, mock_async_playwright
    ):
        """Test _ensure_browser method with exception during browser launch."""
        # Make browser launch raise an exception
        mock_async_playwright.start.return_value.chromium.launch.side_effect = (
            Exception("Browser launch error")
        )

        with (
            patch("src.backends.playwright_backend.PLAYWRIGHT_AVAILABLE", True),
            patch(
                "src.backends.playwright_backend.async_playwright",
                return_value=mock_async_playwright,
            ),
        ):
            with pytest.raises(Exception, match="Browser launch error"):
                await playwright_backend._ensure_browser()

            # Verify playwright was stopped
            assert mock_async_playwright.start.return_value.stop.call_count == 1

    @pytest.mark.asyncio
    async def test_wait_rate_limit(self, playwright_backend):
        """Test _wait_rate_limit method."""
        # First call should not wait
        start_time = time.time()
        await playwright_backend._wait_rate_limit()
        elapsed = time.time() - start_time
        assert elapsed < 0.1  # Should be very quick

        # Second call should wait according to rate limit
        start_time = time.time()
        await playwright_backend._wait_rate_limit()
        elapsed = time.time() - start_time
        expected_wait = 1.0 / playwright_backend.config.rate_limit
        assert elapsed >= expected_wait * 0.9  # Allow for small timing variations

    @pytest.mark.asyncio
    async def test_navigate_with_retry_circuit_breaker_open(self, playwright_backend):
        """Test _navigate_with_retry method when circuit breaker is open."""
        # Mock circuit breaker to be open
        playwright_backend.circuit_breaker.is_open = Mock(return_value=True)

        result = await playwright_backend._navigate_with_retry("https://example.com")

        assert result["success"] is False
        assert result["error"] == "Circuit breaker open"
        assert result["status"] == 503
        assert result["content"] is None

    @pytest.mark.asyncio
    async def test_navigate_with_retry_success(
        self, playwright_backend, mock_async_playwright
    ):
        """Test _navigate_with_retry method with successful navigation."""
        # Mock circuit breaker to be closed
        playwright_backend.circuit_breaker.is_open = Mock(return_value=False)
        playwright_backend.circuit_breaker.record_success = Mock()

        # Mock _ensure_browser to do nothing
        playwright_backend._ensure_browser = AsyncMock()

        # Mock _wait_rate_limit to do nothing
        playwright_backend._wait_rate_limit = AsyncMock()

        # Set up browser and context
        playwright_backend._browser = (
            mock_async_playwright.start.return_value.chromium.launch.return_value
        )
        playwright_backend._context = (
            playwright_backend._browser.new_context.return_value
        )

        with patch("os.makedirs") as mock_makedirs:
            result = await playwright_backend._navigate_with_retry(
                "https://example.com"
            )

            # Verify page was created and navigated
            playwright_backend._context.new_page.assert_called_once()
            page = playwright_backend._context.new_page.return_value
            page.goto.assert_called_once_with(
                "https://example.com",
                wait_until="networkidle",
                timeout=5000,  # 5.0 seconds in ms
            )

            # Verify content was retrieved
            page.content.assert_called_once()

            # Verify screenshot was taken
            mock_makedirs.assert_called_once_with("test_screenshots", exist_ok=True)
            page.screenshot.assert_called_once()

            # Verify page was closed
            page.close.assert_called_once()

            # Verify circuit breaker was updated
            playwright_backend.circuit_breaker.record_success.assert_called_once()

            # Verify result
            assert result["success"] is True
            assert result["status"] == 200
            assert "<title>Test Page</title>" in result["content"]
            assert result["url"] == "https://example.com"
            assert "screenshot" in result

    @pytest.mark.asyncio
    async def test_navigate_with_retry_timeout(
        self, playwright_backend, mock_async_playwright
    ):
        """Test _navigate_with_retry method with timeout error."""
        # Mock circuit breaker
        playwright_backend.circuit_breaker.is_open = Mock(return_value=False)
        playwright_backend.circuit_breaker.record_failure = Mock()

        # Mock _ensure_browser and _wait_rate_limit
        playwright_backend._ensure_browser = AsyncMock()
        playwright_backend._wait_rate_limit = AsyncMock()

        # Set up browser and context
        playwright_backend._browser = (
            mock_async_playwright.start.return_value.chromium.launch.return_value
        )
        playwright_backend._context = (
            playwright_backend._browser.new_context.return_value
        )

        # Make page.goto raise a timeout error
        page = playwright_backend._context.new_page.return_value

        # Import PlaywrightTimeoutError
        with patch("src.backends.playwright_backend.PlaywrightTimeoutError", Exception):
            # Create a new exception class that matches the imported one
            playwright_timeout_error = Exception("Navigation timeout")
            page.goto.side_effect = playwright_timeout_error

            # Mock retry strategy
            playwright_backend.retry_strategy.get_delay = Mock(return_value=0.01)

            result = await playwright_backend._navigate_with_retry(
                "https://example.com"
            )

            # Verify circuit breaker was updated
            assert (
                playwright_backend.circuit_breaker.record_failure.call_count
                == playwright_backend.config.max_retries + 1
            )

            # Verify result
            assert result["success"] is False
            assert result["status"] == 408
            assert "Timeout after" in result["error"]
            assert result["content"] is None

    @pytest.mark.asyncio
    async def test_navigate_with_retry_unexpected_error(
        self, playwright_backend, mock_async_playwright
    ):
        """Test _navigate_with_retry method with unexpected error."""
        # Mock circuit breaker
        playwright_backend.circuit_breaker.is_open = Mock(return_value=False)
        playwright_backend.circuit_breaker.record_failure = Mock()

        # Mock _ensure_browser and _wait_rate_limit
        playwright_backend._ensure_browser = AsyncMock()
        playwright_backend._wait_rate_limit = AsyncMock()

        # Set up browser and context
        playwright_backend._browser = (
            mock_async_playwright.start.return_value.chromium.launch.return_value
        )
        playwright_backend._context = (
            playwright_backend._browser.new_context.return_value
        )

        # Make page.goto raise an unexpected error
        page = playwright_backend._context.new_page.return_value
        page.goto.side_effect = Exception("Unexpected navigation error")

        # Mock retry strategy
        playwright_backend.retry_strategy.get_delay = Mock(return_value=0.01)

        result = await playwright_backend._navigate_with_retry("https://example.com")

        # Verify circuit breaker was updated
        assert (
            playwright_backend.circuit_breaker.record_failure.call_count
            == playwright_backend.config.max_retries + 1
        )

        # Verify result
        assert result["success"] is False
        assert result["status"] == 500
        assert "Unexpected error" in result["error"]
        assert result["content"] is None

    @pytest.mark.asyncio
    async def test_crawl_invalid_url(self, playwright_backend):
        """Test crawl method with invalid URL."""
        # Create a mock URLInfo with invalid URL
        url_info = MagicMock(spec=URLInfo)
        url_info.is_valid = False
        url_info.raw_url = "invalid://url"
        url_info.normalized_url = "invalid://url"
        url_info.error_message = "Invalid URL scheme"

        result = await playwright_backend.crawl(url_info)

        assert result.status == 400
        assert result.error == "Invalid URL: Invalid URL scheme"
        assert result.url == "invalid://url"

    @pytest.mark.asyncio
    async def test_crawl_already_crawled_url(self, playwright_backend, mock_url_info):
        """Test crawl method with already crawled URL."""
        # Add URL to crawled URLs
        playwright_backend._crawled_urls.add(mock_url_info.normalized_url)

        result = await playwright_backend.crawl(mock_url_info)

        assert result.status == 304
        assert result.error == "URL already crawled"
        assert result.metadata["cached"] is True

    @pytest.mark.asyncio
    async def test_crawl_navigation_failure(self, playwright_backend, mock_url_info):
        """Test crawl method with navigation failure."""
        # Mock _navigate_with_retry to return a failure result
        playwright_backend._navigate_with_retry = AsyncMock(
            return_value={
                "success": False,
                "error": "Navigation failed",
                "status": 500,
                "content": None,
            }
        )

        result = await playwright_backend.crawl(mock_url_info)

        assert result.status == 500
        assert result.error == "Navigation failed"
        assert result.metadata["error_details"] == "Navigation failed"
        assert result.metadata["backend"] == "playwright"

    @pytest.mark.asyncio
    async def test_crawl_successful(self, playwright_backend, mock_url_info):
        """Test crawl method with successful navigation."""
        # Mock _navigate_with_retry to return a successful result
        playwright_backend._navigate_with_retry = AsyncMock(
            return_value={
                "success": True,
                "status": 200,
                "content": "<html><body>Test content</body></html>",
                "url": "https://example.com",
                "headers": {"content-type": "text/html"},
                "screenshot": "/path/to/screenshot.png",
            }
        )

        result = await playwright_backend.crawl(mock_url_info)

        assert result.status == 200
        assert result.url == "https://example.com"
        assert result.content["html"] == "<html><body>Test content</body></html>"
        assert result.metadata["headers"] == {"content-type": "text/html"}
        assert result.metadata["screenshot"] == "/path/to/screenshot.png"
        assert result.metadata["backend"] == "playwright"
        assert result.metadata["browser_type"] == "chromium"
        assert result.metadata["javascript_enabled"] is True

        # Verify URL was added to crawled URLs
        assert mock_url_info.normalized_url in playwright_backend._crawled_urls

    @pytest.mark.asyncio
    async def test_validate_valid_content(self, playwright_backend):
        """Test validate method with valid content."""
        content = CrawlResult(
            url="https://example.com",
            content={
                "html": "<html><head><title>Test</title></head><body>Valid content that is long enough to pass validation checks. This content should be more than 100 characters to ensure it passes the length check.</body></html>"
            },
            metadata={},
            status=200,
        )

        is_valid = await playwright_backend.validate(content)
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_invalid_content(self, playwright_backend):
        """Test validate method with invalid content."""
        # None content
        is_valid = await playwright_backend.validate(None)
        assert is_valid is False

        # Empty HTML
        content = CrawlResult(
            url="https://example.com", content={"html": ""}, metadata={}, status=200
        )
        is_valid = await playwright_backend.validate(content)
        assert is_valid is False

        # No HTML field
        content = CrawlResult(
            url="https://example.com", content={}, metadata={}, status=200
        )
        is_valid = await playwright_backend.validate(content)
        assert is_valid is False

        # Content too short
        content = CrawlResult(
            url="https://example.com",
            content={"html": "<html>Short</html>"},
            metadata={},
            status=200,
        )
        is_valid = await playwright_backend.validate(content)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_error_indicators(self, playwright_backend):
        """Test validate method with error indicators in title."""
        # Create content with error indicator in title
        content = CrawlResult(
            url="https://example.com",
            content={
                "html": "<html><head><title>404 Not Found</title></head><body>This page could not be found. This content is long enough to pass the length check but should fail due to the error indicator in the title.</body></html>"
            },
            metadata={},
            status=200,
        )

        is_valid = await playwright_backend.validate(content)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_process_valid_content(self, playwright_backend):
        """Test process method with valid content."""
        content = CrawlResult(
            url="https://example.com",
            content={
                "html": """
            <html>
                <head>
                    <title>Test Page</title>
                    <meta name="description" content="Test description">
                </head>
                <body>
                    <h1>Test Content</h1>
                    <p>This is a test page.</p>
                    <a href="/page1">Page 1</a>
                    <a href="https://example.com/page2" title="Page 2">Page 2</a>
                </body>
            </html>
            """
            },
            metadata={"screenshot": "/path/to/screenshot.png"},
            status=200,
        )

        # Mock content processor
        processed_content = MagicMock()
        processed_content.title = "Test Page"
        processed_content.content = "Test Content This is a test page."
        processed_content.metadata = {"description": "Test description"}
        processed_content.headings = [{"level": 1, "text": "Test Content"}]
        processed_content.assets = []
        processed_content.structure = {
            "sections": [{"title": "Test Content", "content": "This is a test page."}]
        }

        playwright_backend.content_processor.process = AsyncMock(
            return_value=processed_content
        )

        result = await playwright_backend.process(content)

        # Verify content processor was called
        playwright_backend.content_processor.process.assert_called_once_with(
            content=content.content["html"],
            base_url="https://example.com",
            content_type="text/html",
        )

        # Verify result
        assert result["title"] == "Test Page"
        assert result["content"] == "Test Content This is a test page."
        assert "description" in result["metadata"]
        assert result["metadata"]["screenshot"] == "/path/to/screenshot.png"
        assert len(result["links"]) == 2
        assert result["links"][0]["url"].endswith("/page1")
        assert result["links"][1]["url"] == "https://example.com/page2"
        assert result["links"][1]["title"] == "Page 2"
        assert result["headings"] == [{"level": 1, "text": "Test Content"}]
        assert result["assets"] == []
        assert result["structure"] == {
            "sections": [{"title": "Test Content", "content": "This is a test page."}]
        }

    @pytest.mark.asyncio
    async def test_process_no_html_content(self, playwright_backend):
        """Test process method with no HTML content."""
        content = CrawlResult(
            url="https://example.com", content={}, metadata={}, status=200
        )

        result = await playwright_backend.process(content)

        assert "error" in result
        assert "No HTML content found" in result["error"]

    @pytest.mark.asyncio
    async def test_process_error(self, playwright_backend):
        """Test process method with processing error."""
        content = CrawlResult(
            url="https://example.com",
            content={"html": "<html><body>Test</body></html>"},
            metadata={},
            status=200,
        )

        # Mock content processor to raise an exception
        playwright_backend.content_processor.process = AsyncMock(
            side_effect=Exception("Processing error")
        )

        result = await playwright_backend.process(content)

        assert "error" in result
        assert "Processing error" in result["error"]

    @pytest.mark.asyncio
    async def test_close(self, playwright_backend):
        """Test close method."""
        # Save a reference to the mocks before they're replaced by None
        browser_mock = AsyncMock()
        playwright_mock = AsyncMock()

        # Create mock browser and playwright
        playwright_backend._browser = browser_mock
        playwright_backend._playwright = playwright_mock
        playwright_backend._context = AsyncMock()
        playwright_backend._crawled_urls.add("https://example.com")
        playwright_backend._last_request = 123.45

        await playwright_backend.close()

        # Verify browser and playwright were closed
        browser_mock.close.assert_called_once()
        playwright_mock.stop.assert_called_once()
        # Context is only closed implicitly when browser.close() is called
        # We don't assert it's called explicitly

        # Verify state was reset
        assert playwright_backend._browser is None
        assert playwright_backend._playwright is None
        assert playwright_backend._context is None
        assert len(playwright_backend._crawled_urls) == 0
        assert playwright_backend._last_request == 0.0

    @pytest.mark.asyncio
    async def test_close_with_exceptions(self, playwright_backend):
        """Test close method with exceptions."""
        # Create mock browser and playwright that raise exceptions
        playwright_backend._browser = AsyncMock()
        playwright_backend._browser.close.side_effect = Exception("Browser close error")

        playwright_backend._playwright = AsyncMock()
        playwright_backend._playwright.stop.side_effect = Exception(
            "Playwright stop error"
        )

        # Set context and other properties
        playwright_backend._context = AsyncMock()
        playwright_backend._crawled_urls.add("https://example.com")
        playwright_backend._last_request = 123.45

        # Should not raise exceptions
        await playwright_backend.close()

        # Verify methods were called despite exceptions
        playwright_backend._browser.close.assert_called_once()
        playwright_backend._playwright.stop.assert_called_once()

        # Verify state was reset correctly (note: browser and playwright are not None when exceptions occur)
        assert (
            playwright_backend._browser is not None
        )  # Will not be None due to exception
        assert (
            playwright_backend._playwright is not None
        )  # Will not be None due to exception
        assert playwright_backend._context is None
        assert len(playwright_backend._crawled_urls) == 0
        assert playwright_backend._last_request == 0.0
