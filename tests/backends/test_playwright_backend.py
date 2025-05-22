import asyncio
import os
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch, mock_open

# Pydantic v1/v2 compatibility
try:
    from pydantic.v1 import ValidationError
except ImportError:
    from pydantic import ValidationError

from src.backends.playwright_backend import PlaywrightBackend, PlaywrightConfig, PLAYWRIGHT_AVAILABLE
from src.utils.url.factory import create_url_info
from src.backends.base import CrawlResult
from src.processors.content.models import ProcessedContent

# Mock Playwright specific errors if Playwright is available
if PLAYWRIGHT_AVAILABLE:
    from playwright.async_api import TimeoutError as PlaywrightTimeoutError
else:
    # Define a dummy PlaywrightTimeoutError if Playwright is not installed
    # This allows tests to run and be defined even if Playwright isn't in the environment
    class PlaywrightTimeoutError(Exception):
        pass

@pytest.fixture
def default_playwright_config():
    return PlaywrightConfig()

@pytest.fixture
def custom_playwright_config():
    return PlaywrightConfig(
        browser_type="firefox",
        headless=False,
        timeout=10.0,
        max_retries=1,
        wait_time=0.5,
        screenshots=True,
        screenshot_path="/tmp/pw_screenshots",
        rate_limit=1.0,
        concurrent_requests=2,
        proxy="http://localhost:8080"
    )

def test_playwright_config_defaults(default_playwright_config):
    assert default_playwright_config.browser_type == "chromium"
    assert default_playwright_config.headless is True
    assert default_playwright_config.timeout == 30.0
    assert default_playwright_config.max_retries == 3
    assert default_playwright_config.wait_for_load is True
    assert default_playwright_config.wait_until == "networkidle"
    assert default_playwright_config.wait_time == 2.0
    assert default_playwright_config.javascript_enabled is True
    assert default_playwright_config.user_agent == "Lib2DocScrape/1.0 (Playwright) Documentation Crawler"
    assert default_playwright_config.screenshots is False
    assert default_playwright_config.screenshot_path == "screenshots"
    assert default_playwright_config.proxy is None

def test_playwright_config_custom(custom_playwright_config):
    assert custom_playwright_config.browser_type == "firefox"
    assert custom_playwright_config.headless is False
    assert custom_playwright_config.timeout == 10.0
    assert custom_playwright_config.screenshots is True
    assert custom_playwright_config.screenshot_path == "/tmp/pw_screenshots"
    assert custom_playwright_config.proxy == "http://localhost:8080"

def test_playwright_config_validation():
    with pytest.raises(ValidationError):
        PlaywrightConfig(browser_type="invalid_browser") # Though not strictly validated by pydantic here
    with pytest.raises(ValidationError):
        PlaywrightConfig(timeout=0)
    with pytest.raises(ValidationError):
        PlaywrightConfig(max_retries=-1)
    # wait_until could be validated if an Enum was used.

@pytest.fixture
def url_info_pw(): # Renamed to avoid conflict
    return create_url_info("https://example.com/playwright")

@pytest.fixture
def invalid_url_info_pw(): # Renamed
    return create_url_info("invalid-pw-url")

