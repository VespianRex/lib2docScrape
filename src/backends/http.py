import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
from urllib.parse import urljoin
from pydantic import BaseModel

from .base import CrawlerBackend, CrawlResult


class HTTPBackendConfig(BaseModel):
    """Configuration for HTTP backend."""
    timeout: float = 30.0
    max_retries: int = 3
    verify_ssl: bool = True
    follow_redirects: bool = True
    headers: Dict[str, str] = {
        "User-Agent": "Python Documentation Scraper/1.0"
    }


class HTTPBackend(CrawlerBackend):
    """Backend for crawling HTTP content."""
    
    def __init__(self, config: Optional[HTTPBackendConfig] = None) -> None:
        """Initialize HTTP backend."""
        self.name = "http"
        self.config = config or HTTPBackendConfig()
        self.metrics = {
            "pages_crawled": 0,
            "success_rate": 1.0,
            "errors": 0
        }
        
    async def crawl(self, url: str) -> CrawlResult:
        """
        Crawl HTTP content.
        
        Args:
            url: URL to crawl
            
        Returns:
            CrawlResult containing the crawled content
        """
        try:
            async with aiohttp.ClientSession(headers=self.config.headers) as session:
                async with session.get(
                    url,
                    timeout=self.config.timeout,
                    verify_ssl=self.config.verify_ssl,
                    allow_redirects=self.config.follow_redirects
                ) as response:
                    if response.status == 200:
                        content = await response.text()
                        self.metrics["pages_crawled"] += 1
                        return CrawlResult(
                            url=url,
                            content=content,
                            content_type=response.headers.get("content-type", "text/html"),
                            status_code=response.status
                        )
                    else:
                        self.metrics["errors"] += 1
                        return CrawlResult(
                            url=url,
                            content="",
                            content_type="text/html",
                            status_code=response.status,
                            error=f"HTTP {response.status}"
                        )
        except Exception as e:
            self.metrics["errors"] += 1
            return CrawlResult(
                url=url,
                content="",
                content_type="text/html",
                status_code=500,
                error=str(e)
            )
            
    async def validate(self, result: CrawlResult) -> bool:
        """
        Validate crawl result.
        
        Args:
            result: Crawl result to validate
            
        Returns:
            Boolean indicating if result is valid
        """
        if not result.content:
            return False
            
        if result.status_code != 200:
            return False
            
        if "text/html" not in result.content_type.lower():
            return False
            
        return True
        
    async def process(self, result: CrawlResult) -> Optional[Dict[str, Any]]:
        """
        Process crawled content.
        
        Args:
            result: Crawl result to process
            
        Returns:
            Dictionary containing processed content
        """
        if not result.content:
            return None
            
        try:
            soup = BeautifulSoup(result.content, "html.parser")
            
            # Remove navigation, header, footer elements
            for element in soup.find_all(['nav', 'header', 'footer']):
                element.decompose()
            
            # Find main content area
            main_content = None
            content_selectors = [
                "article.content",  # ReadTheDocs
                "div[role='main']",  # Sphinx
                "main",  # Common
                ".body",  # Python docs
                ".document",  # Sphinx
                "#content",
                ".content",
                ".documentation"
            ]
            
            for selector in content_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            if not main_content:
                main_content = soup
            
            # Extract title
            title_element = (
                soup.find('h1') or 
                soup.find('title') or 
                main_content.find('h1')
            )
            title = title_element.get_text(strip=True) if title_element else "Untitled"
            
            # Extract content structure
            content = {
                "text": main_content.get_text(strip=True),
                "structure": [],
                "headings": [],
                "links": []
            }
            
            # Process sections and content
            current_section = None
            for element in main_content.children:
                if not hasattr(element, 'name'):
                    continue
                    
                # Handle headings
                if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    level = int(element.name[1])
                    text = element.get_text(strip=True)
                    heading = {
                        "level": level,
                        "text": text,
                        "id": element.get('id', '')
                    }
                    content["headings"].append(heading)
                    
                    # Create new section
                    current_section = {
                        "type": "section",
                        "heading": heading,
                        "content": []
                    }
                    content["structure"].append(current_section)
                
                # Handle code blocks
                elif element.name in ['pre', 'code']:
                    code_block = {
                        "type": "code",
                        "language": element.get('class', ['text'])[0] if element.get('class') else 'text',
                        "content": element.get_text(strip=False)
                    }
                    if current_section:
                        current_section["content"].append(code_block)
                    else:
                        content["structure"].append(code_block)
                
                # Handle paragraphs and other text
                elif element.name in ['p', 'div']:
                    text = element.get_text(strip=True)
                    if text:
                        text_block = {
                            "type": "text",
                            "content": text
                        }
                        if current_section:
                            current_section["content"].append(text_block)
                        else:
                            content["structure"].append(text_block)
            
            # Extract links
            for a in main_content.find_all("a", href=True):
                href = a.get("href", "")
                if href and not href.startswith(('#', 'javascript:')):
                    content["links"].append({
                        "url": urljoin(result.url, href),
                        "text": a.get_text(strip=True),
                        "title": a.get("title", ""),
                        "section": current_section["heading"]["text"] if current_section and "heading" in current_section else None
                    })
            
            # Extract metadata
            metadata = {
                "meta": {
                    meta.get("name", meta.get("property", "")): meta.get("content", "")
                    for meta in soup.find_all("meta")
                    if meta.get("name") or meta.get("property")
                }
            }
            
            return {
                "title": title,
                "content": content,
                "metadata": metadata
            }
            
        except Exception as e:
            self.metrics["errors"] += 1
            return None
            
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get backend metrics.
        
        Returns:
            Dictionary of metrics
        """
        total = self.metrics["pages_crawled"] + self.metrics["errors"]
        if total > 0:
            self.metrics["success_rate"] = self.metrics["pages_crawled"] / total
        return self.metrics.copy()