import platform
from collections.abc import AsyncGenerator  # Added AsyncGenerator
from typing import Optional
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

if platform.system() != "Windows":
    pass

from bs4 import BeautifulSoup

from src.backends.base import CrawlerBackend, CrawlResult

# Added import for ProjectIdentity and ProjectType
from src.backends.scrapy_backend import (
    ScrapyBackend,
    ScrapyConfig,
)
from src.backends.selector import BackendCriteria, BackendSelector
from src.crawler.crawler import Crawler as DocumentationCrawler
from src.crawler.models import CrawlConfig as CrawlerConfig
from src.models.project import (
    ProjectIdentity,
    ProjectType,
)
from src.organizers.doc_organizer import DocumentOrganizer, OrganizationConfig
from src.processors.content_processor import (
    ContentProcessor,
    ProcessedContent,
    ProcessorConfig,
)
from src.processors.quality_checker import (
    IssueLevel,
    IssueType,
    QualityChecker,
    QualityConfig,
    QualityIssue,
)
from src.utils.url import URLInfo

# Added import for ScrapyConfig and ScrapyBackend
# Import fixtures from fixtures directory


class MockSuccessBackend(CrawlerBackend):
    """Mock backend that always returns success with HTML content including links."""

    def __init__(self):
        super().__init__(name="mock_success_backend")

    async def crawl(
        self,
        url_info: URLInfo,
        config: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> CrawlResult:
        """Return a successful crawl result with HTML content containing links."""
        url = url_info.normalized_url

        # Create different content based on URL for URL discovery tests
        if "discovery_start" in url:
            # First page with link to discover
            html_content = """
            <html>
                <head><title>Discovery Start Page</title></head>
                <body>
                    <h1>Discovery Start Page</h1>
                    <p>This is the starting page for URL discovery.</p>
                    <a href="/test">Discover This Link</a>
                </body>
            </html>
            """
            title = "Discovery Start Page"
            content_text = (
                "This is the starting page for URL discovery.\nDiscover This Link"
            )
            links = [{"text": "Discover This Link", "url": "/test"}]
        elif url.endswith("/test"):
            # Second page that gets discovered
            html_content = """
            <html>
                <head><title>Discovered Page</title></head>
                <body>
                    <h1>Discovered Page</h1>
                    <p>This page was discovered through URL discovery.</p>
                </body>
            </html>
            """
            title = "Discovered Page"
            content_text = "This page was discovered through URL discovery."
            links = []
        else:
            # Default content for other URLs
            html_content = """
            <html>
                <head><title>Sample Document</title></head>
                <body>
                    <h1>Sample Document</h1>
                    <p>Processed content</p>
                    <code class="language-python">def test():
pass</code>
                    <a href="/test">Test Link</a>
                    <img src="/test.jpg" alt="Test Image">
                </body>
            </html>
            """
            title = "Sample Document"
            content_text = (
                "Sample Document\nProcessed content\ndef test():\n    pass\nTest Link"
            )
            links = [{"text": "Test Link", "url": "/test"}]

        # Return backend CrawlResult (from src/backends/base.py)
        # This will be processed by the crawler to create the main CrawlResult
        result = CrawlResult(
            url=url,
            status=200,
            content={
                "html": html_content,
                "text": content_text,
            },
            content_type="text/html",
            metadata={
                "title": title,
                "headers": {"content-type": "text/html"},
            },
            documents=[
                {
                    "url": url,
                    "title": title,
                    "content": {
                        "formatted_content": content_text,
                        "headings": [{"level": 1, "text": title}],
                        "code_blocks": [
                            {"language": "python", "content": "def test():\n    pass"}
                        ]
                        if "Sample Document" in title
                        else [],
                        "links": links,
                    },
                    "metadata": {"title": title},
                    "assets": {
                        "images": ["/test.jpg"] if "Sample Document" in title else [],
                        "stylesheets": [],
                        "scripts": [],
                        "media": [],
                    },
                }
            ],
        )

        return result

    async def validate(self, content: CrawlResult) -> bool:
        """Always validate as successful."""
        return True

    async def process(self, content: CrawlResult) -> dict:
        """Return processed content."""
        return {
            "title": "Sample Document",
            "content": "Processed content",
            "url": content.url,
        }


class MockFailureBackend(CrawlerBackend):
    """Mock backend that always fails."""

    def __init__(self):
        super().__init__(name="mock_failure_backend")
        self.crawl_called = False
        self.validate_called = False
        self.process_called = False

    async def crawl(
        self, url_info: URLInfo, config: Optional[CrawlerConfig] = None
    ) -> CrawlResult:  # Corrected Optional syntax
        self.crawl_called = True
        normalized_url = url_info.normalized_url
        return CrawlResult(
            url=normalized_url,
            content={},
            metadata={"error": "Simulated failure"},
            status=500,
            error="Simulated failure",
            content_type=None,
            documents=[],
        )

    async def validate(self, content: CrawlResult) -> bool:
        self.validate_called = True
        return False

    async def process(self, content: CrawlResult) -> dict:
        self.process_called = True
        return {"error": "Processing failed"}


@pytest.fixture
def sample_html_factory():
    """Factory function to generate sample HTML content with custom parameters."""

    def _factory(
        title="Test Document",
        heading="Test Heading",
        paragraph="This is a test paragraph.",
        link="/test",
    ):
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
    return BeautifulSoup(sample_html_factory(), "html.parser")


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
        extract_code_blocks=True,
    )


