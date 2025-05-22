"""
Shared model definitions for the lib2docScrape crawler module.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from pydantic import BaseModel, Field

class CrawlTarget(BaseModel):
    """Model for a crawl target."""
    url: str
    depth: int = 1
    follow_external: bool = False
    content_types: List[str] = Field(default_factory=lambda: ["text/html"])
    exclude_patterns: List[str] = Field(default_factory=list)
    include_patterns: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    max_pages: int = 1000  # Added
    allowed_paths: List[str] = Field(default_factory=list)  # Added
    excluded_paths: List[str] = Field(default_factory=list)  # Added

class CrawlConfig(BaseModel):
    """Configuration for crawling."""
    max_depth: int = 3
    max_pages: int = 1000
    follow_external: bool = False
    content_types: List[str] = Field(default_factory=lambda: ["text/html"])
    exclude_patterns: List[str] = Field(default_factory=list)
    include_patterns: List[str] = Field(default_factory=list)
    rate_limit: float = 0.5  # seconds between requests
    timeout: int = 30  # seconds
    retry_count: int = 3
    user_agent: str = "lib2docScrape/1.0"

class CrawlStats(BaseModel):
    """Model for crawl statistics."""
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    pages_crawled: int = 0
    successful_crawls: int = 0
    failed_crawls: int = 0
    total_time: float = 0.0
    average_time_per_page: float = 0.0
    quality_issues: int = 0
    bytes_processed: int = 0

class QualityIssue(BaseModel):
    """Model for a quality issue."""
    type: str
    level: str
    message: str
    location: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)

class CrawlResult(BaseModel):
    """Model for crawl results."""
    target: CrawlTarget
    stats: CrawlStats
    documents: List[Dict[str, Any]] = Field(default_factory=list)  # Store documents as dicts
    issues: List[QualityIssue] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    structure: Optional[List[Dict[str, Any]]] = None  # Hold structure for link discovery
    processed_url: Optional[str] = None  # Store the final URL after redirects/normalization
    failed_urls: List[str] = Field(default_factory=list)  # URLs that failed to crawl
    errors: Dict[str, Any] = Field(default_factory=dict)  # Map of URLs to their exceptions
    crawled_pages: Dict[str, Any] = Field(default_factory=dict)  # Map of URLs to page metadata