@pytest_asyncio.fixture
async def mock_playwright_api():
    if not PLAYWRIGHT_AVAILABLE:
        # If playwright is not installed, mock the top-level import path
        # This is tricky because `async_playwright` is a function returning a context manager
        mock_async_playwright_cm = AsyncMock() # Mock for the context manager
        mock_playwright_instance = AsyncMock() # Mock for the playwright object itself

        mock_browser = AsyncMock()
        mock_browser.new_context.return_value = AsyncMock()
        mock_browser.new_context.return_value.new_page.return_value = AsyncMock()
        mock_browser.close = AsyncMock()
        
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_playwright_instance.firefox.launch.return_value = mock_browser
        mock_playwright_instance.webkit.launch.return_value = mock_browser
        mock_playwright_instance.stop = AsyncMock()

        mock_async_playwright_cm.__aenter__.return_value = mock_playwright_instance
        
        with patch('src.backends.playwright_backend.async_playwright', return_value=mock_async_playwright_cm) as mocked_pw:
            yield mocked_pw
    else:
        # If playwright is installed, we still want to mock its actual calls
        mock_async_playwright_cm = AsyncMock()
        mock_playwright_instance = AsyncMock()
        
        mock_browser_instance = AsyncMock()
        mock_browser_instance.new_context = AsyncMock()
        mock_browser_instance.close = AsyncMock()
        
        mock_playwright_instance.chromium.launch = AsyncMock(return_value=mock_browser_instance)
        mock_playwright_instance.firefox.launch = AsyncMock(return_value=mock_browser_instance)
        mock_playwright_instance.webkit.launch = AsyncMock(return_value=mock_browser_instance)
        mock_playwright_instance.stop = AsyncMock()

        mock_async_playwright_cm.__aenter__.return_value = mock_playwright_instance
        
        with patch('playwright.async_api.async_playwright', return_value=mock_async_playwright_cm) as mocked_pw:
            yield mocked_pw


@pytest_asyncio.fixture
async def backend_pw(default_playwright_config, mock_playwright_api): # Renamed
    # The mock_playwright_api fixture handles patching the playwright import
    # So, PlaywrightBackend can be instantiated normally.
    b = PlaywrightBackend(config=default_playwright_config)
    b.content_processor = AsyncMock(spec=ProcessedContent) # Mock content processor
    yield b
    await b.close() # Ensure cleanup

# Test initialization
def test_playwright_backend_initialization(default_playwright_config):
    with patch('src.backends.playwright_backend.ContentProcessor') as mock_cp:
        backend = PlaywrightBackend(config=default_playwright_config)
        assert backend.config == default_playwright_config
        assert backend.name == "playwright"
        assert backend._playwright is None
        assert backend._browser is None
        assert backend._context is None
        mock_cp.assert_called_once()

@pytest.mark.asyncio
async def test_ensure_browser_success(backend_pw: PlaywrightBackend, mock_playwright_api):
    if not PLAYWRIGHT_AVAILABLE: # Conditionally skip if not available, though mock should handle
        pytest.skip("Playwright not installed, skipping direct test of _ensure_browser with mocks")

    # _ensure_browser calls async_playwright().start() which is mock_playwright_api.__aenter__
    # then browser_factory.launch() and browser.new_context()
    
    mock_pw_cm = mock_playwright_api.return_value # The AsyncMock for the context manager
    mock_pw_instance = mock_pw_cm.__aenter__.return_value # The playwright object

    # Mock the launch and new_context calls specifically for this test if needed for assertion
    mock_browser = AsyncMock()
    mock_context = AsyncMock()
    mock_browser.new_context.return_value = mock_context
    mock_pw_instance.chromium.launch.return_value = mock_browser # Assuming chromium is default

    await backend_pw._ensure_browser()

    mock_playwright_api.assert_called_once() # async_playwright()
    mock_pw_cm.__aenter__.assert_called_once() # .start()
    mock_pw_instance.chromium.launch.assert_called_once_with(
        headless=backend_pw.config.headless,
        proxy=None, # Assuming default config
        ignore_https_errors=backend_pw.config.ignore_https_errors
    )
    mock_browser.new_context.assert_called_once()
    assert backend_pw._browser is not None
    assert backend_pw._context is not None

@pytest.mark.asyncio
async def test_ensure_browser_playwright_not_available():
    original_playwright_available = PLAYWRIGHT_AVAILABLE
    try:
        # Simulate Playwright not being available
        with patch('src.backends.playwright_backend.PLAYWRIGHT_AVAILABLE', False):
            backend = PlaywrightBackend()
            with pytest.raises(RuntimeError, match="Playwright is not installed"):
                await backend._ensure_browser()
    finally:
        # Restore original value if necessary for other tests in suite
        with patch('src.backends.playwright_backend.PLAYWRIGHT_AVAILABLE', original_playwright_available):
            pass


