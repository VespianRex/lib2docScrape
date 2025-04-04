import asyncio
import time
import ssl
import certifi
from typing import Any, Dict, Optional, List, Set, Union
import logging
from dataclasses import asdict # Import asdict
from pydantic import Field
from urllib.parse import urljoin, urlparse, urlunparse
import sys
from datetime import datetime

import aiohttp
from bs4 import BeautifulSoup
from pydantic import BaseModel

from .base import CrawlerBackend, CrawlResult
from ..utils.helpers import URLInfo
from ..processors.content_processor import ContentProcessor # Import ContentProcessor
from ..processors.content.models import ProcessedContent # Import ProcessedContent

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('crawler.log')
    ]
)
logger = logging.getLogger('crawl4ai')

class Crawl4AIConfig(BaseModel):
    """Configuration for Crawl4AI backend."""
    max_retries: int = Field(3, ge=0) # Must be >= 0
    timeout: float = Field(30.0, gt=0) # Must be > 0
    headers: Dict[str, str] = {
        "User-Agent": "Crawl4AI/1.0 Documentation Crawler"
    }
    follow_redirects: bool = True
    verify_ssl: bool = False  # Default to False for testing
    max_depth: int = Field(5, ge=0) # Must be >= 0
    rate_limit: float = Field(2.0, gt=0)  # Must be > 0
    follow_links: bool = True  # Whether to follow internal links
    max_pages: int = Field(100, ge=0) # Must be >= 0
    allowed_domains: Optional[List[str]] = None  # Domains to restrict crawling to
    concurrent_requests: int = Field(10, gt=0) # Must be > 0

    def __str__(self) -> str:
        return (
            f"Crawl4AIConfig(max_depth={self.max_depth}, max_pages={self.max_pages}, "
            f"follow_links={self.follow_links}, rate_limit={self.rate_limit}, "
            f"verify_ssl={self.verify_ssl}, concurrent_requests={self.concurrent_requests})"
        )


