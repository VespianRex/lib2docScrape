import pytest
import os
import sys
import asyncio
import pytest_asyncio # Import pytest_asyncio
from typing import Dict, Any, List, Optional # Added Optional
from typing import Dict, Any, List
import logging # Added import
import platform
from unittest.mock import Mock, AsyncMock # Import AsyncMock

if platform.system() != 'Windows':
    import uvloop
    uvloop.install()

from bs4 import BeautifulSoup
# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.backends.base import CrawlerBackend, CrawlResult
from src.backends.selector import BackendCriteria, BackendSelector
from src.crawler import CrawlerConfig, DocumentationCrawler, CrawlTarget # Added CrawlTarget
from src.organizers.doc_organizer import DocumentOrganizer, OrganizationConfig
from src.processors.content_processor import ContentProcessor, ProcessorConfig, ProcessedContent # Import ProcessedContent
from src.processors.quality_checker import QualityChecker, QualityConfig
from src.utils.url_info import URLInfo # Import URLInfo

class MockSuccessBackend(CrawlerBackend):
    """Mock backend that always succeeds."""

    def __init__(self):
        super().__init__(name="mock_success_backend")
        self.crawl_called = False
        self.validate_called = False
        self.process_called = False

    # Updated signature to match crawler call: crawl(url=..., config=...)
    async def crawl(self, url: str, config: Optional[CrawlerConfig] = None) -> CrawlResult: # Make config optional
        """Simulate a successful crawl with a delay."""
        self.crawl_called = True
        # Simulate network delay for rate limiting tests
        await asyncio.sleep(0.15) # Increased delay

        # Use the provided URL directly (assuming it's already normalized by the caller if needed)
        normalized_url = url

        return CrawlResult(
            url=normalized_url, # Use normalized URL
            content={
                "html": f"""
                <html>
                    <head>
                        <title>Test Document for {normalized_url}</title>
                        <meta name="description" content="Test description">
                    </head>
                    <body>
                        <h1>Test Document for {normalized_url}</h1>
                        <p>This is a test paragraph.</p>
                        <pre><code>def test():
    pass</code></pre>
                        <a href="/test">Test Link</a>
                    </body>
                </html>
                """
            },
            metadata={
                "status_code": 200,
                "headers": {
                    "content-type": "text/html"
                }
            },
            status=200
        )

    async def validate(self, content: CrawlResult) -> bool:
        self.validate_called = True
        return True

    async def process(self, content: CrawlResult) -> Dict:
        self.process_called = True
        return {
            "title": "Test Document",
            "content": {
                "headings": [{"level": 1, "text": "Test Document"}],
                "paragraphs": ["This is a test paragraph."],
                "code_blocks": [{
                    "language": "python",
                    "content": "def test():\n    pass"
                }],
                "links": [{
                    "text": "Test Link",
                    "url": "/test",
                    "title": ""
                }]
            },
            "metadata": content.metadata,
            "assets": {}
        }

class MockFailureBackend(CrawlerBackend):
    """Mock backend that always fails."""

    def __init__(self):
        super().__init__(name="mock_failure_backend")
        self.crawl_called = False
        self.validate_called = False
        self.process_called = False

    # Updated signature to match crawler call: crawl(url_info=..., config=...)
    async def crawl(self, url_info: URLInfo, config: CrawlerConfig) -> CrawlResult:
        self.crawl_called = True
        normalized_url = url_info.normalized_url # Get normalized URL
        return CrawlResult(
            url=normalized_url, # Use normalized URL
            content={},
            metadata={"error": "Simulated failure"},
            status=500,
            error="Simulated failure"
        )

    async def validate(self, content: CrawlResult) -> bool:
        self.validate_called = True
        return False

    async def process(self, content: CrawlResult) -> Dict:
        self.process_called = True
        return {"error": "Processing failed"}

@pytest.fixture
def sample_html() -> str:
    """Sample HTML content for testing."""
    return """
    <html>
        <head>
            <title>Test Document</title>
            <meta name="description" content="Test description" />
        </head>
        <body>
            <h1>Test Heading</h1>
            <p>This is a test paragraph.</p>
            <pre><code>def test():
    pass</code></pre>
            <a href="/test">Test Link</a>
        </body>
    </html>
    """

