import pytest
import os
import sys
import asyncio
import pytest_asyncio # Import pytest_asyncio
from typing import Dict, Any, List
import logging # Added import
import platform

if platform.system() != 'Windows':
    import uvloop
    uvloop.install()

from bs4 import BeautifulSoup
# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.backends.base import CrawlerBackend, CrawlResult
from src.backends.selector import BackendCriteria, BackendSelector
from src.crawler import CrawlerConfig, DocumentationCrawler
from src.organizers.doc_organizer import DocumentOrganizer, OrganizationConfig
from src.processors.content_processor import ContentProcessor, ProcessorConfig
from src.processors.quality_checker import QualityChecker, QualityConfig

class MockSuccessBackend(CrawlerBackend):
    """Mock backend that always succeeds."""
    
    def __init__(self):
        super().__init__(name="mock_success_backend")
        self.crawl_called = False
        self.validate_called = False
        self.process_called = False
    
    async def crawl(self, url: str, params: Dict = None) -> CrawlResult:
        """Simulate a successful crawl with a delay."""
        self.crawl_called = True
        # Simulate network delay for rate limiting tests
        await asyncio.sleep(0.15) # Increased delay

        return CrawlResult(
            url=url,
            content={
                "html": """
                <html>
                    <head>
                        <title>Test Document</title>
                        <meta name="description" content="Test description">
                    </head>
                    <body>
                        <h1>Test Document</h1>
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
    
    async def crawl(self, url: str, params: Dict = None) -> CrawlResult:
        self.crawl_called = True
        return CrawlResult(
            url=url,
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
    return ContentProcessor(config=processor_config)

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
            max_retries=1,
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
    async def mock_create_session():
        # This now returns the fixture-provided mock_session
        # which has predefined responses for /page1, /page2 etc.
        return mock_session

    # Re-enable monkeypatch to use the mock_session via mock_create_session
    # monkeypatch.setattr(backend, "_create_session", mock_create_session) # Allow real session for retry test patch

    yield backend # Provide the backend to the test

    # Cleanup
    await backend.close()