@pytest.fixture
def content_processor(processor_config: ProcessorConfig) -> ContentProcessor:
    """Content processor instance for testing."""
    processor = AsyncMock(spec=ContentProcessor)
    processor.config = processor_config

    # Create a dynamic mock that returns different content based on the input
    async def mock_process(content, base_url=None, content_type=None):
        # Extract URL from the base_url to determine what content to return
        url = base_url or "default"

        if "discovery_start" in url:
            # Return content that matches the MockSuccessBackend's HTML for discovery_start
            return ProcessedContent(
                content={
                    "formatted_content": "This is the starting page for URL discovery.\nDiscover This Link",
                    "headings": [{"level": 1, "text": "Discovery Start Page"}],
                    "code_blocks": [],
                    "links": [{"text": "Discover This Link", "url": "/test"}],
                },
                metadata={"title": "Discovery Start Page"},
                assets={"images": [], "stylesheets": [], "scripts": [], "media": []},
                headings=[{"level": 1, "text": "Discovery Start Page"}],
                structure=[
                    {"type": "section", "title": "Discovery Start Page"},
                    {"type": "link", "text": "Discover This Link", "url": "/test"},
                ],
            )
        elif url.endswith("/test"):
            # Return content for the discovered page
            return ProcessedContent(
                content={
                    "formatted_content": "This page was discovered through URL discovery.",
                    "headings": [{"level": 1, "text": "Discovered Page"}],
                    "code_blocks": [],
                    "links": [],
                },
                metadata={"title": "Discovered Page"},
                assets={"images": [], "stylesheets": [], "scripts": [], "media": []},
                headings=[{"level": 1, "text": "Discovered Page"}],
                structure=[
                    {"type": "section", "title": "Discovered Page"},
                ],
            )
        else:
            # Default content for other tests
            return ProcessedContent(
                content={
                    "formatted_content": "Processed content",
                    "headings": [{"level": 1, "text": "Sample Document"}],
                    "code_blocks": [
                        {"language": "python", "content": "def test():\\n    pass"}
                    ],
                    "links": [{"text": "Test Link", "url": "/test"}],
                },
                metadata={"title": "Sample Document"},
                assets={
                    "images": ["/test.jpg"],
                    "stylesheets": [],
                    "scripts": [],
                    "media": [],
                },
                headings=[{"level": 1, "text": "Sample Document"}],
                structure=[
                    {"type": "section", "title": "Sample Document"},
                    {"type": "link", "text": "Test Link", "url": "/test"},
                ],
            )

    processor.process.side_effect = mock_process
    return processor


@pytest.fixture
def quality_config() -> QualityConfig:
    """Default quality checker configuration for testing."""
    return QualityConfig(
        min_content_length=50,
        max_broken_links_ratio=0.1,
        required_elements=["title", "h1"],
    )


@pytest.fixture
def quality_checker(quality_config: QualityConfig) -> QualityChecker:
    """Quality checker instance for testing."""
    checker = AsyncMock(spec=QualityChecker)

    # Create a more flexible mock that can return appropriate issues based on content
    async def mock_check_quality(content):
        issues = []

        # Check if content has 'formatted_content' key (test_quality_checker_content_length)
        if (
            content.content.get("formatted_content", "")
            and len(content.content.get("formatted_content", "")) < 50
        ):
            issues.append(
                QualityIssue(
                    type=IssueType.CONTENT_LENGTH,
                    level=IssueLevel.WARNING,
                    message="Content too short",
                )
            )

        # Content length check for text key
        elif (
            content.content.get("text", "")
            and len(content.content.get("text", "")) < 50
        ):
            issues.append(
                QualityIssue(
                    type=IssueType.CONTENT_LENGTH,
                    level=IssueLevel.WARNING,
                    message="Content too short",
                )
            )

        # Headings check
        if (
            content.content.get("headings") is not None
            and len(content.content.get("headings", [])) == 0
        ):
            issues.append(
                QualityIssue(
                    type=IssueType.HEADING_STRUCTURE,
                    level=IssueLevel.WARNING,
                    message="No headings found",
                )
            )

        # Links check
        if (
            content.content.get("links") is not None
            and len(content.content.get("links", [])) < 2
        ):
            issues.append(
                QualityIssue(
                    type=IssueType.LINK_COUNT,
                    level=IssueLevel.INFO,
                    message="Few links found",
                )
            )

        # Code blocks check
        if content.content.get("code_blocks") is not None:
            for code_block in content.content.get("code_blocks", []):
                if code_block.get("code", "") and len(code_block.get("code", "")) < 10:
                    issues.append(
                        QualityIssue(
                            type=IssueType.CODE_BLOCK_LENGTH,
                            level=IssueLevel.INFO,
                            message="Short code block",
                        )
                    )

        # Metadata check
        if not content.metadata.get("title"):
            issues.append(
                QualityIssue(
                    type=IssueType.METADATA,
                    level=IssueLevel.WARNING,
                    message="Missing title",
                )
            )

        metrics = {
            "score": 0.9,
            "content_score": 0.85,
            "structure_score": 0.9,
            "metadata_score": 0.95,
            "content_length": 100,
            "heading_count": 1,
            "link_count": 2,
            "code_block_count": 1,
        }
        return issues, metrics

    checker.check_quality = mock_check_quality
    checker.config = quality_config
    return checker


