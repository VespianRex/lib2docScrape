import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from urllib.parse import urljoin, urlparse
import collections # Import collections for deque

from pydantic import BaseModel, Field
import aiohttp

from .backends.base import CrawlerBackend, CrawlResult as BackendCrawlResult # Rename to avoid clash
from .backends.selector import BackendSelector, BackendCriteria
# from .backends.http import HTTPBackend, HTTPBackendConfig # http.py is deleted
from .backends.http_backend import HTTPBackend, HTTPBackendConfig # Use http_backend.py
from .organizers.doc_organizer import DocumentOrganizer
from .processors.content_processor import ContentProcessor, ProcessedContent
from .processors.quality_checker import QualityChecker, QualityIssue, IssueType, IssueLevel # Added IssueType, IssueLevel
from .utils.helpers import (
    RateLimiter, RetryStrategy, Timer # Removed URLInfo, URLProcessor
)
# Import the correct URLInfo and sanitize function
from .utils.url import URLInfo # Corrected import path for modular URLInfo
from .processors.content.url_handler import sanitize_and_join_url

from enum import Enum
from dataclasses import dataclass
import re
import itertools

try:
    from duckduckgo_search import DDGS
    DUCKDUCKGO_AVAILABLE = True
except ImportError:
    DUCKDUCKGO_AVAILABLE = False
    logging.warning("DuckDuckGo search functionality not available. Install with: pip install duckduckgo-search")

class ProjectType(Enum):
    """Types of software projects that can be identified."""
    PACKAGE = "package"
    FRAMEWORK = "framework"
    PROGRAM = "program"
    LIBRARY = "library"
    CLI_TOOL = "cli_tool"
    WEB_APP = "web_app"
    API = "api"
    UNKNOWN = "unknown"

@dataclass
class ProjectIdentity:
    """Information about an identified project."""
    name: str
    type: ProjectType
    language: Optional[str] = None
    framework: Optional[str] = None
    repository: Optional[str] = None
    package_manager: Optional[str] = None
    main_doc_url: Optional[str] = None
    related_keywords: List[str] = None
    confidence: float = 0.0

    def __post_init__(self):
        if self.related_keywords is None:
            self.related_keywords = []

