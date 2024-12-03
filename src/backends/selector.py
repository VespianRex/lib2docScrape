from typing import Dict, Optional, Type
from urllib.parse import urlparse
import logging

from pydantic import BaseModel, field_validator

from .base import CrawlerBackend
from .crawl4ai import Crawl4AIBackend, Crawl4AIConfig
from ..utils.helpers import URLProcessor, URLInfo


class BackendCriteria(BaseModel):
    """Criteria for backend selection."""
    priority: int
    content_types: list[str]
    url_patterns: list[str]
    max_load: float = 0.8
    min_success_rate: float = 0.7
    schemes: list[str] = ['http', 'https', 'file']
    netloc_patterns: list[str] = []
    path_patterns: list[str] = []

    @field_validator('url_patterns')
    def validate_url_patterns(cls, v):
        if not v:
            return ["*"]
        return v

    @field_validator('schemes')
    def validate_schemes(cls, v):
        if not v:
            return ['http', 'https', 'file']
        return v


class BackendSelector:
    """Manages and selects appropriate backends for different crawling tasks."""

    def __init__(self) -> None:
        self.backends: Dict[str, CrawlerBackend] = {}
        self.criteria: Dict[str, BackendCriteria] = {}
        
        # Initialize crawl4ai backend by default
        self._init_default_backend()
    
    def _init_default_backend(self) -> None:
        """Initialize the default crawl4ai backend with high priority."""
        crawl4ai_config = Crawl4AIConfig(
            max_retries=3,
            timeout=30.0,
            headers={
                "User-Agent": "Crawl4AI/1.0 Documentation Crawler"
            },
            follow_redirects=True,
            verify_ssl=True,
            max_depth=5
        )
        
        crawl4ai_backend = Crawl4AIBackend(config=crawl4ai_config)
        crawl4ai_criteria = BackendCriteria(
            priority=100,  # Highest priority
            content_types=["text/html", "application/xhtml+xml"],
            url_patterns=["*"],  # Match all URLs
            max_load=0.9,  # Higher load tolerance
            min_success_rate=0.6,  # More lenient success rate
            schemes=['http', 'https']
        )
        
        self.register_backend(crawl4ai_backend, crawl4ai_criteria)

    def register_backend(
        self,
        backend: CrawlerBackend,
        criteria: BackendCriteria
    ) -> None:
        """
        Register a crawler backend with selection criteria.
        
        Args:
            backend: The crawler backend instance
            criteria: Selection criteria for the backend
            
        Raises:
            ValueError: If backend name is not set or if criteria is invalid
        """
        if not hasattr(backend, 'name') or not backend.name:
            raise ValueError("Backend must have a name")
            
        # Set default schemes if not present
        if not hasattr(backend, 'schemes'):
            backend.schemes = criteria.schemes
            
        # Validate URL patterns
        if not criteria.url_patterns:
            criteria.url_patterns = ["*"]  # Accept all URLs by default
            
        self.backends[backend.name] = backend
        self.criteria[backend.name] = criteria

    def _check_url_pattern(self, url: str, patterns: list[str]) -> bool:
        """
        Check if URL matches any of the given patterns.
        
        Args:
            url: URL to check
            patterns: List of URL patterns to match against
            
        Returns:
            bool indicating if URL matches any pattern
        """
        if "*" in patterns:
            return True
            
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        path = parsed_url.path
        
        for pattern in patterns:
            # Check domain pattern
            if pattern.startswith('domain:'):
                domain_pattern = pattern.split(':', 1)[1]
                if domain_pattern in domain:
                    return True
            # Check path pattern
            elif pattern.startswith('path:'):
                path_pattern = pattern.split(':', 1)[1]
                if path_pattern in path:
                    return True
            # Check wildcard pattern
            elif pattern.endswith('*'):
                prefix = pattern[:-1]
                if url.startswith(prefix):
                    return True
            # Check full URL pattern
            elif pattern in url:
                return True
        return False

    def _evaluate_backend(
        self,
        backend_name: str,
        content_type: str,
        url: str
    ) -> float:
        """
        Evaluate how suitable a backend is for the given request.
        
        Args:
            backend_name: Name of the backend to evaluate
            content_type: Content type of the target
            url: URL to crawl
            
        Returns:
            Float score indicating suitability (0-1)
        """
        backend = self.backends[backend_name]
        criteria = self.criteria[backend_name]
        
        # Start with base score from priority
        score = float(criteria.priority) / 100
        
        # Check content type compatibility
        if content_type in criteria.content_types:
            score += 0.3
        
        # Check URL pattern match
        if self._check_url_pattern(url, criteria.url_patterns):
            score += 0.3
        
        # Check backend health
        metrics = backend.get_metrics()
        if metrics["success_rate"] >= criteria.min_success_rate:
            score += 0.2
        
        # Penalize if backend is under heavy load
        pages_crawled = metrics["pages_crawled"]
        if pages_crawled > 0:
            load_factor = pages_crawled / (pages_crawled + 100)  # Simplified load calculation
            if load_factor > criteria.max_load:
                score -= 0.2
        
        return min(max(score, 0), 1)  # Ensure score is between 0 and 1

    async def select_backend(self, url: str, content_type: Optional[str] = None) -> Optional[CrawlerBackend]:
        """
        Select appropriate backend for URL.
        
        Args:
            url: URL to process
            content_type: Optional content type hint
            
        Returns:
            Selected backend or None if no match
            
        Raises:
            ValueError: If no backends are registered
        """
        if not self.backends:
            raise ValueError("No backends registered")
            
        processor = URLProcessor()
        url_info = processor.process_url(url)
        if not url_info.is_valid:
            return None
            
        for name, backend in self.backends.items():
            try:
                criteria = self.criteria[name]
                if await self._matches_criteria(url_info, criteria):
                    if content_type and content_type not in criteria.content_types:
                        continue
                    return backend
            except Exception as e:
                logging.error(f"Error selecting backend {name}: {str(e)}")
                continue
                
        return None

    def get_all_backends(self) -> Dict[str, CrawlerBackend]:
        """
        Get all registered backends.
        
        Returns:
            Dictionary of registered backends
        """
        return self.backends.copy()

    def get_backend_status(self) -> Dict[str, Dict]:
        """
        Get status of all backends including their metrics and criteria.
        
        Returns:
            Dictionary containing status of all backends
        """
        return {
            name: {
                "metrics": backend.get_metrics(),
                "criteria": self.criteria[name].dict()
            }
            for name, backend in self.backends.items()
        }

    async def _matches_criteria(self, url_info: URLInfo, criteria: BackendCriteria) -> bool:
        """
        Check if URL matches backend criteria.
        
        Args:
            url_info: Normalized URL info
            criteria: Backend selection criteria
            
        Returns:
            True if URL matches criteria, False otherwise
        """
        # Check scheme
        if url_info.scheme not in criteria.schemes:
            return False
            
        # Check URL patterns
        if "*" in criteria.url_patterns:
            return True
            
        if not self._check_url_pattern(url_info.normalized, criteria.url_patterns):
            return False
            
        # Check netloc patterns if specified
        if criteria.netloc_patterns and not any(pattern in url_info.netloc for pattern in criteria.netloc_patterns):
            return False
            
        # Check path patterns if specified
        if criteria.path_patterns and not any(pattern in url_info.path for pattern in criteria.path_patterns):
            return False
            
        return True