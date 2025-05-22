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
from ..utils.url.info import URLInfo # Corrected import path
from ..utils.url.factory import create_url_info # Added import for factory
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

    def __init__(self, config: Optional[Crawl4AIConfig] = None, rate_limiter=None) -> None:
        """Initialize the Crawl4AI backend.
        
        Args:
            config: Optional configuration for the backend
            rate_limiter: Optional external rate limiter to use instead of internal one
        """
        super().__init__(name="crawl4ai")
        self.config = config or Crawl4AIConfig()
        self._session: Optional[aiohttp.ClientSession] = None
        self._processing_semaphore = asyncio.Semaphore(self.config.concurrent_requests)
        self._external_rate_limiter = rate_limiter
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
            "start_time": 0.0,
            "end_time": 0.0
        })
        self.content_processor = ContentProcessor() # Initialize ContentProcessor
        logger.info(f"Initialized Crawl4AI backend with config: {self.config}")
        if self._external_rate_limiter:
            logger.info(f"Using external rate limiter with rate: {self._external_rate_limiter.rate} req/s")

    def _initialize_metrics(self) -> Dict[str, Any]:
        """Return the initial structure for the metrics dictionary."""
        return {
            "pages_crawled": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_crawl_time": 0.0,
            "cached_pages": 0,
            "total_pages": 0,
            "start_time": 0.0,
            "end_time": 0.0,
            # Add other base metrics if needed from CrawlerBackend's init
            "success_rate": 0.0,
            "average_response_time": 0.0,
        }

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
        """Check if two URLs belong to the same domain using URLInfo."""
        try:
            url1_info = create_url_info(url=url1)
            url2_info = create_url_info(url=url2)

            # If either URL is invalid, they are not considered the same domain
            if not url1_info.is_valid or not url2_info.is_valid:
                 logger.debug(f"Domain comparison: One or both URLs are invalid. {url1} (valid: {url1_info.is_valid}) vs {url2} (valid: {url2_info.is_valid})")
                 return False

            # Compare registered domains (domain + suffix) for a more robust check
            # This handles subdomains correctly (e.g., www.example.com and example.com are same registered domain)
            domain1_registered = url1_info.registered_domain.lower()
            domain2_registered = url2_info.registered_domain.lower()

            logger.debug(f"Domain comparison (registered domain): {domain1_registered} vs {domain2_registered}")

            return domain1_registered == domain2_registered

        except Exception as e:
            logger.error(f"Error comparing domains {url1} and {url2} using URLInfo: {str(e)}")
            return False

    def _is_in_subfolder(self, base_url: str, link_url: str) -> bool:
        """Check if a link is within the same subfolder structure using URLInfo."""
        try:
            base_url_info = create_url_info(url=base_url)
            link_url_info = create_url_info(url=link_url)

            # If either URL is invalid, cannot determine subfolder relationship
            if not base_url_info.is_valid or not link_url_info.is_valid:
                 logger.debug(f"Subfolder check: One or both URLs are invalid. {base_url} (valid: {base_url_info.is_valid}) vs {link_url} (valid: {link_url_info.is_valid})")
                 return False

            # Must be same registered domain
            if base_url_info.registered_domain.lower() != link_url_info.registered_domain.lower():
                logger.debug(f"Subfolder check: Different registered domains. {base_url_info.registered_domain} vs {link_url_info.registered_domain}")
                return False

            # Get normalized paths from URLInfo
            base_path = base_url_info.path.strip('/').split('/')
            link_path = link_url_info.path.strip('/').split('/')

            # If base path is longer, link can't be in its subfolder
            if len(base_path) > len(link_path):
                logger.debug(f"Subfolder check: Base path longer than link path. {len(base_path)} > {len(link_path)}")
                return False

            # Check if link path starts with base path
            result = all(b == l for b, l in zip(base_path, link_path))
            logger.debug(f"Subfolder check result for {link_url}: {result}")
            return result

        except Exception as e:
            logger.error(f"Error checking subfolder for {link_url} using URLInfo: {str(e)}")
            return False

    def _should_follow_link(self, base_url: str, link: str) -> bool:
        """Determine if a link should be followed."""
        logger.debug(f"\nEvaluating link: {link}")
        logger.debug(f"Base URL: {base_url}")

        if not self.config.follow_links:
            logger.debug("Link following disabled in config")
            return False

        try:
            # Convert relative URLs to absolute using urljoin
            absolute_link_str = urljoin(base_url, link)
            
            # Use URLInfo to validate and normalize the absolute link
            absolute_link_info = create_url_info(url=absolute_link_str)

            if not absolute_link_info.is_valid:
                 logger.debug(f"Skipping invalid link: {absolute_link_str} - Reason: {absolute_link_info.error_message}")
                 return False

            # Use the normalized URL string from URLInfo
            normalized_absolute_link = absolute_link_info.normalized_url
            logger.debug(f"Normalized absolute link: {normalized_absolute_link}")


            # Skip if already crawled
            if normalized_absolute_link in self._crawled_urls:
                logger.debug(f"Link already crawled: {normalized_absolute_link}")
                return False

            # Check if we've hit the page limit
            if len(self._crawled_urls) >= self.config.max_pages:
                logger.debug(f"Page limit reached: {len(self._crawled_urls)} >= {self.config.max_pages}")
                return False

            # Get domain from normalized URLInfo
            link_domain = absolute_link_info.hostname.lower()
            # No need to remove www. here, URLInfo's hostname property should handle it if needed for comparison

            # Only follow links to the same domain as the initial URL
            if self._initial_domain is None:
                # Use URLInfo for the base URL as well
                base_url_info = create_url_info(url=base_url)
                if not base_url_info.is_valid:
                     logger.error(f"Invalid base URL for initial domain check: {base_url}")
                     return False # Cannot determine initial domain from invalid base URL

                self._initial_domain = base_url_info.hostname.lower()
                logger.debug(f"Initial domain set to: {self._initial_domain}")

            if link_domain != self._initial_domain:
                logger.debug(f"Skipping different domain: {link_domain} (initial: {self._initial_domain})")
                return False

            logger.debug(f"Final decision for {normalized_absolute_link}: True")
            return True

        except Exception as e:
            logger.error(f"Error processing link {link}: {str(e)}")
            return False

    async def _fetch_with_retry(self, url: str, params: Optional[Dict[str, Any]] = None) -> CrawlResult:
        """Fetch URL content with retry logic."""
        retries = 0
        last_error = None

        while retries <= self.config.max_retries:
            try:
                await self._ensure_session()
                await self._wait_rate_limit()

                async with self._processing_semaphore:
                    response_obj = await self._session.get(url, params=params)
                    async with response_obj as response:
                        # Check for HTTP errors that should be retried (e.g., 5xx)
                        # or let specific exceptions bubble up
                        response.raise_for_status() # Raise exception for non-2xx status codes

                        html = await response.text()
                        logger.debug(f"_fetch_with_retry: Successful fetch for url='{url}'")
                        return CrawlResult(
                            url=url,
                            content={"html": html},
                            metadata={"headers": dict(response.headers.items())},
                            status=response.status,
                            error=None
                        )

            except aiohttp.ClientResponseError as e:
                # Handle HTTP errors specifically - retry on 5xx, fail immediately on 4xx?
                # For now, treat all ClientResponseErrors like other exceptions for retry
                last_error = f"HTTP {e.status}: {e.message}"
                logger.warning(f"Attempt {retries + 1}/{self.config.max_retries + 1} failed for {url}: {last_error}")
                retries += 1
                if retries <= self.config.max_retries:
                    sleep_time = 2 ** (retries - 1) # Exponential backoff (1, 2, 4...)
                    logger.debug(f"Sleeping for {sleep_time}s before retry {retries + 1}")
                    await asyncio.sleep(sleep_time)
                # Continue to next iteration

            except Exception as e:
                # Handle other exceptions (timeouts, connection errors, etc.)
                last_error = str(e)
                logger.warning(f"Attempt {retries + 1}/{self.config.max_retries + 1} failed for {url}: {last_error}")
                retries += 1
                if retries <= self.config.max_retries:
                    sleep_time = 2 ** (retries - 1) # Exponential backoff
                    logger.debug(f"Sleeping for {sleep_time}s before retry {retries + 1}")
                    await asyncio.sleep(sleep_time)
                # Continue to next iteration

        # If the loop finishes without returning a success result, return the error result
        logger.error(f"Failed to fetch {url} after {self.config.max_retries + 1} attempts.")
        return CrawlResult(
            url=url,
            content={},
            metadata={},
            status=0, # Indicate failure after all retries
            error=f"Failed after {self.config.max_retries} retries: {last_error}"
        )

    # Update signature to match ABC
    async def crawl(self, url_info: URLInfo, config: Optional['CrawlerConfig'] = None, params: Optional[Dict[str, Any]] = None) -> CrawlResult: # Use CrawlResult type hint
        """Crawl the specified URL using the Crawl4AI backend."""
        logger.debug(f"Crawl4AIBackend.crawl received: url_info={repr(url_info)}, is_valid={url_info.is_valid}, error='{url_info.error_message}'") # ADD LOGGING
        # --- Metrics Start ---
        start_crawl_time = time.time() # Use float timestamp
        if not self.metrics.get("start_time"): # Set overall start time only once
             self.metrics["start_time"] = start_crawl_time # Store as float

        # --- URL Initialization and Validation ---
        # The URLInfo object is now passed directly
        if not isinstance(url_info, URLInfo):
             # This should ideally not happen due to type hinting, but handle defensively
             error_msg = f"Crawl4AIBackend.crawl received incorrect type for url_info: {type(url_info)}"
             logger.error(error_msg)
             # Use 400 for bad input type
             result = CrawlResult(url=str(url_info), content={}, metadata={}, status=400, error=error_msg)
             self.metrics["failed_requests"] += 1
             # Update end_time and total_crawl_time here as well
             self.metrics["end_time"] = time.time() # Use float timestamp
             if self.metrics.get("start_time"):
                  self.metrics["total_crawl_time"] = self.metrics["end_time"] - self.metrics["start_time"]
             return result

        # Use the backend's own config for its specific settings
        # current_config = config or self.config # Don't use potentially different passed config for backend settings

        # Validation is now done before calling crawl, but double-check
        if not url_info.is_valid:
             logger.error(f"Invalid URLInfo provided to Crawl4AIBackend: {url_info.raw_url} - Reason: {url_info.error_message}")
             # Use 400 for invalid URL input
             result = CrawlResult(
                 url=url_info.raw_url, # Use raw_url for the result URL on validation failure
                 content={}, metadata={}, status=400, error=f"Invalid URL: {url_info.error_message}"
             )
             self.metrics["failed_requests"] += 1
             self.metrics["end_time"] = time.time() # Use float timestamp
             if self.metrics.get("start_time"): # Check if start_time exists
                  self.metrics["total_crawl_time"] = self.metrics["end_time"] - self.metrics["start_time"]
             return result

        if not url_info.is_valid:
            logger.error(f"Invalid URL provided: {url_info.raw_url} - Reason: {url_info.error_message}")
            # Return result using the raw URL as the reference
            # Use 400 for invalid URL input
            result = CrawlResult(
                url=url_info.raw_url,
                content={}, metadata={}, status=400, error=f"Invalid URL: {url_info.error_message}"
            )
            self.metrics["failed_requests"] += 1
            self.metrics["end_time"] = time.time() # Use float timestamp
            if self.metrics.get("start_time"): # Check if start_time exists
                 self.metrics["total_crawl_time"] = self.metrics["end_time"] - self.metrics["start_time"]
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
             self.metrics["end_time"] = time.time() # Use float timestamp
             if self.metrics.get("start_time"):
                  self.metrics["total_crawl_time"] = self.metrics["end_time"] - self.metrics["start_time"]
             return result
            # No need to prepend 'https://' as URLInfo validation ensures a valid scheme

        # --- Pre-Fetch Checks (Domain, Limits) ---
        # Use the parsed result from the validated URLInfo
        parsed = url_info._parsed

        # Check allowed domains *before* fetching using the backend's config
        if self.config.allowed_domains: # Use self.config
             # Use hostname from URLInfo which handles potential port removal
             parsed_domain = url_info.hostname.lower() if url_info.hostname else ""
             # Normalize www.
             if parsed_domain.startswith('www.'):
                  parsed_domain = parsed_domain[4:]
             is_allowed = any(parsed_domain == domain or parsed_domain.endswith(f'.{domain}')
                            for domain in self.config.allowed_domains) # Use self.config
             if not is_allowed:
                  logger.warning(f"Domain {parsed_domain} not in allowed domains: {self.config.allowed_domains}. Skipping {url_str}")
                  result = CrawlResult( # Use CrawlResult
                      url=url_str, # Use normalized url string
                      content={},
                      metadata={},
                      status=403, # Use 403 Forbidden as expected by test
                      error=f"Domain not allowed: {parsed_domain}"
                  ) # Use CrawlResult
                  self.metrics["failed_requests"] += 1
                  self.metrics["end_time"] = time.time() # Use float timestamp
                  if self.metrics.get("start_time"):
                       self.metrics["total_crawl_time"] = self.metrics["end_time"] - self.metrics["start_time"]
                  return result

        # Check max_pages limit *before* fetching using the backend's config
        if self.config.max_pages is not None and len(self._crawled_urls) >= self.config.max_pages: # Use self.config, Check if None first
             logger.info(f"Max pages limit ({self.config.max_pages}) reached. Skipping {url_str}")
             result = CrawlResult( # Use CrawlResult
                 url=url_str, # Use normalized url string
                 content={},
                 metadata={},
                 status=0, # Keep status 0 for non-HTTP errors like limits
                 error=f"Max pages limit reached ({self.config.max_pages})" # Use self.config
             ) # Use CrawlResult
             # Don't count as failure, just limit reached
             self.metrics["end_time"] = time.time() # Use float timestamp
             if self.metrics.get("start_time"):
                  self.metrics["total_crawl_time"] = self.metrics["end_time"] - self.metrics["start_time"]
             return result

        # Use the validated and normalized url_str
        final_url_to_fetch = url_str
        logger.info(f"Starting crawl of URL: {final_url_to_fetch}")
        logger.debug(f"crawl: Calling _fetch_with_retry with url='{final_url_to_fetch}'") # ADDED LOG
        fetch_result = await self._fetch_with_retry(final_url_to_fetch, params)
        logger.debug(f"crawl: _fetch_with_retry returned CrawlResult with url='{fetch_result.url}'") # ADDED LOG
        # Ensure fetch_result is CrawlResult (from base)
        if not isinstance(fetch_result, CrawlResult):
             logger.error(f"Internal error: _fetch_with_retry did not return CrawlResult for {final_url_to_fetch}")
             # Handle this unexpected situation, perhaps return an error CrawlResult
             fetch_result = CrawlResult(url=final_url_to_fetch, status=0, error="Internal fetch error", content={}, metadata={})
             self.metrics["failed_requests"] += 1
        elif fetch_result.error:
            logger.error(f"Error crawling {final_url_to_fetch}: {fetch_result.error}") # Log the URL actually fetched
            self.metrics["failed_requests"] += 1
            # Update end_time and total_crawl_time here as well
            self.metrics["end_time"] = time.time() # Use float timestamp
            if self.metrics.get("start_time"):
                 self.metrics["total_crawl_time"] = self.metrics["end_time"] - self.metrics["start_time"]
            return fetch_result

        # --- Post-Fetch Checks and Processing ---
        # Check max_pages limit *again* after successful fetch before adding to crawled set using the backend's config
        if self.config.max_pages is not None and len(self._crawled_urls) >= self.config.max_pages: # Use self.config, Check if None first
             logger.info(f"Max pages limit ({self.config.max_pages}) reached after fetching {final_url_to_fetch}. Discarding.")
             limit_result = CrawlResult( # Use CrawlResult
                 url=final_url_to_fetch, # Use the URL actually fetched
                 content={},
                 metadata=fetch_result.metadata, # Keep metadata like headers if needed
                 status=0, # Keep status 0 for non-HTTP errors like limits
                 error=f"Max pages limit reached ({self.config.max_pages}) after fetch" # Use self.config
             ) # Use CrawlResult
             # Don't count as failure, just limit reached
             self.metrics["end_time"] = time.time() # Use float timestamp
             if self.metrics.get("start_time"):
                  self.metrics["total_crawl_time"] = self.metrics["end_time"] - self.metrics["start_time"]
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
        end_crawl_time = time.time()
        self.metrics["end_time"] = end_crawl_time # Use float timestamp
        if self.metrics.get("start_time"): # Ensure start_time was set
             self.metrics["total_crawl_time"] = self.metrics["end_time"] - self.metrics["start_time"]

        # Ensure the returned object is CrawlResult
        if not isinstance(final_result, CrawlResult):
             logger.error(f"Internal error: crawl method returning wrong type {type(final_result)} for {url_str}")
             # Attempt to convert or create a default error result
             final_result = CrawlResult(url=url_str, status=0, error="Internal result type error", content={}, metadata={})


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
                content=html_text, # Changed 'html_content' to 'content'
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
        # Start with a copy of the instance's metrics, then add calculated rates
        metrics = self.metrics.copy()
        metrics.update({
            "success_rate": (
                metrics["successful_requests"] / # Use the copied metrics dict
                (metrics["successful_requests"] + metrics["failed_requests"]) # Use the copied metrics dict
                if metrics["successful_requests"] + metrics["failed_requests"] > 0 # Use the copied metrics dict
                else 0.0
            ),
            "average_response_time": (
                metrics["total_crawl_time"] / metrics["pages_crawled"] # Use the copied metrics dict
                if metrics["pages_crawled"] > 0 # Use the copied metrics dict
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
        """Enforce rate limiting between requests.
        Uses the external rate limiter if provided, otherwise uses internal simple rate limiting.
        """
        if self._external_rate_limiter:
            # Use the external rate limiter
            logger.debug(f"Using external rate limiter: {self._external_rate_limiter}")
            wait_time = await self._external_rate_limiter.acquire()
            if wait_time > 0:
                logger.debug(f"External rate limiter requested wait: {wait_time:.4f}s. Sleeping...")
                await asyncio.sleep(wait_time)
            else:
                logger.debug("External rate limiter acquired token immediately.")
        else:
            # Fallback to internal rate limiting logic
            logger.debug(f"Using internal rate limiter (rate: {self.config.rate_limit} req/s).")
            async with self._rate_limiter: # self._rate_limiter is an asyncio.Lock for this internal logic
                now = time.time()
                if self._last_request:
                    # Calculate time since last request and required delay
                    time_passed_since_last = now - self._last_request
                    required_interval = 1.0 / self.config.rate_limit
                    wait_time = required_interval - time_passed_since_last
                    
                    if wait_time > 0:
                        logger.debug(f"Internal rate limiter: last_request={self._last_request:.4f}, now={now:.4f}, time_passed={time_passed_since_last:.4f}, interval={required_interval:.4f}, calculated_wait_time={wait_time:.4f}s. Sleeping...")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.debug(f"Internal rate limiter: Sufficient time passed ({time_passed_since_last:.4f}s >= {required_interval:.4f}s). No wait needed.")
                else:
                    logger.debug("Internal rate limiter: First request, no wait needed.")
                self._last_request = time.time() # Update last request time for internal limiter