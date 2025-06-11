"""Base components for the documentation crawler backends."""

import logging  # Added import for logger
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional, Union  # Added Type

from pydantic import BaseModel, Field, field_validator

from ..utils.url import URLInfo

# Forward reference for type hinting
if TYPE_CHECKING:
    from ..crawler import CrawlerConfig

logger = logging.getLogger(__name__)  # Define logger for use in this module


class CrawlResult(BaseModel):
    """Model for storing crawl results."""

    url: Union[str, URLInfo]
    content: dict[str, Any]
    metadata: dict[str, Any]
    status: int
    error: Optional[str] = None
    content_type: Optional[str] = None  # Added content_type field
    documents: Optional[list] = None  # Added documents field
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )  # Use timezone-aware datetime

    model_config = {"arbitrary_types_allowed": True}

    @field_validator("url")
    def validate_url(cls, v: Union[str, URLInfo]) -> str:
        """Convert URLInfo to string if needed."""
        logger = logging.getLogger(__name__)  # Get logger
        logger.debug(f"CrawlResult URL validator received: type={type(v)}, value='{v}'")
        if isinstance(v, URLInfo):
            # Return normalized_url if valid, otherwise raw_url
            if v.is_valid and v.normalized_url:
                # Special handling for root path was removed as normalization handles it
                result_str = v.normalized_url
                logger.debug(
                    f"CrawlResult URL validator returning (from URLInfo): '{result_str}'"
                )
                return result_str
            result_str = v.raw_url
            logger.debug(
                f"CrawlResult URL validator returning (from invalid URLInfo): '{result_str}'"
            )
            return result_str
        logger.debug(f"CrawlResult URL validator returning (from str): '{v}'")
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
    async def crawl(self, url_info: URLInfo, config: "CrawlerConfig") -> CrawlResult:
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
    async def process(self, content: CrawlResult) -> dict[str, Any]:
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
        self.metrics["average_response_time"] = self.metrics["total_crawl_time"] / total

        # Update min/max response times
        if crawl_time < self.metrics["min_response_time"] or total == 1:
            self.metrics["min_response_time"] = crawl_time
        if crawl_time > self.metrics["max_response_time"]:
            self.metrics["max_response_time"] = crawl_time

    def get_metrics(self) -> dict[str, Any]:
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
            "min_response_time": float("inf"),
            "max_response_time": 0.0,
        }

    async def close(self) -> None:
        """Optional cleanup method for backend resources (e.g., sessions).

        Subclasses can override this method to implement specific cleanup logic.
        The default implementation logs the closure.
        """
        logger.debug(f"Closing backend: {self.name}")
        # Default implementation - no cleanup needed for base class


# Moved from selector.py to base.py to resolve circular import
_registered_backends: dict[str, type[CrawlerBackend]] = {}


def register_backend(name: str, backend_class: type[CrawlerBackend]):
    """Register a backend class."""
    if not issubclass(backend_class, CrawlerBackend):
        raise TypeError(
            f"{backend_class.__name__} must be a subclass of CrawlerBackend"
        )
    _registered_backends[name] = backend_class
    logger.info(f"Backend '{name}' registered with class {backend_class.__name__}")


def get_backend_class(name: str) -> Optional[type[CrawlerBackend]]:
    """Get a registered backend class by name."""
    return _registered_backends.get(name)


def get_all_backend_names() -> list[str]:
    """Get names of all registered backends."""
    return list(_registered_backends.keys())
