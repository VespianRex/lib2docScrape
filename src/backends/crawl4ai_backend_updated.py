"""
Crawl4AI backend module for using advanced crawling techniques.
This is a full implementation of the Crawl4AI backend.
"""

import asyncio
import logging
import time
from typing import Any, Optional
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, field_validator

from ..processors.content_processor import ContentProcessor
from ..utils.circuit_breaker import CircuitBreaker
from ..utils.retry import ExponentialBackoff
from ..utils.url.info import URLInfo
from .base import CrawlerBackend, CrawlResult

logger = logging.getLogger(__name__)


class Crawl4AIConfig(BaseModel):
    """Configuration for the Crawl4AI backend."""

    max_retries: int = 3
    timeout: float = 30.0
    headers: dict[str, str] = Field(
        default_factory=lambda: {"User-Agent": "Crawl4AI/1.0 Documentation Crawler"}
    )
    follow_redirects: bool = True
    verify_ssl: bool = True
    max_depth: int = 5
    max_pages: int = 1000
    rate_limit: float = 2.0
    concurrent_requests: int = 10
    allowed_domains: Optional[list[str]] = None
    follow_links: bool = True
    extract_links: bool = True
    extract_images: bool = True
    extract_metadata: bool = True
    extract_code_blocks: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_reset_timeout: float = 60.0
    javascript_enabled: bool = False

    @field_validator("max_retries")
    @classmethod
    def validate_max_retries(cls, v):
        if v < 0:
            raise ValueError("max_retries must be non-negative")
        return v

    @field_validator("timeout")
    @classmethod
    def validate_timeout(cls, v):
        if v <= 0:
            raise ValueError("timeout must be positive")
        return v

    @field_validator("max_depth")
    @classmethod
    def validate_max_depth(cls, v):
        if v < 0:
            raise ValueError("max_depth must be non-negative")
        return v

    @field_validator("max_pages")
    @classmethod
    def validate_max_pages(cls, v):
        if v < 0:
            raise ValueError("max_pages must be non-negative")
        return v

    @field_validator("rate_limit")
    @classmethod
    def validate_rate_limit(cls, v):
        if v <= 0:
            raise ValueError("rate_limit must be positive")
        return v

    @field_validator("concurrent_requests")
    @classmethod
    def validate_concurrent_requests(cls, v):
        if v <= 0:
            raise ValueError("concurrent_requests must be positive")
        return v


