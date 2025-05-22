from typing import Any, Dict, Optional, Type
from urllib.parse import urlparse
import logging # Standard logging
import fnmatch
import asyncio
import inspect
from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__) # Define logger for this module

from .base import CrawlerBackend # Relative import for CrawlerBackend


class BackendCriteria(BaseModel):
    priority: int
    content_types: list[str]
    url_patterns: list[str]
    max_load: float = 0.8
    min_success_rate: float = 0.7
    schemes: list[str] = ['http', 'https', 'file']
    netloc_patterns: list[str] = []
    path_patterns: list[str] = []
    domains: list[str] = []
    paths: list[str] = []

    @field_validator('url_patterns')
    def validate_url_patterns(cls, v):
        if not v:  # Handles None or empty list
            return []
        return v

    @field_validator('schemes')
    def validate_schemes(cls, v):
        if not v:
            return ['http', 'https', 'file']
        return v

class BackendSelector:
    def __init__(self):
        self._backends: Dict[str, Type[CrawlerBackend]] = {}
        self._backend_instances: Dict[str, CrawlerBackend] = {}
        self.criteria: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
        self._initialized_backends = False

    def select_backend_for_url(self, url: str, content_type: Optional[str] = None):
        """
        Select a backend instance matching the given URL and optional content type.
        Returns the backend instance or None if no match.
        
        Selection logic:
        1. First try to find a backend that matches both the URL and content_type exactly
        2. If no exact match, find backends that match the URL and can handle any content type
        3. If none found, find a backend with the lowest priority as fallback
        """
        parsed = urlparse(url)
        exact_matches = []
        url_matches = []
        fallback_backends = []

        logger.debug(f"Selecting backend for URL \'{url}\' with content_type \'{content_type}\'")
        # Log all available criteria for debugging
        # for n, c in getattr(self, "criteria", {}).items():
        #     logger.debug(f"Available criteria for backend \'{n}\': schemes={c.schemes}, domains={c.domains}, paths={c.paths}, url_patterns={c.url_patterns}, content_types={c.content_types}")

        for name, criteria in getattr(self, "criteria", {}).items():
            url_match = True
            
            if name == "mock_crawler": logger.debug(f"MockCrawler START: url_match={url_match}, criteria_schemes={criteria.schemes}") # DEBUG MOCK
            if parsed.scheme and criteria.schemes and parsed.scheme not in criteria.schemes:
                url_match = False
                if name == "HTTPBackend": logger.debug(f"HTTPBackend: FAILED scheme check. parsed.scheme=\'{parsed.scheme}\', criteria.schemes={criteria.schemes}")
                if name == "mock_crawler": logger.debug(f"MockCrawler: FAILED scheme check. parsed.scheme=\'{parsed.scheme}\', criteria.schemes={criteria.schemes}") # DEBUG MOCK
            
            if name == "mock_crawler": logger.debug(f"MockCrawler AfterSchemeCheck: url_match={url_match}, criteria_domains={criteria.domains}") # DEBUG MOCK
            if url_match and criteria.domains and parsed.hostname not in criteria.domains:
                url_match = False
                if name == "HTTPBackend": logger.debug(f"HTTPBackend: FAILED domain check. parsed.hostname=\'{parsed.hostname}\', criteria.domains={criteria.domains}")
                if name == "mock_crawler": logger.debug(f"MockCrawler: FAILED domain check. parsed.hostname=\'{parsed.hostname}\', criteria.domains={criteria.domains}") # DEBUG MOCK

            if name == "mock_crawler": logger.debug(f"MockCrawler AfterDomainCheck: url_match={url_match}, criteria_paths={criteria.paths}") # DEBUG MOCK
            if url_match and criteria.paths and not any(parsed.path.startswith(p) for p in criteria.paths):
                url_match = False
                if name == "HTTPBackend": logger.debug(f"HTTPBackend: FAILED path check. parsed.path=\'{parsed.path}\', criteria.paths={criteria.paths}")
                if name == "mock_crawler": logger.debug(f"MockCrawler: FAILED path check. parsed.path=\'{parsed.path}\', criteria.paths={criteria.paths}") # DEBUG MOCK
            
            if name == "mock_crawler": logger.debug(f"MockCrawler AfterPathCheck: url_match={url_match}, criteria_url_patterns={criteria.url_patterns}") # DEBUG MOCK
            if url_match and criteria.url_patterns:
                pattern_matched_for_this_criterion = False
                for pat_idx, pat in enumerate(criteria.url_patterns):
                    is_simple_scheme_prefix = pat.endswith("://") and not any(glob_char in pat[:-3] for glob_char in "*?[]")
                    match_attempted = False
                    current_pat_match = False

                    if is_simple_scheme_prefix:
                        match_attempted = True
                        if url.startswith(pat):
                            pattern_matched_for_this_criterion = True
                            current_pat_match = True
                            if name == "HTTPBackend": logger.debug(f"HTTPBackend: Matched simple scheme prefix \'{pat}\' for url \'{url}\'")
                            if name == "mock_crawler": logger.debug(f"MockCrawler: Matched simple scheme prefix \'{pat}\' for url \'{url}\'") # DEBUG MOCK
                            break
                    else:
                        match_attempted = True
                        if fnmatch.fnmatch(url, pat) or \
                           (parsed.netloc and fnmatch.fnmatch(parsed.netloc, pat)):
                            pattern_matched_for_this_criterion = True
                            current_pat_match = True
                            if name == "HTTPBackend": logger.debug(f"HTTPBackend: Matched fnmatch pattern \'{pat}\' for url \'{url}\' or netloc \'{parsed.netloc}\'")
                            if name == "mock_crawler": logger.debug(f"MockCrawler: Matched fnmatch pattern \'{pat}\' for url \'{url}\' or netloc \'{parsed.netloc}\'") # DEBUG MOCK
                            break
                    
                    if name == "HTTPBackend" and match_attempted:
                         logger.debug(f"HTTPBackend: Pattern \'{pat}\' (idx {pat_idx}, simple_scheme={is_simple_scheme_prefix}) did not match url \'{url}\'. current_pat_match={current_pat_match}")
                    if name == "mock_crawler" and match_attempted: # DEBUG MOCK
                         logger.debug(f"MockCrawler: Pattern \'{pat}\' (idx {pat_idx}, simple_scheme={is_simple_scheme_prefix}) did not match url \'{url}\'. current_pat_match={current_pat_match}")


                if not pattern_matched_for_this_criterion:
                    url_match = False
                    if name == "HTTPBackend": logger.debug(f"HTTPBackend: FAILED url_patterns check. No pattern in {criteria.url_patterns} matched url \'{url}\'")
                    if name == "mock_crawler": logger.debug(f"MockCrawler: FAILED url_patterns check. No pattern in {criteria.url_patterns} matched url \'{url}\'") # DEBUG MOCK
            
            if name == "HTTPBackend": 
                logger.debug(f"HTTPBackend: Final pre-continue url_match state: {url_match} for url \'{url}\'")
            if name == "mock_crawler": logger.debug(f"MockCrawler: Final pre-continue url_match state: {url_match} for url \'{url}\'") # DEBUG MOCK

            if not url_match:
                continue
            
            fallback_backends.append((criteria.priority, name))
            if name == "HTTPBackend": logger.debug(f"HTTPBackend: Added to fallback_backends. Current fallback_backends: {fallback_backends}")
            if name == "mock_crawler": logger.debug(f"MockCrawler: Added to fallback_backends. Current fallback_backends: {fallback_backends}") # DEBUG MOCK


            if name == "HTTPBackend": 
                logger.debug(f"HTTPBackend check 2: content_type=\'{content_type}\', criteria.content_types={criteria.content_types}, exact_matches_len={len(exact_matches)}, url_matches_len={len(url_matches)}, fallback_backends_len={len(fallback_backends)}")
            if name == "mock_crawler": # DEBUG MOCK
                logger.debug(f"MockCrawler check 2: content_type=\'{content_type}\', criteria.content_types={criteria.content_types}, exact_matches_len={len(exact_matches)}, url_matches_len={len(url_matches)}, fallback_backends_len={len(fallback_backends)}")

            if content_type and criteria.content_types:
                if content_type in criteria.content_types:
                    exact_matches.append((criteria.priority, name))
                    logger.debug(f"Exact match found for backend \'{name}\' (priority {criteria.priority})")
                    if name == "HTTPBackend": logger.debug(f"HTTPBackend: Added to exact_matches (specific content_type). Current exact_matches: {exact_matches}")
                    if name == "mock_crawler": logger.debug(f"MockCrawler: Added to exact_matches (specific content_type). Current exact_matches: {exact_matches}") # DEBUG MOCK
            elif not content_type: 
                if criteria.content_types and 'text/html' in criteria.content_types: # Added criteria.content_types check
                    exact_matches.append((criteria.priority, name))
                    logger.debug(f"Selected HTML handler backend \'{name}\' (priority {criteria.priority}) for unknown content type")
                    if name == "HTTPBackend": logger.debug(f"HTTPBackend: Added to exact_matches (HTML for unknown content_type). Current exact_matches: {exact_matches}")
                    if name == "mock_crawler": logger.debug(f"MockCrawler: Added to exact_matches (HTML for unknown content_type). Current exact_matches: {exact_matches}") # DEBUG MOCK
                else: 
                    url_matches.append((criteria.priority, name))
                    if name == "HTTPBackend": logger.debug(f"HTTPBackend: Added to url_matches (no content_type, not HTML handler). Current url_matches: {url_matches}")
                    if name == "mock_crawler": logger.debug(f"MockCrawler: Added to url_matches (no content_type, not HTML handler). Current url_matches: {url_matches}") # DEBUG MOCK
            else: 
                url_matches.append((criteria.priority, name))
                if name == "HTTPBackend": logger.debug(f"HTTPBackend: Added to url_matches (content_type mismatch). Current url_matches: {url_matches}")
                if name == "mock_crawler": logger.debug(f"MockCrawler: Added to url_matches (content_type mismatch). Current url_matches: {url_matches}") # DEBUG MOCK
        
        # Log final lists before selection
        logger.debug(f"Final selection lists: exact_matches={exact_matches}, url_matches={url_matches}, fallback_backends={fallback_backends}")

        if exact_matches:
            best_match = max(exact_matches, key=lambda x: x[0])
            logger.info(f"Selected backend '{best_match[1]}' as exact match")
            return self._backend_instances.get(best_match[1])

        # Use URL matches ordered by priority; for unknown content type apply HTML preference only when content_type is None
        if url_matches:
            if content_type:
                # Choose by priority only
                best_match = max(url_matches, key=lambda x: x[0])
            else:
                best_match = max(url_matches, key=lambda x: (
                    x[0],  # Priority first
                    'text/html' in self.criteria[x[1]].content_types  # HTML capability second
                ))
            logger.info(f"Selected backend '{best_match[1]}' with priority {best_match[0]}")
            return self._backend_instances.get(best_match[1])
        
        # If no exact or URL matches, try to use a fallback backend
        if fallback_backends:
            best_match = max(fallback_backends, key=lambda x: x[0])
            logger.info(f"Selected fallback backend '{best_match[1]}' with priority {best_match[0]}")
            return self._backend_instances.get(best_match[1])
        logger.info(f"Selected backend '{best_match[1]}' with priority {best_match[0]}")
        return self._backend_instances.get(best_match[1])

    # Support both (name, backend_class) and (name, backend_instance, criteria)
    def register_backend(self, name: str, backend, criteria: 'BackendCriteria' = None):
        """
        Register a backend by name.
        - For production: pass (name: str, backend_class: Type[CrawlerBackend])
        - For tests: pass (name: str, backend_instance: CrawlerBackend, criteria: BackendCriteria)
        """
        if not hasattr(self, "criteria"):
            self.criteria = {}
        if inspect.isclass(backend):
            # Production/class registration
            if name in self._backends:
                logger.warning(f"Backend '{name}' is already registered. Overwriting.")
            self._backends[name] = backend
            logger.info(f"Backend class '{name}' registered: {backend}")
        else:
            # Test/mock instance registration
            if name in self._backend_instances:
                logger.warning(f"Backend instance '{name}' is already registered. Overwriting.")
            self._backend_instances[name] = backend
            self._backends[name] = backend  # Ensure test instance is also in _backends for test assertions
            logger.info(f"Backend instance '{name}' registered: {backend}")
            if criteria is not None:
                self.criteria[name] = criteria
                logger.info(f"Criteria for backend '{name}' registered: {criteria}")

    async def unregister_backend(self, name: str):
        async with self._lock:
            if name in self._backends:
                del self._backends[name]
                logger.info(f"Backend class '{name}' unregistered.")
            if name in self._backend_instances:
                backend_instance = self._backend_instances.pop(name)
                try:
                    await backend_instance.close()
                    logger.info(f"Instance of backend '{name}' closed and unregistered.")
                except Exception as e:
                    logger.error(f"Error closing backend instance '{name}': {e}")
            elif name not in self._backends and name not in self._backend_instances:
                logger.warning(f"Backend '{name}' not found for unregistration.")

    def _initialize_known_backends(self):
        if not self._initialized_backends:
            logger.debug("Initializing known backends...")
            try:
                from .scrapy_backend import ScrapyBackend # Relative import
            except ImportError as e:
                logger.warning(f"ScrapyBackend not available or failed to import: {e}")
            try:
                from .playwright_backend import PlaywrightBackend # Relative import
            except ImportError as e:
                logger.info(f"PlaywrightBackend not available: {e}")
            try:
                from .crawl4ai_backend import Crawl4AIBackend # Relative import
            except ImportError as e:
                logger.info(f"Crawl4AIBackend not available: {e}")
            
            self._initialized_backends = True
            logger.info("Known backends initialization process completed.")

    async def get_backend(self, url: str, content_type: Optional[str] = None) -> Optional[CrawlerBackend]:
        """Get backend for URL by first checking existing instances, then creating new if needed."""
        self._initialize_known_backends()

        async with self._lock:
            # Try existing backend instances first
            selected_backend = self.select_backend_for_url(url)
            if selected_backend:
                return selected_backend

            # No existing instance - try to find matching backend class
            parsed = urlparse(url)
            for name, criteria in self.criteria.items():
                if (name in self._backends and
                    (parsed.scheme in criteria.schemes) and
                    any(fnmatch.fnmatch(url, pattern) for pattern in criteria.url_patterns)):
                    
                    # Found a matching backend class - instantiate it
                    backend_class = self._backends[name]
                    try:
                        logger.debug(f"Instantiating backend '{name}' for URL '{url}'")
                        if config and 'config' in inspect.signature(backend_class.__init__).parameters:
                            instance = backend_class(config=config)
                        else:
                            instance = backend_class()
                        
                        self._backend_instances[name] = instance
                        logger.info(f"Created backend instance '{name}'")
                        return instance
                    except Exception as e:
                        logger.error(f"Error initializing backend '{name}': {e}", exc_info=True)
                        continue
            
            logger.error(f"No backend found for URL '{url}'. Available: {list(self._backends.keys())}")
            return None

    async def get_all_backends(self) -> Dict[str, CrawlerBackend]:
        return self._backend_instances.copy()

    async def close_all_backends(self):
        logging.info("Closing all backend instances...")
        for backend, criteria in list(self._backends.items()): # Iterate over items
            try:
                if hasattr(backend, 'close') and asyncio.iscoroutinefunction(backend.close): # Check backend
                    logging.info(f"Closing backend instance '{backend}'...")
                    await backend.close() # Call close on backend
                else:
                    logging.info(f"Backend instance '{backend}' does not have an async close method or close is not a coroutine.")
            except Exception as e:
                logging.error(f"Error closing backend instance '{backend}': {e}", exc_info=True) # Log backend and exc_info
        self._backends.clear()
        logging.info("All backend instances closed and cleared.")

global_backend_selector = BackendSelector()
logger.info(f"Global BackendSelector instance created: {global_backend_selector}")
