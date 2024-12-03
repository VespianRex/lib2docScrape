import asyncio
import time
import ssl
import certifi
from typing import Any, Dict, Optional, List, Set, Union
import logging
from urllib.parse import urljoin, urlparse, urlunparse
import sys
from datetime import datetime

import aiohttp
from bs4 import BeautifulSoup
from pydantic import BaseModel

from .base import CrawlerBackend, CrawlResult
from ..utils.helpers import URLInfo

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
    max_retries: int = 3
    timeout: float = 30.0
    headers: Dict[str, str] = {
        "User-Agent": "Crawl4AI/1.0 Documentation Crawler"
    }
    follow_redirects: bool = True
    verify_ssl: bool = False  # Default to False for testing
    max_depth: int = 5
    rate_limit: float = 2.0  # Requests per second
    follow_links: bool = True  # Whether to follow internal links
    max_pages: int = 100  # Maximum number of pages to crawl
    allowed_domains: Optional[List[str]] = None  # Domains to restrict crawling to
    concurrent_requests: int = 10  # Number of concurrent requests allowed

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
        super().__init__()
        self.name = "crawl4ai"
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
            "total_pages": 0,
            "start_time": None,
            "end_time": None
        })
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

        while retries < self.config.max_retries:
            try:
                await self._ensure_session()
                await self._wait_rate_limit()

                async with self._processing_semaphore:
                    async with self._session.get(url, params=params) as response:
                        html = await response.text()
                        return CrawlResult(
                            url=url,
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
            url=url,
            content={},
            metadata={},
            status=0,
            error=f"Failed after {retries} retries: {last_error}"
        )

    async def crawl(self, url: Union[str, URLInfo], params: Optional[Dict[str, Any]] = None) -> CrawlResult:
        """Crawl the specified URL and return all crawled pages."""
        url_str = None
        try:
            # Convert URLInfo to string safely
            if isinstance(url, URLInfo):
                logger.debug(f"Processing URLInfo object: {url.model_dump()}")
                url_str = url.normalized  # Try using normalized directly instead of safe_normalized
                logger.debug(f"Using normalized URL: {url_str} (type: {type(url_str)})")
            else:
                url_str = url
                logger.debug(f"Using raw URL string: {url_str} (type: {type(url_str)})")

            # Handle package names
            if not url_str.startswith(('http://', 'https://', 'www.')):
                logger.info(f"Handling {url_str} as a package name")
                return CrawlResult(
                    url=url_str,
                    content={
                        "text": f"Package documentation for {url_str} will be implemented soon.",
                        "title": f"Package: {url_str}"
                    },
                    metadata={
                        "type": "package",
                        "name": url_str
                    },
                    status=200
                )

            # Handle URLs
            if not url_str.startswith(('http://', 'https://')):
                url_str = 'https://' + url_str.lstrip('/')

            # Validate URL format
            try:
                parsed = urlparse(url_str)
                logger.debug(f"Parsed URL components: {parsed}")
                if not all([parsed.scheme, parsed.netloc]):
                    raise ValueError("Invalid URL format")
            except Exception as e:
                logger.error(f"Invalid URL format for {url_str}: {str(e)}")
                return CrawlResult(
                    url=url_str,
                    content={},
                    metadata={},
                    status=0,
                    error=f"Invalid URL format: {str(e)}"
                )

            logger.info(f"Starting crawl of URL: {url_str}")
            result = await self._fetch_with_retry(url_str, params)
            if result.error:
                logger.error(f"Error crawling {url_str}: {result.error}")
                return result

            # Process and validate content
            if await self.validate(result):
                processed_content = await self.process(result)
                result.content.update(processed_content)
                logger.info(f"Successfully crawled {url_str}")
                return result
            else:
                logger.error(f"Content validation failed for {url_str}")
                return CrawlResult(
                    url=url_str,
                    content={},
                    metadata={},
                    status=0,
                    error="Content validation failed"
                )

        except Exception as e:
            logger.error(f"Error during crawl of {url_str if url_str else url}: {str(e)}", exc_info=True)
            return CrawlResult(
                url=url_str if url_str else url,
                content={},
                metadata={},
                status=0,
                error=str(e)
            )

    async def validate(self, content: CrawlResult) -> bool:
        """Validate the crawled content."""
        if not content or not content.content.get("html"):
            return False
        return True

    async def process(self, content: CrawlResult) -> Dict[str, Any]:
        """Process the crawled content."""
        if not content.content.get("html"):
            return {}

        try:
            # Extract text content
            soup = BeautifulSoup(content.content["html"], 'html.parser')
            
            # Remove unwanted elements
            for element in soup.select('script, style, meta, link'):
                element.decompose()
                
            # Get clean text
            text = soup.get_text(separator='\n', strip=True)
            
            # Extract links for further crawling
            links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                if self._should_follow_link(content.url, href):
                    links.append(href)
                    
            return {
                "text": text,
                "links": links,
                "title": soup.title.string if soup.title else ""
            }
            
        except Exception as e:
            logger.error(f"Error processing content: {str(e)}")
            return {}

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