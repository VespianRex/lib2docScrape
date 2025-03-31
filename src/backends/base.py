"""Base components for the documentation crawler backends."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, field_validator
from datetime import datetime

from ..utils.helpers import URLInfo


class CrawlResult(BaseModel):
    """Model for storing crawl results."""
    url: Union[str, URLInfo]
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    status: int
    error: Optional[str] = None
    timestamp: datetime = datetime.utcnow()

    @field_validator('url')
    def validate_url(cls, v: Union[str, URLInfo]) -> str:
        """Convert URLInfo to string if needed."""
        if isinstance(v, URLInfo):
            return v.normalized
        return v

    def is_success(self) -> bool:
        """Check if the crawl was successful."""
        return 200 <= self.status < 300 and not self.error


class CrawlerBackend(ABC):
    """Abstract base class for crawler backends."""
    
    def __init__(self, name: Optional[str] = None) -> None:
        """Initialize the crawler backend with metrics tracking."""
        if not name:
            raise ValueError("Backend must have a name")
        self.name = name
        self.reset_metrics()

    @abstractmethod
    async def crawl(self, url: str, params: Optional[Dict[str, Any]] = None) -> CrawlResult:
        """
        Crawl the specified URL and return the content.
        
        Args:
            url: The URL to crawl
            params: Optional parameters for the crawl operation
            
        Returns:
            CrawlResult containing the crawled content and metadata
        
        Raises:
            ValueError: If the URL is invalid
            RuntimeError: If the crawl operation fails
        """
        pass

    @abstractmethod
    async def validate(self, content: CrawlResult) -> bool:
        """
        Validate the crawled content.
        
        Args:
            content: The crawled content to validate
            
        Returns:
            bool indicating if the content is valid
            
        Raises:
            ValueError: If the content is invalid
        """
        pass

    @abstractmethod
    async def process(self, content: CrawlResult) -> Dict[str, Any]:
        """
        Process the crawled content.
        
        Args:
            content: The crawled content to process
            
        Returns:
            Processed content as a dictionary
            
        Raises:
            ValueError: If the content cannot be processed
        """
        pass

    async def update_metrics(self, crawl_time: float, success: bool) -> None:
        """
        Update the crawler metrics.
        
        Args:
            crawl_time: Time taken for the crawl operation in seconds
            success: Whether the crawl was successful
        """
        self.metrics["pages_crawled"] += 1
        self.metrics["total_crawl_time"] += crawl_time
        
        # Update success rate
        total = self.metrics["pages_crawled"]
        current_success = self.metrics["success_rate"] * (total - 1)
        self.metrics["success_rate"] = (current_success + (1 if success else 0)) / total
        
        # Update average response time
        self.metrics["average_response_time"] = (
            self.metrics["total_crawl_time"] / total
        )
        
        # Update min/max response times
        if crawl_time < self.metrics["min_response_time"] or total == 1:
            self.metrics["min_response_time"] = crawl_time
        if crawl_time > self.metrics["max_response_time"]:
            self.metrics["max_response_time"] = crawl_time

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get the current metrics for this crawler.
        
        Returns:
            Dictionary containing the crawler metrics
        """
        return self.metrics.copy()

    def reset_metrics(self) -> None:
        """Reset all metrics to their initial values."""
        self.metrics = {
            "pages_crawled": 0,
            "success_rate": 0.0,
            "average_response_time": 0.0,
            "total_crawl_time": 0.0,
            "min_response_time": float('inf'),
            "max_response_time": 0.0,
        }