@pytest.fixture
def soup(sample_html: str) -> BeautifulSoup:
    """BeautifulSoup object for testing."""
    return BeautifulSoup(sample_html, 'html.parser')

@pytest.fixture
def processor_config() -> ProcessorConfig:
    """Default processor configuration for testing."""
    return ProcessorConfig(
        max_content_length=10000,
        min_content_length=10,
        max_heading_length=100,
        max_heading_level=6,
        max_code_block_size=1000,
        preserve_whitespace=False,
        sanitize_content=True,
        extract_metadata=True,
        extract_assets=True,
        extract_code_blocks=True
    )

@pytest.fixture
def content_processor(processor_config: ProcessorConfig) -> ContentProcessor:
    """Content processor instance for testing."""
    # This fixture now returns a mock that provides a structure with a link
    mock_processed = ProcessedContent(
        content={'formatted_content': 'Processed content'}, # Content dict doesn't need structure
        metadata={'title': 'Mock Title'},
        assets={'images': [], 'stylesheets': [], 'scripts': [], 'media': []},
        headings=[{'level': 1, 'text': 'Mock Title'}],
        # Add a sample link structure matching StructureHandler output
        structure=[{'type': 'text', 'content': [{'type': 'link_inline', 'text': 'Test Link', 'href': '/test'}]}], # Simulate link within a paragraph
        title='Mock Title'
    )
    processor = AsyncMock(spec=ContentProcessor) # Use AsyncMock
    processor.process = AsyncMock(return_value=mock_processed) # Mock the process method
    return processor


@pytest.fixture
def quality_config() -> QualityConfig:
    """Default quality configuration for testing."""
    return QualityConfig(
        min_content_length=100,
        max_content_length=100000,
        min_headings=1,
        max_heading_level=6,
        min_internal_links=2,
        required_metadata=['title', 'description'],
        min_code_block_length=10,
        max_code_block_length=1000
    )

@pytest.fixture
def quality_checker(quality_config: QualityConfig) -> QualityChecker:
    """Quality checker instance for testing."""
    return QualityChecker(config=quality_config)

@pytest.fixture
def create_test_content():
    """Factory function for creating test content."""
    def _create_content(url: str = "", title: str = "", content: Dict[str, Any] = None) -> Any:
        from src.processors.content_processor import ProcessedContent
        return ProcessedContent(
            url=url,
            title=title,
            content=content or {},
            metadata={},
            assets={},
            errors=[]
        )
    return _create_content

@pytest.fixture
def sample_urls() -> List[str]:
    """Sample URLs for testing."""
    return [
        "https://example.com",
        "https://example.com/docs",
        "https://example.com/api"
    ]

@pytest_asyncio.fixture # Use pytest_asyncio fixture
async def mock_success_backend() -> MockSuccessBackend:
    """Mock backend that succeeds."""
    # No async setup needed for this simple mock, just return
    return MockSuccessBackend()

@pytest_asyncio.fixture # Use pytest_asyncio fixture
async def mock_failure_backend() -> MockFailureBackend:
    """Mock backend that fails."""
    # No async setup needed for this simple mock, just return
    return MockFailureBackend()

@pytest.fixture(scope="function") # Explicitly set function scope
def backend_selector(mock_success_backend: MockSuccessBackend) -> BackendSelector:
    """Configured backend selector."""
    selector = BackendSelector() # Initializes with default 'crawl4ai'
    selector.clear_backends() # Clear any existing backends (including the default)

    # Register ONLY the mock backend with high priority and correct criteria
    selector.register_backend(
        mock_success_backend, # This object has name="mock_success_backend"
        BackendCriteria(
            priority=200, # High priority
            domains=["example.com"],
            url_patterns=["https://example.com/doc*"],
            content_types=["text/html"]
        )
    )
    # Log the state JUST before returning
    logging.debug(f"Backend_selector fixture returning selector id={id(selector)}, backends={list(selector.backends.keys())}")
    return selector

