import asyncio
import logging
import re
import os
from datetime import datetime, UTC
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from urllib.parse import urljoin, urlparse
from dataclasses import asdict
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
from .utils.url.info import URLInfo # Corrected import path for modular URLInfo
from .utils.url.factory import create_url_info # Added import for factory
from .processors.content.url_handler import sanitize_and_join_url

# ProjectIdentifier, ProjectType, ProjectIdentity moved to src.utils.project_identifier
from .utils.project_identifier import ProjectIdentifier, ProjectType, ProjectIdentity
from .utils.search import DuckDuckGoSearch # Import from new location

# ProjectIdentifier class removed and moved to src.utils.project_identifier
# DuckDuckGoSearch class moved to src.utils.search

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
    start_time: datetime = Field(default_factory=lambda: datetime.now(UTC))
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
    crawled_urls: Set[str] = Field(default_factory=set)  # Set of normalized URLs that were crawled
    
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


# DuckDuckGoSearch class has been moved to src/utils/search.py
class DocumentationCrawler:
    """Main crawler orchestrator."""

    def __init__(
        self,
        config: Optional[CrawlerConfig] = None,
        backend_selector: Optional[BackendSelector] = None,
        content_processor: Optional[ContentProcessor] = None,
        quality_checker: Optional[QualityChecker] = None,
        document_organizer: Optional[DocumentOrganizer] = None,
        loop: Optional[Any] = None,
        backend: Optional[CrawlerBackend] = None
    ) -> None:
        """Initialize the documentation crawler.
        
        Args:
            config: Optional crawler configuration
            backend_selector: Optional backend selector for choosing appropriate backends
            content_processor: Optional content processor for processing crawled content
            quality_checker: Optional quality checker for checking content quality
            document_organizer: Optional document organizer for organizing crawled content
            loop: Optional event loop for asyncio
            backend: Optional specific backend to use instead of using the selector
        """
        self.config = config or CrawlerConfig()
        logging.debug(f"Crawler __init__ received backend_selector: id={id(backend_selector)}")
        # Optional event loop passed for testing
        self.loop = loop
        if backend_selector:
             logging.debug(f"Received selector initial backends: {list(backend_selector._backends.keys())}")
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
        logging.debug(f"Assigned selector backends BEFORE http registration: {list(self.backend_selector._backends.keys())}")


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
            name=http_backend.name,  # Use the name attribute
            backend=http_backend,    # Pass the instance
            criteria=BackendCriteria( # Pass the criteria
                priority=1,
                content_types=["text/html"],
                url_patterns=["http://", "https://"],  # Match all HTTP(S) URLs
                max_load=0.8,
                min_success_rate=0.7
            )
        )
        logging.debug(f"Assigned selector backends AFTER http registration: {list(self.backend_selector._backends.keys())}")

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

        # Check if external URLs should be followed
        if not target.follow_external:
            target_url_info = create_url_info(target.url) # Base for the entire crawl operation
            logging.debug(f"[_should_crawl_url] target_url_info.scheme: {target_url_info.scheme} for target.url: {target.url}")

            # If schemes are different, it's generally external
            if url_info.scheme != target_url_info.scheme:
                # Allow http -> https upgrade as internal for the same domain
                if not (target_url_info.scheme == 'http' and url_info.scheme == 'https' and \
                        url_info.registered_domain == target_url_info.registered_domain):
                    logging.debug(f"Skipping URL with different scheme: {url_info.normalized_url} (target scheme: {target_url_info.scheme})")
                    return False
            
            # If schemes are http/https, compare registered domains
            elif url_info.scheme in ['http', 'https']:
                if url_info.registered_domain != target_url_info.registered_domain:
                    logging.debug(f"Skipping external http/https domain: {url_info.normalized_url} (target domain: {target_url_info.registered_domain})")
                    return False
            # If schemes are both 'file', they are considered internal to this crawl operation
            elif url_info.scheme == 'file' and target_url_info.scheme == 'file':
                pass # Internal, continue with other checks
            else:
                # Catch-all for other scheme combinations when follow_external is False
                # This also covers cases where one is file and other is http, etc.
                # This also correctly handles the case where url_info.url_type might be EXTERNAL
                # because its base_url (the parent page) was None during its creation,
                # but it's actually internal with respect to the overall target.url.
                logging.debug(f"Skipping URL due to scheme/domain mismatch with follow_external=False: {url_info.normalized_url} (current scheme: {url_info.scheme}, target scheme: {target_url_info.scheme})")
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

    async def _fetch_and_process_with_backend(
        self,
        backend: CrawlerBackend,
        url_info: URLInfo,
        target: CrawlTarget,
        stats: CrawlStats,
        visited_urls: Set[str]
    ) -> Tuple[Optional[ProcessedContent], Optional[BackendCrawlResult], Optional[str]]:
        """Fetches content using the selected backend and processes it.

        Handles redirects and basic content type checks within the backend result.

        Args:
            backend: The selected CrawlerBackend instance.
            url_info: The URLInfo object for the URL being processed.
            target: The CrawlTarget configuration object.
            stats: The CrawlStats object (updated by this method).
            visited_urls: The set of visited normalized URLs (updated by this method).

        Returns:
            A tuple containing:
            - ProcessedContent object if successful, else None.
            - BackendCrawlResult object if fetch was attempted, else None.
            - The final normalized URL processed (after redirects), or None if skipped.
        """
        normalized_url = url_info.normalized_url
        backend_result: Optional[BackendCrawlResult] = None
        processed_content: Optional[ProcessedContent] = None
        final_url_processed: Optional[str] = None
        normalized_final_url: Optional[str] = None

        async with self._processing_semaphore:
            # Pass the URLInfo object and the crawler's config to the backend
            backend_result = await backend.crawl(url_info=url_info, config=self.config) # Pass url_info and config

            if not backend_result or backend_result.status != 200:
                logging.warning(f"Backend crawl failed for {normalized_url}: Status {backend_result.status if backend_result else 'N/A'}, Error: {backend_result.error if backend_result else 'Unknown'}")
                # Error will be handled by the retry loop in _process_url
                return None, backend_result, None

            # Process the content (assuming success)
            # Use the URL from the backend result, as it might have changed due to redirects
            final_url_processed = backend_result.url or normalized_url
            final_url_info = create_url_info(final_url_processed, base_url=target.url) # Re-evaluate URL info after potential redirects
            normalized_final_url = final_url_info.normalized_url

            # Re-check if the final URL was already visited (due to redirects)
            if normalized_final_url in visited_urls and normalized_final_url != normalized_url:
                 logging.debug(f"Skipping redirected URL already visited: {final_url_processed} (Normalized: {normalized_final_url})")
                 return None, backend_result, normalized_final_url # Indicate skipped due to redirect visit

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
            content_type_match = any(ct in content_type for ct in target.content_types)
            logging.debug(f"[_fetch_and_process_with_backend] Content-Type check: value='{content_type_val}', lower='{content_type}', target_types={target.content_types}, match={content_type_match}")
            if not content_type_match:
                logging.debug(f"Skipping URL {final_url_processed} due to non-allowed content type: {content_type}")
                return None, backend_result, normalized_final_url # Indicate skipped due to content type

            # Process content using ContentProcessor
            processed_content = await self.content_processor.process(backend_result.content.get('html', ''), base_url=final_url_processed) # Add await back, process is now async

            stats.successful_crawls += 1
            stats.pages_crawled += 1 # Increment pages crawled on success
            stats.bytes_processed += len(backend_result.content.get('html', '')) # Use content['html']

            return processed_content, backend_result, normalized_final_url


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
            # Check max_pages limit first
            if target.max_pages is not None and len(visited_urls) >= target.max_pages:
                logging.debug(f"Max pages limit ({target.max_pages}) reached before processing {url}. Skipping.")
                return None, [], {}

            # Normalize URL early and check if visited
            # URLs from queue should be absolute, no base needed here.
            url_info = create_url_info(url, base_url=None)
            normalized_url = url_info.normalized_url
            if not url_info.is_valid or normalized_url in visited_urls:
                logging.debug(f"Skipping invalid/visited URL: {url} (Normalized: {normalized_url})")
                logging.debug(f"[_process_url] Returning None due to invalid/visited URL.")
                return None, [], {} # Return None result, no new links, empty metrics
    
            logging.info(f"Processing URL: {normalized_url} (Depth: {current_depth})")
            logging.debug(f"[_process_url] About to add to visited_urls. Current visited_urls: {visited_urls}, normalized_url_to_add: {normalized_url}")
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
                backend = await self.backend_selector.get_backend(normalized_url)
                if backend:
                     logging.debug(f"Selected backend via selector: {backend.name}")

            if not backend:
                logging.error(f"No suitable backend found for URL: {normalized_url}")
                stats.failed_crawls += 1
                # Create a minimal CrawlResult for failure reporting
                crawl_result_data = CrawlResult(
                    target=target, stats=stats, documents=[], issues=[QualityIssue(type=IssueType.GENERAL, level=IssueLevel.ERROR, message=f"No backend for {normalized_url}")], metrics={}, processed_url=normalized_url, failed_urls=[normalized_url], errors={normalized_url: Exception("No suitable backend")} # Use GENERAL type
                )
                logging.debug(f"[_process_url] Returning crawl_result_data (no backend) with documents: {crawl_result_data.documents}")
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


                    # Call the new helper method to fetch and process
                    processed_content, backend_result, normalized_final_url = await self._fetch_and_process_with_backend(
                        backend, url_info, target, stats, visited_urls
                    )

                    # Check results from the helper method
                    if processed_content is not None:
                        # Success path from helper
                        last_error = None # Reset last error on success
                        break # Successful processing, exit retry loop
                    elif backend_result is None:
                        # This case shouldn't happen if _fetch_and_process_with_backend always returns a backend_result on attempt
                        logging.error(f"Unexpected state: _fetch_and_process_with_backend returned None for backend_result for {normalized_url}")
                        last_error = Exception("Unknown error during fetch/process helper call")
                        # Decide if retry is appropriate or break/continue
                        if attempt < self.config.max_retries - 1:
                            delay = self.retry_strategy.get_delay(attempt + 1)
                            await asyncio.sleep(delay)
                        continue # Retry
                    elif normalized_final_url is not None:
                         # Helper indicated skipping (redirect loop or wrong content type)
                         logging.debug(f"Skipping {normalized_url} as indicated by helper (final URL: {normalized_final_url})")
                         return None, [], {} # Exit _process_url as skipped
                    else:
                        # Helper indicated a fetch failure (status != 200 or other backend error)
                        logging.warning(f"Attempt {attempt + 1} failed for {normalized_url} (reported by helper): Status {backend_result.status if backend_result else 'N/A'}, Error: {backend_result.error if backend_result else 'Unknown'}")
                        last_error = Exception(f"Status {backend_result.status if backend_result else 'N/A'}: {backend_result.error if backend_result else 'Fetch error'}")
                        if attempt < self.config.max_retries - 1:
                            delay = self.retry_strategy.get_delay(attempt + 1)
                            await asyncio.sleep(delay)
                        continue # Retry

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
                logging.debug(f"[_process_url] Returning crawl_result_data (processing failed after retries) with documents: {crawl_result_data.documents}")
                return crawl_result_data, [], {} # Return failure result

            # If loop completed successfully (processed_content is not None)
            if processed_content:
                # Perform quality check *after* successful processing
                if self.quality_checker:
                    quality_issues, quality_metrics = await self.quality_checker.check_quality(processed_content)
                else:
                    quality_issues, quality_metrics = [], {}

                # Prepare successful result data
                # Construct a CrawlResult object
                doc_dict = {
                    'url': normalized_final_url,
                    'title': processed_content.title,
                    'content': processed_content.content,
                    'metadata': processed_content.metadata,
                    'assets': processed_content.assets
                }

                crawl_result_data = CrawlResult(
                    target=target,
                    stats=stats, # This is master_stats, passed by ref
                    documents=[doc_dict],
                    issues=quality_issues,
                    metrics=quality_metrics, # This will also be returned in the tuple
                    structure=processed_content.structure, # Use structure from processed_content
                    processed_url=normalized_final_url, # Use final URL from helper
                    failed_urls=[], # No failures in this path
                    errors={}       # No errors in this path
                    # crawled_pages is populated in the main crawl() method
                )
                
                stats.quality_issues += len(quality_issues) # Update master_stats

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
                            resolved_link_info = create_url_info(absolute_href)
                            if self._should_crawl_url(resolved_link_info, target):
                                new_links_to_crawl.append((resolved_link_info.normalized_url, current_depth + 1))


                # Return metrics along with result and links
                logging.debug(f"[_process_url] Returning crawl_result_data with documents: {crawl_result_data.documents if crawl_result_data else 'None'}")
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
            logging.debug(f"[_process_url] Returning crawl_result_data (unhandled exception) with documents: {crawl_result_data.documents}")
            return crawl_result_data, [], {}


    async def _initialize_crawl_queue(self, target: CrawlTarget) -> Tuple[collections.deque, str]:
        """Initializes the crawl queue based on the target URL or package name.

        Handles potential package name discovery and URL resolution.

        Args:
            target: The CrawlTarget configuration object.

        Returns:
            A tuple containing the initialized deque and the actual starting URL used.
        """
        queue = collections.deque()
        initial_url = target.url
        start_url_for_id = initial_url
        queue_initial_content: Union[List[Tuple[str, int]], Tuple[Tuple[str, int], ...]] = []

        # Attempt to identify project and discover URL if target looks like a package name
        is_potential_package = "://" not in initial_url
        discovered_doc_url = None
        if is_potential_package:
            logging.info(f"Target '{initial_url}' looks like a package name. Attempting discovery...")
            discovered_doc_url = await self.project_identifier.discover_doc_url(initial_url)
            if discovered_doc_url:
                logging.info(f"Discovered documentation URL for '{initial_url}': {discovered_doc_url}")
                logging.debug(f"[crawler.crawl] Setting discovered_doc_url for queue: {discovered_doc_url} (target.url was {target.url})")
                queue_initial_content = ((discovered_doc_url, 0),)
                start_url_for_id = discovered_doc_url
            else:
                logging.error(f"Could not resolve target '{initial_url}' as a URL or discover a documentation URL for it as a package.")
                raise ValueError(f"Invalid target: '{initial_url}' is not a valid URL and documentation URL discovery failed.")
        else:
            logging.debug(f"[crawler.crawl] Setting initial_url for queue: {initial_url} (target.url was {target.url})")
            queue_initial_content = ((initial_url, 0),)

        if queue_initial_content:
            if isinstance(queue_initial_content, tuple) and len(queue_initial_content) > 0:
                 queue.append(queue_initial_content[0])
            elif isinstance(queue_initial_content, list) and len(queue_initial_content) > 0:
                 queue.append(queue_initial_content[0])

        logging.debug(f"[crawler.crawl] Initialized queue with content, id: {id(queue)}, content: {list(queue)}")
        return queue, start_url_for_id


    async def crawl(
        self,
        target_url: str,
        depth: int, 
        follow_external: bool, 
        content_types: List[str], 
        exclude_patterns: List[str], 
        required_patterns: List[str], 
        max_pages: Optional[int], 
        allowed_paths: List[str], 
        excluded_paths: List[str], 
        websocket=None
    ) -> CrawlResult:
        """Start the crawl process for a given target."""
        
        target = CrawlTarget(
            url=target_url,
            depth=depth,
            follow_external=follow_external,
            content_types=content_types,
            exclude_patterns=exclude_patterns,
            required_patterns=required_patterns,
            max_pages=max_pages,
            allowed_paths=allowed_paths,
            excluded_paths=excluded_paths
        )
        logging.debug(f"[crawler.crawl ENTRY] Constructed target id: {id(target)}, target.url: {target.url}")
        
        logging.debug(f"[crawler.crawl START] Instance ID: {id(self)}, Initial self._crawled_urls: {self._crawled_urls}")
        self._crawled_urls.clear() # Ensure a fresh start for this crawl operation
        logging.debug(f"[crawler.crawl AFTER CLEAR] Instance ID: {id(self)}, self._crawled_urls: {self._crawled_urls}")
        master_stats = CrawlStats()
        all_documents = []
        all_issues = []
        all_metrics: Dict[str, Dict[str, Any]] = {} # Store metrics per URL
        all_failed_urls: List[str] = [] # Initialize list for failed URLs
        all_errors: Dict[str, Exception] = {} # Initialize dict for errors
        visited_urls: Set[str] = set() # Track visited normalized URLs
        crawled_pages: Dict[str, Any] = {} # Track crawled pages

        # Define initial_url and is_potential_package here so they are in scope for the later except block
        initial_url_for_queue_init = target.url # Use a distinct name for clarity
        is_potential_package_for_queue_init = "://" not in initial_url_for_queue_init

        # Initialize queue using the new helper method
        # Pass the correctly scoped variables to the helper or use target.url directly if that's what _initialize_crawl_queue expects
        queue, start_url_for_id = await self._initialize_crawl_queue(target) # Assuming _initialize_crawl_queue uses target.url


        # Initial project identification based on the *actual* starting URL
        try:
            if "://" in start_url_for_id:
                project_identity = await self.project_identifier.identify_from_url(start_url_for_id)
                logging.info(f"Initial project identity based on '{start_url_for_id}': {project_identity}")
            else:
                project_identity = ProjectIdentity(name=start_url_for_id, type=ProjectType.UNKNOWN)
                logging.info(f"Initial project identity based on package name '{start_url_for_id}': {project_identity}")

            if self.duckduckgo and project_identity.name != "unknown":
                search_queries = self._generate_search_queries(start_url_for_id, project_identity)
                ddg_discovered_urls = set()
                for query in search_queries:
                    urls = await self.duckduckgo.search(query)
                    for url_item in urls: # Renamed url to url_item to avoid conflict
                        if urlparse(url_item).scheme in ['http', 'https']:
                            ddg_discovered_urls.add(url_item)
                logging.info(f"Discovered {len(ddg_discovered_urls)} potential URLs via DuckDuckGo.")
                for url_item in ddg_discovered_urls: # Renamed url to url_item
                    if url_item not in [item[0] for item in queue]: 
                        queue.append((url_item, 0))
        except Exception as e:
            logging.error(f"Error during initial URL identification or DuckDuckGo search: {e}")
            # Use the correctly scoped variables here
            if not queue and not is_potential_package_for_queue_init: # Use the new variable name
                logging.warning(f"Adding original target URL '{initial_url_for_queue_init}' back to queue after error.") # Use the new variable name
                queue.append((initial_url_for_queue_init, 0)) # Use the new variable name
        
        logging.debug(f"[crawler.crawl] Queue after initial population and DDG (if any), id: {id(queue)}, content: {list(queue)}") 
        processed_pages = 0
        while queue and (target.max_pages is None or len(visited_urls) < target.max_pages):
            url_string, current_depth = queue.popleft()

            try:
                 base_for_check = start_url_for_id if "://" in start_url_for_id else None
                 temp_info = create_url_info(url_string, base_url=base_for_check)
                 normalized_check_url = temp_info.normalized_url
                 if not temp_info.is_valid or normalized_check_url in visited_urls:
                      continue 
            except Exception as e:
                 logging.warning(f"Skipping URL due to normalization error before processing: {url_string} ({e})")
                 continue

            try:
                async with Timer(f"Process URL {url_string}"): 
                    result_data, new_links, metrics = await self._process_url(
                        url_string, current_depth, target, master_stats, visited_urls 
                    )

                if result_data:
                    processed_pages += 1 
                    all_documents.extend(result_data.documents)
                    all_issues.extend(result_data.issues)
                    all_failed_urls.extend(result_data.failed_urls)
                    all_errors.update(result_data.errors)
                    processed_url_key = result_data.processed_url or url_string
                    if metrics: 
                         all_metrics[processed_url_key] = metrics
                    
                    if result_data.documents:
                        crawled_pages[processed_url_key] = ProcessedContent(
                            url=processed_url_key,
                            title=result_data.documents[0].get('title', ''),
                            content=result_data.documents[0].get('content', {}),
                            metadata=result_data.documents[0].get('metadata', {}),
                            assets=result_data.documents[0].get('assets', []),
                            structure=result_data.structure
                        )

                    if self.document_organizer and result_data.documents:
                        try:
                            doc_dict = result_data.documents[0]
                            processed_content_obj = ProcessedContent(
                                url=doc_dict.get('url', result_data.processed_url or url_string), 
                                title=doc_dict.get('title', ''),
                                content=doc_dict.get('content', {}),
                                metadata=doc_dict.get('metadata', {}),
                                assets=doc_dict.get('assets', {}),
                                structure=result_data.structure 
                            )
                            doc_org_id = self.document_organizer.add_document(processed_content_obj)
                            logging.debug(f"Added document {processed_content_obj.url} to organizer with id {doc_org_id}")
                        except Exception as org_exc:
                            logging.error(f"Error adding document {result_data.processed_url or url_string} to organizer: {org_exc}", exc_info=True)
                    
                    for link_url, link_depth in new_links:
                        if link_url not in visited_urls:
                                queue.append((link_url, link_depth))

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

                elif result_data is None: 
                     pass 
                else: 
                     pass


            except Exception as e:
                logging.error(f"Critical error during crawl loop for {url_string}: {e}", exc_info=True)
                master_stats.failed_crawls += 1
                all_issues.append(QualityIssue(type=IssueType.GENERAL, level=IssueLevel.ERROR, message=f"Crawler loop error: {str(e)}"))
                if websocket:
                    progress = {
                        "type": "progress",
                        "url": url_string,
                        "status": "error",
                        "depth": current_depth,
                        "pages_processed": processed_pages,
                        "queue_size": len(queue),
                        "issues_found": 1, 
                        "documents_found": 0
                    }
                    await websocket.send_json(progress)


        master_stats.end_time = datetime.now(UTC)
        master_stats.total_time = (master_stats.end_time - master_stats.start_time).total_seconds()
        logging.debug(f"[crawler.crawl] Final visited_urls before setting stats.pages_crawled: {visited_urls}")
        master_stats.pages_crawled = len(visited_urls) 
        if master_stats.pages_crawled > 0: 
            master_stats.average_time_per_page = master_stats.total_time / master_stats.pages_crawled
            
        # Copy all the visited_urls to the crawler's _crawled_urls for test verification
        self._crawled_urls.update(visited_urls)
        
        # Set structure from document organizer results
        structure_from_organizer = None
        if self.document_organizer:
            try:
                # Get the organized structure from the document organizer
                organize_result = await self.document_organizer.organize(all_documents)
                if organize_result and isinstance(organize_result, dict):
                    structure_from_organizer = organize_result.get("structure", None)
            except Exception as e:
                logging.error(f"Error getting structure from document organizer: {e}", exc_info=True)
        
        # Save the _crawled_urls set in the result for testing before returning
        # This allows tests like test_url_discovery to verify the URLs that were actually crawled
        final_result = CrawlResult(
            target=target, # Use the locally created target
            stats=master_stats,
            documents=all_documents,
            issues=all_issues,
            metrics=all_metrics, 
            crawled_pages=crawled_pages, 
            failed_urls=list(set(all_failed_urls)), 
            errors=all_errors,
            structure=structure_from_organizer, # Set the structure from document organizer
            crawled_urls=self._crawled_urls.copy() # Save the set of crawled URLs
        )

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
                        resolved_link_info = create_url_info(absolute_href)
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