@pytest.mark.asyncio
async def test_ensure_browser_launch_failure(backend_pw: PlaywrightBackend, mock_playwright_api):
    if not PLAYWRIGHT_AVAILABLE:
        pytest.skip("Playwright not installed, mock might not perfectly replicate launch failure nuances.")

    mock_pw_cm = mock_playwright_api.return_value
    mock_pw_instance = mock_pw_cm.__aenter__.return_value
    mock_pw_instance.chromium.launch.side_effect = Exception("Launch failed")
    mock_pw_instance.stop = AsyncMock() # Ensure stop can be called

    with pytest.raises(Exception, match="Launch failed"):
        await backend_pw._ensure_browser()
    
    mock_pw_instance.stop.assert_called_once() # Ensure cleanup attempt on failure
    assert backend_pw._browser is None
    assert backend_pw._playwright is None


@pytest.mark.asyncio
async def test_close_playwright_resources(backend_pw: PlaywrightBackend, mock_playwright_api):
    if not PLAYWRIGHT_AVAILABLE:
        pytest.skip("Playwright not installed.")

    # Simulate that browser and playwright were initialized
    mock_pw_cm = mock_playwright_api.return_value
    mock_pw_instance = mock_pw_cm.__aenter__.return_value
    
    backend_pw._browser = mock_pw_instance.chromium.launch.return_value
    backend_pw._playwright = mock_pw_instance
    backend_pw._context = AsyncMock() # just needs to be non-None

    await backend_pw.close()

    backend_pw._browser.close.assert_called_once()
    mock_pw_instance.stop.assert_called_once()
    assert backend_pw._browser is None
    assert backend_pw._playwright is None
    assert backend_pw._context is None


@pytest.mark.asyncio
async def test_crawl_invalid_url_pw(backend_pw: PlaywrightBackend, invalid_url_info_pw):
    result = await backend_pw.crawl(invalid_url_info_pw)
    assert result.status == 400
    assert "Invalid URL" in result.error

@pytest.mark.asyncio
async def test_crawl_already_crawled_pw(backend_pw: PlaywrightBackend, url_info_pw):
    backend_pw._crawled_urls.add(url_info_pw.normalized_url)
    result = await backend_pw.crawl(url_info_pw)
    assert result.status == 304
    assert "URL already crawled" in result.error

@pytest.mark.asyncio
async def test_navigate_with_retry_success(backend_pw: PlaywrightBackend, url_info_pw):
    # Mock _ensure_browser as it's called by _navigate_with_retry
    backend_pw._ensure_browser = AsyncMock()
    # Assume _ensure_browser sets up _context
    backend_pw._context = AsyncMock()
    mock_page = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.url = url_info_pw.normalized_url
    mock_response.headers = {"Content-Type": "text/html"}

    mock_page.goto.return_value = mock_response
    mock_page.content.return_value = "<html>Success</html>"
    mock_page.close = AsyncMock()
    backend_pw._context.new_page.return_value = mock_page
    
    nav_result = await backend_pw._navigate_with_retry(url_info_pw.normalized_url)

    assert nav_result["success"] is True
    assert nav_result["status"] == 200
    assert nav_result["content"] == "<html>Success</html>"
    mock_page.goto.assert_called_once()
    mock_page.content.assert_called_once()
    mock_page.close.assert_called_once()

