import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

from pydantic import BaseModel, Field
import aiohttp

from .backends.base import CrawlerBackend, CrawlResult
from .backends.selector import BackendSelector, BackendCriteria
from .backends.http import HTTPBackend, HTTPBackendConfig
from .organizers.doc_organizer import DocumentOrganizer
from .processors.content_processor import ContentProcessor, ProcessedContent
from .processors.quality_checker import QualityChecker, QualityIssue
from .utils.helpers import (
    RateLimiter, RetryStrategy, Timer, URLInfo,
    URLProcessor, setup_logging
)

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
    documents: List[str]  # Document IDs
    issues: List[QualityIssue]
    metrics: Dict[str, Any]  # Removed QualityMetrics dependency


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
    batch_size: int = 5


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
            for r in self._ddgs.text(search_query, max_results=self.max_results):
                if r.get('link'):
                    url = r['link']
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
        self.backend_selector = backend_selector or BackendSelector()
        self.content_processor = content_processor or ContentProcessor()
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
        
        self.rate_limiter = RateLimiter(self.config.requests_per_second)
        self.retry_strategy = RetryStrategy(
            max_retries=self.config.max_retries
        )
        
        self._crawled_urls: Set[str] = set()
        self._processing_semaphore = asyncio.Semaphore(
            self.config.concurrent_requests
        )
        self.client_session = None
        
        self.duckduckgo = DuckDuckGoSearch(self.config.duckduckgo_max_results) if self.config.use_duckduckgo else None
        self.crawl_tree = {}
        self.current_tasks = set()
        self.project_identifier = ProjectIdentifier()
        
    def _should_crawl_url(self, url: str, target: CrawlTarget) -> bool:
        """
        Determine if a URL should be crawled based on target configuration.
        """
        try:
            # Parse URLs
            target_parsed = urlparse(target.url)
            url_parsed = urlparse(url)
            
            # Get base domains
            target_domain = '.'.join(target_parsed.netloc.split('.')[-2:])  # e.g., python.org from docs.python.org
            url_domain = '.'.join(url_parsed.netloc.split('.')[-2:])        # Get base domain
            
            logging.debug(f"\nEvaluating link: {url}")
            logging.debug(f"Target domain: {target_domain}")
            logging.debug(f"URL domain: {url_domain}")
            
            # Check if domains match
            if target_domain != url_domain:
                logging.debug(f"Skipping different domain: {url_domain} (target: {target_domain})")
                return False
                
            # Check if it's an allowed path
            if target.allowed_paths:
                path_allowed = any(url_parsed.path.startswith(path) for path in target.allowed_paths)
                if not path_allowed:
                    logging.debug(f"Skipping path not in allowed paths: {url_parsed.path}")
                    return False
            
            # Check if it's an excluded path
            if target.excluded_paths:
                path_excluded = any(url_parsed.path.startswith(path) for path in target.excluded_paths)
                if path_excluded:
                    logging.debug(f"Skipping excluded path: {url_parsed.path}")
                    return False
            
            # Additional checks for file types
            path = url_parsed.path.lower()
            if any(path.endswith(ext) for ext in ['.pdf', '.zip', '.tar.gz', '.png', '.jpg', '.jpeg', '.gif']):
                logging.debug(f"Skipping non-documentation file type: {path}")
                return False
                
            logging.debug(f"URL approved for crawling: {url}")
            return True
            
        except Exception as e:
            logging.error(f"Error evaluating URL {url}: {str(e)}")
            return False

    async def _normalize_url(self, url: str) -> URLInfo:
        """Normalize URL and get its info."""
        processor = URLProcessor()
        return processor.process_url(url)

    async def _process_url(
        self,
        url: str,
        target: CrawlTarget,
        stats: CrawlStats
    ) -> Optional[CrawlResult]:
        """Process a single URL."""
        try:
            logging.info(f"Processing URL: {url}")
            
            # Skip if already crawled
            if url in self._crawled_urls:
                logging.debug(f"Skipping already crawled URL: {url}")
                return None
                
            self._crawled_urls.add(url)
            
            # Get backend for this URL
            backend = self.backend_selector.select_backend(url)
            if not backend:
                logging.error(f"No suitable backend found for URL: {url}")
                return None
                
            # Process with retry strategy
            for attempt in range(self.config.max_retries):
                try:
                    logging.debug(f"Attempt {attempt + 1}/{self.config.max_retries}")
                    
                    # Fetch and process content
                    async with self._processing_semaphore:
                        result = await backend.crawl(url)
                        if not result or result.status != 200:
                            logging.error(f"Failed to fetch content from {url}: {result.error if result else 'Unknown error'}")
                            continue
                            
                        # Process the content
                        processed_data = await backend.process(result)
                        if not processed_data or "html" not in processed_data:
                            logging.error(f"Failed to process content from {url}")
                            continue
                            
                        # Process with content processor
                        processed_content = await self.content_processor.process(processed_data["html"])
                        if not processed_content:
                            logging.error(f"Failed to process content from {url}")
                            continue
                            
                        # Update stats
                        stats.pages_crawled += 1
                        stats.successful_crawls += 1
                        
                        return CrawlResult(
                            target=target,
                            stats=stats,
                            documents=[{
                                'url': url,
                                'content': processed_content
                            }],
                            issues=[],
                            metrics={}
                        )
                        
                except Exception as e:
                    logging.error(f"Error processing URL {url} (attempt {attempt + 1}): {str(e)}")
                    if attempt == self.config.max_retries - 1:
                        stats.failed_crawls += 1
                        return None
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    
            return None
            
        except Exception as e:
            logging.error(f"Unhandled error processing URL {url}: {str(e)}")
            stats.failed_crawls += 1
            return None

    async def _process_batch(self, urls: List[str], target: CrawlTarget, stats: CrawlStats) -> List[CrawlResult]:
        """Process a batch of URLs concurrently."""
        tasks = []
        batch_size = self.config.batch_size
        
        # Split URLs into batches
        for i in range(0, len(urls), batch_size):
            batch_urls = urls[i:i + batch_size]
            
            # Create a new target for each batch
            batch_target = CrawlTarget(
                url=" ".join(batch_urls),
                depth=target.depth,
                follow_external=target.follow_external,
                content_types=target.content_types,
                exclude_patterns=target.exclude_patterns,
                required_patterns=target.required_patterns,
                max_pages=target.max_pages,
                allowed_paths=target.allowed_paths,
                excluded_paths=target.excluded_paths
            )
            
            # Process batch
            task = asyncio.create_task(
                self._process_url(batch_target.url, batch_target, stats)
            )
            tasks.append(task)
            
            # Apply rate limiting
            await self.rate_limiter.wait()
        
        # Wait for all batches to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, CrawlResult)]

    async def crawl(self, target: CrawlTarget, websocket=None) -> CrawlResult:
        """Crawl documentation from the target."""
        try:
            stats = CrawlStats()
            
            # Check if target.url is a package name rather than a URL
            if not target.url.startswith(('http://', 'https://')):
                # First check if we have a cached URL
                if target.url in self.project_identifier.package_doc_urls:
                    doc_url = self.project_identifier.package_doc_urls[target.url]
                else:
                    # Try to discover the documentation URL
                    doc_url = await self.project_identifier.discover_doc_url(target.url)
                    if doc_url:
                        # Cache the discovered URL
                        self.project_identifier.add_doc_url(target.url, doc_url)
                    elif target.url in self.project_identifier.fallback_urls:
                        doc_url = self.project_identifier.fallback_urls[target.url]
                    else:
                        logging.error(f"Could not find documentation URL for package: {target.url}")
                        return CrawlResult(
                            target=target,
                            stats=stats,
                            documents=[],
                            issues=[QualityIssue(
                                type="error",
                                message=f"Could not find documentation URL for package: {target.url}",
                                severity="high"
                            )],
                            metrics={}
                        )
                
                target.url = doc_url
            
            with Timer("Crawl"):
                # Initialize aiohttp session
                self.client_session = aiohttp.ClientSession(
                    connector=aiohttp.TCPConnector(verify_ssl=self.config.verify_ssl)
                )
                
                # Process URL
                initial_result = await self._process_url(target.url, target, stats)
                if not initial_result:
                    logging.error(f"Failed to process URL: {target.url}")
                    return CrawlResult(
                        target=target,
                        stats=stats,
                        documents=[],
                        issues=[QualityIssue(
                            type="error",
                            message=f"Failed to process URL: {target.url}",
                            severity="high"
                        )],
                        metrics={}
                    )
                
                return initial_result
                
        except Exception as e:
            logging.error(f"Error during crawl: {str(e)}")
            return CrawlResult(
                target=target,
                stats=stats,
                documents=[],
                issues=[QualityIssue(
                    type=IssueType.GENERAL,
                    level=IssueLevel.ERROR,
                    message=f"Crawl failed due to processing error: {str(e)}",
                    details={'error': str(e)}
                )],
                metrics={}
            )
            
        finally:
            # Clean up
            if self.client_session:
                await self.client_session.close()

    async def close(self) -> None:
        """Cleanup resources with comprehensive error handling."""
        # Quality checker cleanup
        
        # Close backend resources
        for backend in self.backend_selector.get_all_backends().values():
            try:
                if hasattr(backend, 'close'):
                    await backend.close()
            except Exception as e:
                logging.error(f"Error closing backend {backend.name}: {e}")

    def _setup_backends(self) -> None:
        """Setup default backends if none are registered."""
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
            if self.client_session and not self.client_session.closed:
                await self.client_session.close()
            self.client_session = None
            
            
                
                
            for backend in self.backend_selector.get_all_backends().values():
                if hasattr(backend, 'close'):
                    await backend.close()
                    
            if hasattr(self.document_organizer, 'close'):
                await self.document_organizer.close()
                
        except Exception as e:
            logging.error(f"Error during cleanup: {str(e)}")
            raise

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