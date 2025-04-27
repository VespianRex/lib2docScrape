"""Base components for the documentation crawler backends."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union, TYPE_CHECKING # Added TYPE_CHECKING
from pydantic import BaseModel, field_validator, Field # Added Field
from datetime import datetime

from ..utils.url import URLInfo # Corrected import path for modular URLInfo

# Forward reference for type hinting
if TYPE_CHECKING:
    from ..crawler import CrawlerConfig


class CrawlResult(BaseModel):
    """Model for storing crawl results."""
    url: Union[str, URLInfo]
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    status: int
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow) # Use default_factory

    model_config = {
        "arbitrary_types_allowed": True
    }

    @field_validator('url')
    def validate_url(cls, v: Union[str, URLInfo]) -> str:
        """Convert URLInfo to string if needed."""
        if isinstance(v, URLInfo):
            # Return normalized_url if valid, otherwise raw_url
            # For root URLs, ensure we don't add trailing slashes to match test expectations
            if v.is_valid and v.normalized_url:
                # Remove trailing slash from root URLs (e.g., https://example.com/)
                if v.normalized_url.endswith('/') and v.normalized_url.count('/') == 3:
                    return v.normalized_url.rstrip('/')
                return v.normalized_url
            return v.raw_url
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
    # Updated signature to match actual usage by the crawler
    async def crawl(self, url_info: URLInfo, config: 'CrawlerConfig') -> CrawlResult:
        """
        Crawl the specified URL and return the content.

        Args:
            url_info: URLInfo object representing the URL to crawl.
            config: The crawler's configuration object.

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

    async def close(self) -> None:
        """Optional cleanup method for backend resources (e.g., sessions)."""
        pass # Default implementation does nothing