@pytest.mark.asyncio
async def test_navigate_with_retry_timeout_then_success(backend_pw: PlaywrightBackend, url_info_pw):
    backend_pw.config.max_retries = 1 # Allow one retry
    backend_pw._ensure_browser = AsyncMock()
    backend_pw._context = AsyncMock()
    
    mock_page_attempt1 = AsyncMock()
    mock_page_attempt1.goto.side_effect = PlaywrightTimeoutError("Timeout on first attempt")
    mock_page_attempt1.close = AsyncMock()

    mock_page_attempt2 = AsyncMock()
    mock_response_attempt2 = AsyncMock(status=200, url=url_info_pw.normalized_url, headers={})
    mock_page_attempt2.goto.return_value = mock_response_attempt2
    mock_page_attempt2.content.return_value = "<html>Retry Success</html>"
    mock_page_attempt2.close = AsyncMock()

    # new_page should return attempt1 then attempt2
    backend_pw._context.new_page.side_effect = [mock_page_attempt1, mock_page_attempt2]
    
    with patch('asyncio.sleep', AsyncMock()) as mock_sleep: # Mock sleep for retry
        nav_result = await backend_pw._navigate_with_retry(url_info_pw.normalized_url)

    assert nav_result["success"] is True
    assert nav_result["content"] == "<html>Retry Success</html>"
    assert backend_pw._context.new_page.call_count == 2
    mock_page_attempt1.goto.assert_called_once()
    mock_page_attempt2.goto.assert_called_once()
    mock_sleep.assert_called_once() # Called after the first failure


@pytest.mark.asyncio
async def test_navigate_with_retry_persistent_failure(backend_pw: PlaywrightBackend, url_info_pw):
    backend_pw.config.max_retries = 1
    backend_pw._ensure_browser = AsyncMock()
    backend_pw._context = AsyncMock()
    
    mock_page = AsyncMock()
    mock_page.goto.side_effect = PlaywrightTimeoutError("Persistent Timeout")
    mock_page.close = AsyncMock() # Ensure close is always callable

    backend_pw._context.new_page.return_value = mock_page
    
    with patch('asyncio.sleep', AsyncMock()) as mock_sleep:
        nav_result = await backend_pw._navigate_with_retry(url_info_pw.normalized_url)

    assert nav_result["success"] is False
    assert "Timeout after 1 retries" in nav_result["error"]
    assert backend_pw._context.new_page.call_count == backend_pw.config.max_retries + 1
    mock_sleep.assert_called_once()


@pytest.mark.asyncio
async def test_navigate_with_retry_circuit_breaker_opens(backend_pw: PlaywrightBackend, url_info_pw):
    backend_pw.config.max_retries = 0 # Fail fast
    backend_pw.circuit_breaker.failure_threshold = 1 # Open after 1 failure
    backend_pw._ensure_browser = AsyncMock()
    backend_pw._context = AsyncMock()
    
    mock_page = AsyncMock()
    mock_page.goto.side_effect = Exception("Generic navigation error")
    mock_page.close = AsyncMock()
    backend_pw._context.new_page.return_value = mock_page

    # First call should fail and trip the circuit breaker
    nav_result1 = await backend_pw._navigate_with_retry(url_info_pw.normalized_url)
    assert nav_result1["success"] is False
    assert backend_pw.circuit_breaker.is_open()

    # Second call should be blocked by the circuit breaker
    nav_result2 = await backend_pw._navigate_with_retry(url_info_pw.normalized_url)
    assert nav_result2["success"] is False
    assert nav_result2["error"] == "Circuit breaker open"


@pytest.mark.asyncio
async def test_crawl_successful_pw(backend_pw: PlaywrightBackend, url_info_pw):
    html_content = "<html><body>Playwright Success</body></html>"
    mock_nav_result = {
        "success": True, "status": 200, "content": html_content, 
        "screenshot": None, "url": url_info_pw.normalized_url, "headers": {}
    }
    backend_pw._navigate_with_retry = AsyncMock(return_value=mock_nav_result)
    
    mock_processed_content = ProcessedContent(title="PW Page", content=html_content, links=[]) # Simplified
    backend_pw.content_processor.process = AsyncMock(return_value=mock_processed_content)
    backend_pw.validate = AsyncMock(return_value=True)


    result = await backend_pw.crawl(url_info_pw)

    assert result.status == 200
    assert result.content["html"] == html_content
    assert result.metadata["backend"] == "playwright"
    assert url_info_pw.normalized_url in backend_pw._crawled_urls

