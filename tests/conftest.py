"""Test fixtures for the documentation crawler tests."""

import asyncio
import os
import sys
from typing import Dict, Any, List

import pytest
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
        super().__init__()
        self.crawl_called = False
        self.validate_called = False
        self.process_called = False
    
    async def crawl(self, url: str, params: Dict = None) -> CrawlResult:
        self.crawl_called = True
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
        super().__init__()
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


@pytest.fixture
def mock_success_backend() -> MockSuccessBackend:
    """Mock backend that succeeds."""
    return MockSuccessBackend()


@pytest.fixture
def mock_failure_backend() -> MockFailureBackend:
    """Mock backend that fails."""
    return MockFailureBackend()


@pytest.fixture
def backend_selector(mock_success_backend: MockSuccessBackend) -> BackendSelector:
    """Configured backend selector."""
    selector = BackendSelector()
    selector.register_backend(
        mock_success_backend,
        BackendCriteria(
            domains=["example.com"],
            paths=["/docs", "/api"],
            content_types=["text/html"]
        )
    )
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
    backend_selector: BackendSelector,
    content_processor: ContentProcessor,
    quality_checker: QualityChecker,
    document_organizer: DocumentOrganizer
) -> DocumentationCrawler:
    """Configured documentation crawler."""
    return DocumentationCrawler(
        config=CrawlerConfig(
            max_depth=3,
            max_pages=100,
            delay=0.1,
            timeout=30,
            concurrent_requests=5
        ),
        backend_selector=backend_selector,
        content_processor=content_processor,
        quality_checker=quality_checker,
        document_organizer=document_organizer
    )


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
