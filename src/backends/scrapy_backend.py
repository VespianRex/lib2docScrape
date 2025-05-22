import asyncio
import time
import ssl
import certifi
from typing import Any, Dict, Optional, List, TYPE_CHECKING
import logging
import sys

import aiohttp
from pydantic import BaseModel, Field

from .base import register_backend # Changed from .selector to .base
from .base import CrawlerBackend, CrawlResult
from ..utils.url.info import URLInfo
from ..processors.content_processor import ContentProcessor

if TYPE_CHECKING:
    from ..crawler import CrawlerConfig

# Configure logging
logger = logging.getLogger('scrapy_backend')

class ScrapyConfig(BaseModel):
    """Configuration for Scrapy backend."""
    max_retries: int = Field(3, ge=0)  # Must be >= 0
    timeout: float = Field(30.0, gt=0)  # Must be > 0
    headers: Dict[str, str] = {
        "User-Agent": "Scrapy/2.0 Documentation Crawler"
    }
    follow_redirects: bool = True
    verify_ssl: bool = False  # Default to False for testing
    max_depth: int = Field(5, ge=0)  # Must be >= 0
    rate_limit: float = Field(2.0, gt=0)  # Must be > 0
    follow_links: bool = True  # Whether to follow internal links
    max_pages: int = Field(100, ge=0)  # Must be >= 0
    allowed_domains: Optional[List[str]] = None  # Domains to restrict crawling to
    concurrent_requests: int = Field(10, gt=0)  # Must be > 0

    def __str__(self) -> str:
        return (
            f"ScrapyConfig(max_depth={self.max_depth}, max_pages={self.max_pages}, "
            f"follow_links={self.follow_links}, rate_limit={self.rate_limit}, "
            f"verify_ssl={self.verify_ssl}, concurrent_requests={self.concurrent_requests})"
        )