class Crawl4AIBackend(CrawlerBackend):
    """Primary crawler backend using advanced crawling techniques."""

    def __init__(self, config: Optional[Crawl4AIConfig] = None) -> None:
        """Initialize the Crawl4AI backend."""
        super().__init__(name="crawl4ai")
        self.config = config or Crawl4AIConfig()
        self._session: Optional[aiohttp.ClientSession] = None
        self._processing_semaphore = asyncio.Semaphore(self.config.concurrent_requests)
        self._rate_limiter = asyncio.Lock()
        self._last_request = 0.0
        self._crawled_urls: Set[str] = set()
        self._initial_domain = None  # Store the initial domain for subdomain checking
        self._progress_callback = None
        self.metrics.update({
            "successful_requests": 0,
            "failed_requests": 0,
            "total_crawl_time": 0.0,
            "cached_pages": 0,
            "total_pages": 0, # Renamed to pages_crawled for consistency
            "pages_crawled": 0,
            "start_time": None,
            "end_time": None
        })
        self.content_processor = ContentProcessor() # Initialize ContentProcessor
        logger.info(f"Initialized Crawl4AI backend with config: {self.config}")

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

    async def close(self):
        """Close resources."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    def set_progress_callback(self, callback):
        """Set a callback function to receive progress updates."""
        self._progress_callback = callback

    async def _notify_progress(self, url: str, depth: int, status: str):
        """Notify progress callback if set."""
        if self._progress_callback:
            await self._progress_callback(url, depth, status)

    def _is_same_domain(self, url1: str, url2: str) -> bool:
        """Check if two URLs belong to the same domain."""
        try:
            domain1 = urlparse(url1).netloc.lower()
            domain2 = urlparse(url2).netloc.lower()

            # Extract base domain without subdomains
            base1 = '.'.join(domain1.split('.')[-2:])
            base2 = '.'.join(domain2.split('.')[-2:])

            logger.debug(f"Domain comparison: {domain1} vs {domain2}")
            logger.debug(f"Base domain comparison: {base1} vs {base2}")

            # First check exact domain match
            if domain1 == domain2:
                return True

            # Then check if one is a subdomain of the other
            return domain1.endswith(f".{base2}") or domain2.endswith(f".{base1}")

        except Exception as e:
            logger.error(f"Error comparing domains {url1} and {url2}: {str(e)}")
            return False

    def _is_in_subfolder(self, base_url: str, link_url: str) -> bool:
        """Check if a link is within the same subfolder structure."""
        try:
            # Normalize both URLs
            base_url = self._normalize_url(base_url)
            link_url = self._normalize_url(link_url)

            # Must be same domain
            if not self._is_same_domain(base_url, link_url):
                logger.debug(f"Different domains: {urlparse(base_url).netloc} vs {urlparse(link_url).netloc}")
                return False

            # Get paths
            base_path = urlparse(base_url).path.strip('/').split('/')
            link_path = urlparse(link_url).path.strip('/').split('/')

            # If base path is longer, link can't be in its subfolder
            if len(base_path) > len(link_path):
                logger.debug(f"Base path longer than link path: {len(base_path)} > {len(link_path)}")
                return False

            # Check if link path starts with base path
            result = all(b == l for b, l in zip(base_path, link_path))
            logger.debug(f"Subfolder check result for {link_url}: {result}")
            return result

        except Exception as e:
            logger.error(f"Error checking subfolder for {link_url}: {str(e)}")
            return False

    def _normalize_url(self, url: str) -> str:
        """Normalize URL to avoid duplicates."""
        parsed = urlparse(url)

        # Remove default ports and www
        netloc = parsed.netloc.lower()
        if ':' in netloc:
            host, port = netloc.split(':')
            if (parsed.scheme == 'http' and port == '80') or (parsed.scheme == 'https' and port == '443'):
                netloc = host

        # Remove www. prefix
        if netloc.startswith('www.'):
            netloc = netloc[4:]

        # Normalize path - resolve .. and .
        path = parsed.path
        if not path:
            path = '/'
        else:
            # Split path and resolve . and ..
            segments = []
            for segment in path.split('/'):
                if segment == '.' or not segment:
                    continue
                elif segment == '..':
                    if segments:
                        segments.pop()
                else:
                    segments.append(segment)
            path = '/' + '/'.join(segments)

        # Remove trailing slash unless it's the root path
        if path != '/' and path.endswith('/'):
            path = path[:-1]

        # Remove fragments completely
        fragment = ''

        # Sort query parameters
        query = parsed.query
        if query:
            params = []
            for param in sorted(query.split('&')):
                if '=' in param:
                    key, value = param.split('=', 1)
                    params.append(f"{key.lower()}={value}")
                else:
                    params.append(param.lower())
            query = '&'.join(params)

        # Rebuild URL without fragments and with normalized components
        components = (
            parsed.scheme.lower(),
            netloc,
            path,
            '',  # Remove params
            query,
            fragment
        )
        normalized = str(urlunparse(components))

        logger.debug(f"Normalized URL: {url} -> {normalized}")
        return normalized

    def _should_follow_link(self, base_url: str, link: str) -> bool:
        """Determine if a link should be followed."""
        logger.debug(f"\nEvaluating link: {link}")
        logger.debug(f"Base URL: {base_url}")

        if not self.config.follow_links:
            logger.debug("Link following disabled in config")
            return False

        try:
            # Convert relative URLs to absolute and normalize
            absolute_link = self._normalize_url(urljoin(base_url, link))
            logger.debug(f"Absolute link: {absolute_link}")

            # Skip if already crawled
            if absolute_link in self._crawled_urls:
                logger.debug(f"Link already crawled: {absolute_link}")
                return False

            # Check if we've hit the page limit
            if len(self._crawled_urls) >= self.config.max_pages:
                logger.debug(f"Page limit reached: {len(self._crawled_urls)} >= {self.config.max_pages}")
                return False

            # Get domain without www.
            link_domain = urlparse(absolute_link).netloc.lower()
            if link_domain.startswith('www.'):
                link_domain = link_domain[4:]

            # Only follow links to the same subdomain as the initial URL
            if self._initial_domain is None:
                parsed = urlparse(base_url)
                self._initial_domain = parsed.netloc.lower()
                if self._initial_domain.startswith('www.'):
                    self._initial_domain = self._initial_domain[4:]
                logger.debug(f"Initial domain set to: {self._initial_domain}")

            if link_domain != self._initial_domain:
                logger.debug(f"Skipping different subdomain: {link_domain} (initial: {self._initial_domain})")
                return False

            logger.debug(f"Final decision for {absolute_link}: True")
            return True

        except Exception as e:
            logger.error(f"Error processing link {link}: {str(e)}")
            return False

    async def _fetch_with_retry(self, url: str, params: Optional[Dict[str, Any]] = None) -> CrawlResult:
        """Fetch URL content with retry logic."""
        retries = 0
        last_error = None

        while retries <= self.config.max_retries: # Use <= to allow max_retries attempts *after* the initial one
            try:
                await self._ensure_session()
                await self._wait_rate_limit()

                async with self._processing_semaphore:
                    # Call get and await the result
                    response_obj = await self._session.get(url, params=params)
                    # Now use the response object as the context manager
                    async with response_obj as response:
                        html = await response.text()
                        # Use the url_str passed to this method, which might be normalized
                        return CrawlResult(
                            url=url, # Use the 'url' parameter passed to this method
                            content={"html": html},
                            metadata={"headers": dict(response.headers)},
                            status=response.status
                        )

            except Exception as e:
                last_error = str(e)
                retries += 1
                if retries < self.config.max_retries:
                    await asyncio.sleep(2 ** retries)  # Exponential backoff
                logger.warning(f"Retry {retries}/{self.config.max_retries} for {url}: {str(e)}")

        return CrawlResult(
            url=url, # Use the 'url' parameter passed to this method
            content={},
            metadata={},
            status=0,
            error=f"Failed after {retries} retries: {last_error}"
        )

    async def crawl(self, url: Union[str, URLInfo], params: Optional[Dict[str, Any]] = None) -> CrawlResult:
        """Crawl the specified URL and return all crawled pages."""
        # --- Metrics Start ---
        start_crawl_time = datetime.now()
        if self.metrics["start_time"] is None: # Set overall start time only once
             self.metrics["start_time"] = start_crawl_time

        # --- URL Initialization and Validation ---
        if isinstance(url, str):
            url_info = URLInfo(url=url)
        elif isinstance(url, URLInfo):
            url_info = url
        else:
            raise TypeError("Input URL must be a string or URLInfo object")

        if not url_info.is_valid:
            logger.error(f"Invalid URL provided: {url_info.raw_url} - Reason: {url_info.error_message}")
            # Return result using the raw URL as the reference
            result = CrawlResult(
                url=url_info.raw_url,
                content={}, metadata={}, status=0, error=f"Invalid URL: {url_info.error_message}"
            )
            self.metrics["failed_requests"] += 1
            self.metrics["end_time"] = datetime.now()
            self.metrics["total_crawl_time"] = (self.metrics["end_time"] - self.metrics["start_time"]).total_seconds()
            return result

        # Temporarily removed try block for debugging syntax error
        # Use the validated, normalized URL string from now on
        url_str = url_info.normalized_url
        logger.debug(f"Validated and normalized URL: {url_str}")

        # --- Package Name Handling (Check normalized URL) ---
        # This check might need refinement depending on how package names vs URLs are distinguished
        if not url_str.startswith(('http://', 'https://')):
             logger.info(f"Handling '{url_str}' as a potential package name (or invalid URL)")
             # Assuming non-HTTP(S) are treated as packages for now
             # Assuming package lookup is a success for metrics
             result = CrawlResult(
                 url=url_str, # Use the normalized string
                 content={
                     "text": f"Package documentation for {url_str} will be implemented soon.",
                     "title": f"Package: {url_str}"
                 },
                 metadata={"type": "package", "name": url_str},
                 status=200 # Assuming package 'lookup' is always successful
             )
             self.metrics["successful_requests"] += 1
             self.metrics["pages_crawled"] += 1
             self.metrics["end_time"] = datetime.now()
             self.metrics["total_crawl_time"] = (self.metrics["end_time"] - self.metrics["start_time"]).total_seconds()
             return result
            # No need to prepend 'https://' as URLInfo validation ensures a valid scheme

        # --- Pre-Fetch Checks (Domain, Limits) ---
        # URL format validation is already done by URLInfo
        parsed = url_info._parsed # Use the parsed result from URLInfo

        # Check allowed domains *before* fetching
        if self.config.allowed_domains:
             parsed_domain = parsed.netloc.lower()
             # Normalize www.
             if parsed_domain.startswith('www.'):
                  parsed_domain = parsed_domain[4:]
             is_allowed = any(parsed_domain == domain or parsed_domain.endswith(f'.{domain}')
                            for domain in self.config.allowed_domains)
             if not is_allowed:
                  logger.warning(f"Domain {parsed_domain} not in allowed domains: {self.config.allowed_domains}. Skipping {url_str}")
                  result = CrawlResult(
                      url=url_str,
                      content={},
                      metadata={},
                      status=403, # Use 403 Forbidden as expected by test
                      error=f"Domain not allowed: {parsed_domain}"
                  )
                  self.metrics["failed_requests"] += 1
                  self.metrics["end_time"] = datetime.now()
                  self.metrics["total_crawl_time"] = (self.metrics["end_time"] - self.metrics["start_time"]).total_seconds()
                  return result

        # Check max_pages limit *before* fetching
        if len(self._crawled_urls) >= self.config.max_pages:
             logger.info(f"Max pages limit ({self.config.max_pages}) reached. Skipping {url_str}")
             result = CrawlResult(
                 url=url_str,
                 content={},
                 metadata={},
                 status=0, # Or a custom status?
                 error=f"Max pages limit reached ({self.config.max_pages})"
             )
             # Don't count as failure, just limit reached
             self.metrics["end_time"] = datetime.now()
             self.metrics["total_crawl_time"] = (self.metrics["end_time"] - self.metrics["start_time"]).total_seconds()
             return result

        # Use the validated and normalized url_str
        final_url_to_fetch = url_str
        logger.info(f"Starting crawl of URL: {final_url_to_fetch}")
        fetch_result = await self._fetch_with_retry(final_url_to_fetch, params)
        if fetch_result.error:
            logger.error(f"Error crawling {final_url_to_fetch}: {fetch_result.error}") # Log the URL actually fetched
            self.metrics["failed_requests"] += 1
            self.metrics["end_time"] = datetime.now()
            self.metrics["total_crawl_time"] = (self.metrics["end_time"] - self.metrics["start_time"]).total_seconds()
            return fetch_result

        # --- Post-Fetch Checks and Processing ---
        # Check max_pages limit *again* after successful fetch before adding to crawled set
        if len(self._crawled_urls) >= self.config.max_pages:
             logger.info(f"Max pages limit ({self.config.max_pages}) reached after fetching {final_url_to_fetch}. Discarding.")
             limit_result = CrawlResult(
                 url=final_url_to_fetch, # Use the URL actually fetched
                 content={},
                 metadata=fetch_result.metadata, # Keep metadata like headers if needed
                 status=0,
                 error=f"Max pages limit reached ({self.config.max_pages}) after fetch"
             )
             # Don't count as failure, just limit reached
             self.metrics["end_time"] = datetime.now()
             self.metrics["total_crawl_time"] = (self.metrics["end_time"] - self.metrics["start_time"]).total_seconds()
             return limit_result

        # Add to crawled set *before* processing
        self._crawled_urls.add(final_url_to_fetch) # Add the fetched URL to crawled set

        # Process and validate content
        # Only validate and process if fetch was successful (status 200)
        final_result = fetch_result # Start with the fetch result
        if final_result.status == 200:
            if await self.validate(final_result):
                processed_content = await self.process(final_result)
                # Check if processing itself returned an error
                if isinstance(processed_content, dict) and "error" in processed_content:
                     final_result.error = f"Processing error: {processed_content['error']}" # Prepend context
                     # Keep original fetch status (200), but log warning and count as failure for metrics
                     logger.warning(f"Processing issues found for {final_url_to_fetch}: {final_result.error}")
                     self.metrics["failed_requests"] += 1
                else:
                     # Assuming process returns the dict to be merged
                     final_result.content.update(processed_content)
                     logger.info(f"Successfully crawled and processed {final_url_to_fetch}")
                     self.metrics["successful_requests"] += 1
                     self.metrics["pages_crawled"] += 1
                # Return result after processing (might have processing error added)
            else: # Validation failed after successful fetch
                logger.error(f"Content validation failed for {final_url_to_fetch} (status {final_result.status})")
                final_result.error = "Content validation failed"
                self.metrics["failed_requests"] += 1
                # Return result even if validation failed
        else:
            # If fetch failed (non-200 status), count as failure
            # Error/status are already set by _fetch_with_retry
            logger.warning(f"Fetch failed for {final_url_to_fetch} with status {final_result.status}. Skipping processing.")
            self.metrics["failed_requests"] += 1

        # --- Metrics End ---
        self.metrics["end_time"] = datetime.now()
        if self.metrics["start_time"]: # Ensure start_time was set
             self.metrics["total_crawl_time"] = (self.metrics["end_time"] - self.metrics["start_time"]).total_seconds()

        return final_result

    async def validate(self, content: CrawlResult) -> bool:
        """Validate the crawled content."""
        if not content or not content.content.get("html"):
            return False
        return True

    async def process(self, content: CrawlResult) -> Dict[str, Any]:
        """Process the crawled content using ContentProcessor."""
        html_text = content.content.get("html")
        if not html_text:
             logger.warning(f"No HTML content found for URL: {content.url}")
             return {"error": "No HTML content found"}

        try:
            # Use the initialized ContentProcessor
            processed_data: ProcessedContent = await self.content_processor.process( # Add await
                html_content=html_text,
                base_url=content.url # Pass the original URL as base_url
            )

            # Link extraction and queuing are handled by the main Crawler, not the backend.
            # The backend's responsibility is to process the content of a single page.

            # Return the processed data as a dictionary
            # The test expects a dict with a 'content' key or 'error'
            # Let's wrap the ProcessedContent model dump in a 'content' key
            if processed_data.errors:
                 # If ContentProcessor reported errors, return them
                 return {"error": "; ".join(processed_data.errors)}
            else:
                 # Return the full processed data structure
                 # Convert dataclass to dict for serialization
                 return {"content": asdict(processed_data)}

        except Exception as e:
            logger.error(f"Error processing content for {content.url}: {str(e)}", exc_info=True)
            return {"error": f"Failed to process content: {str(e)}"}

    def get_metrics(self) -> Dict[str, Any]:
        """Get current crawler metrics."""
        metrics = super().get_metrics()
        metrics.update({
            "success_rate": (
                self.metrics["successful_requests"] /
                (self.metrics["successful_requests"] + self.metrics["failed_requests"])
                if self.metrics["successful_requests"] + self.metrics["failed_requests"] > 0
                else 0.0
            ),
            "average_response_time": (
                self.metrics["total_crawl_time"] / self.metrics["pages_crawled"]
                if self.metrics["pages_crawled"] > 0
                else 0.0
            )
        })
        return metrics

    def _is_valid_link(self, link: str, base_url: str) -> bool:
        """Check if a link is valid for crawling."""
        try:
            # Convert relative to absolute URL
            absolute_link = urljoin(base_url, link)

            # Parse the URLs
            parsed_link = urlparse(absolute_link)
            parsed_base = urlparse(base_url)

            # Skip code line anchors and other fragment-only links
            if '#' in absolute_link:
                fragment = parsed_link.fragment
                if fragment.startswith('__codelineno-') or fragment == parsed_link.path.lstrip('/'):
                    return False

            # Basic validation
            if not parsed_link.scheme or not parsed_link.netloc:
                return False

            # Check if link is within the same domain
            if parsed_link.netloc != parsed_base.netloc:
                return False

            # Skip links that are just anchors to the same page
            if (parsed_link.scheme == parsed_base.scheme and
                parsed_link.netloc == parsed_base.netloc and
                parsed_link.path == parsed_base.path and
                parsed_link.fragment != parsed_base.fragment):
                return False

            return True
        except Exception as e:
            logging.debug(f"Error validating link {link}: {str(e)}")
            return False

    async def _wait_rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        async with self._rate_limiter:
            now = time.time()
            if self._last_request:
                wait_time = (1.0 / self.config.rate_limit) - (now - self._last_request)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
            self._last_request = time.time()