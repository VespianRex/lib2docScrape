"""
Lightpanda backend module for using the Lightpanda headless browser.
This backend is optimized for JavaScript-heavy documentation sites.
"""
import asyncio
import json
import logging
import os
import subprocess
import tempfile
import time
from typing import Any, Dict, List, Optional, Union, Set
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

from ..utils.url import URLInfo
from .base import CrawlerBackend, CrawlResult
from ..processors.content_processor import ContentProcessor
from ..utils.retry import ExponentialBackoff, RetryWithStrategy
from ..utils.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)

class LightpandaConfig(BaseModel):
    """Configuration for the Lightpanda backend."""
    executable_path: str = "lightpanda"
    host: str = "127.0.0.1"
    port: int = 9222
    timeout: float = 30.0
    max_retries: int = 3
    wait_for_load: bool = True
    wait_time: float = 2.0
    javascript_enabled: bool = True
    user_agent: str = "Lib2DocScrape/1.0 (Lightpanda) Documentation Crawler"
    headers: Dict[str, str] = Field(default_factory=dict)
    viewport_width: int = 1280
    viewport_height: int = 800
    extra_args: List[str] = Field(default_factory=list)
    circuit_breaker_threshold: int = 5
    circuit_breaker_reset_timeout: float = 60.0
    rate_limit: float = 2.0
    concurrent_requests: int = 5
    extract_links: bool = True
    extract_images: bool = True
    extract_metadata: bool = True
    extract_code_blocks: bool = True
    screenshots: bool = False
    screenshot_path: str = "screenshots"