@pytest.fixture
def document_organizer() -> DocumentOrganizer:
    """Configured document organizer."""
    return DocumentOrganizer(
        config=OrganizationConfig(
            output_dir="docs",
            group_by=["domain", "category"],
            index_template="index.html",
            assets_dir="assets"
        )
    )

@pytest.fixture
def crawler(
    # REMOVE backend_selector dependency
    mock_success_backend: MockSuccessBackend, # Inject mock directly
    content_processor: ContentProcessor,
    quality_checker: QualityChecker,
    document_organizer: DocumentOrganizer
) -> DocumentationCrawler:
    """Configured documentation crawler with a dedicated selector for the mock backend."""

    # Create and configure the selector *inside* this fixture
    selector_for_test = BackendSelector()
    selector_for_test.clear_backends() # Start clean
    selector_for_test.register_backend(
        mock_success_backend,
        BackendCriteria(
            priority=200, # High priority
            domains=["example.com"],
            url_patterns=["https://example.com/doc*"],
            content_types=["text/html"]
        )
    )
    logging.debug(f"Crawler fixture created selector id={id(selector_for_test)}, backends={list(selector_for_test.backends.keys())}")

    crawler_instance = DocumentationCrawler(
        config=CrawlerConfig(
            requests_per_second=1, # Set rate limit to 1 req/sec for testing delays
            max_retries=1, # Set max_retries to 1 for faster test failure
            request_timeout=10,
            concurrent_requests=5
        ),
        backend_selector=selector_for_test, # Use the locally created selector
        content_processor=content_processor,
        quality_checker=quality_checker,
        document_organizer=document_organizer
    )
    # The crawler's __init__ will still add the http_backend to this specific selector
    logging.debug(f"Crawler instance using selector id={id(crawler_instance.backend_selector)}, backends={list(crawler_instance.backend_selector.backends.keys())}")
    return crawler_instance

# @pytest.fixture # Comment out custom event loop - let pytest-asyncio handle it
# def event_loop():
#     """Create an instance of the default event loop for each test case."""
#     loop = asyncio.new_event_loop()
#     yield loop
#     loop.close()

# Fixture specifically for Crawl4AIBackend tests
@pytest_asyncio.fixture
async def crawl4ai_backend(monkeypatch):
    """Provides a Crawl4AIBackend instance for testing."""
    from src.backends.crawl4ai import Crawl4AIBackend, Crawl4AIConfig # Import locally
    config = Crawl4AIConfig(
        max_retries=2,
        timeout=10.0,
        headers={"User-Agent": "Test/1.0"},
        rate_limit=0.1,  # Fast rate limit for testing
        max_depth=3,
        concurrent_requests=2
    )
    backend = Crawl4AIBackend(config=config)

    # Use the mock_session fixture passed as an argument
    # This part seems incomplete or potentially problematic if mock_session isn't defined
    # async def mock_create_session():
    #     # This now returns the fixture-provided mock_session
    #     # which has predefined responses for /page1, /page2 etc.
    #     return mock_session # mock_session needs to be defined or injected

    # Re-enable monkeypatch to use the mock_session via mock_create_session
    # monkeypatch.setattr(backend, "_create_session", mock_create_session) # Allow real session for retry test patch

    yield backend # Provide the backend to the test

    # Cleanup
    await backend.close()

# Fixture for a mock aiohttp session (example)
@pytest_asyncio.fixture
async def mock_session():
    session = AsyncMock(spec=aiohttp.ClientSession)
    # Configure mock responses as needed for tests using crawl4ai_backend
    # Example:
    # async def mock_get(*args, **kwargs):
    #     url = args[0]
    #     response = AsyncMock(spec=aiohttp.ClientResponse)
    #     if "page1" in url:
    #         response.status = 200
    #         response.text = AsyncMock(return_value="<html>Page 1</html>")
    #     else:
    #         response.status = 404
    #     return response
    # session.get = mock_get
    yield session
    # No explicit close needed for mock usually