@pytest.mark.asyncio
async def test_crawl_navigation_fail_pw(backend_pw: PlaywrightBackend, url_info_pw):
    mock_nav_result = {"success": False, "error": "Nav Failed", "status": 500}
    backend_pw._navigate_with_retry = AsyncMock(return_value=mock_nav_result)

    result = await backend_pw.crawl(url_info_pw)

    assert result.status == 500
    assert "Failed to navigate to URL" in result.error
    assert "Nav Failed" in result.metadata["error_details"]


@pytest.mark.asyncio
async def test_validate_content_pw(backend_pw: PlaywrightBackend):
    valid_cr = CrawlResult(url="http://example.com", content={"html": "<p>" + "a"*100 + "</p>"}, status=200)
    short_cr = CrawlResult(url="http://example.com", content={"html": "<p>short</p>"}, status=200)
    error_title_cr = CrawlResult(url="http://example.com", content={"html": "<title>404</title>" + "<p>" + "a"*100 + "</p>"}, status=200)

    assert await backend_pw.validate(valid_cr) is True
    assert await backend_pw.validate(short_cr) is False
    assert await backend_pw.validate(error_title_cr) is False


@pytest.mark.asyncio
async def test_process_content_pw(backend_pw: PlaywrightBackend, url_info_pw):
    html_text = "<html><title>Test</title><body><a href='next'>Next</a></body></html>"
    cr = CrawlResult(url=url_info_pw.normalized_url, content={"html": html_text}, status=200)
    
    mock_processed_obj = ProcessedContent(
        title="Test", content="Next", links=[{"url": f"{url_info_pw.normalized_url}/next", "text": "Next", "raw_href":"next"}], 
        metadata={}, headings=[], assets={}, structure=[], errors=[]
    )
    backend_pw.content_processor.process = AsyncMock(return_value=mock_processed_obj)
    backend_pw.config.extract_links = True # Ensure link extraction is on

    processed_data = await backend_pw.process(cr)
    
    assert processed_data["title"] == "Test"
    assert "Next" in processed_data["content"]
    assert len(processed_data["links"]) == 1
    assert processed_data["links"][0]["url"] == f"{url_info_pw.normalized_url}/next"


@pytest.mark.asyncio
async def test_screenshot_generation_pw(backend_pw: PlaywrightBackend, url_info_pw, tmp_path):
    backend_pw.config.screenshots = True
    backend_pw.config.screenshot_path = str(tmp_path)

    backend_pw._ensure_browser = AsyncMock()
    backend_pw._context = AsyncMock()
    
    mock_page = AsyncMock()
    mock_response = AsyncMock(status=200, url=url_info_pw.normalized_url, headers={})
    mock_page.goto.return_value = mock_response
    mock_page.content.return_value = "<html>Screenshot Content</html>"
    mock_page.screenshot = AsyncMock() # This is the important part
    mock_page.close = AsyncMock()
    backend_pw._context.new_page.return_value = mock_page

    with patch('os.makedirs') as mock_makedirs: # Mock makedirs as it's called directly
        nav_result = await backend_pw._navigate_with_retry(url_info_pw.normalized_url)

    assert nav_result["success"] is True
    assert nav_result["screenshot"] is not None
    assert nav_result["screenshot"].startswith(str(tmp_path))
    assert nav_result["screenshot"].endswith(".png")
    
    mock_makedirs.assert_called_once_with(str(tmp_path), exist_ok=True)
    mock_page.screenshot.assert_called_once()
    # Example: mock_page.screenshot.assert_called_once_with(path=nav_result["screenshot"], full_page=True)