@pytest.fixture
def organization_config() -> OrganizationConfig:
    """Default document organizer configuration for testing."""
    return OrganizationConfig(max_depth=5, group_by_sections=True)


@pytest.fixture
def document_organizer(organization_config: OrganizationConfig) -> DocumentOrganizer:
    """Document organizer instance for testing."""
    organizer = MagicMock(spec=DocumentOrganizer)
    # Return a document with the expected structure field
    organizer.add_document = MagicMock(return_value="mock_doc_id_1")

    # Mock organize to properly set the structure field that will be accessed by CrawlResult
    async def mock_organize(*args, **kwargs):
        # This mocks setting the structure field on any documents passed to organize
        # The crawler will read this structure field and assign it to CrawlResult.structure
        # Return a list of dictionaries as expected by the CrawlResult model
        return {
            "structure": [{"type": "section", "title": "organized"}],
            "summary": "summary",
        }

    organizer.organize = AsyncMock(side_effect=mock_organize)
    organizer.config = organization_config
    return organizer


@pytest_asyncio.fixture
async def backend_selector_with_mock_backends(
    mock_success_backend_instance: MockSuccessBackend,
    mock_failure_backend_instance: MockFailureBackend,
) -> AsyncGenerator[BackendSelector, None]:
    selector = BackendSelector()

    # Mock for successful responses from example.com
    selector.register_backend(
        name=mock_success_backend_instance.name,
        backend=mock_success_backend_instance,
        criteria=BackendCriteria(
            priority=50,
            schemes=["http", "https"],
            domains=["example.com"],
            url_patterns=["*"],  # Use * wildcard for fnmatch instead of regex .*
            content_types=["text/html"],
        ),
    )

    # Mock for failure responses from example.com URLs containing "failure"
    selector.register_backend(
        name=mock_failure_backend_instance.name,
        backend=mock_failure_backend_instance,
        criteria=BackendCriteria(
            priority=100,
            schemes=["http", "https"],
            domains=["example.com"],
            url_patterns=["*failure*"],  # Use shell-style wildcards for fnmatch
            content_types=["text/html"],
        ),
    )

    yield selector
    await selector.close_all_backends()


@pytest.fixture
def crawler_config() -> CrawlerConfig:
    """Default crawler configuration for testing."""
    return CrawlerConfig(
        rate_limit=1.0,  # This gives requests_per_second=1
        max_concurrent_requests=5,
        max_retries=1,
        timeout=10,
        use_duckduckgo=False,  # Disable DuckDuckGo for tests
        project_identity=ProjectIdentity(name="TestProject", type=ProjectType.LIBRARY),
    )


@pytest_asyncio.fixture
async def crawler(
    crawler_config: CrawlerConfig,
    backend_selector_with_mock_backends: BackendSelector,
    content_processor: ContentProcessor,
    quality_checker: QualityChecker,
    document_organizer: DocumentOrganizer,
) -> DocumentationCrawler:
    """DocumentationCrawler instance for testing."""
    import asyncio

    crawler_instance = DocumentationCrawler(
        config=crawler_config,
        backend_selector=backend_selector_with_mock_backends,
        content_processor=content_processor,
        quality_checker=quality_checker,
        document_organizer=document_organizer,
        loop=asyncio.get_running_loop(),
    )
    return crawler_instance


@pytest_asyncio.fixture
async def fresh_backend_selector() -> (
    AsyncGenerator[BackendSelector, None]
):  # Corrected return type
    selector = BackendSelector()
    yield selector
    await selector.close_all_backends()


@pytest.fixture
def mock_success_backend_instance() -> MockSuccessBackend:
    return MockSuccessBackend()


@pytest.fixture
def mock_failure_backend_instance() -> MockFailureBackend:
    return MockFailureBackend()


@pytest.fixture
def scrapy_config_fixture() -> ScrapyConfig:
    return ScrapyConfig(
        allowed_domains=["example.com"],
        start_urls=["https://example.com"],
        custom_settings={},
    )


@pytest.fixture
def scrapy_backend_fixture(scrapy_config_fixture: ScrapyConfig) -> ScrapyBackend:
    return ScrapyBackend(config=scrapy_config_fixture)


# Pytest marker registration (if needed, typically in pytest.ini or here)
# Example:
# def pytest_configure(config):
#     config.addinivalue_line(
#         "markers", "integration: mark test as integration to run only on demand"
#     )
#     # Other existing marker registrations can remain...
