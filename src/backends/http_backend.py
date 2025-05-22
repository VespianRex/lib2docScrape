"""HTTP backend for fetching documentation content."""

import logging
from typing import Dict, Optional, Any, TYPE_CHECKING
import aiohttp
from aiohttp import ClientResponseError, ClientConnectionError # Added specific aiohttp exceptions
import asyncio # Added asyncio for TimeoutError
from dataclasses import dataclass
# Import CrawlerConfig from src.crawler conditionally for type hinting
if TYPE_CHECKING:
    from src.crawler import CrawlerConfig
from src.utils.url import URLInfo # Import URLInfo
from .base import CrawlerBackend, CrawlResult


@dataclass
class HTTPBackendConfig:
    """Configuration for HTTP backend."""
    timeout: float = 30.0
    verify_ssl: bool = True
    follow_redirects: bool = True
    headers: Dict[str, str] = None


class HTTPBackend(CrawlerBackend):
    """Backend for fetching content over HTTP."""
    
    def __init__(self, config: HTTPBackendConfig):
        """Initialize the HTTP backend."""
        super().__init__(name="http_backend")
        self.config = config
        self.session = None
        
    async def crawl(self, url_info: URLInfo, config: Optional['CrawlerConfig'] = None, params: Optional[Dict[str, Any]] = None) -> CrawlResult:
        """Crawl a URL and return the content."""
        # If a specific CrawlerConfig is passed, use its timeout and headers, otherwise use the backend's default config.
        # This allows per-request overrides if needed, though typically the backend's config is sufficient.
        current_config = self.config
        # Ensure 'config' is an instance of the actual CrawlerConfig if it's not None
        # This check is tricky with forward refs, but isinstance will work if src.crawler is imported elsewhere
        # For now, we rely on the caller to pass the correct type or None.
        # if config and isinstance(config, CrawlerConfig) and hasattr(config, 'request_timeout'):
        if config and hasattr(config, 'request_timeout'): # Simpler check for now
             # We'd need to map CrawlerConfig fields to HTTPBackendConfig fields or adjust HTTPBackendConfig
             # For now, assume self.config (HTTPBackendConfig) is primarily used.
             # If direct_backend is used, DocumentationCrawler._process_url passes its own config.
             pass


        url_to_fetch = url_info.normalized_url

        try:
            if not self.session:
                # Use headers from self.config (HTTPBackendConfig)
                # User-Agent can be overridden by CrawlerConfig if provided and different
                headers_to_use = self.config.headers or {}
                if config and config.user_agent and headers_to_use.get("User-Agent") != config.user_agent:
                    headers_to_use["User-Agent"] = config.user_agent
                
                self.session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=current_config.timeout),
                    headers=headers_to_use
                )
            
            async with self.session.get(
                url_to_fetch,
                ssl=None if not current_config.verify_ssl else True, # Use current_config
                allow_redirects=current_config.follow_redirects,    # Use current_config
                params=params
            ) as response:
                content = await response.text()
                # The URL in CrawlResult should be the final URL after redirects
                final_url = str(response.url)
                return CrawlResult(
                    url=final_url, # Use the URL from the response
                    content={"html": content},
                    metadata={
                        "status": response.status,
                        "headers": dict(response.headers),
                        "content_type": response.headers.get("content-type", "")
                    },
                    status=response.status
                )
                
        except ClientResponseError as e:
            # Handle HTTP errors (4xx, 5xx). Populate status with the actual HTTP status code.
            logging.error(f"HTTP error fetching {url_to_fetch}: Status {e.status}, Message: {e.message}")
            return CrawlResult(
                url=url_to_fetch,
                content={},
                metadata={"status": e.status, "headers": dict(e.headers) if e.headers else {}},
                status=e.status, # Use the actual HTTP status code
                error=f"HTTP Error: {e.status} {e.message}" # Include status and message in error description
            )
        except asyncio.TimeoutError:
            # Handle request timeouts. Set status to 504 (Gateway Timeout).
            logging.error(f"Timeout fetching {url_to_fetch}")
            return CrawlResult(
                url=url_to_fetch,
                content={},
                metadata={},
                status=504, # Gateway Timeout
                error="Request timed out" # Specific error message for timeout
            )
        except ClientConnectionError as e:
            # Handle connection errors (e.g., host not found, connection refused). Set status to 503 (Service Unavailable).
            logging.error(f"Connection error fetching {url_to_fetch}: {e}")
            return CrawlResult(
                url=url_to_fetch,
                content={},
                metadata={},
                status=503, # Service Unavailable or a custom code
                error=f"Connection Error: {e}" # Include connection error details
            )
        except Exception as e:
            # Handle any other unexpected errors. Set status to 500 (Internal Server Error).
            logging.error(f"Unexpected error fetching {url_to_fetch}: {str(e)}")
            return CrawlResult(
                url=url_to_fetch,
                content={},
                metadata={},
                status=500, # Internal Server Error
                error=f"Unexpected Error: {str(e)}" # Include unexpected error details
            )
            
    async def validate(self, content: CrawlResult) -> bool:
        """Validate the crawled content."""
        if not content or not content.content:
            return False
            
        if content.status != 200:
            return False
            
        html = content.content.get("html")
        if not html:
            return False
            
        return True
        
    async def process(self, content: CrawlResult) -> Dict[str, Any]:
        """Process the crawled content."""
        if not await self.validate(content):
            return {}
            
        return {
            "url": content.url,
            "html": content.content["html"],
            "metadata": content.metadata
        }
        
    async def close(self):
        """Close the HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
