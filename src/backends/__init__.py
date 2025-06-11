"""Backend module for lib2docScrape.

This module provides the backend infrastructure for crawling and processing
documentation from various sources.
"""

from .base import CrawlerBackend, CrawlResult
from .selector import BackendCriteria, BackendSelector

__all__ = [
    "CrawlerBackend",
    "CrawlResult",
    "BackendSelector",
    "BackendCriteria",
]
