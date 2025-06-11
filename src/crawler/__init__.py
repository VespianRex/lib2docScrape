"""
Crawler module for lib2docScrape.

This module provides the main crawler functionality for documentation scraping,
including configuration models and backward compatibility aliases.
"""

from pydantic import BaseModel

# Import classes that tests expect to be available
from ..backends.selector import BackendSelector
from ..organizers.doc_organizer import DocumentOrganizer
from ..processors.content_processor import ContentProcessor
from . import models
from .crawler import Crawler

# Use the new Crawler class as DocumentationCrawler
DocumentationCrawler = Crawler

# Define aliases for backward compatibility
CrawlerConfig = models.CrawlConfig
CrawlConfig = models.CrawlConfig
CrawlTarget = models.CrawlTarget
CrawlResult = models.CrawlResult
CrawlStats = models.CrawlStats
QualityIssue = models.QualityIssue


# Create missing classes for backwards compatibility
class CrawlerQualityCheckConfig(BaseModel):
    """Configuration for quality checking in crawler."""

    min_quality_score: float = 0.5
    ignore_low_quality: bool = False
    max_broken_links: int = 10
    check_spelling: bool = False
    check_grammar: bool = False


class CrawlerOrganizationConfig(BaseModel):
    """Configuration for document organization in crawler."""

    skip_organization: bool = False
    organization_delay: float = 0.5
    min_similarity_score: float = 0.3
    max_versions_to_keep: int = 10


__all__ = [
    "CrawlTarget",
    "CrawlConfig",
    "CrawlerQualityCheckConfig",
    "CrawlerOrganizationConfig",
    "Crawler",
    "DocumentationCrawler",
    "CrawlerConfig",
    "CrawlResult",
    "CrawlStats",
    "QualityIssue",
    "BackendSelector",
    "DocumentOrganizer",
    "ContentProcessor",
]
