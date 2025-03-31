"""HTTP backend for fetching documentation content."""

import logging
from typing import Dict, Optional, Any
import aiohttp
from dataclasses import dataclass
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
        
    async def crawl(self, url: str, params: Optional[Dict[str, Any]] = None) -> CrawlResult:
        """Crawl a URL and return the content."""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout),
                    headers=self.config.headers or {}
                )
            
            async with self.session.get(
                url,
                ssl=None if not self.config.verify_ssl else True,
                allow_redirects=self.config.follow_redirects,
                params=params
            ) as response:
                content = await response.text()
                return CrawlResult(
                    url=url,
                    content={"html": content},
                    metadata={
                        "status": response.status,
                        "headers": dict(response.headers),
                        "content_type": response.headers.get("content-type", "")
                    },
                    status=response.status
                )
                
        except Exception as e:
            logging.error(f"Error fetching {url}: {str(e)}")
            return CrawlResult(
                url=url,
                content={},
                metadata={},
                status=500,
                error=str(e)
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
