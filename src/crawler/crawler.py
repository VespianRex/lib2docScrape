"""
Crawler implementation for lib2docScrape.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Optional, Union  # Keep Union for config_or_depth
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from src.backends.http_backend import HTTPBackend, HTTPBackendConfig

# Relative imports for crawler components - these seemed problematic, will use direct src paths
from src.backends.selector import BackendCriteria, BackendSelector
from src.models.project import ProjectIdentity, ProjectType
from src.organizers.doc_organizer import DocumentOrganizer
from src.processors.content.models import ProcessedContent
from src.processors.content_processor import ContentProcessor
from src.processors.quality_checker import QualityChecker
from src.utils.helpers import RateLimiter, RetryStrategy  # Combined imports

# from src.utils.helpers import RetryStrategy # Already imported
from src.utils.project_identifier import ProjectIdentifier
from src.utils.search import DuckDuckGoSearch
from src.utils.url.factory import create_url_info

from ..processors.quality_checker import IssueLevel, IssueType
from ..processors.quality_checker import (  # Renamed for clarity
    QualityIssue as ProcessorQualityIssue,
)
from .models import (  # .models.QualityIssue for crawler's own use
    CrawlConfig,
    CrawlResult,
    CrawlStats,
    CrawlTarget,
    QualityIssue,
)

logger = logging.getLogger(__name__)


class CrawlerOptions(BaseModel):
    headers: dict[str, str] = Field(default_factory=dict)  # Use dict
    cookies: dict[str, str] = Field(default_factory=dict)  # Use dict
    # ... existing CrawlerOptions fields ...
    proxy: Optional[str] = None
    verify_ssl: bool = True
    allow_redirects: bool = True
    max_redirects: int = 5
    respect_robots_txt: bool = True
    javascript_rendering: bool = False
    javascript_timeout: int = 10
    extract_metadata: bool = True
    extract_links: bool = True
    extract_images: bool = True
    # ... (all other extract_... fields remain the same)
    extract_documentvisitcpy: bool = True
    extract_documentvisitcpz: bool = True


class Crawler:
    """
    Crawler for lib2docScrape.
    Crawls documentation sites and extracts content.
    """

    def __init__(
        self,
        config: Optional[CrawlConfig] = None,
        backend_selector: Optional[BackendSelector] = None,
        content_processor: Optional[ContentProcessor] = None,
        quality_checker: Optional[QualityChecker] = None,
        document_organizer: Optional[DocumentOrganizer] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        backend: Optional[Any] = None,
    ) -> None:
        self.config: CrawlConfig = config or CrawlConfig()

        self.backend_selector: BackendSelector = backend_selector or BackendSelector()
        self.content_processor: ContentProcessor = (
            content_processor or ContentProcessor()
        )
        self.quality_checker: QualityChecker = quality_checker or QualityChecker()
        self.document_organizer: DocumentOrganizer = (
            document_organizer or DocumentOrganizer()
        )

        self.loop = loop or asyncio.get_event_loop()  # Ensure loop is set
        self.backend = backend
        self.direct_backend = backend
        self._crawled_urls: set[str] = set()
        self.crawled_urls: set[str] = self._crawled_urls  # Public alias
        self.active_tasks: int = 0
        self._current_crawl_config: Optional[CrawlConfig] = None

        self.visited_urls: set[str] = set()
        self.crawl_queue: list[CrawlTarget] = []  # Use list

        http_backend = HTTPBackend(
            HTTPBackendConfig(
                timeout=self.config.request_timeout,
                verify_ssl=self.config.verify_ssl,
                follow_redirects=self.config.follow_redirects,
                headers=self.config.headers
                or {
                    "User-Agent": self.config.user_agent
                },  # Use config headers if available
            )
        )

        self.backend_selector.register_backend(
            name=http_backend.name,
            backend=http_backend,
            criteria=BackendCriteria(
                priority=1,
                content_types=["text/html"],
                url_patterns=["http://", "https://"],
                max_load=0.8,
                min_success_rate=0.7,
            ),
        )

        self.duckduckgo: Optional[DuckDuckGoSearch] = (
            DuckDuckGoSearch(self.config.duckduckgo_max_results)
            if self.config.use_duckduckgo
            else None
        )

        self.client_session: Optional[Any] = None  # aiohttp.ClientSession
        self._processing_semaphore = asyncio.Semaphore(self.config.concurrent_requests)
        self.rate_limiter = RateLimiter(self.config.requests_per_second)
        self.retry_strategy = RetryStrategy(max_retries=self.config.max_retries)

        logger.info(
            f"Crawler initialized with max_depth={self.config.max_depth}, max_pages={self.config.max_pages}"
        )

    def add_target(self, target: CrawlTarget):
        self.crawl_queue.append(target)

    async def crawl(
        self,
        target_url_or_target: Union[str, CrawlTarget, None] = None,
        config_or_depth: Union[CrawlConfig, int, None] = None,
        follow_external: Optional[bool] = None,  # Default to None, will use config
        content_types: Optional[list[str]] = None,
        exclude_patterns: Optional[list[str]] = None,
        include_patterns: Optional[list[str]] = None,
        max_pages: Optional[int] = None,
        allowed_paths: Optional[list[str]] = None,
        excluded_paths: Optional[list[str]] = None,
        required_patterns: Optional[list[str]] = None,  # Backward compatibility
        backend: Optional[Any] = None,
        **kwargs: Any,
    ) -> CrawlResult:
        if target_url_or_target is None and "target_url" in kwargs:
            target_url_or_target = kwargs.pop("target_url")

        if config_or_depth is None and "depth" in kwargs:
            config_or_depth = kwargs.pop("depth")

        current_target: CrawlTarget
        effective_config: CrawlConfig

        if isinstance(target_url_or_target, CrawlTarget):
            current_target = target_url_or_target
            if isinstance(config_or_depth, CrawlConfig):
                effective_config = config_or_depth
                logger.info(
                    f"Crawling {current_target.url} with depth={current_target.depth} (CrawlTarget + CrawlConfig)"
                )
            else:
                # If not a CrawlConfig, assume it might be a backend (old interface) or None
                if config_or_depth and hasattr(
                    config_or_depth, "crawl"
                ):  # it's a backend
                    backend = config_or_depth
                # Create an effective_config from the target and global config
                effective_config = CrawlConfig(
                    target_url=current_target.url,
                    max_depth=current_target.depth,
                    follow_external=current_target.follow_external,
                    content_types=current_target.content_types,
                    exclude_patterns=current_target.exclude_patterns,
                    include_patterns=current_target.include_patterns,
                    max_pages=current_target.max_pages,
                    allowed_paths=current_target.allowed_paths,
                    excluded_paths=current_target.excluded_paths,
                    # Inherit other settings from self.config
                    request_timeout=self.config.request_timeout,
                    user_agent=self.config.user_agent,
                    verify_ssl=self.config.verify_ssl,
                    follow_redirects=self.config.follow_redirects,
                    max_retries=self.config.max_retries,
                    concurrent_requests=self.config.concurrent_requests,
                    requests_per_second=self.config.requests_per_second,
                    use_duckduckgo=self.config.use_duckduckgo,
                    duckduckgo_max_results=self.config.duckduckgo_max_results,
                    quality_config=self.config.quality_config,
                    headers=self.config.headers,
                )
                logger.info(
                    f"Crawling {current_target.url} with depth={current_target.depth} (CrawlTarget, using derived CrawlConfig)"
                )

            if backend:
                self.backend = backend  # Override instance backend if provided

        elif isinstance(target_url_or_target, str):
            target_url_str = target_url_or_target
            depth_val = (
                config_or_depth
                if isinstance(config_or_depth, int)
                else self.config.max_depth
            )

            # Use provided params or fall back to self.config for CrawlTarget creation
            current_target = CrawlTarget(
                url=target_url_str,
                depth=depth_val,
                follow_external=follow_external
                if follow_external is not None
                else self.config.follow_external,
                content_types=content_types or self.config.content_types or [],
                exclude_patterns=exclude_patterns or self.config.exclude_patterns or [],
                include_patterns=include_patterns
                or required_patterns
                or self.config.include_patterns
                or [],  # Handle required_patterns
                max_pages=max_pages if max_pages is not None else self.config.max_pages,
                allowed_paths=allowed_paths
                or getattr(self.config, "allowed_paths", [])
                or [],  # getattr for safety
                excluded_paths=excluded_paths
                or getattr(self.config, "excluded_paths", [])
                or [],  # getattr for safety
                required_patterns=required_patterns
                or include_patterns
                or self.config.include_patterns
                or [],  # Ensure this is set
            )
            # Create an effective_config from the target and global config
            effective_config = CrawlConfig(
                target_url=current_target.url,
                max_depth=current_target.depth,
                follow_external=current_target.follow_external,
                content_types=current_target.content_types,
                exclude_patterns=current_target.exclude_patterns,
                include_patterns=current_target.include_patterns,
                max_pages=current_target.max_pages,
                allowed_paths=current_target.allowed_paths,
                excluded_paths=current_target.excluded_paths,
                request_timeout=self.config.request_timeout,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
                follow_redirects=self.config.follow_redirects,
                max_retries=self.config.max_retries,
                concurrent_requests=self.config.concurrent_requests,
                requests_per_second=self.config.requests_per_second,
                use_duckduckgo=self.config.use_duckduckgo,
                duckduckgo_max_results=self.config.duckduckgo_max_results,
                quality_config=self.config.quality_config,
                headers=self.config.headers,
            )
            logger.info(
                f"Crawling {current_target.url} with depth={current_target.depth} (URL string, using derived CrawlConfig)"
            )
        else:
            raise ValueError(
                "Invalid arguments for crawl method. Provide URL string or CrawlTarget."
            )

        self._current_crawl_config = effective_config  # Store the config for this crawl

        stats = CrawlStats()
        stats.start_time = (
            asyncio.get_event_loop().time()
        )  # Initialize start_time for stats

        visited_urls_session: set[str] = set()
        all_documents_session: list[dict[str, Any]] = []
        all_issues_session: list[ProcessorQualityIssue] = []  # Initialize properly
        all_metrics_session: dict[str, Any] = {}
        crawled_urls_list_session: list[str] = []
        all_errors_session: dict[str, Exception] = {}
        all_crawled_pages_session: dict[str, ProcessedContent] = {}

        queue, start_url = await self._initialize_crawl_queue(current_target)

        project_identifier = ProjectIdentifier()
        project_identity = await project_identifier.identify_from_url(
            current_target.url
        )

        if self.duckduckgo and project_identity and project_identity.name != "unknown":
            search_queries = self._generate_search_queries(
                current_target.url, project_identity
            )
            ddg_discovered_urls: set[str] = set()
            for query in search_queries:
                try:
                    # DuckDuckGoSearch.search is async, so we need to await it
                    urls_result = await self.duckduckgo.search(query)
                    if urls_result:
                        for url_item_ddg in urls_result:
                            url_to_add = None
                            if isinstance(url_item_ddg, dict) and "url" in url_item_ddg:
                                url_to_add = url_item_ddg["url"]
                            elif isinstance(url_item_ddg, str):
                                url_to_add = url_item_ddg

                            if url_to_add and urlparse(url_to_add).scheme in [
                                "http",
                                "https",
                            ]:
                                ddg_discovered_urls.add(url_to_add)
                except Exception as e:
                    logger.warning(f"DuckDuckGo search failed for query '{query}': {e}")

            for url_item_ddg_add in ddg_discovered_urls:
                if not any(item[0] == url_item_ddg_add for item in queue):
                    queue.append((url_item_ddg_add, 0))  # Add with depth 0

        while queue and (
            current_target.max_pages is None
            or len(visited_urls_session) < current_target.max_pages
        ):
            url_to_crawl, current_depth_val = queue.pop(0)

            # Pass current_target (which holds specific rules for this crawl)
            # and effective_config (which holds broader settings like quality)
            result_data, new_links, metrics, error = await self._process_url(
                url_to_crawl,
                current_depth_val,
                current_target,
                stats,
                visited_urls_session,
            )

            if error:
                all_errors_session[url_to_crawl] = error
                logger.debug(f"Error recorded for URL {url_to_crawl}: {error}")

            if result_data is not None:
                if result_data.documents:
                    all_documents_session.extend(result_data.documents)
                crawled_urls_list_session.append(url_to_crawl)

                if result_data.issues:  # issues are now ProcessorQualityIssue
                    all_issues_session.extend(result_data.issues)

                if metrics:
                    all_metrics_session.update(metrics)

                if result_data.crawled_pages:
                    all_crawled_pages_session.update(result_data.crawled_pages)

                if current_depth_val < current_target.depth:
                    for link_url_item in new_links:
                        if not any(item[0] == link_url_item for item in queue):
                            queue.append((link_url_item, current_depth_val + 1))

        from datetime import UTC, datetime  # Keep import here for now

        stats.end_time = datetime.now(UTC)  # Use datetime directly
        if stats.start_time:  # Ensure start_time was set
            current_time_for_total = asyncio.get_event_loop().time()
            stats.total_time = (
                current_time_for_total - stats.start_time
            )  # Use loop time
        if stats.pages_crawled > 0 and stats.total_time is not None:
            stats.average_time_per_page = stats.total_time / stats.pages_crawled

        if hasattr(self, "_current_crawl_config"):  # Cleanup
            delattr(self, "_current_crawl_config")

        final_structure = None
        if (
            self.document_organizer and all_documents_session
        ):  # Check if documents exist
            try:
                # Pass only the content of the documents if organizer expects that
                docs_for_organizer = [
                    doc.get("content", "")
                    for doc in all_documents_session
                    if isinstance(doc, dict)
                ]
                if not all(
                    isinstance(d, str) for d in docs_for_organizer
                ):  # Basic check
                    docs_for_organizer = all_documents_session  # Pass full dicts if content extraction is complex

                organizer_result = await self.document_organizer.organize(
                    docs_for_organizer
                )  # or all_documents_session
                if (
                    isinstance(organizer_result, dict)
                    and "structure" in organizer_result
                ):
                    final_structure = organizer_result["structure"]
                elif isinstance(organizer_result, list):
                    final_structure = organizer_result
                else:  # Fallback
                    final_structure = [
                        {"type": "section", "title": "Organized Content (fallback)"}
                    ]
            except Exception as e:
                logger.error(f"Error during document organization: {e}")
                final_structure = [{"type": "section", "title": "Organization Error"}]
        elif not all_documents_session:
            final_structure = [{"type": "section", "title": "No documents to organize"}]

        # Convert ProcessorQualityIssue objects to QualityIssue objects for CrawlResult
        converted_issues = []
        for issue in all_issues_session:
            converted_issue = QualityIssue(
                type=str(issue.type.value)
                if hasattr(issue.type, "value")
                else str(issue.type),
                level=str(issue.level.value)
                if hasattr(issue.level, "value")
                else str(issue.level),
                message=issue.message,
                location=issue.location,
                details=issue.details,
            )
            converted_issues.append(converted_issue)

        return CrawlResult(
            target=current_target,  # Use the specific target for this crawl
            stats=stats,
            documents=all_documents_session,
            issues=converted_issues,  # Now list[QualityIssue] from crawler.models
            metrics=all_metrics_session,
            structure=final_structure,
            crawled_urls=crawled_urls_list_session,
            errors=all_errors_session,
            crawled_pages=all_crawled_pages_session,
            project_identity=project_identity,
        )

    def _extract_major_minor_version(
        self, version: str
    ) -> Optional[list[str]]:  # Use list
        try:
            return version.split(".")
        except (AttributeError, ValueError):
            return None

    def _generate_search_queries(
        self,
        url_or_config: Union[str, CrawlConfig],
        identity: Optional[ProjectIdentity] = None,
    ) -> list[str]:  # Use list
        queries: list[str] = []
        url_str: str = ""

        if isinstance(url_or_config, CrawlConfig):
            config = url_or_config
            identity = (
                config.project_identity
            )  # Assuming CrawlConfig has project_identity
            url_str = config.target_url if hasattr(config, "target_url") else ""
        elif isinstance(url_or_config, str):
            url_str = url_or_config

        if not identity or identity.name == "unknown":
            if url_str:
                try:
                    domain = urlparse(url_str).netloc
                    if domain:
                        queries.append(f"{domain} documentation")
                except Exception:
                    pass  # Ignore parsing errors for query generation
            return queries

        # Handle if name is valid
        if identity.name != "unknown":
            base_name = identity.name
            version_str = (
                identity.version if isinstance(identity.version, str) else None
            )

            if identity.type == ProjectType.LIBRARY:
                if version_str:
                    queries.append(f"{base_name} {version_str} documentation")
                    queries.append(f"{base_name} {version_str} api reference")
                    try:
                        parts = self._extract_major_minor_version(version_str)
                        if parts and len(parts) >= 2:
                            queries.append(
                                f"{base_name} {parts[0]}.{parts[1]} documentation"
                            )
                            # Add major version only
                            queries.append(f"{base_name} {parts[0]} documentation")
                    except Exception:
                        pass
                    queries.append(f"{base_name} documentation")  # Always add base name
                else:
                    # When no version, add all documentation-related queries
                    queries.append(f"{base_name} documentation")
                    queries.append(f"{base_name} api reference")
                    queries.append(f"{base_name} tutorial")
                    queries.append(f"{base_name} guide")
            else:  # Other project types
                if version_str:
                    queries.append(f"{base_name} {version_str} documentation")
                queries.append(f"{base_name} documentation")
                queries.append(f"{base_name} guide")
                queries.append(f"{base_name} tutorial")
                queries.append(f"{base_name} how to")
        return list(set(queries))  # Remove duplicates

    async def _process_file_url(
        self, url_info: Any, current_depth: int, target: CrawlTarget, stats: CrawlStats
    ) -> tuple[Optional[CrawlResult], list[str], dict[str, Any]]:  # Use list, dict
        import os  # Keep local
        # from urllib.parse import urlparse # Already imported at top

        parsed_url = urlparse(url_info.normalized_url)
        file_path = parsed_url.path

        issues_file: list[ProcessorQualityIssue] = []  # Use ProcessorQualityIssue
        documents_file: list[dict[str, Any]] = []  # Use list[dict]
        new_links_file: list[str] = []  # Use list
        metrics_file: dict[str, Any] = {}  # Use dict

        try:
            if not os.path.exists(file_path):
                issues_file.append(
                    ProcessorQualityIssue(
                        type=IssueType.GENERAL,
                        level=IssueLevel.ERROR,
                        message=f"File not found: {file_path}",
                        location=url_info.normalized_url,
                    )
                )
            elif os.path.isdir(file_path):
                index_path = os.path.join(file_path, "index.html")
                if not os.path.exists(index_path):
                    issues_file.append(
                        ProcessorQualityIssue(
                            type=IssueType.GENERAL,
                            level=IssueLevel.ERROR,
                            message=f"Directory has no index.html: {file_path}",
                            location=url_info.normalized_url,
                        )
                    )
                else:
                    file_path = index_path  # Process index.html

            if not issues_file and os.path.isfile(
                file_path
            ):  # Ensure it's a file before reading
                try:
                    with open(file_path, encoding="utf-8") as f:
                        content_file_raw = f.read()

                    processed_content_obj: Optional[ProcessedContent] = None
                    if self.content_processor:
                        # Determine content type based on file extension
                        content_type_for_file = None
                        if url_info.normalized_url.endswith(
                            ".html"
                        ) or url_info.normalized_url.endswith(".htm"):
                            content_type_for_file = "text/html"
                        elif url_info.normalized_url.endswith(".md"):
                            content_type_for_file = "text/markdown"
                        elif url_info.normalized_url.endswith(".rst"):
                            content_type_for_file = "text/x-rst"
                        elif url_info.normalized_url.endswith(".txt"):
                            content_type_for_file = "text/plain"

                        processed_content_obj = await self.content_processor.process(
                            content_file_raw,
                            url_info.normalized_url,
                            content_type_for_file,
                        )

                    if processed_content_obj:
                        if processed_content_obj.structure:
                            new_links_file = self._find_links_recursive(
                                processed_content_obj.structure
                            )  # Pass structure

                        # Safely extract content with type checking
                        content_for_doc = content_file_raw  # Default fallback
                        if processed_content_obj.content and isinstance(
                            processed_content_obj.content, dict
                        ):
                            content_for_doc = processed_content_obj.content.get(
                                "formatted_content", content_file_raw
                            )
                        elif isinstance(processed_content_obj.content, str):
                            content_for_doc = processed_content_obj.content

                        documents_file.append(
                            {
                                "url": url_info.normalized_url,
                                "title": processed_content_obj.title
                                or os.path.basename(file_path),
                                "content": content_for_doc,
                                "links": new_links_file,  # Store extracted links
                                "doc_id": None,  # Placeholder for doc_id
                            }
                        )

                        if self.quality_checker:
                            # check_quality only expects ProcessedContent
                            (
                                quality_issues_from_checker,
                                quality_metrics_from_checker,
                            ) = await self.quality_checker.check_quality(
                                processed_content_obj
                            )
                            if quality_issues_from_checker:
                                issues_file.extend(quality_issues_from_checker)
                            if quality_metrics_from_checker:
                                metrics_file.update(quality_metrics_from_checker)
                    else:  # Fallback if processor fails or no processor
                        documents_file.append(
                            {
                                "url": url_info.normalized_url,
                                "title": os.path.basename(file_path),
                                "content": content_file_raw,
                                "links": [],
                                "doc_id": None,
                            }
                        )

                except OSError as e_os:
                    issues_file.append(
                        ProcessorQualityIssue(
                            type=IssueType.GENERAL,
                            level=IssueLevel.ERROR,
                            message=f"File read error: {str(e_os)}",
                            location=url_info.normalized_url,
                        )
                    )
                except Exception as e_proc:  # Catch processing errors
                    issues_file.append(
                        ProcessorQualityIssue(
                            type=IssueType.GENERAL,
                            level=IssueLevel.ERROR,
                            message=f"File processing error: {str(e_proc)}",
                            location=url_info.normalized_url,
                        )
                    )

        except Exception as e_gen:  # Catch general errors
            issues_file.append(
                ProcessorQualityIssue(
                    type=IssueType.GENERAL,
                    level=IssueLevel.ERROR,
                    message=f"General file processing error: {str(e_gen)}",
                    location=url_info.normalized_url,
                )
            )

        if (
            not documents_file and not issues_file
        ):  # If no docs and no specific issues, maybe it's just not a processable file
            stats.skipped_pages += 1
        elif issues_file:  # If there were issues, count as failed
            stats.failed_crawls += 1
        if documents_file:  # If documents were produced, count as crawled
            stats.pages_crawled += 1
            stats.successful_crawls += (
                1  # Count as successful if documents were produced
            )
            if documents_file[0].get("content"):
                stats.bytes_processed += len(str(documents_file[0]["content"]))

        stats.quality_issues += len(issues_file)

        # Convert ProcessorQualityIssue objects to crawler QualityIssue objects
        converted_issues = []
        for processor_issue in issues_file:
            converted_issue = QualityIssue(
                type=str(processor_issue.type),  # Convert enum to string
                level=str(processor_issue.level),  # Convert enum to string
                message=processor_issue.message,
                location=processor_issue.location,
                details=processor_issue.details,
            )
            converted_issues.append(converted_issue)

        # This method is for test compatibility, CrawlResult might not be fully populated
        crawl_result_file = CrawlResult(
            target=target,
            stats=stats,
            documents=documents_file,
            issues=converted_issues,
            metrics=metrics_file,
            crawled_urls=[url_info.normalized_url]
            if documents_file
            else [],  # Add if crawled
            errors={},
            crawled_pages={},
            project_identity=None,  # Defaults for test context
        )
        return crawl_result_file, new_links_file, metrics_file

    def _find_links_recursive(self, structure_element: Any) -> list[str]:  # Use list
        # This version directly processes structure elements (dict or list)
        links_found: list[str] = []  # Use list
        if isinstance(structure_element, dict):
            # Check for link types used by content processor
            if structure_element.get("type") in ["link", "link_inline"]:
                # Check for both "url" and "href" fields
                link_url = structure_element.get("url") or structure_element.get("href")
                if isinstance(link_url, str):
                    links_found.append(link_url)
            # BeautifulSoup-like structure (common in some tests or direct HTML parsing)
            elif structure_element.get("tag_name") == "a" and isinstance(
                structure_element.get("attrs", {}).get("href"), str
            ):
                links_found.append(structure_element["attrs"]["href"])

            # Recursively check children or other nested structures
            if "children" in structure_element and isinstance(
                structure_element["children"], list
            ):
                for child in structure_element["children"]:
                    links_found.extend(self._find_links_recursive(child))
            # Some processors might put content in a 'content' field that could be a list of structures
            if "content" in structure_element and isinstance(
                structure_element["content"], list
            ):
                for item_in_content in structure_element["content"]:
                    links_found.extend(self._find_links_recursive(item_in_content))
            # Generic recursion for other dict values that might be structures
            for key, value in structure_element.items():
                if key not in [
                    "url",
                    "href",
                    "children",
                    "content",
                    "tag_name",
                    "attrs",
                    "type",
                ] and isinstance(value, (dict, list)):
                    links_found.extend(self._find_links_recursive(value))

        elif isinstance(structure_element, list):
            for item_in_list in structure_element:
                links_found.extend(self._find_links_recursive(item_in_list))

        # Deduplicate and return
        return list(set(links_found))

    def _extract_hrefs_from_structure(
        self, structure_element: Any
    ) -> list[str]:  # Use list
        # This is kept for compatibility if some tests call it directly,
        # but _find_links_recursive is now the primary internal method.
        return self._find_links_recursive(structure_element)

    def _should_crawl_url(self, url_info: Any, target: CrawlTarget) -> bool:
        import re  # Keep local

        if not url_info or not url_info.is_valid:  # Add check for url_info itself
            return False

        normalized_url = url_info.normalized_url

        if normalized_url in self._crawled_urls:  # Check against instance's set
            return False

        if url_info.scheme not in ["http", "https", "file"]:
            return False

        # follow_external logic
        if target.follow_external is False:  # Explicit check for False
            target_url_info = create_url_info(target.url)  # Create once
            if not target_url_info or not target_url_info.is_valid:  # Safety check
                return False  # Cannot determine externality if target URL is invalid

            # Same URL is internal
            if normalized_url == target_url_info.normalized_url:
                pass
            # Different schemes (unless http -> https upgrade on same domain)
            elif url_info.scheme != target_url_info.scheme:
                is_upgrade = (
                    target_url_info.scheme == "http"
                    and url_info.scheme == "https"
                    and hasattr(url_info, "registered_domain")  # Pylance check
                    and hasattr(target_url_info, "registered_domain")  # Pylance check
                    and url_info.registered_domain == target_url_info.registered_domain
                )
                if not is_upgrade:
                    return False
            # Different registered domains for http/https
            elif url_info.scheme in ["http", "https"] and target_url_info.scheme in [
                "http",
                "https",
            ]:
                if (
                    hasattr(url_info, "registered_domain")
                    and hasattr(target_url_info, "registered_domain")
                    and url_info.registered_domain != target_url_info.registered_domain
                ):
                    return False
            # File URL externality (simplified: different base directory)
            elif url_info.scheme == "file" and target_url_info.scheme == "file":
                import os  # local import

                target_path_norm = os.path.normpath(target_url_info.path)
                url_path_norm = os.path.normpath(url_info.path)

                target_base_dir = (
                    os.path.dirname(target_path_norm)
                    if not os.path.isdir(target_path_norm)
                    else target_path_norm
                )
                url_base_dir = (
                    os.path.dirname(url_path_norm)
                    if not os.path.isdir(url_path_norm)
                    else url_path_norm
                )

                if not url_base_dir.startswith(target_base_dir):
                    return False

        # Exclude patterns
        if target.exclude_patterns and any(
            re.search(p, normalized_url) for p in target.exclude_patterns if p
        ):  # Ensure pattern is not empty
            return False

        # Required/Include patterns (allow initial target URL to bypass)
        # CrawlTarget now uses 'include_patterns' primarily. 'required_patterns' is for backward compat.
        effective_include_patterns = (
            target.include_patterns or target.required_patterns or []
        )
        if effective_include_patterns:
            target_url_info_for_bypass = create_url_info(target.url)
            if not (
                target_url_info_for_bypass
                and normalized_url == target_url_info_for_bypass.normalized_url
            ):  # Not initial URL
                if not any(
                    re.search(p, normalized_url)
                    for p in effective_include_patterns
                    if p
                ):
                    return False

        # Allowed paths
        if target.allowed_paths:
            path_part = url_info.path or "/"  # Ensure path is not None
            if not any(path_part.startswith(ap) for ap in target.allowed_paths if ap):
                return False

        # Excluded paths
        if target.excluded_paths:
            path_part = url_info.path or "/"
            if any(path_part.startswith(ep) for ep in target.excluded_paths if ep):
                return False

        return True

    async def _fetch_and_process_with_backend(
        self,
        backend: Any,
        url_info: Any,
        target_rules: CrawlTarget,  # Renamed target to target_rules
        stats: CrawlStats,
        visited_urls_session: set[str],  # Use session set
        backend_result_override: Optional[Any] = None,  # For pre-fetched results
    ) -> tuple[
        Optional[ProcessedContent],
        Optional[Any],
        Optional[str],
        dict[str, Any],
        Optional[Exception],
    ]:
        current_backend_result = backend_result_override
        if current_backend_result is None:
            if not backend or not hasattr(backend, "crawl"):  # Safety check
                logger.error(
                    f"Invalid backend provided for URL: {url_info.normalized_url}"
                )
                return None, None, url_info.normalized_url, {}, None
            current_backend_result = await backend.crawl(
                url_info
            )  # Assuming backend.crawl is async

        if not current_backend_result:  # Backend failed to return anything
            logger.warning(f"Backend returned None for {url_info.normalized_url}")
            return None, None, url_info.normalized_url, {}, None

        final_url_str = getattr(current_backend_result, "url", url_info.normalized_url)

        if (
            final_url_str != url_info.normalized_url
            and final_url_str in visited_urls_session
        ):
            return (
                None,
                current_backend_result,
                final_url_str,
                {},
                None,
            )  # Redirect to already visited

        content_type_header = "text/html"  # Default
        backend_meta = getattr(current_backend_result, "metadata", None)
        if (
            backend_meta
            and isinstance(backend_meta, dict)
            and "headers" in backend_meta
        ):
            content_type_header = backend_meta["headers"].get(
                "Content-Type", "text/html"
            )

        # Use content_types from target_rules (passed as CrawlTarget)
        # Ensure target_rules.content_types is not None and items are strings
        allowed_cts = target_rules.content_types or []
        if not any(
            ct_allowed in content_type_header
            for ct_allowed in allowed_cts
            if isinstance(ct_allowed, str)
        ):
            logger.debug(
                f"Content type {content_type_header} not allowed for {final_url_str}"
            )
            return None, current_backend_result, final_url_str, {}, None

        # Attempt to get ProcessedContent from backend or process raw content
        final_processed_content: Optional[ProcessedContent] = None

        # Scenario 1: Backend already returned ProcessedContent(s)
        backend_docs = getattr(current_backend_result, "documents", None)
        if backend_docs and isinstance(backend_docs, list) and backend_docs:
            if isinstance(backend_docs[0], ProcessedContent):
                final_processed_content = backend_docs[0]
            elif isinstance(
                backend_docs[0], dict
            ):  # Try to adapt dict to ProcessedContent
                try:
                    # Ensure content field is properly formatted before creating ProcessedContent
                    doc_dict_for_pc = backend_docs[0].copy()
                    if "content" in doc_dict_for_pc:
                        content_val = doc_dict_for_pc["content"]
                        if isinstance(content_val, str):
                            # Convert string content to expected dictionary format
                            doc_dict_for_pc["content"] = {
                                "raw_content": content_val,
                                "formatted_content": content_val,
                            }
                        elif not isinstance(content_val, dict):
                            # If content is neither string nor dict, use default
                            doc_dict_for_pc["content"] = {
                                "raw_content": "",
                                "formatted_content": "",
                            }

                    final_processed_content = ProcessedContent(**doc_dict_for_pc)
                except Exception:
                    pass  # If adaptation fails, will try raw content processing

        # Scenario 2: Process raw HTML from backend result if no ProcessedContent yet
        if final_processed_content is None and self.content_processor:
            raw_html_from_backend = None
            backend_content_field = getattr(current_backend_result, "content", None)
            if (
                isinstance(backend_content_field, dict)
                and "html" in backend_content_field
            ):
                raw_html_from_backend = backend_content_field["html"]
            elif isinstance(backend_content_field, str):  # If content is just a string
                raw_html_from_backend = backend_content_field

            if raw_html_from_backend:
                try:
                    # Pass raw HTML, URL, and content type from backend
                    metadata_for_processor = backend_meta or {}
                    content_type_for_processor = None
                    if hasattr(current_backend_result, "content_type"):
                        content_type_for_processor = current_backend_result.content_type
                    elif metadata_for_processor and "headers" in metadata_for_processor:
                        headers = metadata_for_processor["headers"]
                        if isinstance(headers, dict) and "content-type" in headers:
                            content_type_for_processor = headers["content-type"]
                        elif isinstance(headers, dict) and "Content-Type" in headers:
                            content_type_for_processor = headers["Content-Type"]

                    final_processed_content = await self.content_processor.process(
                        raw_html_from_backend, final_url_str, content_type_for_processor
                    )
                except Exception as e_proc_raw:
                    logger.error(
                        f"Content processor failed for {final_url_str}: {e_proc_raw}"
                    )
                    # Return the exception so it can be recorded in result.errors
                    return None, current_backend_result, final_url_str, {}, e_proc_raw
            elif (
                backend_docs
                and isinstance(backend_docs, list)
                and backend_docs
                and isinstance(backend_docs[0], dict)
            ):
                # If backend_docs had a dict but it wasn't ProcessedContent, and no raw HTML, try to use it
                # This is a fallback if the dict was not directly convertible to ProcessedContent earlier
                # but might contain enough info for a basic ProcessedContent object.
                doc_dict = backend_docs[0]
                # Ensure content is always a dictionary
                content_from_dict = doc_dict.get(
                    "content", {"raw_content": "", "formatted_content": ""}
                )
                if isinstance(content_from_dict, str):
                    # If content is a string, wrap it in the expected dictionary format
                    content_from_dict = {
                        "raw_content": content_from_dict,
                        "formatted_content": content_from_dict,
                    }
                elif not isinstance(content_from_dict, dict):
                    # If content is neither string nor dict, use default
                    content_from_dict = {"raw_content": "", "formatted_content": ""}

                final_processed_content = ProcessedContent(
                    url=doc_dict.get("url", final_url_str),
                    title=doc_dict.get("title", "Untitled"),
                    content=content_from_dict,
                    metadata=doc_dict.get("metadata", backend_meta or {}),
                    assets=doc_dict.get("assets", {}),
                    structure=doc_dict.get("structure", []),
                    headings=doc_dict.get("headings", []),
                    errors=doc_dict.get("errors", []),
                )

        # Scenario 3: No processor or processing failed, but backend gave some data
        if final_processed_content is None:
            # Construct a minimal ProcessedContent if possible from backend_result
            # This is important if the content_processor is None or failed, but we still got data
            raw_content_fallback = ""
            if hasattr(current_backend_result, "content"):
                if (
                    isinstance(current_backend_result.content, dict)
                    and "html" in current_backend_result.content
                ):
                    raw_content_fallback = current_backend_result.content["html"]
                elif isinstance(current_backend_result.content, str):
                    raw_content_fallback = current_backend_result.content

            final_processed_content = ProcessedContent(
                url=final_url_str,
                title=getattr(current_backend_result, "title", "Untitled Document"),
                content={
                    "raw_content": raw_content_fallback,
                    "formatted_content": raw_content_fallback,
                },
                metadata=backend_meta or {},
                assets={},
                structure=[],
                headings=[],
                errors=[],  # Defaults
            )

        # Quality Check
        quality_metrics_qc = {}  # Initialize quality metrics
        if self.quality_checker and final_processed_content:
            try:
                # Use _current_crawl_config for quality settings
                crawl_cfg_for_quality = (
                    self._current_crawl_config or self.config
                )  # Fallback to global

                # check_quality only expects ProcessedContent
                # It should return (list[ProcessorQualityIssue], dict_metrics)
                (
                    quality_issues_qc,
                    quality_metrics_qc,
                ) = await self.quality_checker.check_quality(final_processed_content)

                # Add issues from quality checker to the ProcessedContent object itself
                if quality_issues_qc:
                    final_processed_content.errors.extend(
                        quality_issues_qc
                    )  # Assuming errors field exists and is a list

                current_quality_score = 1.0  # Default
                if quality_metrics_qc and isinstance(quality_metrics_qc, dict):
                    current_quality_score = quality_metrics_qc.get("quality_score", 1.0)

                min_score_thresh = 0.0
                ignore_low_qual = False
                if crawl_cfg_for_quality and crawl_cfg_for_quality.quality_config:
                    min_score_thresh = (
                        crawl_cfg_for_quality.quality_config.min_quality_score
                    )
                    ignore_low_qual = (
                        crawl_cfg_for_quality.quality_config.ignore_low_quality
                    )

                if current_quality_score < min_score_thresh and not ignore_low_qual:
                    logger.warning(
                        f"Content quality score {current_quality_score} for {final_url_str} below minimum {min_score_thresh}. Discarding."
                    )
                    # Do not return the content if it's below threshold and not ignored
                    quality_error = Exception(
                        f"Content quality score {current_quality_score} below minimum threshold {min_score_thresh}"
                    )
                    return (
                        None,
                        current_backend_result,
                        final_url_str,
                        quality_metrics_qc,
                        quality_error,
                    )

            except Exception as e_qc:
                logger.error(f"Quality checker failed for {final_url_str}: {e_qc}")
                # Do not discard content due to quality checker error, but log it.
                if (
                    final_processed_content
                ):  # Add error to processed content if possible
                    final_processed_content.errors.append(
                        ProcessorQualityIssue(
                            type=IssueType.GENERAL,
                            level=IssueLevel.WARNING,
                            message=str(e_qc),
                            location=final_url_str,
                        )
                    )

        # Update stats if content was successfully processed (or minimally constructed)
        if final_processed_content:
            stats.successful_crawls += (
                1  # Count as successful if we have some ProcessedContent
            )
            stats.pages_crawled += 1  # Count as crawled
            content_bytes = 0
            if final_processed_content.content and isinstance(
                final_processed_content.content, dict
            ):
                content_bytes = len(
                    str(final_processed_content.content.get("formatted_content", ""))
                )
            stats.bytes_processed += content_bytes
        else:  # If final_processed_content is still None after all attempts
            stats.failed_crawls += (
                1  # Count as failed if no ProcessedContent could be made
            )

        return (
            final_processed_content,
            current_backend_result,
            final_url_str,
            quality_metrics_qc,
            None,
        )

    async def _process_url(
        self,
        url: str,
        current_depth: int,
        target_rules: CrawlTarget,  # Renamed target to target_rules
        stats: CrawlStats,
        visited_urls_session: set[str],  # Use session set
    ) -> tuple[Optional[CrawlResult], list[str], dict[str, Any], Optional[Exception]]:
        url_info_obj = create_url_info(url)
        logger.debug(
            f"_process_url: Processing URL {url}, normalized: {url_info_obj.normalized_url if url_info_obj else 'N/A'}, is_valid: {url_info_obj.is_valid if url_info_obj else False}"
        )

        if not url_info_obj or not url_info_obj.is_valid:
            logger.warning(f"Skipping invalid URL: {url}")
            return None, [], {}, ValueError(f"Invalid URL: {url}")

        normalized_url_str = url_info_obj.normalized_url

        if normalized_url_str in visited_urls_session:  # Use the session's visited set
            logger.debug(
                f"_process_url: URL {normalized_url_str} already visited in this session"
            )
            return None, [], {}, None

        # Use max_pages from target_rules (passed as CrawlTarget)
        if (
            target_rules.max_pages is not None
            and len(visited_urls_session) >= target_rules.max_pages
        ):
            logger.debug(
                f"_process_url: Max pages limit ({target_rules.max_pages}) reached for this target."
            )
            return None, [], {}, None

        # Use target_rules for _should_crawl_url decision
        if not self._should_crawl_url(url_info_obj, target_rules):
            logger.debug(
                f"_process_url: URL {normalized_url_str} should not be crawled based on target rules."
            )
            stats.skipped_pages += 1
            return None, [], {}, None

        visited_urls_session.add(normalized_url_str)  # Add to session's visited set

        last_exception: Optional[Exception] = None
        processed_content_final: Optional[ProcessedContent] = None

        # Use max_retries from the current crawl's effective config
        max_retries_for_url = (
            self._current_crawl_config.max_retries
            if self._current_crawl_config
            else self.config.max_retries
        )

        for attempt in range(max_retries_for_url):
            try:
                if (
                    hasattr(self, "rate_limiter") and self.rate_limiter
                ):  # Check existence
                    await self.rate_limiter.acquire()

                selected_backend = self.backend  # Use instance override if set
                if not selected_backend:
                    selected_backend = await self.backend_selector.get_backend(
                        normalized_url_str
                    )

                if not selected_backend:
                    raise ConnectionError(
                        f"No suitable backend found for {normalized_url_str}"
                    )

                logger.debug(
                    f"_process_url: Using backend: {getattr(selected_backend, 'name', 'N/A')} (attempt {attempt + 1}) for {normalized_url_str}"
                )

                # Fetch raw data using backend first
                # This might return a simple response object or a more complex one
                # depending on the backend (e.g. HTTPBackendResult)
                backend_fetch_result = await selected_backend.crawl(
                    url_info_obj
                )  # Pass UrlInfo object

                if (
                    backend_fetch_result
                    and hasattr(backend_fetch_result, "status")
                    and backend_fetch_result.status >= 400
                ):
                    error_message_http = f"HTTP {backend_fetch_result.status}"
                    if (
                        hasattr(backend_fetch_result, "error")
                        and backend_fetch_result.error
                    ):
                        error_message_http += f": {backend_fetch_result.error}"

                    stats.failed_crawls += 1
                    stats.pages_crawled += (
                        1  # Count failed HTTP status as a crawled page
                    )

                    # Use ProcessorQualityIssue for internal tracking, then convert to QualityIssue for CrawlResult
                    http_issue_processor = ProcessorQualityIssue(
                        type=IssueType.GENERAL,
                        level=IssueLevel.ERROR,
                        message=error_message_http,
                        location=normalized_url_str,
                    )

                    # Convert to QualityIssue for CrawlResult
                    http_issue = QualityIssue(
                        type=str(http_issue_processor.type.value)
                        if hasattr(http_issue_processor.type, "value")
                        else str(http_issue_processor.type),
                        level=str(http_issue_processor.level.value)
                        if hasattr(http_issue_processor.level, "value")
                        else str(http_issue_processor.level),
                        message=http_issue_processor.message,
                        location=http_issue_processor.location,
                        details=http_issue_processor.details,
                    )

                    # For _process_url, we return components, not a full CrawlResult yet for this specific error path
                    # The main crawl loop will aggregate these.
                    # However, if we want to return a partial CrawlResult-like structure for this URL:
                    partial_result_for_error = CrawlResult(
                        target=target_rules,
                        stats=CrawlStats(),  # Minimal stats for this URL
                        documents=[],
                        issues=[http_issue],
                        metrics={},
                        crawled_urls=[],
                        errors={normalized_url_str: Exception(error_message_http)},
                        crawled_pages={},
                        project_identity=None,
                    )
                    return (
                        partial_result_for_error,
                        [],
                        {},
                        Exception(error_message_http),
                    )

                if (
                    backend_fetch_result
                    and hasattr(backend_fetch_result, "error")
                    and backend_fetch_result.error
                ):
                    raise Exception(f"Backend error: {backend_fetch_result.error}")

                if not backend_fetch_result:  # If backend returned None
                    raise ConnectionError(
                        f"Backend returned no result for {normalized_url_str}"
                    )

                # Now, process the fetched data (which might involve the content processor, quality checker)
                # Pass target_rules for specific filtering/processing rules for this URL
                (
                    processed_content_final,
                    _,
                    _,
                    quality_metrics_from_backend,
                    process_exception,
                ) = await self._fetch_and_process_with_backend(
                    selected_backend,
                    url_info_obj,
                    target_rules,
                    stats,
                    visited_urls_session,
                    backend_fetch_result,
                )

                # Handle content processing exception if it occurred
                if process_exception:
                    logger.error(
                        f"Content processing exception for {normalized_url_str}: {process_exception}"
                    )
                    stats.failed_crawls += 1
                    stats.pages_crawled += (
                        1  # Count as crawled even if processing failed
                    )

                    # This is crucial for test_crawler_invalid_content and test_crawler_quality_threshold
                    # We need to make sure the error is properly propagated all the way to the final CrawlResult
                    return (None, [], {}, process_exception)

                # If _fetch_and_process_with_backend returns None for processed_content_final,
                # it means the content was discarded (e.g., low quality, wrong type).
                # This is not necessarily a retryable error for this loop.
                if processed_content_final is None:
                    logger.debug(
                        f"Content from {normalized_url_str} was discarded or not processable by _fetch_and_process_with_backend."
                    )
                    # Don't retry if content was explicitly discarded.
                    # The stats for skipped/failed would be handled in _fetch_and_process_with_backend.
                    # We need to decide if this means _process_url returns None or a result with no docs.
                    # Let's return a result with no docs for this URL.
                    return (
                        CrawlResult(
                            target=target_rules,
                            stats=CrawlStats(),
                            documents=[],
                            issues=[],
                            metrics={},
                            crawled_urls=[],
                            errors={},
                            crawled_pages={},
                            project_identity=None,
                        ),
                        [],
                        {},
                        None,
                    )

                break  # Success

            except Exception as e_retry:
                last_exception = e_retry
                logger.warning(
                    f"Error processing {normalized_url_str} (attempt {attempt + 1}/{max_retries_for_url}): {e_retry}"
                )
                if attempt == max_retries_for_url - 1:
                    break  # Max retries reached

                retry_delay = self.retry_strategy.get_delay(attempt)
                logger.info(
                    f"Retrying {normalized_url_str} in {retry_delay:.2f} seconds..."
                )
                await asyncio.sleep(retry_delay)  # Use global asyncio

        if last_exception and processed_content_final is None:
            stats.failed_crawls += 1
            stats.pages_crawled += (
                1  # Count as crawled even if all retries failed for test compatibility
            )

            error_msg_final = str(last_exception) or type(last_exception).__name__
            if isinstance(last_exception, asyncio.TimeoutError):  # global asyncio
                error_msg_final = "Timeout during processing"

            final_issue_processor = ProcessorQualityIssue(
                type=IssueType.GENERAL,
                level=IssueLevel.ERROR,
                message=error_msg_final,
                location=normalized_url_str,
            )

            # Convert to QualityIssue for CrawlResult
            final_issue = QualityIssue(
                type=str(final_issue_processor.type.value)
                if hasattr(final_issue_processor.type, "value")
                else str(final_issue_processor.type),
                level=str(final_issue_processor.level.value)
                if hasattr(final_issue_processor.level, "value")
                else str(final_issue_processor.level),
                message=final_issue_processor.message,
                location=final_issue_processor.location,
                details=final_issue_processor.details,
            )

            partial_result_for_final_error = CrawlResult(
                target=target_rules,
                stats=CrawlStats(),
                documents=[],
                issues=[final_issue],
                metrics={},
                crawled_urls=[],
                errors={normalized_url_str: last_exception},
                crawled_pages={},
                project_identity=None,
            )
            return partial_result_for_final_error, [], {}, last_exception

        # If processed_content_final is still None here, it means it was discarded by _fetch_and_process_with_backend
        # or an unretryable error occurred there.
        if processed_content_final is None:
            logger.debug(
                f"No processable content obtained for {normalized_url_str} after all attempts or due to discard."
            )
            # Return a CrawlResult indicating no documents for this URL.
            # Stats for skipped/failed pages should have been updated in _fetch_and_process_with_backend.
            return (
                CrawlResult(
                    target=target_rules,
                    stats=CrawlStats(),
                    documents=[],
                    issues=[],
                    metrics={},
                    crawled_urls=[],
                    errors={},
                    crawled_pages={},
                    project_identity=None,
                ),
                [],
                {},
                None,
            )

        # Successfully processed content
        document_list_for_result: list[dict[str, Any]] = []
        if processed_content_final:  # Should be ProcessedContent object
            # Safely extract content with type checking
            content_for_doc_data = ""  # Default fallback
            if processed_content_final.content and isinstance(
                processed_content_final.content, dict
            ):
                content_for_doc_data = processed_content_final.content.get(
                    "formatted_content", ""
                )
            elif isinstance(processed_content_final.content, str):
                content_for_doc_data = processed_content_final.content

            doc_data = {
                "url": normalized_url_str,
                "title": processed_content_final.title or "Untitled",
                "content": content_for_doc_data,
                "doc_id": None,  # Will be set if added to organizer
            }
            document_list_for_result.append(doc_data)

            # Add to document organizer if available
            if self.document_organizer:
                try:
                    # Pass the ProcessedContent object directly
                    doc_id_org = self.document_organizer.add_document(
                        processed_content_final
                    )
                    doc_data["doc_id"] = doc_id_org  # Update doc_id in the dict
                    logger.debug(
                        f"Added document {normalized_url_str} to organizer with id {doc_id_org}"
                    )
                except Exception as e_org_add:
                    logger.error(
                        f"Error adding document {normalized_url_str} to organizer: {e_org_add}"
                    )
                    processed_content_final.errors.append(
                        ProcessorQualityIssue(
                            type=IssueType.GENERAL,
                            level=IssueLevel.WARNING,
                            message=str(e_org_add),
                            location=normalized_url_str,
                        )
                    )

        # Issues are now part of ProcessedContent.errors
        current_issues_processor: list[ProcessorQualityIssue] = (
            processed_content_final.errors if processed_content_final else []
        )

        # Convert ProcessorQualityIssue objects to QualityIssue objects for CrawlResult
        current_issues: list[QualityIssue] = []
        for issue in current_issues_processor:
            converted_issue = QualityIssue(
                type=str(issue.type.value)
                if hasattr(issue.type, "value")
                else str(issue.type),
                level=str(issue.level.value)
                if hasattr(issue.level, "value")
                else str(issue.level),
                message=issue.message,
                location=issue.location,
                details=issue.details,
            )
            current_issues.append(converted_issue)

        # Metrics (can be enhanced later, e.g. from quality checker)
        current_metrics: dict[str, Any] = {
            normalized_url_str: {"processed_at": datetime.now().isoformat()}
        }  # Use datetime.now()
        if (
            processed_content_final
            and hasattr(processed_content_final, "metadata")
            and processed_content_final.metadata
        ):
            if (
                "quality_metrics" in processed_content_final.metadata
            ):  # If QC added metrics to metadata
                current_metrics[normalized_url_str].update(
                    processed_content_final.metadata["quality_metrics"]
                )

        # Add quality metrics from backend processing
        if quality_metrics_from_backend:
            current_metrics[normalized_url_str].update(quality_metrics_from_backend)

        crawled_pages_map: dict[str, ProcessedContent] = {}
        if processed_content_final:
            crawled_pages_map[normalized_url_str] = processed_content_final

        # This CrawlResult is specific to this single URL's processing
        url_crawl_result = CrawlResult(
            target=target_rules,  # The CrawlTarget rules for this specific URL
            stats=CrawlStats(),  # Stats are aggregated globally, this is for this URL's contribution if needed
            documents=document_list_for_result,
            issues=current_issues,  # Now list[QualityIssue] from crawler.models
            metrics=current_metrics,
            crawled_urls=[normalized_url_str] if document_list_for_result else [],
            errors={},  # Errors handled by last_exception return
            crawled_pages=crawled_pages_map,
            project_identity=None,  # Project identity is part of the main CrawlResult
        )

        # Extract new links for further crawling
        links_to_follow: list[str] = []  # Use list
        if current_depth < target_rules.depth and processed_content_final:
            # Use _find_links_recursive with the structure from ProcessedContent
            if processed_content_final.structure:
                try:
                    hrefs_found = self._find_links_recursive(
                        processed_content_final.structure
                    )
                    from urllib.parse import urljoin  # Local import

                    for href in hrefs_found:
                        if href and isinstance(
                            href, str
                        ):  # Ensure href is a non-empty string
                            abs_url = urljoin(normalized_url_str, href.strip())
                            # Basic validation of the formed absolute URL
                            parsed_abs_url = urlparse(abs_url)
                            if parsed_abs_url.scheme in ["http", "https", "file"]:
                                links_to_follow.append(abs_url)
                except Exception as e_link_extract:
                    logger.warning(
                        f"Link extraction failed for {normalized_url_str}: {e_link_extract}"
                    )

        return url_crawl_result, links_to_follow, current_metrics, None

    async def _initialize_crawl_queue(
        self, target: CrawlTarget
    ) -> tuple[list[tuple[str, int]], str]:  # Use list
        initial_url = target.url
        parsed_initial = urlparse(initial_url)

        if not parsed_initial.scheme and parsed_initial.path:  # Likely a package name
            logger.info(
                f"Target '{initial_url}' appears to be a package name. Attempting to discover documentation URL."
            )
            try:
                # ProjectIdentifier is already imported at the top
                identifier = ProjectIdentifier()
                discovered_doc_url = await identifier.discover_doc_url(initial_url)
                if discovered_doc_url:
                    logger.info(
                        f"Discovered documentation URL for '{initial_url}': {discovered_doc_url}"
                    )
                    initial_url = discovered_doc_url
                else:
                    logger.error(
                        f"Could not discover documentation URL for package: {initial_url}"
                    )
                    raise ValueError(
                        f"Invalid target: '{initial_url}' is not a valid URL and documentation URL discovery failed."
                    )
            except Exception as e_discover:  # Catch any error during discovery
                logger.error(
                    f"Error discovering doc URL for '{initial_url}': {e_discover}"
                )
                raise ValueError(
                    f"Invalid target: '{initial_url}' is not a valid URL and documentation URL discovery failed with error: {e_discover}"
                ) from e_discover

        # Queue items are (url_string, depth_integer)
        crawl_queue_init: list[tuple[str, int]] = [(initial_url, 0)]  # Use list
        return crawl_queue_init, initial_url

    def _setup_backends(self):  # For test compatibility, __init__ handles main setup
        # This method is mostly for ensuring test environments that might call it
        # have a basic HTTP backend registered if they bypass the main __init__.
        # The main __init__ already registers the HTTP backend.
        if not self.backend_selector.get_backend_by_name(
            "HTTPBackend"
        ):  # Check if already registered
            http_config_test = HTTPBackendConfig(
                timeout=self.config.request_timeout,
                verify_ssl=self.config.verify_ssl,
                follow_redirects=self.config.follow_redirects,
                headers=self.config.headers or {"User-Agent": self.config.user_agent},
            )
            http_backend_test = HTTPBackend(http_config_test)
            http_criteria_test = BackendCriteria(
                priority=1,
                content_types=["text/html"],
                url_patterns=["http://", "https://"],
            )
            self.backend_selector.register_backend(
                name=http_backend_test.name,
                backend=http_backend_test,
                criteria=http_criteria_test,
            )
            logger.info(
                "HTTPBackend registered via _setup_backends (likely test environment)."
            )

    async def cleanup(self):
        logger.info("Cleaning up crawler resources...")
        self._crawled_urls.clear()  # Clear the instance's set
        self.visited_urls.clear()  # Clear test compatibility set
        self.crawl_queue.clear()  # Clear test compatibility queue
        self.active_tasks = 0

        if (
            self.client_session
            and hasattr(self.client_session, "close")
            and not self.client_session.closed
        ):
            await self.client_session.close()
        self.client_session = None

        # Cleanup components if they have an async cleanup method
        for component in [
            self.quality_checker,
            self.document_organizer,
            self.content_processor,
        ]:
            if hasattr(component, "cleanup") and callable(component.cleanup):
                try:
                    # Check if it's an async method
                    if asyncio.iscoroutinefunction(component.cleanup):
                        await component.cleanup()
                    else:
                        component.cleanup()  # Call synchronously if not async
                except Exception as e_cleanup:
                    logger.error(
                        f"Error during cleanup of {component.__class__.__name__}: {e_cleanup}"
                    )
        logger.info("Crawler cleanup complete.")


# Backward compatibility alias
DocumentationCrawler = Crawler
