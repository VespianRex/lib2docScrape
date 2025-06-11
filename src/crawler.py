import asyncio
import logging
import os
import re
import time
import traceback
from datetime import UTC, datetime, timezone
from typing import Any, Optional, Union

from pydantic import BaseModel, Field

from .backends.base import CrawlerBackend
from .backends.base import CrawlResult as BackendCrawlResult
from .backends.http_backend import HTTPBackend, HTTPBackendConfig
from .backends.selector import BackendCriteria, BackendSelector
from .organizers.doc_organizer import DocumentOrganizer
from .processors.content_processor import ContentProcessor, ProcessedContent
from .processors.quality_checker import (
    IssueLevel as PQ_IssueLevel,
)
from .processors.quality_checker import (
    IssueType as PQ_IssueType,
)
from .processors.quality_checker import (
    QualityChecker as PQ_QualityChecker,
)
from .processors.quality_checker import (
    QualityIssue as PQ_QualityIssue,
)
from .utils.helpers import RateLimiter, RetryStrategy
from .utils.project_identifier import ProjectIdentifier
from .utils.search import DuckDuckGoSearch
from .utils.url.factory import create_url_info
from .utils.url.info import URLInfo

# Set up logger
logger = logging.getLogger(__name__)

# ProjectIdentifier class removed and moved to src.utils.project_identifier
# DuckDuckGoSearch class moved to src.utils.search


class CrawlTarget(BaseModel):
    """Model for crawl target configuration."""

    url: str = Field(default="https://docs.python.org/3/")  # Default to Python docs
    depth: int = Field(default=1)
    follow_external: bool = Field(default=False)
    content_types: list[str] = Field(default=["text/html"])
    exclude_patterns: list[str] = Field(default_factory=list)
    required_patterns: list[str] = Field(
        default_factory=list
    )  # Changed from ["/3/"] to empty list
    max_pages: Optional[int] = Field(
        default=1000
    )  # Changed from None to 1000 to match test expectations
    allowed_paths: list[str] = Field(default_factory=list)
    excluded_paths: list[str] = Field(default_factory=list)


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
    documents: list[dict[str, Any]]
    issues: list[PQ_QualityIssue]  # Use aliased QualityIssue
    metrics: dict[str, Any]
    structure: Optional[list[dict[str, Any]]] = None
    processed_url: Optional[
        str
    ] = None  # Added to store the final URL processed (after redirects, normalization)
    failed_urls: list[str] = Field(
        default_factory=list
    )  # List of URLs that failed to crawl
    errors: dict[str, Exception] = Field(
        default_factory=dict
    )  # Map of URLs to their exceptions
    crawled_pages: dict[str, Any] = Field(
        default_factory=dict
    )  # Dictionary of crawled pages
    crawled_urls: set[str] = Field(
        default_factory=set
    )  # Set of normalized URLs that were crawled

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
    headers: dict[str, str] = Field(default_factory=dict)
    use_duckduckgo: bool = True
    duckduckgo_max_results: int = 10
    batch_size: int = (
        5  # Kept for potential future use, but not used in current crawl logic
    )
    # Add missing attributes that the new implementation expects
    max_async_tasks: int = 10  # Alias for concurrent_requests
    rate_limit: float = 0.2  # seconds between requests (1/requests_per_second)
    max_depth: int = 3  # Maximum crawl depth
    max_pages: int = 1000  # Maximum pages to crawl