class ProjectIdentifier:
    """Identifies project type and provides relevant configuration."""

    def __init__(self):
        self.package_doc_urls = {}
        self.fallback_urls = {}

        # Common documentation patterns
        self.doc_patterns = [
            "https://{package}.readthedocs.io/en/latest/",
            "https://{package}.readthedocs.io/en/stable/",
            "https://docs.{package}.org/",
            "https://{package}.org/docs/",
            "https://www.{package}.org/docs/",
            "https://github.com/{package}/{package}/blob/main/README.md"
        ]

        self.language_patterns = {
            'python': [r'\.py$', r'requirements\.txt$', r'setup\.py$', r'pyproject\.toml$'],
            'javascript': [r'\.js$', r'package\.json$', r'node_modules'],
            'java': [r'\.java$', r'pom\.xml$', r'build\.gradle$'],
            'ruby': [r'\.rb$', r'Gemfile$'],
            'go': [r'\.go$', r'go\.mod$'],
            'rust': [r'\.rs$', r'Cargo\.toml$'],
            'php': [r'\.php$', r'composer\.json$'],
        }

        self.framework_patterns = {
            'django': [r'django', r'urls\.py$', r'wsgi\.py$'],
            'flask': [r'flask', r'app\.py$'],
            'react': [r'react', r'jsx$', r'tsx$'],
            'angular': [r'angular', r'component\.ts$'],
            'vue': [r'vue', r'vue-cli'],
            'spring': [r'spring-boot', r'springframework'],
            'rails': [r'rails', r'activerecord'],
        }

        self.doc_platforms = {
            'readthedocs.org': 0.9,
            'docs.python.org': 0.9,
            'developer.mozilla.org': 0.8,
            'docs.microsoft.com': 0.8,
            'docs.oracle.com': 0.8,
            'pkg.go.dev': 0.8,
            'docs.rs': 0.8,
            'hexdocs.pm': 0.8,
            'rubydoc.info': 0.8,
            'godoc.org': 0.8,
        }

        self.package_managers = {
            'python': ['pip', 'conda', 'poetry'],
            'javascript': ['npm', 'yarn', 'pnpm'],
            'java': ['maven', 'gradle'],
            'ruby': ['gem', 'bundler'],
            'php': ['composer'],
            'rust': ['cargo'],
            'go': ['go get'],
        }

    async def discover_doc_url(self, package_name: str) -> Optional[str]:
        """Dynamically discover documentation URL for a package."""
        try:
            # Try PyPI API first
            async with aiohttp.ClientSession() as session:
                pypi_url = f"https://pypi.org/pypi/{package_name}/json"
                async with session.get(pypi_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'info' in data:
                            # Check various documentation fields
                            for field in ['documentation_url', 'project_urls', 'home_page']:
                                if field in data['info'] and data['info'][field]:
                                    if field == 'project_urls':
                                        # Look for documentation-related URLs
                                        for key, url in data['info'][field].items():
                                            if any(doc_term in key.lower() for doc_term in ['doc', 'wiki', 'guide']):
                                                return url
                                    else:
                                        return data['info'][field]

            # Try common documentation patterns
            for pattern in self.doc_patterns:
                url = pattern.format(package=package_name.lower())
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.head(url, allow_redirects=True) as response:
                            if response.status == 200:
                                return url
                except:
                    continue

            return None

        except Exception as e:
            logging.error(f"Error discovering documentation URL for {package_name}: {str(e)}")
            return None

    def add_doc_url(self, package_name: str, url: str) -> None:
        """Add or update a package documentation URL."""
        self.package_doc_urls[package_name] = url

    def add_fallback_url(self, package_name: str, url: str) -> None:
        """Add or update a fallback URL for a package."""
        self.fallback_urls[package_name] = url

    async def identify_from_url(self, url: str) -> ProjectIdentity:
        """Identify project type from a URL."""
        confidence = 0.0
        project_type = ProjectType.UNKNOWN
        language = None
        framework = None

        # Check if it's a known documentation platform
        for platform, conf in self.doc_platforms.items():
            if platform in url:
                confidence = max(confidence, conf)
                break

        # Extract potential project name from URL
        name = self._extract_name_from_url(url)

        # Identify language from URL patterns
        for lang, patterns in self.language_patterns.items():
            if any(re.search(pattern, url, re.I) for pattern in patterns):
                language = lang
                confidence = max(confidence, 0.7)
                break

        # Identify framework from URL patterns
        for fw, patterns in self.framework_patterns.items():
            if any(re.search(pattern, url, re.I) for pattern in patterns):
                framework = fw
                project_type = ProjectType.FRAMEWORK
                confidence = max(confidence, 0.8)
                break

        return ProjectIdentity(
            name=name,
            type=project_type,
            language=language,
            framework=framework,
            confidence=confidence
        )

    async def identify_from_content(self, content: str) -> ProjectIdentity:
        """Identify project type from content."""
        # Initialize counters for different project types
        type_scores = {
            ProjectType.PACKAGE: 0,
            ProjectType.FRAMEWORK: 0,
            ProjectType.PROGRAM: 0,
            ProjectType.LIBRARY: 0,
            ProjectType.CLI_TOOL: 0,
            ProjectType.WEB_APP: 0,
            ProjectType.API: 0,
        }

        # Keywords associated with different project types
        type_keywords = {
            ProjectType.PACKAGE: ['import', 'require', 'dependency', 'module'],
            ProjectType.FRAMEWORK: ['framework', 'middleware', 'plugin', 'extension'],
            ProjectType.PROGRAM: ['executable', 'binary', 'command-line', 'CLI'],
            ProjectType.LIBRARY: ['library', 'SDK', 'toolkit', 'API'],
            ProjectType.CLI_TOOL: ['command', 'terminal', 'shell', 'console'],
            ProjectType.WEB_APP: ['webapp', 'website', 'frontend', 'backend'],
            ProjectType.API: ['API', 'REST', 'GraphQL', 'endpoint'],
        }

        # Score content based on keywords
        for project_type, keywords in type_keywords.items():
            score = sum(1 for keyword in keywords if re.search(rf'\b{keyword}\b', content, re.I))
            type_scores[project_type] = score

        # Get the project type with highest score
        project_type = max(type_scores.items(), key=lambda x: x[1])[0]
        if type_scores[project_type] == 0:
            project_type = ProjectType.UNKNOWN

        # Extract potential name from content
        name = self._extract_name_from_content(content)

        # Calculate confidence based on keyword matches
        max_score = max(type_scores.values())
        total_matches = sum(type_scores.values())
        confidence = max_score / (total_matches + 1) if total_matches > 0 else 0.0

        return ProjectIdentity(
            name=name,
            type=project_type,
            confidence=confidence
        )

    def _extract_name_from_url(self, url: str) -> str:
        """Extract potential project name from URL."""
        # Remove common prefixes and suffixes
        url = re.sub(r'^https?://(www\.)?', '', url)
        url = re.sub(r'\.html?$', '', url)

        # Try to extract name from common documentation URLs
        doc_patterns = [
            r'([^/]+)\.readthedocs\.org',
            r'docs\.([^/]+)\.org',
            r'/([^/]+)/docs?/',
            r'/projects?/([^/]+)',
            r'/packages?/([^/]+)',
        ]

        for pattern in doc_patterns:
            match = re.search(pattern, url, re.I)
            if match:
                return match.group(1)

        # Fall back to last meaningful URL segment
        segments = [s for s in url.split('/') if s and not s.startswith('?')]
        return segments[-1] if segments else "unknown"

    def _extract_name_from_content(self, content: str) -> str:
        """Extract potential project name from content."""
        # Look for common project name indicators
        patterns = [
            r'<title>([^<]+)</title>',
            r'# ([^\n]+)',
            r'== ([^=]+) ==',
            r'project["\']\s*:\s*["\']([^"\']+)',
            r'name["\']\s*:\s*["\']([^"\']+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                name = match.group(1).strip()
                # Clean up common suffixes
                name = re.sub(r'\s*(-|–|—)\s*(documentation|docs|manual|guide)$', '', name, flags=re.I)
                return name

        return "unknown"

class CrawlTarget(BaseModel):
    """Model for crawl target configuration."""
    url: str = "https://docs.python.org/3/"  # Default to Python docs
    depth: int = 1
    follow_external: bool = False
    content_types: List[str] = ["text/html"]
    exclude_patterns: List[str] = []
    required_patterns: List[str] = ["/3/"]  # Only crawl Python 3 docs
    max_pages: Optional[int] = None
    allowed_paths: List[str] = []
    excluded_paths: List[str] = []

class CrawlStats(BaseModel):
    """Model for crawl statistics."""
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    pages_crawled: int = 0
    successful_crawls: int = 0
    failed_crawls: int = 0
    total_time: float = 0.0
    average_time_per_page: float = 0.0
    quality_issues: int = 0
    bytes_processed: int = 0


class CrawlResult(BaseModel):
    """Model for crawl results."""
    target: CrawlTarget
    stats: CrawlStats
    documents: List[Dict[str, Any]]  # Changed from List[str] to store dicts
    issues: List[QualityIssue]
    metrics: Dict[str, Any]  # Removed QualityMetrics dependency
    structure: Optional[List[Dict[str, Any]]] = None # Added to hold structure for link discovery
    processed_url: Optional[str] = None # Added to store the final URL processed (after redirects, normalization)
    failed_urls: List[str] = Field(default_factory=list)  # List of URLs that failed to crawl
    errors: Dict[str, Exception] = Field(default_factory=dict)  # Map of URLs to their exceptions
    crawled_pages: Dict[str, Any] = Field(default_factory=dict)  # Dictionary of crawled pages
    
    model_config = {
        "arbitrary_types_allowed": True  # Allow arbitrary types like Exception
    }


class CrawlerConfig(BaseModel):
    """Configuration for the crawler."""
    concurrent_requests: int = 10
    requests_per_second: float = 5.0
    max_retries: int = 3
    request_timeout: float = 30.0
    respect_robots_txt: bool = True
    follow_redirects: bool = True
    verify_ssl: bool = True
    user_agent: str = "Python Documentation Scraper/1.0"
    headers: Dict[str, str] = Field(default_factory=dict)
    use_duckduckgo: bool = True
    duckduckgo_max_results: int = 10
    batch_size: int = 5 # Kept for potential future use, but not used in current crawl logic


class DuckDuckGoSearch:
    """DuckDuckGo search integration."""

    def __init__(self, max_results: int = 10):
        self.max_results = max_results
        self._ddgs = DDGS() if DUCKDUCKGO_AVAILABLE else None

    async def search(self, query: str) -> List[str]:
        """Search DuckDuckGo for documentation URLs."""
        if not DUCKDUCKGO_AVAILABLE:
            logging.warning("DuckDuckGo search not available. Install duckduckgo-search package.")
            return []

        try:
            # Focus search on documentation sites
            search_query = f"{query} site:readthedocs.org OR site:docs.python.org OR site:rtfd.io OR site:pythonhosted.org"

            # Use DuckDuckGo API to search
            results = []
            # Use async version if available, otherwise sync in executor (simplified for now)
            # Note: DDGS().text is sync, consider running in executor for async context
            # For simplicity here, we run it synchronously within the async function
            # A better approach would use asyncio.to_thread in Python 3.9+
            sync_results = self._ddgs.text(search_query, max_results=self.max_results)
            for r in sync_results:
                if r.get('href'): # DDGS uses 'href' now
                    url = r['href']
                    # Verify it's a documentation URL
                    if any(domain in url.lower() for domain in [
                        'readthedocs.org', 'docs.python.org', 'rtfd.io',
                        'pythonhosted.org', '.readthedocs.io'
                    ]):
                        results.append(url)

            return results[:self.max_results]

        except Exception as e:
            logging.error(f"DuckDuckGo search error: {str(e)}")
            return []

    async def close(self):
        """Close the search session."""
        pass  # No cleanup needed for DDGS


class DocumentationCrawler:
    """Main crawler orchestrator."""

    def __init__(
        self,
        config: Optional[CrawlerConfig] = None,
        backend_selector: Optional[BackendSelector] = None,
        content_processor: Optional[ContentProcessor] = None,
        quality_checker: Optional[QualityChecker] = None,
        document_organizer: Optional[DocumentOrganizer] = None,
        backend: Optional[CrawlerBackend] = None
    ) -> None:
        """Initialize the documentation crawler.
        
        Args:
            config: Optional crawler configuration
            backend_selector: Optional backend selector for choosing appropriate backends
            content_processor: Optional content processor for processing crawled content
            quality_checker: Optional quality checker for checking content quality
            document_organizer: Optional document organizer for organizing crawled content
            backend: Optional specific backend to use instead of using the selector
        """
        self.config = config or CrawlerConfig()
        logging.debug(f"Crawler __init__ received backend_selector: id={id(backend_selector)}")
        if backend_selector:
             logging.debug(f"Received selector initial backends: {list(backend_selector.backends.keys())}")
        self.backend_selector = backend_selector or BackendSelector()
        self.content_processor = content_processor or ContentProcessor()
        self.quality_checker = quality_checker or QualityChecker()
        self.document_organizer = document_organizer or DocumentOrganizer()
        
        # If a specific backend is provided, use it directly
        self.direct_backend = backend
        # Also set self.backend for direct access in tests
        self.backend = backend
        logging.debug(f"Direct backend provided: {backend is not None}")
        
        logging.debug(f"Crawler assigned self.backend_selector: id={id(self.backend_selector)}")
        logging.debug(f"Assigned selector backends BEFORE http registration: {list(self.backend_selector.backends.keys())}")


        # Set up HTTP backend
        http_backend = HTTPBackend(
            HTTPBackendConfig(
                timeout=self.config.request_timeout,
                verify_ssl=self.config.verify_ssl,
                follow_redirects=self.config.follow_redirects,
                headers={"User-Agent": self.config.user_agent}
            )
        )

        # Register HTTP backend with criteria
        self.backend_selector.register_backend(
            http_backend,
            BackendCriteria(
                priority=1,
                content_types=["text/html"],
                url_patterns=["http://", "https://"],  # Match all HTTP(S) URLs
                max_load=0.8,
                min_success_rate=0.7
            )
        )
        logging.debug(f"Assigned selector backends AFTER http registration: {list(self.backend_selector.backends.keys())}")

        self.rate_limiter = RateLimiter(self.config.requests_per_second)
        self.retry_strategy = RetryStrategy(
            max_retries=self.config.max_retries
        ) # Corrected closing parenthesis

        self._crawled_urls: Set[str] = set() # Store normalized URLs
        self._processing_semaphore = asyncio.Semaphore(
            self.config.concurrent_requests
        )
        self.client_session = None # Session managed by HTTPBackend now

        self.duckduckgo = DuckDuckGoSearch(self.config.duckduckgo_max_results) if self.config.use_duckduckgo else None
        # self.crawl_tree = {} # Removed, not used in new logic
        # self.current_tasks = set() # Removed, managed by asyncio.gather
        self.project_identifier = ProjectIdentifier()

    def _find_links_recursive(self, structure_element) -> List[str]:
        """Recursively find all 'href' values from link elements in the structure."""
        links = []
        if isinstance(structure_element, dict):
            # Check if the current element itself is a link
            if structure_element.get('type') in ['link', 'link_inline'] and structure_element.get('href'):
                links.append(structure_element['href'])
            # Recursively check values that are lists or dicts
            for value in structure_element.values():
                if isinstance(value, (dict, list)):
                    links.extend(self._find_links_recursive(value))
        elif isinstance(structure_element, list):
            # Recursively check items in the list
            for item in structure_element:
                links.extend(self._find_links_recursive(item))
        return links

    def _should_crawl_url(self, url_info: URLInfo, target: CrawlTarget) -> bool:
        """Check if a URL should be crawled based on target rules."""
        if not url_info.is_valid:
            logging.debug(f"Skipping invalid URL: {url_info.raw_url} ({url_info.error_message})")
            return False

        normalized_url = url_info.normalized_url

        # Check if already crawled
        if normalized_url in self._crawled_urls:
            logging.debug(f"Skipping already crawled URL: {normalized_url}")
            return False

        # Check scheme
        if url_info.scheme not in ['http', 'https', 'file']:
            logging.debug(f"Skipping non-HTTP/S/file URL: {normalized_url}")
            return False

        # Check external domains (only for http/https, not for file)
        if not target.follow_external and url_info.scheme in ['http', 'https']:
            # Use URLInfo's netloc attribute
            if url_info.netloc != urlparse(target.url).netloc.lower():
                 logging.debug(f"Skipping external domain: {url_info.netloc} (target: {urlparse(target.url).netloc.lower()})")
                 return False

        # Check exclude patterns
        if any(re.search(pattern, normalized_url) for pattern in target.exclude_patterns):
            logging.debug(f"Skipping URL due to exclude pattern: {normalized_url}")
            return False

        # Check required patterns (if any)
        if target.required_patterns and not any(re.search(pattern, normalized_url) for pattern in target.required_patterns):
            logging.debug(f"Skipping URL due to missing required pattern: {normalized_url}")
            return False

        # Check allowed paths (if any)
        if target.allowed_paths:
            path = url_info.path
            if not any(path.startswith(allowed) for allowed in target.allowed_paths):
                logging.debug(f"Skipping URL due to not being in allowed paths: {normalized_url}")
                return False

        # Check excluded paths (if any)
        if target.excluded_paths:
            path = url_info.path
            if any(path.startswith(excluded) for excluded in target.excluded_paths):
                logging.debug(f"Skipping URL due to being in excluded paths: {normalized_url}")
                return False

        return True

    async def _process_url(
        self,
        url: str,
        current_depth: int,
        target: CrawlTarget,
        stats: CrawlStats,
        visited_urls: Set[str]
    ) -> Tuple[Optional[CrawlResult], List[Tuple[str, int]], Dict[str, Any]]:
        """Process a single URL, returning its result and discovered links."""
        new_links_to_crawl = []
        crawl_result_data = None
        quality_metrics = {} # Initialize quality metrics
        normalized_url = url # Default if URLInfo fails

        try:
            # Normalize URL early and check if visited
            url_info = URLInfo(url, base_url=target.url) # Use target.url as base for initial URLInfo
            normalized_url = url_info.normalized_url
            if not url_info.is_valid or normalized_url in visited_urls:
                logging.debug(f"Skipping invalid/visited URL: {url} (Normalized: {normalized_url})")
                return None, [], {} # Return None result, no new links, empty metrics

            logging.info(f"Processing URL: {normalized_url} (Depth: {current_depth})")
            visited_urls.add(normalized_url) # Add normalized URL to visited set

            # Handle file:// URLs differently
            if url_info.scheme == 'file':
                return await self._process_file_url(url_info, current_depth, target, stats)

            # Get backend for this URL
            # Prioritize direct backend if provided (e.g., for testing)
            if self.direct_backend:
                backend = self.direct_backend
                logging.debug(f"Using direct backend: {backend.name}")
            else:
                backend = await self.backend_selector.select_backend(normalized_url)
                if backend:
                     logging.debug(f"Selected backend via selector: {backend.name}")

            if not backend:
                logging.error(f"No suitable backend found for URL: {normalized_url}")
                stats.failed_crawls += 1
                # Create a minimal CrawlResult for failure reporting
                crawl_result_data = CrawlResult(
                    target=target, stats=stats, documents=[], issues=[QualityIssue(type=IssueType.GENERAL, level=IssueLevel.ERROR, message=f"No backend for {normalized_url}")], metrics={}, processed_url=normalized_url, failed_urls=[normalized_url], errors={normalized_url: Exception("No suitable backend")} # Use GENERAL type
                )
                return crawl_result_data, [], {}

            # Process with retry strategy
            processed_content: Optional[ProcessedContent] = None
            last_error = None
            backend_result: Optional[BackendCrawlResult] = None

            for attempt in range(self.config.max_retries):
                try:
                    logging.debug(f"Attempt {attempt + 1}/{self.config.max_retries} for {normalized_url}")
                    # Apply rate limiting - prioritize backend's external limiter if it exists and is not None
                    limiter_to_use = None
                    if hasattr(backend, '_external_rate_limiter'):
                        backend_limiter = getattr(backend, '_external_rate_limiter', None)
                        if backend_limiter is not None:
                            limiter_to_use = backend_limiter
                            
                    if limiter_to_use is None:
                        limiter_to_use = self.rate_limiter # Fallback to crawler's limiter

                    wait_time = await limiter_to_use.acquire()
                    # Ensure wait_time is a float before comparison
                    if isinstance(wait_time, (int, float)) and wait_time > 0:
                        logging.debug(f"Rate limit hit for {normalized_url}, sleeping for {wait_time:.4f}s (using {'backend' if limiter_to_use is not self.rate_limiter else 'crawler'} limiter)")
                        await asyncio.sleep(wait_time)
                    elif not isinstance(wait_time, (int, float)):
                         logging.warning(f"Rate limiter acquire() returned non-numeric value: {type(wait_time)}. Skipping sleep.")


                    async with self._processing_semaphore:
                        # Pass the crawler's config to the backend crawl method
                        backend_result = await backend.crawl(url=normalized_url) # Pass url only

                        if not backend_result or backend_result.status != 200:
                            logging.warning(f"Attempt {attempt + 1} failed for {normalized_url}: Status {backend_result.status if backend_result else 'N/A'}, Error: {backend_result.error if backend_result else 'Unknown'}")
                            last_error = Exception(f"Status {backend_result.status if backend_result else 'N/A'}: {backend_result.error if backend_result else 'Fetch error'}")
                            if attempt < self.config.max_retries - 1:
                                delay = self.retry_strategy.get_delay(attempt + 1)
                                await asyncio.sleep(delay)
                            continue # Retry

                        # Process the content (assuming success)
                        # Use the URL from the backend result, as it might have changed due to redirects
                        final_url_processed = backend_result.url or normalized_url
                        final_url_info = URLInfo(final_url_processed, base_url=target.url) # Re-evaluate URL info after potential redirects
                        normalized_final_url = final_url_info.normalized_url

                        # Re-check if the final URL was already visited (due to redirects)
                        if normalized_final_url in visited_urls and normalized_final_url != normalized_url:
                             logging.debug(f"Skipping redirected URL already visited: {final_url_processed} (Normalized: {normalized_final_url})")
                             return None, [], {} # Already visited via redirect

                        # Add final URL to visited if different from initial normalized
                        if normalized_final_url != normalized_url:
                             visited_urls.add(normalized_final_url)

                        # Check content type if backend provides it
                        # Case-insensitive header lookup
                        headers_dict = backend_result.metadata.get('headers', {})
                        content_type_val = ''
                        for key, value in headers_dict.items():
                            if key.lower() == 'content-type':
                                content_type_val = value
                                break
                        content_type = content_type_val.lower()
                        if not any(ct in content_type for ct in target.content_types):
                             logging.debug(f"Skipping URL {final_url_processed} due to non-allowed content type: {content_type}")
                             return None, [], {} # Skip non-HTML content

                        # Process content using ContentProcessor
                        processed_content = await self.content_processor.process(backend_result.content.get('html', ''), base_url=final_url_processed) # Add await back, process is now async

                        stats.successful_crawls += 1
                        stats.pages_crawled += 1 # Increment pages crawled on success
                        stats.bytes_processed += len(backend_result.content.get('html', '')) # Use content['html']
                        last_error = None # Reset last error on success
                        break # Successful processing, exit retry loop

                except Exception as e:
                    last_error = e
                    logging.error(f"Error during attempt {attempt + 1} for {normalized_url}: {str(e)}")
                    if attempt < self.config.max_retries - 1:
                        delay = self.retry_strategy.get_delay(attempt + 1)
                        await asyncio.sleep(delay)
                    # Continue to next retry or fail after loop

            # After retry loop
            if last_error:
                stats.failed_crawls += 1
                logging.error(f"Processing failed for {normalized_url} after {self.config.max_retries} attempts: {str(last_error)}")
                # Include exception type name in the message
                error_type_name = type(last_error).__name__
                error_str = str(last_error)
                # Corrected message format
                issue_message = f"Failed after retries: {error_type_name}({error_str})"

                crawl_result_data = CrawlResult(
                    target=target, 
                    stats=stats, 
                    documents=[], 
                    issues=[QualityIssue(url=normalized_url, type=IssueType.GENERAL, level=IssueLevel.ERROR, message=issue_message)], # Use GENERAL for all processing errors
                    metrics={}, 
                    processed_url=normalized_url,
                    failed_urls=[normalized_url],
                    errors={normalized_url: last_error}
                )
                return crawl_result_data, [], {} # Return failure result

            # If loop completed successfully (processed_content is not None)
            if processed_content:
                # Perform quality check *after* successful processing
                if self.quality_checker:
                    quality_issues, quality_metrics = await self.quality_checker.check_quality(processed_content)
                else:
                    quality_issues, quality_metrics = [], {}

                # Prepare successful result data
                crawl_result_data = CrawlResult(
                    target=target,
                    stats=stats,
                    documents=[{
                        'url': normalized_final_url, # Use the final normalized URL
                        'content': processed_content.content,
                        'metadata': processed_content.metadata,
                        'assets': processed_content.assets,
                        'title': processed_content.title
                    }],
                    issues=quality_issues, # Assign the unpacked issues list
                    metrics=quality_metrics, # Assign the unpacked metrics dict
                    structure=processed_content.structure, # Use the top-level structure attribute
                    processed_url=normalized_final_url
                )
                stats.quality_issues += len(crawl_result_data.issues)

                # Extract new links if depth allows
                logging.debug(f"Checking links for depth {current_depth} (target depth: {target.depth})")
                if current_depth < target.depth:
                    # Use the recursive helper to find all hrefs
                    found_hrefs = self._find_links_recursive(processed_content.structure)
                    logging.debug(f"Found {len(found_hrefs)} potential links: {found_hrefs}")
                    for href in found_hrefs:
                        if href:
                            # Explicitly resolve the URL first
                            absolute_href = urljoin(normalized_final_url, href)
                            # Create URLInfo from the absolute URL
                            resolved_link_info = URLInfo(absolute_href)
                            if self._should_crawl_url(resolved_link_info, target):
                                new_links_to_crawl.append((resolved_link_info.normalized_url, current_depth + 1))


                # Return metrics along with result and links
                return crawl_result_data, new_links_to_crawl, quality_metrics
            else:
                 # Should not be reached if last_error logic is correct, but handle defensively
                 logging.error(f"Processing loop for {normalized_url} finished without success or error.")
                 stats.failed_crawls += 1 # Count as failed if no content processed
                 crawl_result_data = CrawlResult(
                     target=target, stats=stats, documents=[], issues=[QualityIssue(type=IssueType.GENERAL, level=IssueLevel.ERROR, message="Processing finished unexpectedly")], metrics={}, processed_url=normalized_url, failed_urls=[normalized_url], errors={normalized_url: Exception("Unknown processing error")}
                 )
                 return crawl_result_data, [], {}

        except Exception as e:
            logging.error(f"Unhandled error in _process_url for {url}: {str(e)}", exc_info=True)
            stats.failed_crawls += 1
            # Ensure crawl_result_data is defined even in case of early exception
            # Include exception type name in the message
            error_type_name = type(e).__name__
            error_str = str(e)
            # Corrected message format
            issue_message = f"Unhandled exception: {error_type_name}({error_str})"

            crawl_result_data = CrawlResult(
                target=target, 
                stats=stats, 
                documents=[], 
                issues=[QualityIssue(type=IssueType.GENERAL, level=IssueLevel.ERROR, message=issue_message)], 
                metrics={}, 
                processed_url=url, # Use GENERAL type
                failed_urls=[url],  # Add the failed URL to the list
                errors={url: e}  # Map the URL to its exception
            )
            return crawl_result_data, [], {} # Return the result containing the unhandled exception issue


    async def crawl(self, target: CrawlTarget, websocket=None) -> CrawlResult:
        """Start the crawl process for a given target."""
        master_stats = CrawlStats()
        all_documents = []
        all_issues = []
        all_metrics: Dict[str, Dict[str, Any]] = {} # Store metrics per URL
        all_failed_urls: List[str] = [] # Initialize list for failed URLs
        all_errors: Dict[str, Exception] = {} # Initialize dict for errors
        visited_urls: Set[str] = set() # Track visited normalized URLs
        crawled_pages: Dict[str, Any] = {} # Track crawled pages

        # Use a deque for BFS queue
        initial_url = target.url
        queue = collections.deque() # Initialize empty queue
        start_url_for_id = initial_url # Default to original target

        # Attempt to identify project and discover URL if target looks like a package name
        is_potential_package = "://" not in initial_url
        discovered_doc_url = None
        if is_potential_package:
            logging.info(f"Target '{initial_url}' looks like a package name. Attempting discovery...")
            discovered_doc_url = await self.project_identifier.discover_doc_url(initial_url)
            if discovered_doc_url:
                logging.info(f"Discovered documentation URL for '{initial_url}': {discovered_doc_url}")
                queue.append((discovered_doc_url, 0)) # Start with discovered URL
                start_url_for_id = discovered_doc_url # Use discovered URL for identification
            else:
                # If discovery fails after assuming it's a package name, raise error
                logging.error(f"Could not resolve target '{initial_url}' as a URL or discover a documentation URL for it as a package.")
                raise ValueError(f"Invalid target: '{initial_url}' is not a valid URL and documentation URL discovery failed.")
        else:
             # If it looks like a URL, add it directly
             queue.append((initial_url, 0))

        # Initial project identification based on the *actual* starting URL
        try:
            # Only identify if it looks like a valid URL structure
            if "://" in start_url_for_id:
                 project_identity = await self.project_identifier.identify_from_url(start_url_for_id)
                 logging.info(f"Initial project identity based on '{start_url_for_id}': {project_identity}")
            else:
                 # Handle case where initial target was package name and discovery failed
                 project_identity = ProjectIdentity(name=start_url_for_id, type=ProjectType.UNKNOWN)
                 logging.info(f"Initial project identity based on package name '{start_url_for_id}': {project_identity}")

            # Use DuckDuckGo to find potential documentation URLs if enabled and identity found
            if self.duckduckgo and project_identity.name != "unknown":
                search_queries = self._generate_search_queries(start_url_for_id, project_identity)
                ddg_discovered_urls = set()
                for query in search_queries:
                    urls = await self.duckduckgo.search(query)
                    for url in urls:
                        # Basic validation before adding to queue
                        if urlparse(url).scheme in ['http', 'https']:
                            ddg_discovered_urls.add(url)
                logging.info(f"Discovered {len(ddg_discovered_urls)} potential URLs via DuckDuckGo.")
                # Add discovered URLs to the queue (depth 0)
                for url in ddg_discovered_urls:
                     if url not in [item[0] for item in queue]: # Avoid adding duplicates already in queue
                          queue.append((url, 0))
        except Exception as e:
             logging.error(f"Error during initial URL identification or DuckDuckGo search: {e}")
             # If the queue is empty after failed identification/search, and the original was a URL, add it back.
             if not queue and not is_potential_package:
                  logging.warning(f"Adding original target URL '{initial_url}' back to queue after error.")
                  queue.append((initial_url, 0))


        processed_pages = 0
        while queue and (target.max_pages is None or processed_pages < target.max_pages):
            url_string, current_depth = queue.popleft()

            # Check if already visited *before* processing
            # Need to normalize here briefly for the check, URLInfo handles full normalization later
            try:
                 # Use start_url_for_id as base if url_string is relative (shouldn't happen often here)
                 base_for_check = start_url_for_id if "://" in start_url_for_id else None
                 temp_info = URLInfo(url_string, base_url=base_for_check)
                 normalized_check_url = temp_info.normalized_url
                 if not temp_info.is_valid or normalized_check_url in visited_urls:
                      continue # Skip if invalid or already visited
            except Exception as e:
                 logging.warning(f"Skipping URL due to normalization error before processing: {url_string} ({e})")
                 continue

            # Process the URL
            try:
                async with Timer(f"Process URL {url_string}"): # Time the processing
                    result_data, new_links, metrics = await self._process_url(
                        url_string, current_depth, target, master_stats, visited_urls
                    )

                if result_data:
                    processed_pages += 1 # Increment only if result_data is not None
                    all_documents.extend(result_data.documents)
                    all_issues.extend(result_data.issues)
                    # Aggregate failed URLs and errors
                    all_failed_urls.extend(result_data.failed_urls)
                    all_errors.update(result_data.errors)
                    # Store metrics per URL if successful or partially successful
                    processed_url_key = result_data.processed_url or url_string
                    if metrics: # Only add metrics if they exist
                         all_metrics[processed_url_key] = metrics
                    
                    # Store processed content in crawled_pages
                    if result_data.documents:
                        crawled_pages[processed_url_key] = ProcessedContent(
                            url=processed_url_key,
                            title=result_data.documents[0].get('title', ''),
                            content=result_data.documents[0].get('content', {}),
                            metadata=result_data.documents[0].get('metadata', {}),
                            assets=result_data.documents[0].get('assets', []),
                            structure=result_data.structure
                        )

                    # --- Add document to organizer ---
                    if self.document_organizer and result_data.documents:
                        try:
                            doc_dict = result_data.documents[0]
                            # Reconstruct ProcessedContent object for the organizer
                            # Note: Ensure all necessary fields are present in doc_dict or result_data
                            processed_content_obj = ProcessedContent(
                                url=doc_dict.get('url', result_data.processed_url or url_string), # Use best available URL
                                title=doc_dict.get('title', ''),
                                content=doc_dict.get('content', {}),
                                metadata=doc_dict.get('metadata', {}),
                                assets=doc_dict.get('assets', {}),
                                structure=result_data.structure # Get structure from the main result
                                # Add other fields if ProcessedContent requires them
                            )
                            doc_org_id = self.document_organizer.add_document(processed_content_obj)
                            logging.debug(f"Added document {processed_content_obj.url} to organizer with id {doc_org_id}")
                        except Exception as org_exc:
                            logging.error(f"Error adding document {result_data.processed_url or url_string} to organizer: {org_exc}", exc_info=True)
                            # Optionally add an issue to all_issues
                    # --- End organizer call ---

                    # Add new valid links to the queue
                    # The check `current_depth < target.depth` is done within _process_url before returning new_links
                    for link_url, link_depth in new_links:
                        # Double-check visited here as well, although _should_crawl_url handles it
                        if link_url not in visited_urls:
                                queue.append((link_url, link_depth))

                    # Send progress update via WebSocket if available
                    if websocket:
                        progress = {
                            "type": "progress",
                            "url": result_data.processed_url or url_string,
                            "status": "success" if not result_data.issues or all(i.level != IssueLevel.ERROR for i in result_data.issues) else "error",
                            "depth": current_depth,
                            "pages_processed": processed_pages,
                            "queue_size": len(queue),
                            "issues_found": len(result_data.issues),
                            "documents_found": len(result_data.documents)
                        }
                        await websocket.send_json(progress)

                elif result_data is None: # Indicates skipped URL (invalid, visited, wrong type etc.)
                     pass # Already logged in _process_url or _should_crawl_url
                else: # Should have result_data if an error occurred during processing
                     # Log unexpected case if needed
                     pass


            except Exception as e:
                logging.error(f"Critical error during crawl loop for {url_string}: {e}", exc_info=True)
                master_stats.failed_crawls += 1
                all_issues.append(QualityIssue(type=IssueType.GENERAL, level=IssueLevel.ERROR, message=f"Crawler loop error: {str(e)}"))
                # Send progress update for critical failure
                if websocket:
                    progress = {
                        "type": "progress",
                        "url": url_string,
                        "status": "error",
                        "depth": current_depth,
                        "pages_processed": processed_pages,
                        "queue_size": len(queue),
                        "issues_found": 1, # Report this critical issue
                        "documents_found": 0
                    }
                    await websocket.send_json(progress)


        master_stats.end_time = datetime.utcnow()
        master_stats.total_time = (master_stats.end_time - master_stats.start_time).total_seconds()
        master_stats.pages_crawled = len(visited_urls) # Count unique visited URLs
        if master_stats.pages_crawled > 0: # Use pages_crawled for average calculation
            master_stats.average_time_per_page = master_stats.total_time / master_stats.pages_crawled

        # Track failed URLs and errors during crawl
        # Note: all_failed_urls and all_errors are already being collected during the crawl loop
        # when processing each URL in the _process_url method. We don't need to reinitialize them here.
        # Instead, we should preserve the values that were collected during the crawl.
        
        # Final result compilation
        final_result = CrawlResult(
            target=target,
            stats=master_stats,
            documents=all_documents,
            issues=all_issues,
            metrics=all_metrics, # Use the aggregated metrics
            crawled_pages=crawled_pages, # Include crawled pages dict
            failed_urls=list(set(all_failed_urls)), # Add aggregated failed URLs (remove duplicates)
            errors=all_errors # Add aggregated errors
            # structure=self.crawl_tree # Removed crawl_tree
        )

        # Organize documents if an organizer is provided
        # Removed call to non-existent finalize_organization
        # if self.document_organizer:
        #     await self.document_organizer.finalize_organization()

        logging.info(f"Crawl finished. Stats: {master_stats}")
        return final_result

    def _setup_backends(self) -> None:
        """Initialize and register crawler backends."""
        # Example: Register HTTP backend
        http_config = HTTPBackendConfig(
            timeout=self.config.request_timeout,
            verify_ssl=self.config.verify_ssl,
            follow_redirects=self.config.follow_redirects,
            headers=self.config.headers
        )
        http_backend = HTTPBackend(http_config)
        http_criteria = BackendCriteria(
            priority=1,
            content_types=["text/html"],
            url_patterns=["http://", "https://"]
        )
        self.backend_selector.register_backend(http_backend, http_criteria)

        # Example: Register File backend (if needed)
        # from .backends.file_backend import FileBackend
        # file_backend = FileBackend()
        # file_criteria = BackendCriteria(priority=2, schemes=["file"])
        # self.backend_selector.register_backend(file_backend, file_criteria)

        # Example: Register Crawl4AI backend (if needed)
        # from .backends.crawl4ai import Crawl4AIBackend, Crawl4AIConfig
        # crawl4ai_config = Crawl4AIConfig() # Use default or load from config
        # crawl4ai_backend = Crawl4AIBackend(crawl4ai_config)
        # crawl4ai_criteria = BackendCriteria(priority=0) # Default backend
        # self.backend_selector.register_backend(crawl4ai_backend, crawl4ai_criteria)


    async def _process_file_url(
        self,
        url_info: URLInfo,
        current_depth: int,
        target: CrawlTarget,
        stats: CrawlStats
    ) -> Tuple[Optional[CrawlResult], List[Tuple[str, int]], Dict[str, Any]]:
        """Process a file:// URL, reading from the local filesystem."""
        normalized_url = url_info.normalized_url
        new_links_to_crawl = []
        quality_metrics = {}
        
        try:
            # Convert file:// URL to local path
            file_path = url_info.path
            if os.name == 'nt' and file_path.startswith('/'):  # Windows path handling
                file_path = file_path[1:]  # Remove leading slash
            
            logging.info(f"Processing file URL: {normalized_url} (Path: {file_path})")
            
            if not os.path.exists(file_path):
                logging.error(f"File not found: {file_path}")
                stats.failed_crawls += 1
                return CrawlResult(
                    target=target, 
                    stats=stats, 
                    documents=[], 
                    issues=[QualityIssue(type=IssueType.GENERAL, level=IssueLevel.ERROR, message=f"File not found: {file_path}")],
                    metrics={}, 
                    processed_url=normalized_url,
                    failed_urls=[normalized_url],
                    errors={normalized_url: FileNotFoundError(f"File not found: {file_path}")}
                ), [], {}
            
            # Read file content
            if os.path.isdir(file_path):
                # For directories, look for index.html
                index_path = os.path.join(file_path, "index.html")
                if os.path.exists(index_path):
                    file_path = index_path
                else:
                    logging.error(f"Directory has no index.html: {file_path}")
                    stats.failed_crawls += 1
                    return CrawlResult(
                        target=target, 
                        stats=stats, 
                        documents=[], 
                        issues=[QualityIssue(type=IssueType.GENERAL, level=IssueLevel.ERROR, message=f"Directory has no index.html: {file_path}")],
                        metrics={}, 
                        processed_url=normalized_url,
                        failed_urls=[normalized_url],
                        errors={normalized_url: FileNotFoundError(f"Directory has no index.html: {file_path}")}
                    ), [], {}
            
            # Read the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Process content using ContentProcessor
            processed_content = await self.content_processor.process(content, base_url=normalized_url)
            
            stats.successful_crawls += 1
            stats.pages_crawled += 1
            stats.bytes_processed += len(content)
            
            # Perform quality check
            if self.quality_checker:
                quality_issues, quality_metrics = await self.quality_checker.check_quality(processed_content)
            else:
                quality_issues, quality_metrics = [], {}
            
            # Prepare result data
            crawl_result = CrawlResult(
                target=target,
                stats=stats,
                documents=[{
                    'url': normalized_url,
                    'content': processed_content.content,
                    'metadata': processed_content.metadata,
                    'assets': processed_content.assets,
                    'title': processed_content.title
                }],
                issues=quality_issues,
                metrics=quality_metrics,
                structure=processed_content.structure,
                processed_url=normalized_url
            )
            stats.quality_issues += len(crawl_result.issues)
            
            # Extract new links if depth allows
            if current_depth < target.depth:
                found_hrefs = self._find_links_recursive(processed_content.structure)
                for href in found_hrefs:
                    if href:
                        # Resolve relative URLs
                        absolute_href = urljoin(normalized_url, href)
                        resolved_link_info = URLInfo(absolute_href)
                        if self._should_crawl_url(resolved_link_info, target):
                            new_links_to_crawl.append((resolved_link_info.normalized_url, current_depth + 1))
            
            return crawl_result, new_links_to_crawl, quality_metrics
            
        except Exception as e:
            logging.error(f"Error processing file URL {normalized_url}: {str(e)}", exc_info=True)
            stats.failed_crawls += 1
            return CrawlResult(
                target=target, 
                stats=stats, 
                documents=[], 
                issues=[QualityIssue(type=IssueType.GENERAL, level=IssueLevel.ERROR, message=f"File processing error: {str(e)}")],
                metrics={}, 
                processed_url=normalized_url,
                failed_urls=[normalized_url],
                errors={normalized_url: e}
            ), [], {}

    async def cleanup(self):
        """Clean up resources, like closing the aiohttp session."""
        if self.client_session and not self.client_session.closed:
            await self.client_session.close()
            self.client_session = None
            logging.info("Crawler client session closed.")
        # Close DuckDuckGo session if it exists and has a close method
        if hasattr(self.duckduckgo, 'close') and asyncio.iscoroutinefunction(self.duckduckgo.close):
             await self.duckduckgo.close()
             logging.info("DuckDuckGo session closed.")


    def _generate_search_queries(self, url: str, identity: ProjectIdentity) -> List[str]:
        """Generate search queries based on project identity."""
        queries = []
        
        # Base query with project name
        if identity.name != "unknown":
            queries.append(f"{identity.name} documentation")
            
            # Add language/framework specific queries
            if identity.language:
                queries.append(f"{identity.name} {identity.language} documentation")
            if identity.framework:
                queries.append(f"{identity.name} {identity.framework} documentation")
                
            # Add type specific queries
            if identity.type != ProjectType.UNKNOWN:
                queries.append(f"{identity.name} {identity.type.value} documentation")
                
            # Add queries based on related keywords
            for keyword in identity.related_keywords[:3]: # Limit keywords
                queries.append(f"{identity.name} {keyword} documentation")

        # Fallback query based on URL domain if name is unknown
        if not queries:
            try:
                domain = urlparse(url).netloc
                if domain:
                    queries.append(f"{domain} documentation")
            except Exception:
                pass # Ignore URL parsing errors for fallback

        # Limit number of queries
        return queries[:5]