class Crawl4AIBackend(CrawlerBackend):
    """
    A crawler backend that uses advanced crawling techniques.
    This backend is optimized for documentation sites.
    """

    def __init__(self, config: Optional[Crawl4AIConfig] = None, rate_limiter=None):
        """Initialize the Crawl4AI backend."""
        super().__init__(name="crawl4ai")
        self.config = config or Crawl4AIConfig()
        self._session = None
        # Initialize semaphore and rate limiter immediately
        self._processing_semaphore = asyncio.Semaphore(self.config.concurrent_requests)
        self._external_rate_limiter = rate_limiter
        self._rate_limiter = asyncio.Lock()
        self._last_request = 0.0
        self._crawled_urls = set()
        self.content_processor = ContentProcessor()

        # Initialize retry strategy
        self.retry_strategy = ExponentialBackoff(
            base_delay=1.0, max_delay=30.0, jitter=True
        )

        # Initialize circuit breaker
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=self.config.circuit_breaker_threshold,
            reset_timeout=self.config.circuit_breaker_reset_timeout,
        )

        # Initialize additional metrics specific to Crawl4AI backend
        self.metrics.update(
            {
                "successful_requests": 0,
                "failed_requests": 0,
                "start_time": 0.0,
                "end_time": 0.0,
                "min_response_time": float("inf"),
                "max_response_time": 0.0,
            }
        )

    async def _ensure_session(self):
        """Ensure an aiohttp session exists."""
        if self._session is None:
            self._session = aiohttp.ClientSession(
                headers=self.config.headers,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            )

    async def _wait_rate_limit(self):
        """Enforce rate limiting between requests.
        Uses the external rate limiter if provided, otherwise uses internal simple rate limiting.
        """
        if self._external_rate_limiter:
            # Use the external rate limiter
            logger.debug(f"Using external rate limiter: {self._external_rate_limiter}")
            wait_time = await self._external_rate_limiter.acquire()
            if wait_time > 0:
                logger.debug(
                    f"External rate limiter requested wait: {wait_time:.4f}s. Sleeping..."
                )
                await asyncio.sleep(wait_time)
            else:
                logger.debug("External rate limiter acquired token immediately.")
        else:
            # Fallback to internal rate limiting logic
            logger.debug(
                f"Using internal rate limiter (rate: {self.config.rate_limit} req/s)."
            )
            async with self._rate_limiter:
                now = time.time()
                if self._last_request > 0:
                    elapsed = now - self._last_request
                    required_interval = 1.0 / self.config.rate_limit

                    if elapsed < required_interval:
                        await asyncio.sleep(required_interval - elapsed)

                self._last_request = time.time()

    async def _fetch_with_retry(self, url: str, config=None) -> CrawlResult:
        """Fetch a URL with retry logic and circuit breaker protection."""
        # Check if circuit breaker is open
        if self.circuit_breaker.is_open():
            logger.warning(f"Circuit breaker open, skipping request to {url}")
            return CrawlResult(
                url=url,
                content={},
                metadata={"circuit_breaker": "open"},
                status=503,  # Service Unavailable
                error="Circuit breaker open",
            )

        await self._ensure_session()
        await self._wait_rate_limit()

        for attempt in range(self.config.max_retries + 1):
            try:
                async with self._processing_semaphore:
                    # Handle case where session.get may be an async function returning a context manager
                    get_call = self._session.get(
                        url,
                        allow_redirects=self.config.follow_redirects,
                        ssl=None if not self.config.verify_ssl else True,
                    )
                    resp_ctx = (
                        await get_call if asyncio.iscoroutine(get_call) else get_call
                    )
                    async with resp_ctx as response:
                        content = await response.text()

                        # Record success in circuit breaker
                        self.circuit_breaker.record_success()

                        return CrawlResult(
                            url=str(response.url),
                            content={"html": content},
                            metadata={
                                "headers": dict(response.headers)
                                if hasattr(response.headers, "items")
                                else {},
                                "status": response.status,
                                "content_type": response.headers.get("content-type", "")
                                if hasattr(response.headers, "get")
                                else "",
                            },
                            status=response.status,
                        )
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                # Record failure in circuit breaker
                self.circuit_breaker.record_failure()

                logger.warning(
                    f"Attempt {attempt + 1}/{self.config.max_retries + 1} failed for {url}: {str(e)}"
                )

                if attempt < self.config.max_retries:
                    # Use retry strategy for delay
                    delay = self.retry_strategy.get_delay(attempt)
                    logger.debug(f"Retrying in {delay:.2f} seconds")
                    await asyncio.sleep(delay)
                else:
                    return CrawlResult(
                        url=url,
                        content={},
                        metadata={"circuit_breaker": "failure_recorded"},
                        status=0,
                        error=f"Failed after {self.config.max_retries} retries: {str(e)}",
                    )
            except Exception as e:
                # Record failure in circuit breaker
                self.circuit_breaker.record_failure()

                logger.error(f"Unexpected error fetching {url}: {str(e)}")
                return CrawlResult(
                    url=url,
                    content={},
                    metadata={"circuit_breaker": "failure_recorded"},
                    status=500,
                    error=f"Unexpected error: {str(e)}",
                )

    async def crawl(self, url_info: URLInfo, config=None) -> CrawlResult:
        """
        Crawl the specified URL using the Crawl4AI backend.

        Args:
            url_info: URLInfo object representing the URL to crawl
            config: Optional crawler configuration (merged with self.config if provided)

        Returns:
            CrawlResult containing the crawled content and metadata
        """
        # Merge configuration if provided
        if config:
            # In a real implementation, we would merge the configs
            # For now, we'll just log that a custom config was provided
            logger.debug(
                f"Custom config provided for {url_info.normalized_url}: {config}"
            )
        start_time = time.time()

        # Initialize timing metrics if not set
        if self.metrics.get("start_time", 0.0) == 0.0:
            self.metrics["start_time"] = start_time

        # Validate URL
        if not url_info.is_valid:
            return CrawlResult(
                url=url_info.raw_url,
                content={},
                metadata={},
                status=400,
                error=f"Invalid URL: {url_info.error_message}",
            )

        url = url_info.normalized_url
        logger.info(f"Crawling {url} with Crawl4AI backend")

        # Check if circuit breaker is open BEFORE any fetch logic
        if self.circuit_breaker.is_open():
            logger.warning(f"Circuit breaker open, skipping request to {url}")
            return CrawlResult(
                url=url,
                content={},
                metadata={"circuit_breaker": "open"},
                status=503,  # Service Unavailable
                error="Circuit breaker open",
            )

        # Check if URL is already crawled
        if url in self._crawled_urls:
            logger.info(f"URL {url} already crawled, skipping")
            return CrawlResult(
                url=url,
                content={},
                metadata={"cached": True},
                status=304,  # Not Modified
                error="URL already crawled",
            )

        # Check allowed domains
        if self.config.allowed_domains:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]

            if not any(
                domain == allowed_domain or domain.endswith(f".{allowed_domain}")
                for allowed_domain in self.config.allowed_domains
            ):
                logger.warning(
                    f"Domain {domain} not in allowed domains: {self.config.allowed_domains}"
                )
                return CrawlResult(
                    url=url,
                    content={},
                    metadata={},
                    status=403,  # Forbidden
                    error=f"Domain not allowed: {domain}",
                )

        # Check max pages limit before fetching
        if len(self._crawled_urls) >= self.config.max_pages:
            logger.warning(
                f"Max pages limit reached ({self.config.max_pages}), skipping {url}"
            )
            return CrawlResult(
                url=url,
                content={},
                metadata={},
                status=429,  # Too Many Requests
                error=f"Max pages limit reached: {self.config.max_pages}",
            )

        # Fetch the URL
        result = await self._fetch_with_retry(url, config)

        # Update metrics for failed requests
        if result.error or result.status >= 400:
            self.metrics["failed_requests"] += 1
            crawl_time = time.time() - start_time
            await self.update_metrics(crawl_time, False)
            return result

        # Add to crawled URLs if successful
        if result.status >= 200 and result.status < 300:
            self._crawled_urls.add(url)

            # Validate content
            if not await self.validate(result):
                logger.warning(f"Content validation failed for {url}")
                self.metrics["failed_requests"] += 1
                crawl_time = time.time() - start_time
                await self.update_metrics(crawl_time, False)
                return CrawlResult(
                    url=url,
                    content={},
                    metadata={},
                    status=422,  # Unprocessable Entity
                    error="Content validation failed",
                )

            # Process content
            processed_data = await self.process(result)
            if "error" in processed_data:
                logger.warning(
                    f"Content processing failed for {url}: {processed_data['error']}"
                )
                self.metrics["failed_requests"] += 1
                crawl_time = time.time() - start_time
                await self.update_metrics(crawl_time, False)
                return CrawlResult(
                    url=url,
                    content=processed_data,
                    metadata=result.metadata,
                    status=500,  # Internal Server Error
                    error=processed_data["error"],
                )

            # Success case
            self.metrics["successful_requests"] += 1
            crawl_time = time.time() - start_time
            await self.update_metrics(crawl_time, True)

            return CrawlResult(
                url=url,
                content=processed_data,
                metadata=result.metadata,
                status=result.status,
            )

        # Other status codes
        self.metrics["failed_requests"] += 1
        crawl_time = time.time() - start_time
        await self.update_metrics(crawl_time, False)
        return result

    async def validate(self, content: CrawlResult) -> bool:
        """Validate the crawled content."""
        if not content or not content.content.get("html"):
            return False

        # Check if content is valid HTML
        html = content.content.get("html", "")
        if not html.strip():
            return False

        # Check if content has a title
        try:
            soup = BeautifulSoup(html, "html.parser")
            title = soup.title
            if not title or not title.string:
                logger.warning(f"No title found in {content.url}")
                # Don't fail validation just because of missing title
        except Exception as e:
            logger.error(f"Error parsing HTML from {content.url}: {str(e)}")
            return False

        return True

    async def process(self, content: CrawlResult) -> dict[str, Any]:
        """Process the crawled content."""
        html = content.content.get("html")
        if not html:
            logger.warning(f"No HTML content found for URL: {content.url}")
            return {"error": "No HTML content found"}

        try:
            # Process content using ContentProcessor
            processed_content = await self.content_processor.process(
                content=html, base_url=content.url
            )

            # Extract links if configured
            links = []
            if self.config.extract_links:
                soup = BeautifulSoup(html, "html.parser")
                for a_tag in soup.find_all("a", href=True):
                    href = a_tag.get("href")
                    if href:
                        absolute_url = urljoin(content.url, href)
                        links.append(
                            {
                                "url": absolute_url,
                                "text": a_tag.get_text(strip=True),
                                "title": a_tag.get("title", ""),
                            }
                        )

            # Extract metadata if configured
            metadata = {}
            if self.config.extract_metadata:
                soup = BeautifulSoup(html, "html.parser")
                # Extract meta tags
                for meta in soup.find_all("meta"):
                    name = meta.get("name") or meta.get("property")
                    content = meta.get("content")
                    if name and content:
                        metadata[name] = content

            return {
                "title": processed_content.title,
                "content": processed_content.content,
                "links": links,
                "metadata": {**metadata, **processed_content.metadata},
                "headings": processed_content.headings,
                "assets": processed_content.assets,
            }

        except Exception as e:
            logger.error(f"Error processing content for {content.url}: {str(e)}")
            return {"error": f"Processing error: {str(e)}"}

    async def update_metrics(self, crawl_time: float, success: bool) -> None:
        """Update the crawler metrics with additional timing information."""
        # Update end time
        self.metrics["end_time"] = time.time()

        # Update min/max response times
        if crawl_time < self.metrics["min_response_time"]:
            self.metrics["min_response_time"] = crawl_time
        if crawl_time > self.metrics["max_response_time"]:
            self.metrics["max_response_time"] = crawl_time

        # Call parent update_metrics
        await super().update_metrics(crawl_time, success)

    async def _create_session(self):
        """Create a new aiohttp session."""
        return aiohttp.ClientSession(
            headers=self.config.headers,
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
        )

    def _is_same_domain(self, url1: str, url2: str) -> bool:
        """
        Check if two URLs are from the same domain.

        Args:
            url1: First URL to compare
            url2: Second URL to compare

        Returns:
            bool: True if URLs are from the same domain, False otherwise
        """
        try:
            parsed1 = urlparse(url1)
            parsed2 = urlparse(url2)

            domain1 = parsed1.netloc.lower()
            domain2 = parsed2.netloc.lower()

            # Remove www. prefix for comparison
            if domain1.startswith("www."):
                domain1 = domain1[4:]
            if domain2.startswith("www."):
                domain2 = domain2[4:]

            # Remove port numbers for comparison (same domain with different ports)
            if ":" in domain1:
                domain1 = domain1.split(":")[0]
            if ":" in domain2:
                domain2 = domain2.split(":")[0]

            return domain1 == domain2

        except Exception:
            return False

    def _is_in_subfolder(self, base_url: str, link_url: str) -> bool:
        """
        Check if a link URL is in a subfolder of the base URL.

        Args:
            base_url: The base URL to check against
            link_url: The link URL to check

        Returns:
            bool: True if link is in subfolder of base, False otherwise
        """
        try:
            # First check if they're the same domain
            if not self._is_same_domain(base_url, link_url):
                return False

            base_parsed = urlparse(base_url)
            link_parsed = urlparse(link_url)

            base_path = base_parsed.path.rstrip("/")
            link_path = link_parsed.path.rstrip("/")

            # If base_path is empty, everything is in subfolder
            if not base_path:
                return True

            # Check if link path starts with base path
            return link_path.startswith(base_path + "/") or link_path == base_path

        except Exception:
            return False

    def _should_follow_link(self, current_url: str, link_url: str) -> bool:
        """
        Determine if a link should be followed based on configuration.

        Args:
            current_url: The current URL being processed
            link_url: The link URL found on the current page

        Returns:
            bool: True if link should be followed, False otherwise
        """
        # Check if link following is enabled
        if not self.config.follow_links:
            return False

        # Check if max pages limit reached
        if len(self._crawled_urls) >= self.config.max_pages:
            return False

        # Resolve relative links
        try:
            absolute_link = urljoin(current_url, link_url)
        except Exception:
            return False

        # Check if already crawled
        if absolute_link in self._crawled_urls:
            return False

        # Set initial domain if not set
        if not hasattr(self, "_initial_domain") or self._initial_domain is None:
            parsed = urlparse(current_url)
            self._initial_domain = parsed.netloc.lower()
            if self._initial_domain.startswith("www."):
                self._initial_domain = self._initial_domain[4:]

        # Check if same domain
        if not self._is_same_domain(current_url, absolute_link):
            return False

        # Validate the link URL
        try:
            parsed_link = urlparse(absolute_link)
            if not parsed_link.scheme or not parsed_link.netloc:
                return False
        except Exception:
            return False

        return True

    def set_progress_callback(self, callback):
        """Set a progress callback function."""
        self._progress_callback = callback

    async def _notify_progress(self, url: str, current: int, status: str):
        """Notify progress if callback is set."""
        if hasattr(self, "_progress_callback") and self._progress_callback:
            await self._progress_callback(url, current, status)

    async def close(self) -> None:
        """Close resources."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
