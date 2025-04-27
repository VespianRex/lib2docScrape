from typing import Dict, Optional, Type
from urllib.parse import urlparse
import logging

# Set logging level
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from pydantic import BaseModel, field_validator

from .base import CrawlerBackend
from .crawl4ai import Crawl4AIBackend, Crawl4AIConfig
from src.utils.url import URLInfo # Use absolute import path from src root


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
    domains: list[str] = []  # List of domain names to match
    paths: list[str] = []  # List of URL paths to match

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
        # Configure logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
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
    def clear_backends(self) -> None:
        """Clear all registered backends."""
        self.backends = {}
        self.criteria = {}

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
        """
        if "*" in patterns:
            return True

        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        path = parsed_url.path
        normalized_url = url.rstrip('/').lower()  # Normalize and convert to lowercase

        for pattern in patterns:
            try:
                pattern = pattern.lower()  # Case-insensitive matching
                
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
                    if normalized_url.startswith(prefix):
                        return True
                        
                # Check substring pattern (new)
                elif pattern.startswith('contains:'):
                    substring = pattern.split(':', 1)[1]
                    if substring in normalized_url:
                        return True
                        
                # Regular URL pattern matching - now includes substring matching
                else:
                    pattern_norm = pattern.rstrip('/')
                    # Exact match
                    if pattern_norm == normalized_url:
                        return True
                    # Substring match
                    if pattern_norm in normalized_url:
                        return True

            except Exception as e:
                self.logger.error(f"_check_url_pattern: Error matching pattern '{pattern}': {str(e)}")
                # Continue to next pattern on error

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
        self.logger.debug(f"Evaluating backend '{backend_name}' with criteria: {criteria.dict()}")
        
        # Start with base score from priority
        score = float(criteria.priority) / 100  # Priority has more influence

        # Identify backend type
        is_specialized = bool(criteria.domains or criteria.paths or 
                             criteria.netloc_patterns or criteria.path_patterns)
        is_type_specific = criteria.content_types != ["*"]
        # Refined fallback definition
        is_fallback = (
            "*" in criteria.url_patterns and
            not criteria.domains and
            not criteria.paths and
            not criteria.netloc_patterns and
            not criteria.path_patterns and
            criteria.content_types == ["*"]
        )

        # Adjust base score based on backend type
        if is_fallback:
            score = float(criteria.priority) / 1000  # Very low base score for fallbacks
        elif is_specialized:
            score *= 2  # Double score for specialized backends

        # Check content type compatibility
        if content_type:  # Only check content type if one is provided
            supports_requested_type = content_type in criteria.content_types
            supports_wildcard = "*" in criteria.content_types
            is_html_backend = "text/html" in criteria.content_types

            if supports_requested_type:
                score += 0.5  # Large bonus for exact match
            elif supports_wildcard:
                 score += 0.1 # Small bonus for wildcard support
            elif is_type_specific:
                 # Apply penalty, but less harsh for the html 'fallback'
                 penalty = 0.1 if is_html_backend else 0.5
                 score -= penalty
                 self.logger.debug(f"Backend '{backend_name}': Applied penalty {penalty} for content type mismatch (requested: {content_type}, supports: {criteria.content_types})")

        # Handle scoring when no content_type is provided in the request
        elif not content_type:
            # Prefer 'text/html' or wildcard '*' as default
            supports_html = "text/html" in criteria.content_types
            supports_wildcard = "*" in criteria.content_types

            if supports_html:
                score += 0.15 # Bonus for supporting default HTML
            elif supports_wildcard:
                score += 0.1 # Smaller bonus for wildcard
            elif is_type_specific:
                score -= 0.2 # Penalty if backend expects specific types other than html/wildcard

        # Parse URL once
        parsed_url = urlparse(url)
        
        # Check URL pattern match
        matches_pattern = self._check_url_pattern(url, criteria.url_patterns)
        if matches_pattern:
            score += 0.2
        elif criteria.url_patterns != ["*"]:  # Only penalize if backend has specific patterns
            score -= 0.1
        
        # Check domain match with case insensitivity
        if criteria.domains:
            netloc_lower = parsed_url.netloc.lower()
            if any(domain.lower() in netloc_lower for domain in criteria.domains):
                score += 0.2
            elif "*" not in criteria.domains:
                score -= 0.1
                
        # Check path match with improved matching
        if criteria.paths:
            if any(parsed_url.path.startswith(p) for p in criteria.paths):
                score += 0.2
            elif "*" not in criteria.paths:
                score -= 0.1
                
        # Check netloc pattern match
        if criteria.netloc_patterns:
            netloc_lower = parsed_url.netloc.lower()
            if any(pattern.lower() in netloc_lower for pattern in criteria.netloc_patterns):
                score += 0.2
            else:
                score -= 0.1
                
        # Check path pattern match
        if criteria.path_patterns:
            if any(pattern in parsed_url.path for pattern in criteria.path_patterns):
                score += 0.2
            else:
                score -= 0.1
        
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
        
        self.logger.debug(f"Backend '{backend_name}' calculated score: {score}")
        return max(score, 0) # Ensure score is not negative

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
            
        url_info = URLInfo(url)
        self.logger.debug(f"select_backend: Processing URL '{url}'")
        
        if not url_info.is_valid:
            self.logger.debug(f"select_backend: URL is invalid (error: {url_info.error_message})")
            return None
            
        best_backend: Optional[CrawlerBackend] = None
        best_score: float = -1.0

        for name, backend in self.backends.items():
            self.logger.debug(f"Evaluating backend: '{name}'")
            try:
                criteria = self.criteria[name]
                matches = await self._matches_criteria(url_info, criteria)
                self.logger.debug(f"Backend '{name}': Criteria match result: {matches}")

                if matches:
                    score = self._evaluate_backend(name, content_type, url)
                    self.logger.debug(f"Backend '{name}': Score: {score}")

                    if score > best_score:
                        self.logger.debug(f"Backend '{name}': New best score ({score} > {best_score})")
                        best_score = score
                        best_backend = backend
            except Exception as e:
                self.logger.error(f"Error evaluating backend {name}: {str(e)}")
                continue

        if best_backend:
            self.logger.debug(f"Selected backend: {best_backend.name} with score {best_score}")
            return best_backend
        
        self.logger.debug("No suitable backend found")
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
        try:
            # Check if URL is valid
            if not url_info.is_valid:
                return False

            # Always allow fallback backends (those with wildcards and no specific restrictions)
            is_fallback = (
                "*" in criteria.url_patterns and
                not criteria.domains and
                not criteria.paths and
                not criteria.netloc_patterns and
                not criteria.path_patterns and
                criteria.content_types == ["*"]
            )
            if is_fallback:
                return True

            # Check scheme
            if criteria.schemes and url_info.scheme not in criteria.schemes:
                return False

            # Check URL patterns - if not wildcard
            if "*" not in criteria.url_patterns:
                pattern_match = self._check_url_pattern(url_info.normalized_url, criteria.url_patterns)
                if not pattern_match:
                    return False

            # Check domain match
            if criteria.domains:
                domain_match = any(
                    domain.lower() in url_info.netloc.lower()
                    for domain in criteria.domains
                )
                if not domain_match:
                    return False

            # Check path match
            if criteria.paths:
                path_match = any(
                    url_info.path.startswith(p)
                    for p in criteria.paths
                )
                if not path_match:
                    return False

            # Check netloc patterns
            if criteria.netloc_patterns:
                netloc_match = any(
                    pattern.lower() in url_info.netloc.lower()
                    for pattern in criteria.netloc_patterns
                )
                if not netloc_match:
                    return False

            # Check path patterns
            if criteria.path_patterns:
                path_match = any(
                    pattern in url_info.path
                    for pattern in criteria.path_patterns
                )
                if not path_match:
                    return False

            return True
            
        except Exception as e:
            self.logger.error(f"Error checking URL criteria: {str(e)}")
            return False
