from typing import Dict, Optional, Type
from urllib.parse import urlparse
import logging

# Set logging level
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
        # print(f"DEBUG: _check_url_pattern: Checking URL '{url}' against patterns {patterns}") # Removed print

        if "*" in patterns:
            # print("DEBUG: _check_url_pattern: Found wildcard pattern '*', returning True.") # Removed print
            return True

        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        path = parsed_url.path
        normalized_url = url.rstrip('/')  # Remove trailing slash for comparison
        # print(f"DEBUG: _check_url_pattern: Normalized URL: {normalized_url}, Domain: {domain}, Path: {path}") # Removed print

        for pattern in patterns:
            # print(f"DEBUG: _check_url_pattern: Checking against pattern: '{pattern}'") # Removed print
            try:
                # Check domain pattern
                if pattern.startswith('domain:'):
                    domain_pattern = pattern.split(':', 1)[1]
                    match = domain_pattern in domain
                    # print(f"DEBUG: _check_url_pattern: Domain pattern '{domain_pattern}' vs '{domain}' = {match}") # Removed print
                    if match: return True
                # Check path pattern
                elif pattern.startswith('path:'):
                    path_pattern = pattern.split(':', 1)[1]
                    match = path_pattern in path
                    # print(f"DEBUG: _check_url_pattern: Path pattern '{path_pattern}' vs '{path}' = {match}") # Removed print
                    if match: return True
                # Check wildcard pattern
                elif pattern.endswith('*'):
                    prefix = pattern[:-1]
                    match = url.startswith(prefix)
                    # print(f"DEBUG: _check_url_pattern: Wildcard pattern '{prefix}*' vs '{url}' = {match}") # Removed print
                    if match: return True
                # Regular URL pattern matching
                else:
                    pattern_norm = pattern.rstrip('/')
                    url_norm = normalized_url # Already normalized
                    match = (pattern_norm == url_norm)
                    # print(f"DEBUG: _check_url_pattern: Exact match pattern '{pattern_norm}' vs '{url_norm}' = {match}") # Removed print
                    if match: return True

                    # Prefix match check (if needed in future)
                    # prefix_match = url_norm.startswith(pattern_norm)
                    # print(f"DEBUG: _check_url_pattern: Prefix match pattern '{pattern_norm}' vs '{url_norm}' = {prefix_match}") # Removed print
                    # if prefix_match: return True

            except Exception as e:
                self.logger.error(f"_check_url_pattern: Error matching pattern '{pattern}': {str(e)}") # Kept logger for errors
                # Continue to next pattern on error

        # print(f"DEBUG: _check_url_pattern: No patterns matched for URL '{url}'. Returning False.") # Removed print
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
        score = float(criteria.priority) / 100  # Priority has more influence
        
        # Calculate initial score based on priority
        score = float(criteria.priority) / 100

        # Identify backend type
        is_specialized = bool(criteria.domains or criteria.paths)
        is_type_specific = criteria.content_types != ["*"]
        # Refined fallback definition
        is_fallback = (
            "*" in criteria.url_patterns and
            not criteria.domains and
            not criteria.paths and
            criteria.content_types == ["*"] # Explicitly check for wildcard content types
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
            is_html_backend = "text/html" in criteria.content_types # Check if it's the 'fallback' type for this test

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
        elif not content_type: # Handle scoring when no content_type is provided
            # Prefer 'text/html' or wildcard '*' as default
            supports_html = "text/html" in criteria.content_types
            supports_wildcard = "*" in criteria.content_types

            if supports_html:
                score += 0.15 # Bonus for supporting default HTML
            elif supports_wildcard:
                score += 0.1 # Smaller bonus for wildcard
            elif is_type_specific: # Penalize if specific types are required but none match default
                score -= 0.2 # Penalty if backend expects specific types other than html/wildcard

        # Parse URL once
        parsed_url = urlparse(url)
        
        # Check URL pattern match
        matches_pattern = self._check_url_pattern(url, criteria.url_patterns)
        if matches_pattern:
            score += 0.2
        elif criteria.url_patterns != ["*"]:  # Only penalize if backend has specific patterns
            score -= 0.1
        
        # Check domain match - more lenient for fallback backends
        if criteria.domains:
            if parsed_url.netloc in criteria.domains:
                score += 0.2
            elif "*" not in criteria.domains:  # Only penalize if not a wildcard domain
                score -= 0.1
                
        # Check path match - more lenient scoring
        if criteria.paths:
            if any(parsed_url.path.startswith(p) for p in criteria.paths):
                score += 0.2
            elif "*" not in criteria.paths:  # Only penalize if not a wildcard path
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
        
        logging.debug(f"Backend {backend_name} score: {score}") # Debug log
        return min(max(score, 0), 1)  # Ensure score is between 0 and 1

    async def select_backend(self, url: str, content_type: Optional[str] = None) -> Optional[CrawlerBackend]:
        """
        Select appropriate backend for URL.
        """
        """
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
        print(f"DEBUG: select_backend: url_info for '{url}': {url_info}") # Added print back
        if not url_info.is_valid:
            print(f"DEBUG: select_backend: url_info is invalid (error: {url_info.error_msg}), returning None.") # Added print back
            return None
            
        best_backend: Optional[CrawlerBackend] = None
        best_score: float = -1.0

        for name, backend in self.backends.items():
            try:
                criteria = self.criteria[name]
                matches = await self._matches_criteria(url_info, criteria) # Store result
                self.logger.debug(f"Backend '{name}': _matches_criteria result: {matches}") # Log result

                if matches: # Use stored result
                    # Original simpler check: Only skip if content_type is given and doesn't match specific backend types
                    # Content type matching is handled by the scoring function (_evaluate_backend)
                    # No need for explicit filtering here anymore.

                    score = self._evaluate_backend(name, content_type, url)
                    self.logger.debug(f"Backend '{name}': Calculated score: {score}") # Log score

                    if score > best_score:
                        self.logger.debug(f"Backend '{name}': New best score ({score} > {best_score}). Selecting.")
                        best_score = score
                        best_backend = backend
                    else:
                        self.logger.debug(f"Backend '{name}': Score {score} not better than best score {best_score}.")
            except Exception as e:
                logging.error(f"Error selecting backend {name}: {str(e)}")
                continue

        if best_backend:
            logging.debug(f"Best backend selected: {best_backend.name}") # Debug log
            return best_backend
        
        logging.debug("No backend selected.") # Debug log
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
        # print(f"DEBUG: _matches_criteria: Checking URL '{url_info.normalized}' against criteria: {criteria.dict()}") # Removed print

        # Always allow fallback backends (those with wildcards and no specific restrictions)
        is_fallback = (
            "*" in criteria.url_patterns and
            not criteria.domains and
            not criteria.paths and
            not criteria.netloc_patterns and
            not criteria.path_patterns and
            criteria.content_types == ["*"] # Assuming ["*"] means all types
        )
        if is_fallback:
            # print("DEBUG: _matches_criteria: Backend is fallback, returning True.") # Removed print
            return True

        # Check scheme
        scheme_match = url_info.scheme in criteria.schemes
        # print(f"DEBUG: _matches_criteria: Scheme check: '{url_info.scheme}' in {criteria.schemes} = {scheme_match}") # Removed print
        if not scheme_match:
            return False

        # Check URL patterns - if not wildcard
        if "*" not in criteria.url_patterns:
            pattern_match = self._check_url_pattern(url_info.normalized_url, criteria.url_patterns)
            # print(f"DEBUG: _matches_criteria: URL pattern check result: {pattern_match}") # Removed print
            if not pattern_match:
                return False
        else:
             # print("DEBUG: _matches_criteria: URL pattern is wildcard ('*'), skipping specific pattern check.") # Removed print
             pass # Explicitly do nothing if wildcard


        # Check domain match
        if criteria.domains:
            domain_match = url_info.netloc in criteria.domains
            # print(f"DEBUG: _matches_criteria: Domain check: '{url_info.netloc}' in {criteria.domains} = {domain_match}") # Removed print
            if not domain_match:
                return False
        else:
            # print("DEBUG: _matches_criteria: No specific domains in criteria, skipping domain check.") # Removed print
            pass # Explicitly do nothing if no domains

        # Check path match
        if criteria.paths:
            path_match = any(url_info.path.startswith(p) for p in criteria.paths)
            # print(f"DEBUG: _matches_criteria: Path check: '{url_info.path}' starts with any of {criteria.paths} = {path_match}") # Removed print
            if not path_match:
                return False
        else:
            # print("DEBUG: _matches_criteria: No specific paths in criteria, skipping path check.") # Removed print
            pass # Explicitly do nothing if no paths

        # print(f"DEBUG: _matches_criteria: All checks passed for URL '{url_info.normalized}'. Returning True.") # Removed print
        return True