# DuckDuckGoSearch class has been moved to src/utils/search.py
class DocumentationCrawler:
    """Main crawler orchestrator."""

    def __init__(
        self,
        config: Optional[CrawlerConfig] = None,
        backend_selector: Optional[BackendSelector] = None,
        content_processor: Optional[ContentProcessor] = None,
        quality_checker: Optional[
            PQ_QualityChecker
        ] = None,  # Use aliased PQ_QualityChecker
        document_organizer: Optional[DocumentOrganizer] = None,
        loop: Optional[Any] = None,  # Restored Any type
        backend: Optional[
            CrawlerBackend
        ] = None,  # Corrected syntax: Optional[CrawlerBackend]
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
        logging.debug(
            f"Crawler __init__ received backend_selector: id={id(backend_selector)}"
        )
        # Optional event loop passed for testing
        self.loop = loop
        if backend_selector:
            logging.debug(
                f"Received selector initial backends: {list(backend_selector._backends.keys())}"
            )
        self.backend_selector = backend_selector or BackendSelector()
        self.content_processor = content_processor or ContentProcessor()
        self.quality_checker = (
            quality_checker or PQ_QualityChecker()
        )  # Use aliased PQ_QualityChecker
        self.document_organizer = document_organizer or DocumentOrganizer()

        # If a specific backend is provided, use it directly
        self.direct_backend = backend
        # Also set self.backend for direct access in tests
        self.backend = backend
        logging.debug(f"Direct backend provided: {backend is not None}")

        logging.debug(
            f"Crawler assigned self.backend_selector: id={id(self.backend_selector)}"
        )
        logging.debug(
            f"Assigned selector backends BEFORE http registration: {list(self.backend_selector._backends.keys())}"
        )

        # Set up HTTP backend
        http_backend = HTTPBackend(
            HTTPBackendConfig(
                timeout=self.config.request_timeout,
                verify_ssl=self.config.verify_ssl,
                follow_redirects=self.config.follow_redirects,
                headers={"User-Agent": self.config.user_agent},
            )
        )

        # Register HTTP backend with criteria
        self.backend_selector.register_backend(
            name=http_backend.name,  # Use the name attribute
            backend=http_backend,  # Pass the instance
            criteria=BackendCriteria(  # Pass the criteria
                priority=1,
                content_types=["text/html"],
                url_patterns=["http://", "https://"],  # Match all HTTP(S) URLs
                max_load=0.8,
                min_success_rate=0.7,
            ),
        )
        logging.debug(
            f"Assigned selector backends AFTER http registration: {list(self.backend_selector._backends.keys())}"
        )

        self.rate_limiter = RateLimiter(self.config.requests_per_second)
        self.retry_strategy = RetryStrategy(
            max_retries=self.config.max_retries
        )  # Corrected closing parenthesis

        self._crawled_urls: set[str] = set()  # Store normalized URLs
        self._processing_semaphore = asyncio.Semaphore(self.config.concurrent_requests)
        self.client_session = None  # Session managed by HTTPBackend now

        self.duckduckgo = (
            DuckDuckGoSearch(self.config.duckduckgo_max_results)
            if self.config.use_duckduckgo
            else None
        )
        # self.crawl_tree = {} # Removed, not used in new logic
        # self.current_tasks = set() # Removed, managed by asyncio.gather
        self.project_identifier = ProjectIdentifier()

    def _find_links_recursive(
        self, html_content: str, base_url: str = None
    ) -> list[str]:
        """Extract links from HTML content."""
        import re
        from urllib.parse import urljoin

        links = []
        if not html_content:
            return links

        # Simple regex to find href attributes in HTML
        href_pattern = r'href=["\']([^"\']+)["\']'
        matches = re.findall(href_pattern, html_content, re.IGNORECASE)

        for match in matches:
            # Skip empty links, anchors, and javascript
            if not match or match.startswith("#") or match.startswith("javascript:"):
                continue

            # Resolve relative URLs if base_url is provided
            if base_url and not match.startswith(("http://", "https://", "file://")):
                try:
                    resolved_url = urljoin(base_url, match)
                    links.append(resolved_url)
                except Exception:
                    continue
            else:
                links.append(match)

        return links

    def _extract_links_from_element(
        self, element, url_info: URLInfo, depth: int
    ) -> list[tuple[str, int]]:
        """Extract links from a single structure element."""
        from urllib.parse import urljoin

        links = []

        if isinstance(element, dict):
            # Check if the current element itself is a link
            if element.get("type") == "link" and element.get("url"):
                # Resolve relative URLs
                try:
                    link_url = element["url"]
                    if not link_url.startswith(("http://", "https://")):
                        # Relative URL - resolve against base URL
                        link_url = urljoin(url_info.normalized_url, link_url)
                    links.append((link_url, depth))
                except Exception as e:
                    logging.warning(
                        f"Error processing link URL {element.get('url')}: {e}"
                    )

            # Check for 'href' attribute as well
            if element.get("href"):
                try:
                    link_url = element["href"]
                    if not link_url.startswith(("http://", "https://")):
                        # Relative URL - resolve against base URL
                        link_url = urljoin(url_info.normalized_url, link_url)
                    links.append((link_url, depth))
                except Exception as e:
                    logging.warning(
                        f"Error processing href URL {element.get('href')}: {e}"
                    )

            # Recursively check children
            if "children" in element and isinstance(element["children"], list):
                for child in element["children"]:
                    links.extend(
                        self._extract_links_from_element(child, url_info, depth)
                    )

        elif isinstance(element, list):
            # Recursively check items in the list
            for item in element:
                if isinstance(item, dict):
                    links.extend(
                        self._extract_links_from_element(item, url_info, depth)
                    )

        return links

    def _should_crawl_url(self, url_info: URLInfo, target: CrawlTarget) -> bool:
        """Check if a URL should be crawled based on target rules."""
        if not url_info.is_valid:
            logging.debug(
                f"Skipping invalid URL: {url_info.raw_url} ({url_info.error_message})"
            )
            return False

        normalized_url = url_info.normalized_url

        # Check if already crawled
        if normalized_url in self._crawled_urls:
            logging.debug(f"Skipping already crawled URL: {normalized_url}")
            return False

        # Check scheme
        if url_info.scheme not in ["http", "https", "file"]:
            logging.debug(f"Skipping non-HTTP/S/file URL: {normalized_url}")
            return False

        # Check if external URLs should be followed
        if not target.follow_external:
            target_url_info = create_url_info(
                target.url
            )  # Base for the entire crawl operation
            logging.debug(
                f"[_should_crawl_url] target_url_info.scheme: {target_url_info.scheme} for target.url: {target.url}"
            )

            # If schemes are different, it's generally external
            if url_info.scheme != target_url_info.scheme:
                # Allow http -> https upgrade as internal for the same domain
                if not (
                    target_url_info.scheme == "http"
                    and url_info.scheme == "https"
                    and url_info.registered_domain == target_url_info.registered_domain
                ):
                    logging.debug(
                        f"Skipping URL with different scheme: {url_info.normalized_url} (target scheme: {target_url_info.scheme})"
                    )
                    return False

            # If schemes are http/https, compare registered domains
            elif url_info.scheme in ["http", "https"]:
                if url_info.registered_domain != target_url_info.registered_domain:
                    logging.debug(
                        f"Skipping external http/https domain: {url_info.normalized_url} (target domain: {target_url_info.registered_domain})"
                    )
                    return False
            # If schemes are both 'file', they are considered internal to this crawl operation
            elif url_info.scheme == "file" and target_url_info.scheme == "file":
                pass  # Internal, continue with other checks
            else:
                # Catch-all for other scheme combinations when follow_external is False
                # This also covers cases where one is file and other is http, etc.
                # This also correctly handles the case where url_info.url_type might be EXTERNAL
                # because its base_url (the parent page) was None during its creation,
                # but it's actually internal with respect to the overall target.url.
                logging.debug(
                    f"Skipping URL due to scheme/domain mismatch with follow_external=False: {url_info.normalized_url} (current scheme: {url_info.scheme}, target scheme: {target_url_info.scheme})"
                )
                return False

        # Check exclude patterns
        if any(
            re.search(pattern, normalized_url) for pattern in target.exclude_patterns
        ):
            logging.debug(f"Skipping URL due to exclude pattern: {normalized_url}")
            return False

        # Check required patterns (if any)
        if target.required_patterns and not any(
            re.search(pattern, normalized_url) for pattern in target.required_patterns
        ):
            logging.debug(
                f"Skipping URL due to missing required pattern: {normalized_url}"
            )
            return False

        # Check allowed paths (if any)
        if target.allowed_paths:
            path = url_info.path
            if not any(path.startswith(allowed) for allowed in target.allowed_paths):
                logging.debug(
                    f"Skipping URL due to not being in allowed paths: {normalized_url}"
                )
                return False

        # Check excluded paths (if any)
        if target.excluded_paths:
            path = url_info.path
            if any(path.startswith(excluded) for excluded in target.excluded_paths):
                logging.debug(
                    f"Skipping URL due to being in excluded paths: {normalized_url}"
                )
                return False

        return True

    async def _fetch_and_process_with_backend(
        self,
        backend: CrawlerBackend,
        url_info: URLInfo,
        target: CrawlTarget,
        stats: CrawlStats,
        visited_urls: set[str],
    ) -> tuple[Optional[ProcessedContent], Optional[BackendCrawlResult], Optional[str]]:
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
            backend_result = await backend.crawl(
                url_info=url_info, config=self.config
            )  # Pass url_info and config

            if not backend_result or backend_result.status != 200:
                logging.warning(
                    f"Backend crawl failed for {normalized_url}: Status {backend_result.status if backend_result else 'N/A'}, Error: {backend_result.error if backend_result else 'Unknown'}"
                )
                # Error will be handled by the retry loop in _process_url
                return None, backend_result, None

            # Process the content (assuming success)
            # Use the URL from the backend result, as it might have changed due to redirects
            final_url_processed = backend_result.url or normalized_url
            final_url_info = create_url_info(
                final_url_processed, base_url=target.url
            )  # Re-evaluate URL info after potential redirects
            normalized_final_url = final_url_info.normalized_url

            # Re-check if the final URL was already visited (due to redirects)
            if (
                normalized_final_url in visited_urls
                and normalized_final_url != normalized_url
            ):
                logging.debug(
                    f"Skipping redirected URL already visited: {final_url_processed} (Normalized: {normalized_final_url})"
                )
                return (
                    None,
                    backend_result,
                    normalized_final_url,
                )  # Indicate skipped due to redirect visit

            # Add final URL to visited if different from initial normalized
            if normalized_final_url != normalized_url:
                visited_urls.add(normalized_final_url)

            # Check content type if backend provides it
            # Case-insensitive header lookup
            headers_dict = backend_result.metadata.get("headers", {})
            content_type_val = ""
            for key, value in headers_dict.items():
                if key.lower() == "content-type":
                    content_type_val = value
                    break
            content_type = content_type_val.lower()
            content_type_match = any(ct in content_type for ct in target.content_types)
            logging.debug(
                f"[_fetch_and_process_with_backend] Content-Type check: value='{content_type_val}', lower='{content_type}', target_types={target.content_types}, match={content_type_match}"
            )
            if not content_type_match:
                logging.debug(
                    f"Skipping URL {final_url_processed} due to non-allowed content type: {content_type}"
                )
                return (
                    None,
                    backend_result,
                    normalized_final_url,
                )  # Indicate skipped due to content type

            # Process content using ContentProcessor
            processed_content = await self.content_processor.process(
                backend_result.content.get("html", ""), base_url=final_url_processed
            )  # Add await back, process is now async

            # Add document to organizer if we have one and the content processing was successful
            if self.document_organizer and processed_content:
                try:
                    logging.debug(
                        f"Backend processing: Adding document to organizer: url={processed_content.url}, title={processed_content.title}"
                    )
                    doc_org_id = self.document_organizer.add_document(processed_content)
                    logging.debug(
                        f"Backend processing: Added document {processed_content.url} to organizer with id {doc_org_id}"
                    )
                except Exception as org_exc:
                    logging.error(
                        f"Backend processing: Error adding document {final_url_processed} to organizer: {org_exc}",
                        exc_info=True,
                    )

            stats.successful_crawls += 1
            stats.pages_crawled += 1  # Increment pages crawled on success
            stats.bytes_processed += len(
                backend_result.content.get("html", "")
            )  # Use content['html']

            return processed_content, backend_result, normalized_final_url

    async def _process_url(
        self,
        url: str,
        current_depth: int,
        target: CrawlTarget,
        stats: CrawlStats,
        visited_urls: set[str],
    ) -> tuple[Optional[CrawlResult], list[tuple[str, int]], dict[str, Any]]:
        """Process a single URL, returning its result and discovered links."""
        new_links_to_crawl = []
        crawl_result_data = None
        quality_metrics = {}  # Initialize quality metrics
        normalized_url = url  # Default if URLInfo fails

        try:
            # Check max_pages limit first
            if target.max_pages is not None and len(visited_urls) >= target.max_pages:
                logging.debug(
                    f"Max pages limit ({target.max_pages}) reached before processing {url}. Skipping."
                )
                return None, [], {}

            # Normalize URL early and check if visited
            # URLs from queue should be absolute, no base needed here.
            url_info = create_url_info(url, base_url=None)
            normalized_url = url_info.normalized_url
            if not url_info.is_valid or normalized_url in visited_urls:
                logging.debug(
                    f"Skipping invalid/visited URL: {url} (Normalized: {normalized_url})"
                )
                logging.debug(
                    "[_process_url] Returning None due to invalid/visited URL."
                )
                return None, [], {}  # Return None result, no new links, empty metrics

            logging.info(f"Processing URL: {normalized_url} (Depth: {current_depth})")
            logging.debug(
                f"[_process_url] About to add to visited_urls. Current visited_urls: {visited_urls}, normalized_url_to_add: {normalized_url}"
            )
            visited_urls.add(normalized_url)  # Add normalized URL to visited set

            # Handle file:// URLs differently
            if url_info.scheme == "file":
                (
                    file_result,
                    file_new_links,
                    file_metrics,
                ) = await self._process_file_url(url_info, current_depth, target, stats)

                # Add document to organizer if we have one and the file processing was successful
                logging.debug(
                    f"File processing result: document_organizer={self.document_organizer is not None}, file_result={file_result is not None}, file_result.documents={file_result.documents if file_result else None}"
                )
                logging.debug(
                    f"File result type: {type(file_result)}, File result: {file_result}"
                )
                if self.document_organizer and file_result and file_result.documents:
                    try:
                        doc_dict = file_result.documents[0]
                        logging.debug(
                            f"Processing file document for organizer: {doc_dict}"
                        )
                        # Create ProcessedContent with proper field mapping
                        processed_content_obj = ProcessedContent(
                            url=doc_dict.get(
                                "url",
                                file_result.processed_url or url_info.normalized_url,
                            ),
                            title=doc_dict.get("title", "Untitled Document"),
                            content=doc_dict.get("content", {})
                            if isinstance(doc_dict.get("content"), dict)
                            else {"formatted_content": doc_dict.get("content", "")},
                            metadata=doc_dict.get("metadata", {}),
                            assets=doc_dict.get("assets", {})
                            if isinstance(doc_dict.get("assets"), dict)
                            else {
                                "images": [],
                                "stylesheets": [],
                                "scripts": [],
                                "media": [],
                            },
                            structure=file_result.structure or [],
                            headings=doc_dict.get("headings", []),
                            errors=[],
                        )
                        logging.debug(
                            f"Created ProcessedContent object: url={processed_content_obj.url}, title={processed_content_obj.title}"
                        )
                        doc_org_id = self.document_organizer.add_document(
                            processed_content_obj
                        )
                        # Store the doc_id in the document for later reference
                        doc_dict["doc_id"] = doc_org_id
                        # Also store URL to doc_id mapping in the organizer's URL to doc ID map
                        if hasattr(self.document_organizer, "url_to_doc_id"):
                            self.document_organizer.url_to_doc_id[
                                processed_content_obj.url
                            ] = doc_org_id
                        logging.debug(
                            f"Added file document {processed_content_obj.url} to organizer with id {doc_org_id}"
                        )
                    except Exception as org_exc:
                        logging.error(
                            f"Error adding file document {file_result.processed_url or url_info.normalized_url} to organizer: {org_exc}",
                            exc_info=True,
                        )
                else:
                    logging.debug(
                        f"Skipping document organizer for file: document_organizer={self.document_organizer is not None}, file_result={file_result is not None}, has_documents={file_result.documents if file_result else 'N/A'}"
                    )

                return file_result, file_new_links, file_metrics

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
                    target=target,
                    stats=stats,
                    documents=[],
                    issues=[
                        PQ_QualityIssue(  # Use aliased QualityIssue, IssueType, IssueLevel
                            type=PQ_IssueType.GENERAL,
                            level=PQ_IssueLevel.ERROR,
                            message=f"No backend for {normalized_url}",
                        )
                    ],
                    metrics={},
                    processed_url=normalized_url,
                    failed_urls=[normalized_url],
                    errors={normalized_url: Exception("No suitable backend")},
                )
                logging.debug(
                    f"[_process_url] Returning crawl_result_data (no backend) with documents: {crawl_result_data.documents}"
                )
                return crawl_result_data, [], {}

            # Process with retry strategy
            processed_content: Optional[ProcessedContent] = None
            last_error = None
            backend_result: Optional[BackendCrawlResult] = None

            for attempt in range(self.config.max_retries):
                try:
                    logging.debug(
                        f"Attempt {attempt + 1}/{self.config.max_retries} for {normalized_url}"
                    )
                    # Apply rate limiting - prioritize backend's external limiter if it exists and is not None
                    limiter_to_use = None
                    if hasattr(backend, "_external_rate_limiter"):
                        backend_limiter = getattr(
                            backend, "_external_rate_limiter", None
                        )
                        if backend_limiter is not None:
                            limiter_to_use = backend_limiter

                    if limiter_to_use is None:
                        limiter_to_use = (
                            self.rate_limiter
                        )  # Fallback to crawler's limiter

                    wait_time = await limiter_to_use.acquire()
                    # Ensure wait_time is a float before comparison
                    if isinstance(wait_time, (int, float)) and wait_time > 0:
                        logging.debug(
                            f"Rate limit hit for {normalized_url}, sleeping for {wait_time:.4f}s (using {'backend' if limiter_to_use is not self.rate_limiter else 'crawler'} limiter)"
                        )
                        await asyncio.sleep(wait_time)
                    elif not isinstance(wait_time, (int, float)):
                        logging.warning(
                            f"Rate limiter acquire() returned non-numeric value: {type(wait_time)}. Skipping sleep."
                        )

                    # Call the new helper method to fetch and process
                    (
                        processed_content,
                        backend_result,
                        normalized_final_url,
                    ) = await self._fetch_and_process_with_backend(
                        backend, url_info, target, stats, visited_urls
                    )

                    # Check results from the helper method
                    if processed_content is not None:
                        # Success path from helper
                        last_error = None  # Reset last error on success
                        break  # Successful processing, exit retry loop
                    elif backend_result is None:
                        # This case shouldn't happen if _fetch_and_process_with_backend always returns a backend_result on attempt
                        logging.error(
                            f"Unexpected state: _fetch_and_process_with_backend returned None for backend_result for {normalized_url}"
                        )
                        last_error = Exception(
                            "Unknown error during fetch/process helper call"
                        )
                        # Decide if retry is appropriate or break/continue
                        if attempt < self.config.max_retries - 1:
                            delay = self.retry_strategy.get_delay(attempt + 1)
                            await asyncio.sleep(delay)
                        continue  # Retry
                    elif normalized_final_url is not None:
                        # Helper indicated skipping (redirect loop or wrong content type)
                        logging.debug(
                            f"Skipping {normalized_url} as indicated by helper (final URL: {normalized_final_url})"
                        )
                        return None, [], {}  # Exit _process_url as skipped
                    else:
                        # Helper indicated a fetch failure (status != 200 or other backend error)
                        logging.warning(
                            f"Attempt {attempt + 1} failed for {normalized_url} (reported by helper): Status {backend_result.status if backend_result else 'N/A'}, Error: {backend_result.error if backend_result else 'Unknown'}"
                        )
                        last_error = Exception(
                            f"Status {backend_result.status if backend_result else 'N/A'}: {backend_result.error if backend_result else 'Fetch error'}"
                        )
                        if attempt < self.config.max_retries - 1:
                            delay = self.retry_strategy.get_delay(attempt + 1)
                            await asyncio.sleep(delay)
                        continue  # Retry

                except Exception as e:
                    last_error = e
                    logging.error(
                        f"Error during attempt {attempt + 1} for {normalized_url}: {str(e)}"
                    )
                    if attempt < self.config.max_retries - 1:
                        delay = self.retry_strategy.get_delay(attempt + 1)
                        await asyncio.sleep(delay)
                    # Continue to next retry or fail after loop

            # After retry loop
            if last_error:
                stats.failed_crawls += 1
                logging.error(
                    f"Processing failed for {normalized_url} after {self.config.max_retries} attempts: {str(last_error)}"
                )
                # Include exception type name in the message
                error_type_name = type(last_error).__name__
                error_str = str(last_error)
                # Corrected message format
                issue_message = f"Failed after retries: {error_type_name}({error_str})"

                crawl_result_data = CrawlResult(
                    target=target,
                    stats=stats,
                    documents=[],
                    issues=[
                        PQ_QualityIssue(  # Use aliased QualityIssue, IssueType, IssueLevel
                            type=PQ_IssueType.GENERAL,
                            level=PQ_IssueLevel.ERROR,
                            message=issue_message,
                            location=normalized_url,  # Use 'location' for URL
                        )
                    ],
                    metrics={},
                    processed_url=normalized_url,
                    failed_urls=[normalized_url],
                    errors={normalized_url: last_error},
                )
                logging.debug(
                    f"[_process_url] Returning crawl_result_data (processing failed after retries) with documents: {crawl_result_data.documents}"
                )
                return crawl_result_data, [], {}  # Return failure result

            # If loop completed successfully (processed_content is not None)
            if processed_content:
                # Perform quality check *after* successful processing
                if self.quality_checker:
                    (
                        quality_issues,
                        quality_metrics,
                    ) = await self.quality_checker.check_quality(processed_content)
                else:
                    quality_issues, quality_metrics = [], {}

                # Prepare successful result data
                # Construct a CrawlResult object
                doc_dict = {
                    "url": normalized_final_url,
                    "title": processed_content.title,
                    "content": processed_content.content,
                    "metadata": processed_content.metadata,
                    "assets": processed_content.assets,
                }

                crawl_result_data = CrawlResult(
                    target=target,
                    stats=stats,  # This is master_stats, passed by ref
                    documents=[doc_dict],
                    issues=quality_issues,
                    metrics=quality_metrics,  # This will also be returned in the tuple
                    structure=processed_content.structure,  # Use structure from processed_content
                    processed_url=normalized_final_url,  # Use final URL from helper
                )

                # Update stats with crawled page information
                stats.successful_crawls += 1
                stats.pages_crawled += 1
                stats.bytes_processed += len(processed_content.content.get("html", ""))

                # Add to crawled URLs
                self._crawled_urls.add(normalized_final_url)

                logging.info(
                    f"Successfully processed and crawled URL: {normalized_final_url}"
                )
                logging.debug(
                    f"[_process_url] Returning successful crawl_result_data with documents: {crawl_result_data.documents}"
                )
                return crawl_result_data, new_links_to_crawl, quality_metrics

        except Exception as e:
            logging.error(
                f"Unexpected error processing URL {url}: {type(e).__name__}({e})"
            )
            # Handle specific cases for file URLs
            if url.startswith("file://"):
                url_info = create_url_info(url, base_url=None)
                file_path = url_info.path

                if not os.path.exists(file_path):
                    issue = PQ_QualityIssue(
                        type=PQ_IssueType.FILE_SYSTEM,
                        level=PQ_IssueLevel.ERROR,
                        message=f"File not found: {file_path}",
                        location=url_info.normalized_url,
                    )
                    stats.failed_crawls += 1
                    return (
                        CrawlResult(
                            target=target,
                            stats=stats,
                            documents=[],
                            issues=[issue],
                            metrics={},
                            processed_url=url_info.normalized_url,
                            failed_urls=[url_info.normalized_url],
                            errors={
                                url_info.normalized_url: FileNotFoundError(file_path)
                            },
                        ),
                        [],
                        {},
                    )

                if os.path.isdir(file_path):
                    index_path = os.path.join(file_path, "index.html")
                    if not os.path.exists(index_path):
                        issue = PQ_QualityIssue(
                            type=PQ_IssueType.FILE_SYSTEM,
                            level=PQ_IssueLevel.ERROR,
                            message=f"Directory has no index.html: {file_path}",
                            location=url_info.normalized_url,
                        )
                        stats.failed_crawls += 1
                        return (
                            CrawlResult(
                                target=target,
                                stats=stats,
                                documents=[],
                                issues=[issue],
                                metrics={},
                                processed_url=url_info.normalized_url,
                                failed_urls=[url_info.normalized_url],
                                errors={
                                    url_info.normalized_url: FileNotFoundError(
                                        f"index.html not in {file_path}"
                                    )
                                },
                            ),
                            [],
                            {},
                        )
                    file_path = index_path  # Process index.html of the directory
                    # Update url_info if processing index.html of a directory
                    url_info = create_url_info(
                        f"file://{os.path.abspath(index_path)}", base_url=target.url
                    )

            # General error handling for other URLs
            issue = PQ_QualityIssue(
                type=PQ_IssueType.CONTENT_PROCESSING,  # More general error type
                level=PQ_IssueLevel.ERROR,
                message=f"Unexpected error processing URL {url}: {type(e).__name__}({e})",
                location=url,
                details=str(e),
            )
            stats.failed_crawls += 1
            return (
                CrawlResult(
                    target=target,
                    stats=stats,
                    documents=[],
                    issues=[issue],  # Populate issues here
                    metrics={},
                    processed_url=url,
                    failed_urls=[url],
                    errors={url: e},
                ),
                [],
                {},
            )

    async def _process_file_url(
        self,
        url_info: URLInfo,
        current_depth: int,
        target_cfg: CrawlTarget,
        stats_obj: CrawlStats,
    ) -> tuple[Optional[CrawlResult], list[tuple[str, int]], dict[str, Any]]:
        """Process a single file URL."""
        print(f"DEBUG CRAWLER: _process_file_url called with {url_info.normalized_url}")
        print("DEBUG CRAWLER: About to create CrawlResult")
        logging.debug(
            f"Processing file URL: {url_info.normalized_url} at depth {current_depth}"
        )
        result = CrawlResult(
            target=target_cfg, stats=stats_obj, documents=[], issues=[]
        )
        print("DEBUG CRAWLER: CrawlResult created successfully")

        # Initialize local lists for collecting documents and issues
        collected_documents: list[dict[str, Any]] = []
        collected_issues: list[PQ_QualityIssue] = []

        new_links: list[URLInfo] = []
        metrics: dict[str, Any] = {
            "content_size": 0,
            "link_count": 0,
            "processing_time_ms": 0,
        }
        start_time = time.perf_counter()

        file_path = url_info.path
        if file_path is None:
            file_path = ""  # Ensure file_path is a string

        url_str = url_info.normalized_url

        try:
            exists_result = os.path.exists(file_path)
            print(f"DEBUG CRAWLER: os.path.exists({file_path}) = {exists_result}")
            logging.debug(f"DEBUG: os.path.exists({file_path}) = {exists_result}")
            if not exists_result:
                raise FileNotFoundError(f"File not found: {file_path}")
            if os.path.isdir(file_path):
                # Attempt to find and process an index file if the path is a directory
                index_file_path = None
                for index_name in ["index.html", "index.htm"]:
                    potential_index_path = os.path.join(file_path, index_name)
                    if os.path.exists(potential_index_path) and os.path.isfile(
                        potential_index_path
                    ):
                        index_file_path = potential_index_path
                        url_str = create_url_info(
                            f"file://{index_file_path}"
                        ).normalized_url  # Update url_str to index file
                        file_path = index_file_path  # Update file_path to index file
                        logging.info(f"Processing directory index file: {file_path}")
                        break
                if not index_file_path:
                    raise IsADirectoryError(
                        f"Path is a directory without a recognized index file: {file_path}"
                    )

            with open(file_path, encoding="utf-8", errors="ignore") as f:
                file_content = f.read()

            metrics["content_size"] = len(file_content.encode("utf-8"))

        except FileNotFoundError as e:
            logger.warning(f"File not found for URL {url_str}: {e}")
            issue = PQ_QualityIssue(
                issue_type=PQ_IssueType.FILE_NOT_FOUND,
                level=PQ_IssueLevel.WARNING,  # Changed to WARNING as it might be an expected skip
                message=str(e),
                details={"file_path": file_path, "error": str(e)},
                url_context=url_str,
            )
            collected_issues.append(issue)
            stats_obj.skipped_pages += 1  # Changed from failed_crawls
            result.failed_urls.append(
                {"url": url_str, "reason": f"FileNotFoundError: {e}"}
            )

            end_time = time.perf_counter()
            metrics["processing_time_ms"] = (end_time - start_time) * 1000
            result.metrics.update(metrics)
            result.documents = collected_documents
            result.issues = collected_issues
            return result, new_links, metrics

        except IsADirectoryError as e:
            logger.warning(f"Path is a directory for URL {url_str}: {e}")
            issue = PQ_QualityIssue(
                issue_type=PQ_IssueType.FILE_SYSTEM_ERROR,  # Or a more specific type
                level=PQ_IssueLevel.WARNING,
                message=str(e),
                details={"file_path": file_path, "error": str(e)},
                url_context=url_str,
            )
            collected_issues.append(issue)
            stats_obj.skipped_pages += 1
            result.failed_urls.append(
                {"url": url_str, "reason": f"IsADirectoryError: {e}"}
            )

            end_time = time.perf_counter()
            metrics["processing_time_ms"] = (end_time - start_time) * 1000
            result.metrics.update(metrics)
            result.documents = collected_documents
            result.issues = collected_issues
            return result, new_links, metrics

        except OSError as e:
            logger.error(f"OSError processing file URL {url_str}: {e}")
            issue = PQ_QualityIssue(
                issue_type=PQ_IssueType.FILE_SYSTEM_ERROR,
                level=PQ_IssueLevel.ERROR,
                message=f"File system error for {url_str}: {e}",
                details={"file_path": file_path, "error": str(e)},
                url_context=url_str,
            )
            collected_issues.append(issue)
            stats_obj.failed_crawls += 1
            stats_obj.errors += 1
            result.failed_urls.append({"url": url_str, "reason": f"OSError: {e}"})

            end_time = time.perf_counter()
            metrics["processing_time_ms"] = (end_time - start_time) * 1000
            result.metrics.update(metrics)
            result.documents = collected_documents
            result.issues = collected_issues
            return result, new_links, metrics

        processed_content: Optional[ProcessedContent] = None
        try:
            if not self.content_processor:
                logger.warning(
                    f"Content processor not available for crawler when processing {url_str}."
                )
                # Create a basic ProcessedContent if no processor
                processed_content = ProcessedContent(
                    url=url_str,
                    title=os.path.basename(file_path) or url_str,
                    content={
                        "text": file_content,
                        "html": "",
                        "formatted_content": "",
                    },  # Basic content
                    metadata={"source": "file", "content_type": "text/plain"},
                    assets={},
                    structure=[],
                    headings=[],
                    errors=[],
                )
            else:
                # Determine content_type, default to text/html for .html files, else text/plain
                content_type = "text/plain"
                if file_path.lower().endswith((".html", ".htm")):
                    content_type = "text/html"

                processed_content = await self.content_processor.process(
                    content=file_content,
                    url=url_str,
                    content_type=content_type,
                    source_type="file",
                )

            if processed_content:
                doc_dict = {
                    "url": processed_content.url,
                    "title": processed_content.title,
                    "content": processed_content.content,
                    "metadata": processed_content.metadata,
                    "assets": processed_content.assets,
                    "structure": processed_content.structure,
                    "raw_content": file_content,
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                }
                collected_documents.append(doc_dict)
                result.processed_url = url_info.normalized_url
                stats_obj.successful_crawls += 1
                stats_obj.bytes_processed += len(file_content.encode("utf-8"))

                # Link extraction (simplified, assuming _find_links_recursive handles HTML content)
                # For file URLs, links are often relative paths.
                # Base URL for resolving relative links should be the directory of the current file.
                base_url_for_links = url_info.normalized_url
                if os.path.isfile(
                    file_path
                ):  # Ensure file_path is a file before dirname
                    # Construct a file:// URL for the directory containing the file
                    dir_path = os.path.dirname(file_path)
                    base_url_for_links = create_url_info(
                        f"file://{dir_path}/"
                    ).normalized_url

                extracted_link_strs = self._find_links_recursive(
                    processed_content.content.get(
                        "html", ""
                    ),  # Use HTML content for link finding
                    base_url_for_links,  # Pass the base URL for resolving relative links
                )

                for link_url_str in extracted_link_strs:
                    try:
                        # Resolve relative links against the file's directory URL
                        link_info = create_url_info(
                            link_url_str, base_url=base_url_for_links
                        )
                        if link_info and self._should_follow_link(
                            link_info, target_cfg, current_depth
                        ):
                            new_links.append(link_info)
                    except ValueError as ve:
                        logger.warning(
                            f"Skipping invalid link URL '{link_url_str}' found in {url_str}: {ve}"
                        )

                metrics["link_count"] = len(new_links)

                if self.quality_checker and hasattr(
                    self.quality_checker, "check_quality"
                ):
                    (
                        quality_issues,
                        quality_metrics,
                    ) = await self.quality_checker.check_quality(
                        processed_content, raw_content=file_content
                    )
                    if quality_issues:
                        collected_issues.extend(quality_issues)
                    if quality_metrics:  # quality_metrics is a dict
                        if not hasattr(result, "metrics") or result.metrics is None:
                            result.metrics = {}  # Should already be a dict from CrawlResult init
                        result.metrics.update(
                            quality_metrics
                        )  # Update the main metrics dict
                else:
                    logger.debug(
                        f"Quality checker not available or check_quality not implemented for {url_str}"
                    )

            else:  # processed_content is None
                logger.warning(f"Content processing returned None for {url_str}")
                issue = PQ_QualityIssue(
                    issue_type=PQ_IssueType.CONTENT_PROCESSING_ERROR,
                    level=PQ_IssueLevel.WARNING,
                    message=f"Content processor returned no content for {url_str}.",
                    details={"file_path": file_path},
                    url_context=url_str,
                )
                collected_issues.append(issue)
                stats_obj.failed_crawls += 1  # Or skipped_pages, depending on severity
                result.failed_urls.append(
                    {"url": url_str, "reason": "Content processor returned None"}
                )

        except Exception as e:
            logger.error(
                f"Error processing content for file URL {url_str}: {e}", exc_info=True
            )
            issue = PQ_QualityIssue(
                issue_type=PQ_IssueType.CONTENT_PROCESSING_ERROR,
                level=PQ_IssueLevel.ERROR,
                message=f"Content processing error for {url_str}: {e}",
                details={
                    "file_path": file_path,
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                },
                url_context=url_str,
            )
            collected_issues.append(issue)
            stats_obj.failed_crawls += 1
            stats_obj.errors += 1
            result.failed_urls.append(
                {"url": url_str, "reason": f"ContentProcessingError: {e}"}
            )

        end_time = time.perf_counter()
        metrics["processing_time_ms"] = (end_time - start_time) * 1000
        result.metrics.update(
            metrics
        )  # Update with timing and potentially other metrics

        # Assign collected lists to the result object before returning
        result.documents = collected_documents
        result.issues = collected_issues

        logger.debug(
            f"Finished processing file URL: {url_str}. Documents: {len(result.documents)}, Issues: {len(result.issues)}, New links: {len(new_links)}"
        )
        return (
            result,
            new_links,
            result.metrics,
        )  # Return result.metrics as it's the most complete

    async def crawl(
        self,
        targets: Union[CrawlTarget, list[CrawlTarget]],
        config: Optional[CrawlerConfig] = None,
    ) -> list[CrawlResult]:
        """Start the crawling process.

        Args:
            targets: A single CrawlTarget or a list of CrawlTarget objects
            config: Optional crawler configuration (overrides default or target-specific config)

        Returns:
            A list of CrawlResult objects for the crawled targets
        """
        if isinstance(targets, CrawlTarget):
            targets = [targets]  # Wrap in list if single target

        results: list[CrawlResult] = []
        for target in targets:
            # Merge target-specific config with global config
            merged_config = self.config.copy()
            if config:
                merged_config.update(config)

            # Adjust max_depth and max_pages based on target settings
            merged_config.max_depth = (
                target.depth if target.depth > 0 else merged_config.max_depth
            )
            merged_config.max_pages = (
                target.max_pages
                if target.max_pages is not None
                else merged_config.max_pages
            )

            # Initialize stats for this target
            stats = CrawlStats()

            # Start processing each target URL
            for start_url in [
                target.url
            ]:  # Currently just the single URL from the target
                logging.info(
                    f"Starting crawl for target: {target.url} (Depth: {target.depth})"
                )
                result, _, _ = await self._process_url(
                    start_url, 0, target, stats, set()
                )
                if result:
                    results.append(result)

            # Finalize stats and results
            if results:
                final_result = results[-1]  # Take the last result as the final one
                final_result.stats = stats
                final_result.target = target  # Ensure target is set
                final_result.processed_url = (
                    final_result.processed_url or final_result.documents[0].get("url")
                )
                final_result.issues = list(
                    {issue.message: issue for issue in final_result.issues}.values()
                )  # Deduplicate issues by message

                # Log final stats for the target
                logging.info(
                    f"Finished crawl for target: {target.url}. Pages crawled: {stats.pages_crawled}, Successful: {stats.successful_crawls}, Failed: {stats.failed_crawls}, Time: {stats.total_time:.2f}s"
                )

        return results