class LightpandaBackend(CrawlerBackend):
    """
    A crawler backend that uses Lightpanda for JavaScript-rendered content.
    Lightpanda is an AI-native web browser with minimal memory footprint.
    """

    def __init__(self, config: Optional[LightpandaConfig] = None):
        """Initialize the Lightpanda backend."""
        super().__init__(name="lightpanda")
        self.config = config or LightpandaConfig()
        self._process = None
        self._ws_endpoint = None
        self._session = None
        self._ws = None
        self._browser_context_id = None
        self._processing_semaphore = asyncio.Semaphore(self.config.concurrent_requests)
        self._rate_limiter = asyncio.Lock()
        self._last_request = 0.0
        self._crawled_urls: Set[str] = set()
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

    async def _start_browser(self) -> str:
        """Start the Lightpanda browser process and return the WebSocket endpoint."""
        if self._process is not None:
            return self._ws_endpoint

        # Check if executable exists
        if not os.path.exists(self.config.executable_path) and not self._is_in_path(self.config.executable_path):
            raise RuntimeError(f"Lightpanda executable not found at {self.config.executable_path}")

        # Start Lightpanda process
        cmd = [
            self.config.executable_path,
            "serve",
            "--host", self.config.host,
            "--port", str(self.config.port)
        ]
        cmd.extend(self.config.extra_args)

        logger.info(f"Starting Lightpanda browser: {' '.join(cmd)}")

        # Start process with stdout/stderr redirection
        self._process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Wait for browser to start
        for _ in range(10):  # Try 10 times with 0.5s delay
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"http://{self.config.host}:{self.config.port}/json/version") as response:
                        if response.status == 200:
                            data = await response.json()
                            self._ws_endpoint = data.get("webSocketDebuggerUrl")
                            if self._ws_endpoint:
                                logger.info(f"Lightpanda started with WebSocket endpoint: {self._ws_endpoint}")
                                return self._ws_endpoint
            except aiohttp.ClientError:
                pass

            await asyncio.sleep(0.5)

        # If we get here, browser didn't start properly
        self._cleanup_process()
        raise RuntimeError("Failed to start Lightpanda browser")

    def _is_in_path(self, executable: str) -> bool:
        """Check if the executable is in the system PATH."""
        return any(
            os.path.exists(os.path.join(path, executable))
            for path in os.environ.get("PATH", "").split(os.pathsep)
        )

    def _cleanup_process(self):
        """Clean up the browser process."""
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None

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

    async def _connect_browser(self):
        """Connect to the browser via WebSocket."""
        if self._session is not None:
            return

        ws_endpoint = await self._start_browser()
        self._session = aiohttp.ClientSession()
        self._ws = await self._session.ws_connect(ws_endpoint)

        # Create a browser context
        context_response = await self._send_command("Target.createBrowserContext")
        self._browser_context_id = context_response.get("browserContextId")

    async def _send_command(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a command to the browser and wait for the response."""
        if self._ws is None:
            raise RuntimeError("WebSocket connection not established")

        command_id = id(method) + id(params or {})
        message = {
            "id": command_id,
            "method": method,
            "params": params or {}
        }

        await self._ws.send_json(message)

        # Wait for response with matching id
        async for msg in self._ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)
                if data.get("id") == command_id:
                    if "error" in data:
                        logger.error(f"Error executing command {method}: {data['error']}")
                        raise RuntimeError(f"Command error: {data['error']}")
                    return data.get("result", {})

        raise RuntimeError(f"No response received for command {method}")

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

        await self._connect_browser()
        await self._wait_rate_limit()

        for attempt in range(self.config.max_retries + 1):
            try:
                async with self._processing_semaphore:
                    # Create a new page
                    create_target_response = await self._send_command(
                        "Target.createTarget",
                        {
                            "url": "about:blank",
                            "browserContextId": self._browser_context_id
                        }
                    )
                    target_id = create_target_response.get("targetId")

                    try:
                        # Attach to the page
                        session_response = await self._send_command(
                            "Target.attachToTarget",
                            {
                                "targetId": target_id,
                                "flatten": True
                            }
                        )

                        # Set viewport size
                        await self._send_command(
                            "Emulation.setDeviceMetricsOverride",
                            {
                                "width": self.config.viewport_width,
                                "height": self.config.viewport_height,
                                "deviceScaleFactor": 1,
                                "mobile": False
                            }
                        )

                        # Set user agent
                        await self._send_command(
                            "Network.setUserAgentOverride",
                            {
                                "userAgent": self.config.user_agent
                            }
                        )

                        # Navigate to URL
                        navigate_response = await self._send_command(
                            "Page.navigate",
                            {
                                "url": url
                            }
                        )

                        # Wait for page to load
                        if self.config.wait_for_load:
                            await asyncio.sleep(self.config.wait_time)

                        # Get page content
                        content_response = await self._send_command(
                            "Runtime.evaluate",
                            {
                                "expression": "document.documentElement.outerHTML",
                                "returnByValue": True
                            }
                        )

                        html_content = content_response.get("result", {}).get("value", "")

                        # Take screenshot if configured
                        screenshot = None
                        if self.config.screenshots:
                            os.makedirs(self.config.screenshot_path, exist_ok=True)
                            screenshot_response = await self._send_command(
                                "Page.captureScreenshot",
                                {
                                    "format": "png",
                                    "quality": 80,
                                    "fromSurface": True
                                }
                            )

                            if "data" in screenshot_response:
                                import base64
                                screenshot_file = os.path.join(
                                    self.config.screenshot_path,
                                    f"{hash(url)}_{int(time.time())}.png"
                                )
                                with open(screenshot_file, "wb") as f:
                                    f.write(base64.b64decode(screenshot_response["data"]))
                                screenshot = screenshot_file

                        # Record success in circuit breaker
                        self.circuit_breaker.record_success()

                        return {
                            "success": True,
                            "status": 200,
                            "content": html_content,
                            "screenshot": screenshot,
                            "target_id": target_id
                        }
                    finally:
                        # Always close the page to avoid leaking resources
                        try:
                            await self._send_command(
                                "Target.closeTarget",
                                {
                                    "targetId": target_id
                                }
                            )
                        except Exception as close_error:
                            logger.warning(f"Error closing target: {str(close_error)}")
            except Exception as e:
                # Record failure in circuit breaker
                self.circuit_breaker.record_failure()

                logger.warning(f"Attempt {attempt + 1}/{self.config.max_retries + 1} failed for {url}: {str(e)}")

                if attempt < self.config.max_retries:
                    # Use retry strategy for delay
                    delay = self.retry_strategy.get_delay(attempt)
                    logger.debug(f"Retrying in {delay:.2f} seconds")
                    await asyncio.sleep(delay)
                else:
                    return {
                        "success": False,
                        "error": f"Failed after {self.config.max_retries} retries: {str(e)}",
                        "status": 500,
                        "content": None,
                        "screenshot": None
                    }

    async def crawl(self, url_info: URLInfo, config=None) -> CrawlResult:
        """
        Crawl the specified URL using Lightpanda browser.

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
        logger.info(f"Crawling {url} with Lightpanda backend")

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

        # Navigate to URL with retry logic
        result = await self._navigate_with_retry(url)

        if not result["success"]:
            return CrawlResult(
                url=url,
                content={},
                metadata={
                    "error_details": result.get("error", "Unknown error"),
                    "backend": "lightpanda"
                },
                status=result.get("status", 500),
                error=result.get("error", "Failed to navigate to URL")
            )

        # Add to crawled URLs
        self._crawled_urls.add(url)

        # Return successful result
        return CrawlResult(
            url=url,
            content={"html": result["content"]},
            metadata={
                "screenshot": result.get("screenshot"),
                "backend": "lightpanda",
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
        logger.info("Closing Lightpanda backend resources")

        # Close WebSocket connection
        if hasattr(self, '_ws') and self._ws:
            try:
                await self._ws.close()
            except Exception as e:
                logger.error(f"Error closing WebSocket connection: {str(e)}")
            self._ws = None

        # Close HTTP session
        if self._session:
            try:
                await self._session.close()
            except Exception as e:
                logger.error(f"Error closing HTTP session: {str(e)}")
            self._session = None

        # Clean up browser process
        self._cleanup_process()

        # Reset state
        self._browser_context_id = None
        self._crawled_urls.clear()
        self._last_request = 0.0

        logger.info("Lightpanda backend resources closed")