class ScrapyBackend(CrawlerBackend):
    """
    A crawler backend that uses Scrapy to fetch and process web content.
    """
    name = "scrapy"

    def __init__(self, config: Optional[ScrapyConfig] = None) -> None:
        """Initialize the Scrapy backend.
        
        Args:
            config: Optional configuration for the backend
        """
        super().__init__(name=self.name) # Use self.name instead of hardcoded "scrapy"
        self.config = config or ScrapyConfig()
        self._session: Optional[aiohttp.ClientSession] = None
        self._processing_semaphore = asyncio.Semaphore(self.config.concurrent_requests)
        self._rate_limiter = asyncio.Lock()
        self._last_request = 0.0
        self._crawled_urls = set()
        self._progress_callback = None
        self.metrics.update({
            "successful_requests": 0,
            "failed_requests": 0,
            "total_crawl_time": 0.0,
            "cached_pages": 0,
            "total_pages": 0,
            "pages_crawled": 0,
            "start_time": 0.0,
            "end_time": 0.0
        })
        # self.content_processor = ContentProcessor()
        logger.info(f"Initialized Scrapy backend with config: {self.config}")

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _create_session(self) -> aiohttp.ClientSession:
        """Create a new session with proper SSL configuration."""
        ssl_context = None
        if self.config.verify_ssl:
            ssl_context = ssl.create_default_context(cafile=certifi.where())
        else:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        return aiohttp.ClientSession(
            headers=self.config.headers,
            timeout=timeout,
            connector=aiohttp.TCPConnector(ssl=ssl_context)
        )

    async def _ensure_session(self):
        """Ensure aiohttp session exists and is properly configured."""
        if self._session is None:
            self._session = await self._create_session()

    def set_progress_callback(self, callback):
        """Set a callback function to receive progress updates."""
        self._progress_callback = callback

    async def _notify_progress(self, url: str, depth: int, status: str):
        """Notify progress callback if set."""
        if self._progress_callback:
            await self._progress_callback(url, depth, status)

    async def _wait_rate_limit(self):
        """Enforce rate limiting between requests."""
        async with self._rate_limiter:
            now = time.time()
            if self._last_request:
                time_passed = now - self._last_request
                required_interval = 1.0 / self.config.rate_limit
                wait_time = required_interval - time_passed
                if wait_time > 0:
                    logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)
            self._last_request = time.time()

    async def crawl(self, url_info: URLInfo, config: 'CrawlerConfig') -> CrawlResult:
        """Crawl the specified URL using the Scrapy backend."""
        if not isinstance(url_info, URLInfo) or not url_info.is_valid:
            error_msg = f"Invalid URL provided: {getattr(url_info, 'raw_url', 'Unknown')}"
            logger.error(error_msg)
            return CrawlResult(
                url=getattr(url_info, 'raw_url', 'Unknown'),
                content={},
                metadata={},
                status=400,
                error=error_msg
            )

        start_time = time.time()
        if not self.metrics.get("start_time"):
            self.metrics["start_time"] = start_time

        url = url_info.normalized_url
        await self._notify_progress(url, 0, "Started")

        try:
            await self._ensure_session()
            await self._wait_rate_limit()

            async with self._processing_semaphore:
                async with self._session.get(url) as response:
                    content_text = await response.text()
                    result = CrawlResult(
                        url=url,
                        content={"html": content_text},
                        metadata={"headers": dict(response.headers)},
                        status=response.status,
                        error=None
                    )

                    if response.status == 200:
                        self.metrics["successful_requests"] += 1
                        self.metrics["pages_crawled"] += 1
                        await self._notify_progress(url, 0, "Completed")
                    else:
                        self.metrics["failed_requests"] += 1
                        await self._notify_progress(url, 0, f"Failed: {response.status}")

                    return result

        except Exception as e:
            error_msg = f"Error crawling {url}: {str(e)}"
            logger.error(error_msg)
            self.metrics["failed_requests"] += 1
            await self._notify_progress(url, 0, f"Error: {str(e)}")
            return CrawlResult(
                url=url,
                content={},
                metadata={},
                status=0,
                error=error_msg
            )
        finally:
            end_time = time.time()
            self.metrics["end_time"] = end_time
            if self.metrics.get("start_time"):
                 self.metrics["total_crawl_time"] = end_time - self.metrics["start_time"]

    async def process(self, content: CrawlResult) -> Dict[str, Any]:
        """
        Process a single item scraped by the crawler.
        """
        logger.info(f"Processing item from URL: {content.url}")
        # Placeholder: simply return the content dictionary
        # A real implementation would use self.content_processor
        # e.g., return self.content_processor.process(content.content.get("html"), content.url)
        if content.content and "html" in content.content:
            # Potentially parse or transform content.content["html"]
            return {"processed_html": content.content["html"][:500]} # Example processing
        return content.content if content.content else {}

    async def validate(self, content: CrawlResult) -> bool:
        """
        Validate a single item against a set of rules.
        """
        logger.info(f"Validating item from URL: {content.url}")
        if not content.is_success():
            logger.warning(f"Content for {content.url} indicates crawl failure (status: {content.status}, error: {content.error}). Validation fails.")
            return False
        if not content.content or "html" not in content.content or not content.content["html"]:
            logger.warning(f"No HTML content to validate for {content.url}. Validation fails.")
            return False
        # Placeholder: basic validation
        # A real implementation would check for specific elements or patterns
        logger.info(f"Content for {content.url} appears valid (basic check).")
        return True

    async def close(self):
        """Close resources."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    def get_metrics(self) -> Dict[str, Any]:
        """Get current crawler metrics."""
        metrics = self.metrics.copy()
        total_requests = metrics["successful_requests"] + metrics["failed_requests"]
        
        metrics.update({
            "success_rate": (
                metrics["successful_requests"] / total_requests
                if total_requests > 0 else 0.0
            ),
            "average_response_time": (
                metrics["total_crawl_time"] / metrics["pages_crawled"]
                if metrics["pages_crawled"] > 0 else 0.0
            )
        })
        return metrics

# Register the backend upon class definition
try:
    register_backend(ScrapyBackend.name, ScrapyBackend)
except Exception as e:
    logger.error(f"Failed to register ScrapyBackend: {e}")