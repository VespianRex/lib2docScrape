"""
Playwright backend module for handling browser-based crawling.
This backend provides full browser automation capabilities for JavaScript-heavy sites.
"""
import asyncio
import logging
import os
import time
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING

from pydantic import BaseModel, Field
from bs4 import BeautifulSoup

from .base import CrawlerBackend, CrawlResult
from ..utils.url.info import URLInfo
from ..processors.content_processor import ContentProcessor
from ..utils.retry import ExponentialBackoff, RetryWithStrategy
from ..utils.circuit_breaker import CircuitBreaker

# Conditional import to avoid errors if playwright is not installed
try:
    from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

logger = logging.getLogger(__name__)

class PlaywrightConfig(BaseModel):
    """Configuration for the Playwright backend."""
    browser_type: str = "chromium"  # chromium, firefox, or webkit
    headless: bool = True
    timeout: float = 30.0
    max_retries: int = 3
    wait_for_load: bool = True
    wait_until: str = "networkidle"  # domcontentloaded, load, networkidle
    wait_time: float = 2.0
    javascript_enabled: bool = True
    user_agent: str = "Lib2DocScrape/1.0 (Playwright) Documentation Crawler"
    viewport_width: int = 1280
    viewport_height: int = 800
    ignore_https_errors: bool = False
    proxy: Optional[str] = None
    extra_http_headers: Dict[str, str] = Field(default_factory=dict)
    screenshots: bool = False
    screenshot_path: str = "screenshots"
    circuit_breaker_threshold: int = 5
    circuit_breaker_reset_timeout: float = 60.0
    rate_limit: float = 2.0
    concurrent_requests: int = 5
    extract_links: bool = True
    extract_images: bool = True
    extract_metadata: bool = True
    extract_code_blocks: bool = True

