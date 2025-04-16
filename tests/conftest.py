from typing import Dict, Any, List, Optional, Union
import aiohttp
import os
import sys
import platform
import asyncio
import logging
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock

if platform.system() != 'Windows':
    pass  # Removed uvloop.install() to avoid ImportError
    # import uvloop  # Comment out uvloop import for troubleshooting
    # uvloop.install()

from bs4 import BeautifulSoup

# Remove manual sys.path manipulation.
# Instead, ensure your test runner (e.g., pytest) is configured with the correct PYTHONPATH,
# or use organization-approved import hooks or test utilities.
#
# For example, in pytest.ini or pyproject.toml:
# [pytest]
# pythonpath = src
#
# Or use organization-specific test bootstrap utilities if available.

from src.backends.base import CrawlerBackend, CrawlResult
from src.backends.selector import BackendCriteria, BackendSelector
from src.crawler import CrawlerConfig, DocumentationCrawler, CrawlTarget
from src.organizers.doc_organizer import DocumentOrganizer, OrganizationConfig
from src.processors.content_processor import ContentProcessor, ProcessorConfig, ProcessedContent
from src.processors.quality_checker import QualityChecker, QualityConfig
from src.utils.url import URLInfo

class MockSuccessBackend(CrawlerBackend):
    """Mock backend that always succeeds."""

    def __init__(self, delay: float = 0.0):
        super().__init__(name="mock_success_backend")
        self.crawl_called = False
        self.validate_called = False
        self.process_called = False
        self.delay = delay  # Make delay configurable

    async def crawl(self, url: Union[str, URLInfo], config: Optional[CrawlerConfig] = None) -> CrawlResult:
        """Simulate a successful crawl with a configurable delay."""
        self.crawl_called = True
        if self.delay > 0:
            await asyncio.sleep(self.delay)  # Use configurable delay

        normalized_url = url.normalized_url if isinstance(url, URLInfo) else url

        return CrawlResult(
            url=normalized_url,
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

    async def crawl(self, url: Union[str, URLInfo], config: Optional[CrawlerConfig] = None) -> CrawlResult:
        self.crawl_called = True
        normalized_url = url.normalized_url if isinstance(url, URLInfo) else url
        return CrawlResult(
            url=normalized_url,
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
def sample_html_factory():
    """Factory function to generate sample HTML content with custom parameters."""
    def _factory(title="Test Document", heading="Test Heading", paragraph="This is a test paragraph.", link="/test"):
        return f"""
        <html>
            <head>
                <title>{title}</title>
                <meta name="description" content="Test description" />
            </head>
            <body>
                <h1>{heading}</h1>
                <p>{paragraph}</p>
                <pre><code>def test():
    pass</code></pre>
                <a href="{link}">Test Link</a>
            </body>
        </html>
        """
    return _factory

@pytest.fixture
def soup(sample_html_factory) -> BeautifulSoup:
    """BeautifulSoup object for testing."""
    return BeautifulSoup(sample_html_factory(), 'html.parser')

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
        content={
            'formatted_content': 'Processed content',
            'headings': [{'level': 1, 'text': 'Sample Document'}],
            'code_blocks': [{'language': 'python', 'content': 'def test():\n    pass'}],
            'links': [{'text': 'Test Link', 'url': '/test'}]
        },
        metadata={'title': 'Sample Document'},
        assets={'images': ['/test.jpg'], 'stylesheets': [], 'scripts': [], 'media': []},
        headings=[{'level': 1, 'text': 'Sample Document'}],
        # Add a sample link structure matching StructureHandler output
        structure=[{'type': 'text', 'content': [{'type': 'link_inline', 'text': 'Test Link', 'href': '/test'}]}], # Simulate link within a paragraph
        title='Sample Document'
    )
    processor = AsyncMock(spec=ContentProcessor) # Use AsyncMock
    processor.process = AsyncMock(return_value=mock_processed) # Mock the process method
    # Add config attribute to the mock to fix test_content_size_limits
    processor.config = processor_config
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

@pytest_asyncio.fixture
async def mock_success_backend() -> MockSuccessBackend:
    """Mock backend that succeeds."""
    # No async setup needed for this simple mock, just return
    return MockSuccessBackend()

@pytest_asyncio.fixture
async def mock_failure_backend() -> MockFailureBackend:
    """Mock backend that fails."""
    # No async setup needed for this simple mock, just return
    return MockFailureBackend()

@pytest.fixture(scope="function")
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
    mock_success_backend: MockSuccessBackend,
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

@pytest_asyncio.fixture
async def crawl4ai_backend(mock_session):
    """Provides a Crawl4AIBackend instance for testing with injected mock session."""
    from src.backends.crawl4ai import Crawl4AIBackend, Crawl4AIConfig
    config = Crawl4AIConfig(
        max_retries=2,
        timeout=10.0,
        headers={"User-Agent": "Test/1.0"},
        rate_limit=0.1,
        max_depth=3,
        concurrent_requests=2
    )
    backend = Crawl4AIBackend(config=config)
    # Patch the backend's _create_session method to return the mock_session
    async def mock_create_session():
        return mock_session
    backend._create_session = mock_create_session
    return backend

@pytest_asyncio.fixture
async def mock_session():
    session = AsyncMock(spec=aiohttp.ClientSession)
    return session