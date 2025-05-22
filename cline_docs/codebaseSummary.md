# Codebase Summary

## Key Components and Their Interactions

### Core Components
1. Processors
   - ContentProcessor: Handles content processing and extraction
   - DocumentProcessor: Manages document-level operations
   - HTMLProcessor: Processes HTML content
   - LinkProcessor: Handles URL and link processing
   - QualityChecker: Validates content quality

2. Backend System
   - BackendSelector: Manages different backend implementations (e.g., HTTP, Crawl4AI, potentially Scrapy)
   - HTTP Backend: Handles standard web requests using libraries like `aiohttp`
   - Crawl4AI: Specialized crawler implementation
   - Scrapy Backend (Planned/Under Consideration): Integration of the Scrapy framework as an alternative backend

3. Models
   - Quality: Quality-related data structures
   - URL:
     - URLInfo: Main URL validator and normalizer (now created via `src/utils/url/factory.py` using `tldextract` and `idna`)
     - Security: URL security rules and checks
     - Parsing: URL resolution and protocol handling
     - Normalization: URL component normalization
     - Classification: URL relationship detection (internal/external)
   - CrawlResult: Data model for results from individual backends (`src/backends/base.py`) and for the aggregated crawl result (`src/crawler.py`).

### Data Flow
1. Input URL/Document → 
2. Backend Processing (returns `BackendCrawlResult`) →
3. Document Extraction from `BackendCrawlResult.content.get("documents", [])` →
4. Document Aggregation into `DocumentationCrawler.CrawlResult.documents` →
5. Quality Validation

## External Dependencies

Key external dependencies identified from `requirements.txt` and `pyproject.toml`:

- `aiohttp`: Asynchronous HTTP client/server framework.
- `beautifulsoup4`: Library for pulling data out of HTML and XML files.
- `duckduckgo-search`: Python library for DuckDuckGo search API integration.
- `pydantic`: Data validation and settings management using Python type hints.
- `markdownify`: HTML to Markdown conversion.
- `tldextract`: Accurately separates the gTLD, domain, and subdomain of a URL.
- `idna`: Support for Internationalized Domain Names in Applications (IDNA).
- `fastapi`: Web framework for building APIs (used for the GUI).
- `httpx`: A fully featured HTTP client for Python 3, which provides sync and async APIs.
- `pytest`: Testing framework.
- `pytest-asyncio`: Pytest plugin for testing asyncio applications.
- `uvloop`: Fast, drop-in replacement of the default asyncio event loop.
- `black`: Uncompromising Python code formatter.
- `ruff`: An extremely fast Python linter and code formatter.
- `mypy`: Optional static typing for Python.
- `requests`: Elegant and simple HTTP library (used in some utilities).
- `certifi`: Mozilla's collection of Root Certificates.
- `bleach`: An allowed-list-based HTML sanitizing library.
- `scrapy`: Fast and powerful scraping and web crawling framework (potential backend).
- `selenium`: Browser automation framework (present in requirements, status in project needs verification).
- `sqlalchemy`: SQL toolkit and Object-Relational Mapper (ORM) (present in requirements, status in project needs verification).
- `redis`: In-memory data structure store, used as a database, cache, and message broker (present in requirements, status in project needs verification).

## Recent Significant Changes

### Bug Fixes and Warning Resolutions (May 2025)
A series of critical bugs, test failures, and warnings were addressed:
- **`AttributeError` in `src/crawler.py`:** Corrected document access from `BackendCrawlResult.content` (was `result_data.documents`, now `result_data.content.get("documents", [])`) around line 951.
- **`RuntimeWarning` in `tests/test_content_processor.py`:** Added `await` for `ContentProcessor.process`.
- **`RuntimeWarning` in `src/backends/crawl4ai.py`:** Added `await` for `AsyncMockMixin._execute_mock_call`.
- **`RuntimeWarning` in `tests/test_crawler_advanced.py`:** Added `await` for `AsyncMockMixin._execute_mock_call`.
- **`DeprecationWarning: datetime.datetime.utcnow()`:** Investigated; likely from a dependency as no instances were found in project code.
- **`FAILED tests/test_crawler.py::test_depth_limited_crawling`:** Corrected `max_pages` enforcement in `src/crawler.py`.
- **`FAILED tests/test_crawler.py::test_duckduckgo_search`:** Mocked DuckDuckGo API calls in the test.
- **`FAILED tests/test_integration_advanced.py::test_rate_limiting_integration`:** Ensured `Crawl4AIBackend` uses the external `RateLimiter` correctly in `src/backends/crawl4ai.py`.
- **`PytestDeprecationWarning` in `tests/test_crawler_advanced.py`:** Changed `@pytest.fixture` to `@pytest_asyncio.fixture` for `patched_rate_limiter`.
- **`DeprecationWarning` for `TemplateResponse` in `src/gui/app.py`:** Updated parameter order for `TemplateResponse`.

### Backend Selector Enhancements
- Refactored `BackendSelector` to use the correct `URLInfo` class from `src/utils/url/factory.py` for URL processing, replacing the deprecated `URLProcessor`.
- Simplified the scoring logic within `BackendSelector._evaluate_backend` by removing a redundant content type evaluation block, aiming to improve clarity and consistency in backend selection.

### URL Handling Enhancement & Modularization (URLInfo Factory)
- The URL handling implementation has been refactored to use `tldextract` library and modularized into specialized components (`security.py`, `normalization.py`, `parsing.py`, `classification.py`).
- `URLInfo` object creation is now centralized in `src/utils/url/factory.py` via the `create_url_info` function.
- Benefits:
  - Proper domain parsing, enhanced component extraction.
  - Maintained security validation.
  - Reduced code complexity and improved maintainability.
  - Targeted unit tests and improved performance.

#### Migration Notes
- `URLInfo` is now primarily instantiated via `from src.utils.url.factory import create_url_info`.
- New properties available include: `root_domain`, `suffix`, `registered_domain`, `subdomain`.

### Documentation Cleanup and Next Steps Planning (May 2025)
- Completed a comprehensive review of project documentation, identifying outdated files and those requiring updates.
- Created a plan (`project_cleanup_and_next_steps_plan.md`) outlining the documentation cleanup process and prioritizing future code development tasks.
- Initiated the process of updating key documentation files, including this `codebaseSummary.md`.

## User Feedback Integration
This section is pending updates based on future test results and user feedback.