class PlaywrightBackend(CrawlerBackend):
    """
    A crawler backend that uses Playwright to fetch and process web content.
    Playwright provides cross-browser automation capabilities.
    """

    def __init__(self, config: Optional[PlaywrightConfig] = None):
        """Initialize the Playwright backend."""
        super().__init__(name="playwright")
        self.config = config or PlaywrightConfig()
        self._playwright = None
        self._browser = None
        self._context = None
        self._processing_semaphore = asyncio.Semaphore(self.config.concurrent_requests)
        self._rate_limiter = asyncio.Lock()
        self._last_request = 0.0
        self._crawled_urls = set()
        self.content_processor = ContentProcessor()

        # Initialize retry strategy
        self.retry_strategy = ExponentialBackoff(
            base_delay=1.0,
            max_delay=30.0,
            jitter=True
        )

        # Initialize circuit breaker
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=self.config.circuit_breaker_threshold,
            reset_timeout=self.config.circuit_breaker_reset_timeout
        )

        # Check if Playwright is available
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("Playwright is not installed. Please install it with 'pip install playwright' and run 'playwright install'")

    async def _ensure_browser(self):
        """Ensure browser is launched and ready."""
        if self._browser is not None:
            return

        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright is not installed. Please install it with 'pip install playwright' and run 'playwright install'")

        try:
            self._playwright = await async_playwright().start()

            # Select browser type
            if self.config.browser_type == "firefox":
                browser_factory = self._playwright.firefox
            elif self.config.browser_type == "webkit":
                browser_factory = self._playwright.webkit
            else:
                browser_factory = self._playwright.chromium

            # Launch browser
            self._browser = await browser_factory.launch(
                headless=self.config.headless,
                proxy={"server": self.config.proxy} if self.config.proxy else None,
                ignore_https_errors=self.config.ignore_https_errors
            )

            # Create browser context
            self._context = await self._browser.new_context(
                viewport={"width": self.config.viewport_width, "height": self.config.viewport_height},
                user_agent=self.config.user_agent,
                extra_http_headers=self.config.extra_http_headers
            )

            logger.info(f"Playwright {self.config.browser_type} browser launched")
        except Exception as e:
            logger.error(f"Failed to launch Playwright browser: {str(e)}")
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
            raise

    async def _wait_rate_limit(self):
        """Enforce rate limiting between requests."""
        async with self._rate_limiter:
            now = time.time()
            if self._last_request > 0:
                elapsed = now - self._last_request
                required_interval = 1.0 / self.config.rate_limit

                if elapsed < required_interval:
                    await asyncio.sleep(required_interval - elapsed)

            self._last_request = time.time()

    async def _navigate_with_retry(self, url: str) -> Dict[str, Any]:
        """Navigate to a URL with retry logic and circuit breaker protection."""
        # Check if circuit breaker is open
        if self.circuit_breaker.is_open():
            logger.warning(f"Circuit breaker open, skipping request to {url}")
            return {
                "success": False,
                "error": "Circuit breaker open",
                "status": 503,  # Service Unavailable
                "content": None,
                "screenshot": None
            }

        await self._ensure_browser()
        await self._wait_rate_limit()

        for attempt in range(self.config.max_retries + 1):
            try:
                async with self._processing_semaphore:
                    # Create a new page
                    page = await self._context.new_page()

                    try:
                        # Navigate to URL
                        response = await page.goto(
                            url,
                            wait_until=self.config.wait_until,
                            timeout=self.config.timeout * 1000  # Convert to ms
                        )

                        # Wait additional time if configured
                        if self.config.wait_for_load and self.config.wait_time > 0:
                            await asyncio.sleep(self.config.wait_time)

                        # Get page content
                        content = await page.content()

                        # Take screenshot if configured
                        screenshot = None
                        if self.config.screenshots:
                            os.makedirs(self.config.screenshot_path, exist_ok=True)
                            screenshot_file = os.path.join(
                                self.config.screenshot_path,
                                f"{hash(url)}_{int(time.time())}.png"
                            )
                            await page.screenshot(path=screenshot_file, full_page=True)
                            screenshot = screenshot_file

                        # Record success in circuit breaker
                        self.circuit_breaker.record_success()

                        return {
                            "success": True,
                            "status": response.status if response else 200,
                            "content": content,
                            "screenshot": screenshot,
                            "url": response.url if response else url,
                            "headers": dict(response.headers) if response else {}
                        }
                    finally:
                        await page.close()
            except PlaywrightTimeoutError as e:
                # Record failure in circuit breaker
                self.circuit_breaker.record_failure()

                logger.warning(f"Attempt {attempt + 1}/{self.config.max_retries + 1} timed out for {url}: {str(e)}")

                if attempt < self.config.max_retries:
                    # Use retry strategy for delay
                    delay = self.retry_strategy.get_delay(attempt)
                    logger.debug(f"Retrying in {delay:.2f} seconds")
                    await asyncio.sleep(delay)
                else:
                    return {
                        "success": False,
                        "error": f"Timeout after {self.config.max_retries} retries: {str(e)}",
                        "status": 408,  # Request Timeout
                        "content": None,
                        "screenshot": None
                    }
            except Exception as e:
                # Record failure in circuit breaker
                self.circuit_breaker.record_failure()

                logger.error(f"Unexpected error navigating to {url}: {str(e)}")

                if attempt < self.config.max_retries:
                    # Use retry strategy for delay
                    delay = self.retry_strategy.get_delay(attempt)
                    logger.debug(f"Retrying in {delay:.2f} seconds")
                    await asyncio.sleep(delay)
                else:
                    return {
                        "success": False,
                        "error": f"Unexpected error: {str(e)}",
                        "status": 500,  # Internal Server Error
                        "content": None,
                        "screenshot": None
                    }

    async def crawl(self, url_info: URLInfo, config=None) -> CrawlResult:
        """
        Crawl the specified URL using Playwright browser.

        Args:
            url_info: URLInfo object representing the URL to crawl
            config: Optional crawler configuration

        Returns:
            CrawlResult containing the crawled content and metadata
        """
        if not url_info.is_valid:
            return CrawlResult(
                url=url_info.raw_url,
                content={},
                metadata={},
                status=400,
                error=f"Invalid URL: {url_info.error_message}"
            )

        url = url_info.normalized_url
        logger.info(f"Crawling {url} with Playwright backend")

        # Check if URL is already crawled
        if url in self._crawled_urls:
            logger.info(f"URL {url} already crawled, skipping")
            return CrawlResult(
                url=url,
                content={},
                metadata={"cached": True},
                status=304,  # Not Modified
                error="URL already crawled"
            )

        # Navigate to URL
        result = await self._navigate_with_retry(url)

        if not result["success"]:
            return CrawlResult(
                url=url,
                content={},
                metadata={
                    "error_details": result.get("error", "Unknown error"),
                    "backend": "playwright"
                },
                status=result.get("status", 500),
                error=result.get("error", "Failed to navigate to URL")
            )

        # Add to crawled URLs
        self._crawled_urls.add(url)

        # Return successful result
        return CrawlResult(
            url=result.get("url", url),
            content={"html": result["content"]},
            metadata={
                "headers": result.get("headers", {}),
                "screenshot": result.get("screenshot"),
                "backend": "playwright",
                "browser_type": self.config.browser_type,
                "javascript_enabled": self.config.javascript_enabled
            },
            status=result.get("status", 200),
            content_type="text/html"
        )

    async def validate(self, content: CrawlResult) -> bool:
        """
        Validate the crawled content.

        Args:
            content: The crawled content to validate

        Returns:
            bool indicating if the content is valid
        """
        if not content or not content.content.get("html"):
            return False

        html = content.content.get("html", "")

        # Check if content is too short (likely an error page)
        if len(html) < 100:
            logger.warning(f"Content for {content.url} is too short ({len(html)} bytes)")
            return False

        # Check if content contains common error indicators
        error_indicators = [
            "404 Not Found",
            "403 Forbidden",
            "500 Internal Server Error",
            "Service Unavailable",
            "Page Not Found",
            "Access Denied"
        ]

        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.text if soup.title else ""

        for indicator in error_indicators:
            if indicator in title:
                logger.warning(f"Error indicator '{indicator}' found in title for {content.url}")
                return False

        return True

    async def process(self, content: CrawlResult) -> Dict[str, Any]:
        """
        Process the crawled content.

        Args:
            content: The crawled content to process

        Returns:
            Processed content as a dictionary
        """
        html_text = content.content.get("html")
        if not html_text:
            logger.warning(f"No HTML content found for URL: {content.url}")
            return {"error": "No HTML content found"}

        try:
            # Process content using ContentProcessor
            processed_content = await self.content_processor.process(
                content=html_text,
                base_url=content.url,
                content_type="text/html"
            )

            # Extract links if configured
            links = []
            if self.config.extract_links:
                soup = BeautifulSoup(html_text, "html.parser")
                for a_tag in soup.find_all("a", href=True):
                    href = a_tag.get("href")
                    if href:
                        from urllib.parse import urljoin
                        absolute_url = urljoin(content.url, href)
                        links.append({
                            "url": absolute_url,
                            "text": a_tag.get_text(strip=True),
                            "title": a_tag.get("title", "")
                        })

            return {
                "title": processed_content.title,
                "content": processed_content.content,
                "links": links,
                "metadata": {**processed_content.metadata, **content.metadata},
                "headings": processed_content.headings,
                "assets": processed_content.assets,
                "structure": processed_content.structure
            }
        except Exception as e:
            logger.error(f"Error processing content for {content.url}: {str(e)}")
            return {"error": f"Processing error: {str(e)}"}

    async def close(self) -> None:
        """Clean up resources."""
        if self._browser:
            try:
                await self._browser.close()
                self._browser = None
            except Exception as e:
                logger.error(f"Error closing browser: {str(e)}")

        if self._playwright:
            try:
                await self._playwright.stop()
                self._playwright = None
            except Exception as e:
                logger.error(f"Error stopping playwright: {str(e)}")

        # Reset state
        self._context = None
        self._crawled_urls.clear()
        self._last_request = 0.0
