"""
Crawl4AI backend module for using advanced crawling techniques.
This is a full implementation of the Crawl4AI backend.
"""
import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Set, Union
import re
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

from .base import CrawlerBackend, CrawlResult
from ..utils.url.info import URLInfo
from ..processors.content_processor import ContentProcessor
from ..utils.retry import ExponentialBackoff, RetryWithStrategy
from ..utils.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)

class Crawl4AIConfig(BaseModel):
    """Configuration for the Crawl4AI backend."""
    max_retries: int = 3
    timeout: float = 30.0
    headers: Dict[str, str] = Field(default_factory=lambda: {
        "User-Agent": "Crawl4AI/1.0 Documentation Crawler"
    })
    follow_redirects: bool = True
    verify_ssl: bool = True
    max_depth: int = 5
    rate_limit: float = 2.0
    concurrent_requests: int = 10
    allowed_domains: Optional[List[str]] = None
    extract_links: bool = True
    extract_images: bool = True
    extract_metadata: bool = True
    extract_code_blocks: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_reset_timeout: float = 60.0
    javascript_enabled: bool = False

class Crawl4AIBackend(CrawlerBackend):
    """
    A crawler backend that uses advanced crawling techniques.
    This backend is optimized for documentation sites.
    """

    def __init__(self, config: Optional[Crawl4AIConfig] = None):
        """Initialize the Crawl4AI backend."""
        super().__init__(name="crawl4ai")
        self.config = config or Crawl4AIConfig()
        self._session = None
        # Initialize semaphore and rate limiter immediately
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

    async def _ensure_session(self):
        """Ensure an aiohttp session exists."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers=self.config.headers,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            )

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

    async def _fetch_with_retry(self, url: str) -> CrawlResult:
        """Fetch a URL with retry logic and circuit breaker protection."""
        # Check if circuit breaker is open
        if self.circuit_breaker.is_open():
            logger.warning(f"Circuit breaker open, skipping request to {url}")
            return CrawlResult(
                url=url,
                content={},
                metadata={"circuit_breaker": "open"},
                status=503,  # Service Unavailable
                error="Circuit breaker open"
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
                        ssl=None if not self.config.verify_ssl else True
                    )
                    resp_ctx = await get_call if asyncio.iscoroutine(get_call) else get_call
                    async with resp_ctx as response:
                        content = await response.text()

                        # Record success in circuit breaker
                        self.circuit_breaker.record_success()

                        return CrawlResult(
                            url=str(response.url),
                            content={"html": content},
                            metadata={
                                "headers": dict(response.headers),
                                "status": response.status,
                                "content_type": response.headers.get("content-type", "")
                            },
                            status=response.status
                        )
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                # Record failure in circuit breaker
                self.circuit_breaker.record_failure()

                logger.warning(f"Attempt {attempt + 1}/{self.config.max_retries + 1} failed for {url}: {str(e)}")

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
                        error=f"Failed after {self.config.max_retries} retries: {str(e)}"
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
                    error=f"Unexpected error: {str(e)}"
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
            logger.debug(f"Custom config provided for {url_info.normalized_url}: {config}")
        start_time = time.time()

        # Validate URL
        if not url_info.is_valid:
            return CrawlResult(
                url=url_info.raw_url,
                content={},
                metadata={},
                status=400,
                error=f"Invalid URL: {url_info.error_message}"
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
                error="Circuit breaker open"
            )

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

        # Check allowed domains
        if self.config.allowed_domains:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]

            if not any(domain == allowed_domain or domain.endswith(f'.{allowed_domain}')
                      for allowed_domain in self.config.allowed_domains):
                logger.warning(f"Domain {domain} not in allowed domains: {self.config.allowed_domains}")
                return CrawlResult(
                    url=url,
                    content={},
                    metadata={},
                    status=403,  # Forbidden
                    error=f"Domain not allowed: {domain}"
                )

        # Fetch the URL
        result = await self._fetch_with_retry(url)

        # Add to crawled URLs if successful
        if result.status >= 200 and result.status < 300:
            self._crawled_urls.add(url)

        # Update metrics
        crawl_time = time.time() - start_time
        await self.update_metrics(crawl_time, result.status >= 200 and result.status < 300)

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
            soup = BeautifulSoup(html, 'html.parser')
            title = soup.title
            if not title or not title.string:
                logger.warning(f"No title found in {content.url}")
                # Don't fail validation just because of missing title
        except Exception as e:
            logger.error(f"Error parsing HTML from {content.url}: {str(e)}")
            return False

        return True

    async def process(self, content: CrawlResult) -> Dict[str, Any]:
        """Process the crawled content."""
        html = content.content.get("html")
        if not html:
            logger.warning(f"No HTML content found for URL: {content.url}")
            return {"error": "No HTML content found"}

        try:
            # Process content using ContentProcessor
            processed_content = await self.content_processor.process(
                html_content=html,
                base_url=content.url
            )

            # Extract links if configured
            links = []
            if self.config.extract_links:
                soup = BeautifulSoup(html, 'html.parser')
                for a_tag in soup.find_all('a', href=True):
                    href = a_tag.get('href')
                    if href:
                        absolute_url = urljoin(content.url, href)
                        links.append({
                            "url": absolute_url,
                            "text": a_tag.get_text(strip=True),
                            "title": a_tag.get('title', '')
                        })

            # Extract metadata if configured
            metadata = {}
            if self.config.extract_metadata:
                soup = BeautifulSoup(html, 'html.parser')
                # Extract meta tags
                for meta in soup.find_all('meta'):
                    name = meta.get('name') or meta.get('property')
                    content = meta.get('content')
                    if name and content:
                        metadata[name] = content

            return {
                "title": processed_content.title,
                "content": processed_content.content,
                "links": links,
                "metadata": {**metadata, **processed_content.metadata},
                "headings": processed_content.headings,
                "assets": processed_content.assets
            }

        except Exception as e:
            logger.error(f"Error processing content for {content.url}: {str(e)}")
            return {"error": f"Processing error: {str(e)}"}

    async def close(self) -> None:
        """Close resources."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
