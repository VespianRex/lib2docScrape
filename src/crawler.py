import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
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
from .utils.url_info import URLInfo
from .processors.content.url_handler import sanitize_and_join_url

from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Dict, Set, Union
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
        document_organizer: Optional[DocumentOrganizer] = None
    ) -> None:
        """Initialize the documentation crawler."""
        self.config = config or CrawlerConfig()
        logging.debug(f"Crawler __init__ received backend_selector: id={id(backend_selector)}")
        if backend_selector:
             logging.debug(f"Received selector initial backends: {list(backend_selector.backends.keys())}")
        self.backend_selector = backend_selector or BackendSelector()
        self.content_processor = content_processor or ContentProcessor()
        logging.debug(f"Crawler assigned self.backend_selector: id={id(self.backend_selector)}")
        logging.debug(f"Assigned selector backends BEFORE http registration: {list(self.backend_selector.backends.keys())}")
        self.quality_checker = quality_checker or QualityChecker()
        self.document_organizer = document_organizer or DocumentOrganizer()

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
        )

        self._crawled_urls: Set[str] = set() # Store normalized URLs
        self._processing_semaphore = asyncio.Semaphore(
            self.config.concurrent_requests
        )
        self.client_session = None # Session managed by HTTPBackend now

        self.duckduckgo = DuckDuckGoSearch(self.config.duckduckgo_max_results) if self.config.use_duckduckgo else None
        # self.crawl_tree = {} # Removed, not used in new logic
        # self.current_tasks = set() # Removed, managed by asyncio.gather
        self.project_identifier = ProjectIdentifier()

    def _should_crawl_url(self, url_info: URLInfo, target: CrawlTarget) -> bool:
        """
        Determine if a URL should be crawled based on target configuration and URLInfo.
        Uses the new URLInfo object for checks.
        """
        if not url_info or not url_info.is_valid:
            logging.debug(f"Skipping invalid or non-HTTP(S) URL: {url_info.original_url if url_info else 'N/A'}")
            return False

        # Use normalized URL for checks
        normalized_url = url_info.normalized_url
        parsed_url = urlparse(normalized_url) # Parse the normalized URL

        # 1. Check against crawled URLs
        if normalized_url in self._crawled_urls:
            logging.debug(f"Skipping already crawled URL: {normalized_url}")
            return False

        # 2. Domain Check (if not following external links)
        if not target.follow_external:
            try:
                target_info = URLInfo(target.url) # Process target URL once
                if not target_info.is_valid:
                     logging.error(f"Target URL '{target.url}' is invalid. Cannot perform domain check.")
                     return False # Cannot crawl if target is invalid

                # Compare base domains (e.g., example.com)
                target_domain = '.'.join(target_info.netloc.split('.')[-2:])
                url_domain = '.'.join(parsed_url.netloc.split('.')[-2:])
                if target_domain != url_domain:
                    logging.debug(f"Skipping external domain: {parsed_url.netloc} (target: {target_info.netloc})")
                    return False
            except Exception as e:
                 logging.error(f"Error during domain check for {normalized_url} against {target.url}: {e}")
                 return False


        # 3. Exclude Patterns
        if target.exclude_patterns and any(re.search(pattern, normalized_url) for pattern in target.exclude_patterns):
            logging.debug(f"Skipping URL matching exclude pattern: {normalized_url}")
            return False

        # 4. Required Patterns (if any)
        logging.debug(f"Checking required patterns for {url_info.normalized_url}. Target patterns: {target.required_patterns}") # ADDED DEBUG
        if target.required_patterns and not any(re.search(pattern, normalized_url) for pattern in target.required_patterns):
            logging.debug(f"Skipping URL not matching required pattern: {normalized_url}")
            return False

        # 5. Allowed Paths (if any)
        if target.allowed_paths and not any(parsed_url.path.startswith(path) for path in target.allowed_paths):
            logging.debug(f"Skipping path not in allowed paths: {parsed_url.path}")
            return False

        # 6. Excluded Paths (if any)
        if target.excluded_paths and any(parsed_url.path.startswith(path) for path in target.excluded_paths):
            logging.debug(f"Skipping excluded path: {parsed_url.path}")
            return False

        # 7. File Type Check (basic check on extension)
        path_lower = parsed_url.path.lower()
        excluded_extensions = ['.pdf', '.zip', '.tar.gz', '.png', '.jpg', '.jpeg', '.gif', '.css', '.js'] # Add css/js
        if any(path_lower.endswith(ext) for ext in excluded_extensions):
            logging.debug(f"Skipping non-HTML file type based on extension: {path_lower}")
            return False

        logging.debug(f"URL approved for crawling: {normalized_url}")
        return True

    # _normalize_url removed, using URLInfo directly

    async def _process_url(
        self,
        url: str,
        current_depth: int, # Added depth tracking
        target: CrawlTarget,
        stats: CrawlStats,
        visited_urls: Set[str] # Pass visited set
    ) -> Tuple[Optional[CrawlResult], List[Tuple[str, int]], Dict[str, Any]]: # Return result, new URLs, and metrics
        """Process a single URL, returning its result and discovered links."""
        new_links_to_crawl = []
        crawl_result_data = None

        try:
            # Normalize URL early and check if visited
            url_info = URLInfo(url, base_url=target.url) # Use target.url as base for initial URLInfo
            normalized_url = url_info.normalized_url
            if not url_info.is_valid or normalized_url in visited_urls:
                logging.debug(f"Skipping invalid/visited URL: {url} (Normalized: {normalized_url})")
                return None, [] # Return None result, no new links

            logging.info(f"Processing URL: {normalized_url} (Depth: {current_depth})")
            visited_urls.add(normalized_url) # Add normalized URL to visited set

            # Get backend for this URL
            backend = await self.backend_selector.select_backend(normalized_url)
            if not backend:
                logging.error(f"No suitable backend found for URL: {normalized_url}")
                stats.failed_crawls += 1
                # Create a minimal CrawlResult for failure reporting
                crawl_result_data = CrawlResult(
                    target=target, stats=stats, documents=[], issues=[QualityIssue(type=IssueType.GENERAL, level=IssueLevel.ERROR, message=f"No backend for {normalized_url}")], metrics={}, processed_url=normalized_url # Use GENERAL type
                )
                return crawl_result_data, []

            # Process with retry strategy
            processed_content: Optional[ProcessedContent] = None
            last_error = None
            backend_result: Optional[BackendCrawlResult] = None

            for attempt in range(self.config.max_retries):
                try:
                    logging.debug(f"Attempt {attempt + 1}/{self.config.max_retries} for {normalized_url}")
                    # Apply rate limiting
                    wait_time = await self.rate_limiter.acquire() # Add await
                    if wait_time > 0:
                        logging.debug(f"Rate limit hit for {normalized_url}, sleeping for {wait_time:.4f}s")
                        await asyncio.sleep(wait_time)

                    async with self._processing_semaphore:
                        backend_result = await backend.crawl(normalized_url) # Use normalized URL

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
                             return None, [] # Already visited via redirect

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
                             return None, [] # Skip non-HTML content

                        # Process content using ContentProcessor
                        processed_content = await self.content_processor.process(backend_result.content.get('html', ''), base_url=final_url_processed) # Add await back, process is now async

                        stats.successful_crawls += 1
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
                crawl_result_data = CrawlResult(
                    target=target, stats=stats, documents=[], issues=[QualityIssue(type=IssueType.GENERAL, level=IssueLevel.ERROR, message=f"Failed after retries: {str(last_error)}")], metrics={}, processed_url=normalized_url # Use GENERAL type
                )
                return crawl_result_data, [], {} # Return empty metrics dict as well

            # If successful processing occurred
            if processed_content:
                stats.pages_crawled += 1 # Increment only on successful processing
                # Extract links if depth allows further crawling
                if current_depth < target.depth:
                    # Use the structure from the processed content
                    page_structure = processed_content.structure # Use the top-level structure attribute
                    base_for_links = processed_content.metadata.get('base_url') or final_url_processed # Use base from metadata or final URL

                    for item in page_structure:
                        links_to_process = []
                        if item.get('type') == 'link': # Standalone link
                            links_to_process.append(item)
                        elif item.get('type') == 'text': # Paragraph containing inline elements
                            for part in item.get('content', []):
                                if part.get('type') == 'link_inline':
                                    links_to_process.append(part) # Add inline link for processing

                        # Process found links (either standalone or inline)
                        for link_item in links_to_process:
                            href = link_item.get('href')
                            if href:
                                absolute_link = sanitize_and_join_url(href, base_for_links)
                                if absolute_link:
                                    link_info = URLInfo(absolute_link, base_url=target.url)
                                    if self._should_crawl_url(link_info, target):
                                        new_links_to_crawl.append((link_info.normalized_url, current_depth + 1))

                # Prepare successful result data
                # Perform quality check *before* creating CrawlResult
                if self.quality_checker:
                    # Only unpack issues, ignore metrics for now
                    quality_issues, quality_metrics = await self.quality_checker.check_quality(processed_content) # Assign metrics too
                else:
                    quality_issues, quality_metrics = [], {} # Assign default empty list/dict

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

            # Perform quality check *before* creating CrawlResult
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
                structure=processed_content.content.get('structure'),
                processed_url=normalized_final_url
            )
            stats.quality_issues += len(crawl_result_data.issues)

            # Return metrics along with result and links
            return crawl_result_data, new_links_to_crawl, quality_metrics

        except Exception as e:
            logging.error(f"Unhandled error in _process_url for {url}: {str(e)}", exc_info=True)
            stats.failed_crawls += 1
            # Ensure crawl_result_data is defined even in case of early exception
            crawl_result_data = CrawlResult(
                target=target, stats=stats, documents=[], issues=[QualityIssue(type=IssueType.GENERAL, level=IssueLevel.ERROR, message=f"Unhandled exception: {str(e)}")], metrics={}, processed_url=url # Use GENERAL type
            )
            return crawl_result_data, [], {} # Return the result containing the unhandled exception issue
            return crawl_result_data, [], {} # Return failure result, no new links, empty metrics

    # _process_batch removed as crawl logic is now queue-based

    async def crawl(self, target: CrawlTarget, websocket=None) -> CrawlResult:
        """Crawl documentation starting from the target URL recursively."""
        master_stats = CrawlStats()
        all_documents = []
        all_issues = []
        aggregated_metrics: Dict[str, Any] = {} # Initialize metrics dict
        self._crawled_urls.clear() # Clear visited set for new crawl

        # Use deque for efficient queue operations
        queue = collections.deque([(target.url, 0)]) # Queue stores (url, depth)

        # Check if target.url is a package name
        if not target.url.startswith(('http://', 'https://')):
            # (Package name discovery logic remains the same)
            if target.url in self.project_identifier.package_doc_urls:
                doc_url = self.project_identifier.package_doc_urls[target.url]
            else:
                doc_url = await self.project_identifier.discover_doc_url(target.url)
                if doc_url:
                    self.project_identifier.add_doc_url(target.url, doc_url)
                elif target.url in self.project_identifier.fallback_urls:
                    doc_url = self.project_identifier.fallback_urls[target.url]
                else:
                    logging.error(f"Could not find documentation URL for package: {target.url}")
                    master_stats.end_time = datetime.utcnow()
                    return CrawlResult(target=target, stats=master_stats, documents=[], issues=[QualityIssue(type=IssueType.GENERAL, level=IssueLevel.ERROR, message=f"No URL for package: {target.url}")], metrics={}) # Use GENERAL type
            target.url = doc_url # Update target URL
            queue = collections.deque([(target.url, 0)]) # Re-initialize queue with resolved URL

        # Initialize aiohttp session (managed by HTTPBackend now, but keep reference for potential direct use?)
        # self.client_session = aiohttp.ClientSession(...) # Consider if needed directly

        processed_pages = 0
        tasks = set()

        try:
            with Timer("Crawl") as crawl_timer:
                while queue:
                    # Check max pages limit
                    if target.max_pages is not None and processed_pages >= target.max_pages:
                        logging.info(f"Reached max page limit ({target.max_pages}). Stopping crawl.")
                        break

                    # Manage concurrent tasks
                    while len(tasks) >= self.config.concurrent_requests and queue:
                        # Wait for some tasks to complete before adding more
                        done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                        # Process results from completed tasks
                        for future in done:
                            result_tuple = await future
                            # Check if result_tuple is valid before unpacking
                            if result_tuple and len(result_tuple) == 3:
                                page_result, new_links, page_metrics = result_tuple
                                # Always extend issues, regardless of success/failure
                                if page_result and page_result.issues:
                                     all_issues.extend(page_result.issues)

                                # Process successful results
                                if page_result and page_result.stats.successful_crawls > 0:
                                    processed_pages += 1
                                    all_documents.extend(page_result.documents)
                                    # Stats are accumulated directly in the stats object passed to _process_url

                                # Add newly discovered valid links to the queue
                                for link_url, next_depth in new_links:
                                    if next_depth <= target.depth:
                                         # Check visited again before adding to prevent race conditions
                                         link_info_check = URLInfo(link_url)
                                         if link_info_check.normalized_url not in self._crawled_urls:
                                             queue.append((link_info_check.normalized_url, next_depth))
                                             self._crawled_urls.add(link_info_check.normalized_url) # Add here too
                                         else:
                                             logging.debug(f"Skipping link already visited/queued: {link_info_check.normalized_url}")


                    # Dequeue next URL if queue is not empty
                    if not queue:
                         break # Exit outer loop if queue is empty

                    current_url, current_depth = queue.popleft()

                    # Create and add new task
                    # Pass a copy of stats to avoid race conditions if needed, though current _process_url modifies it directly
                    # For simplicity, we pass the master_stats, assuming _process_url handles its updates correctly for now.
                    # A safer approach might involve returning stat deltas from _process_url.
                    task = asyncio.create_task(self._process_url(current_url, current_depth, target, master_stats, self._crawled_urls))
                    tasks.add(task)

                # Wait for any remaining tasks to complete
                if tasks:
                    done, _ = await asyncio.wait(tasks)
                    # Process results from final tasks
                    for future in done:
                        result_tuple = await future
                        # Check if result_tuple is valid before unpacking
                        if result_tuple and len(result_tuple) == 3:
                            page_result, new_links, page_metrics = result_tuple
                            # Always extend issues, regardless of success/failure
                            if page_result and page_result.issues:
                                 all_issues.extend(page_result.issues)

                            # Process successful results
                            if page_result and page_result.stats.successful_crawls > 0:
                                processed_pages += 1
                                all_documents.extend(page_result.documents)
                                # Stats are accumulated directly in the stats object passed to _process_url
                                # Store metrics from the processed page
                                if page_metrics:
                                     aggregated_metrics = page_metrics # Overwrite OK here? Or aggregate? Assuming overwrite for now.
                            # Failed crawls are also accumulated directly in the stats object


            # Finalize stats
            master_stats.end_time = datetime.utcnow()
            master_stats.total_time = crawl_timer.duration # Use the duration property
            master_stats.pages_crawled = processed_pages # Use counter instead of successful_crawls
            if master_stats.pages_crawled > 0:
                master_stats.average_time_per_page = master_stats.total_time / master_stats.pages_crawled

            # Organize documents
            # organized_docs = self.document_organizer.organize(all_documents) # Removed call to non-existent method

            return CrawlResult(
                target=target,
                stats=master_stats,
                documents=all_documents, # Return the list of document dicts collected
                issues=all_issues,
                metrics=aggregated_metrics # Pass aggregated metrics
            )

        except Exception as e:
            logging.error(f"Unhandled error during crawl: {str(e)}", exc_info=True)
            master_stats.end_time = datetime.utcnow()
            # Ensure stats reflect failure if error occurs outside _process_url
            # master_stats.failed_crawls = max(master_stats.failed_crawls, 1) # Ensure at least one failure
            return CrawlResult(target=target, stats=master_stats, documents=all_documents, issues=all_issues + [QualityIssue(type=IssueType.GENERAL, level=IssueLevel.ERROR, message=f"Unhandled crawl error: {str(e)}")], metrics=aggregated_metrics) # Include potentially gathered metrics
        finally:
            await self.cleanup() # Ensure cleanup runs

    async def close(self) -> None:
        """Cleanup resources with comprehensive error handling."""
        await self.cleanup() # Call the cleanup method

    def _setup_backends(self) -> None:
        """Setup default backends if none are registered."""
        # This logic seems redundant with the __init__ setup, consider removing or merging
        if not self.backend_selector.backends:
            # Add default HTTP backend
            http_backend = HTTPBackend(
                config=HTTPBackendConfig(
                    timeout=self.config.request_timeout,
                    headers=self.config.headers,
                    verify_ssl=self.config.verify_ssl
                )
            )
            self.backend_selector.register_backend(
                http_backend,
                BackendCriteria(
                    priority=100,
                    content_types=["text/html"],
                    url_patterns=["*"],
                    max_load=0.8,
                    min_success_rate=0.7
                )
            )

    async def cleanup(self):
        """Clean up resources."""
        try:
            # Client session is managed by HTTPBackend, no need to close here if using that pattern
            # if self.client_session and not self.client_session.closed:
            #     await self.client_session.close()
            # self.client_session = None

            if hasattr(self.quality_checker, 'close'):
                await self.quality_checker.close()

            for backend in self.backend_selector.get_all_backends().values():
                if hasattr(backend, 'close'):
                    await backend.close()

            if hasattr(self.document_organizer, 'close'):
                # Assuming close is async, if not, remove await
                if asyncio.iscoroutinefunction(self.document_organizer.close):
                     await self.document_organizer.close()
                else:
                     self.document_organizer.close() # Call synchronously if not async

        except Exception as e:
            logging.error(f"Error during cleanup: {str(e)}")
            # Don't raise here, allow cleanup to finish as much as possible

    def _generate_search_queries(self, url: str, identity: ProjectIdentity) -> List[str]:
        """Generate search queries based on project identity."""
        queries = []

        # Base query with project name
        base_query = identity.name
        if identity.name != "unknown":
            queries.append(f"{base_query} documentation")

        # Add type-specific queries
        if identity.type == ProjectType.FRAMEWORK:
            queries.extend([
                f"{base_query} framework tutorial",
                f"{base_query} framework guide",
                f"{base_query} getting started",
                f"{base_query} API reference"
            ])
        elif identity.type == ProjectType.PROGRAM:
            queries.extend([
                f"{base_query} user manual",
                f"{base_query} usage guide",
                f"{base_query} command reference",
                f"{base_query} examples"
            ])
        elif identity.type == ProjectType.LIBRARY:
            queries.extend([
                f"{base_query} library reference",
                f"{base_query} API documentation",
                f"{base_query} usage examples",
                f"{base_query} code samples"
            ])
        elif identity.type == ProjectType.CLI_TOOL:
            queries.extend([
                f"{base_query} CLI documentation",
                f"{base_query} command reference",
                f"{base_query} usage options",
                f"{base_query} examples"
            ])

        # Add language/framework specific queries
        if identity.language:
            queries.append(f"{base_query} {identity.language} documentation")
        if identity.framework:
            queries.append(f"{base_query} {identity.framework} documentation")

        return queries