"""Tests for the crawler orchestrator component."""

import asyncio
from typing import Dict, List, Set

import pytest

from src.backends.base import CrawlerBackend, CrawlResult
from src.backends.selector import BackendCriteria, BackendSelector
from src.crawler import (CrawlerConfig, CrawlResult as OrchestratorResult,
                      CrawlStats, CrawlTarget, DocumentationCrawler)
from src.processors.content_processor import ProcessedContent
from src.models.project import ProjectType, ProjectIdentity, ProjectIdentifier
from src.utils.search import DuckDuckGoSearch, DUCKDUCKGO_AVAILABLE


class MockCrawlerBackend(CrawlerBackend):
    """Mock crawler backend for testing the orchestrator."""
    
    def __init__(self, urls: Set[str], delay: float = 0.1):
        super().__init__(name="mock_crawler")
        self.urls = urls
        self.delay = delay
        self.crawled_urls: Set[str] = set()

    async def crawl(self, url: str, params: Dict = None) -> CrawlResult:
        """Simulate crawling with configurable delay."""
        self.crawled_urls.add(url)
        await asyncio.sleep(self.delay)
        
        if url in self.urls:
            return CrawlResult(
                url=url,
                content={
                    "html": f"""
                    <html>
                        <head><title>Test {url}</title></head>
                        <body>
                            <h1>Test {url}</h1>
                            <p>Content for {url}</p>
                            <a href="{url}/subpage">Link</a>
                        </body>
                    </html>
                    """
                },
                metadata={"status_code": 200},
                status=200
            )
        else:
            return CrawlResult(
                url=url,
                content={},
                metadata={"error": "Not found"},
                status=404,
                error="Not found"
            )

    async def validate(self, content: CrawlResult) -> bool:
        """Validate crawled content."""
        return content.status == 200

    async def process(self, content: CrawlResult) -> Dict:
        """Process crawled content."""
        if content.status != 200:
            return {"error": "Processing failed"}
            
        return {
            "title": f"Test {content.url}",
            "content": {
                "text": f"Content for {content.url}",
                "links": [{"url": f"{content.url}/subpage", "text": "Link"}]
            },
            "metadata": content.metadata
        }


@pytest.fixture
def test_urls() -> Set[str]:
    """Fixture providing test URLs."""
    return {
        "https://example.com/doc1",
        "https://example.com/doc2",
        "https://example.com/doc3"
    }


@pytest.fixture
def mock_backend(test_urls: Set[str]) -> MockCrawlerBackend:
    """Fixture providing configured mock backend."""
    return MockCrawlerBackend(test_urls)


@pytest.fixture
def backend_selector(mock_backend: MockCrawlerBackend) -> BackendSelector:
    """Fixture providing configured backend selector."""
    selector = BackendSelector()
    selector.register_backend(
        mock_backend,
        BackendCriteria(
            priority=100,
            content_types=["text/html"],
            url_patterns=["*"],
            max_load=0.8,
            min_success_rate=0.7
        )
    )
    return selector


@pytest.mark.asyncio
async def test_crawler_initialization(crawler: DocumentationCrawler):
    """Test crawler initialization and configuration."""
    assert crawler.config is not None
    assert crawler.backend_selector is not None
    assert crawler.content_processor is not None
    assert crawler.quality_checker is not None
    assert crawler.document_organizer is not None
    assert crawler._crawled_urls == set()
    assert crawler._processing_semaphore is not None


@pytest.mark.asyncio
async def test_url_filtering(
    crawler: DocumentationCrawler,
    test_urls: Set[str]
):
    """Test URL filtering logic."""
    target = CrawlTarget(
        url="https://example.com/doc1",
        depth=2,
        follow_external=False,
        exclude_patterns=["/excluded/"],
        required_patterns=["/doc"],
        max_pages=10
    )
    
    # Test valid URL
    assert crawler._should_crawl_url("https://example.com/doc1", target)
    
    # Test excluded pattern
    assert not crawler._should_crawl_url(
        "https://example.com/excluded/page",
        target
    )
    
    # Test external URL
    assert not crawler._should_crawl_url(
        "https://other-domain.com/doc1",
        target
    )
    
    # Test already crawled URL
    crawler._crawled_urls.add("https://example.com/doc1")
    assert not crawler._should_crawl_url("https://example.com/doc1", target)


@pytest.mark.asyncio
async def test_single_url_processing(
    crawler: DocumentationCrawler,
    test_urls: Set[str]
):
    """Test processing of a single URL."""
    target = CrawlTarget(
        url=next(iter(test_urls)),
        depth=1,
        follow_external=False,
        content_types=["text/html"],
        max_pages=1
    )
    
    stats = CrawlStats()
    doc_id, discovered_urls = await crawler._process_url(
        target.url,
        0,
        target,
        stats
    )
    
    assert doc_id is not None
    assert len(discovered_urls) > 0
    assert stats.pages_crawled == 1
    assert stats.successful_crawls == 1


@pytest.mark.asyncio
async def test_depth_limited_crawling(
    crawler: DocumentationCrawler,
    test_urls: Set[str]
):
    """Test crawling with depth limitation."""
    target = CrawlTarget(
        url=next(iter(test_urls)),
        depth=2,
        follow_external=False,
        content_types=["text/html"],
        max_pages=10
    )
    
    result = await crawler.crawl(target)
    
    assert result.stats.pages_crawled > 0
    assert result.stats.pages_crawled <= target.max_pages
    assert len(crawler._crawled_urls) <= target.max_pages


@pytest.mark.asyncio
async def test_concurrent_processing(
    crawler: DocumentationCrawler,
    test_urls: Set[str]
):
    """Test concurrent URL processing."""
    target = CrawlTarget(
        url=next(iter(test_urls)),
        depth=1,
        follow_external=False,
        content_types=["text/html"],
        max_pages=len(test_urls)
    )
    
    # Process multiple URLs concurrently
    tasks = []
    stats = CrawlStats()
    for url in test_urls:
        task = crawler._process_url(url, 0, target, stats)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    
    assert len(results) == len(test_urls)
    assert stats.pages_crawled == len(test_urls)
    assert all(doc_id is not None for doc_id, _ in results)


@pytest.mark.asyncio
async def test_rate_limiting(
    crawler: DocumentationCrawler,
    test_urls: Set[str]
):
    """Test crawler rate limiting."""
    target = CrawlTarget(
        url=next(iter(test_urls)),
        depth=1,
        max_pages=len(test_urls)
    )
    
    start_time = asyncio.get_event_loop().time()
    result = await crawler.crawl(target)
    end_time = asyncio.get_event_loop().time()
    
    # Check if rate limiting was applied
    expected_min_time = (
        result.stats.pages_crawled / crawler.config.requests_per_second
    )
    assert end_time - start_time >= expected_min_time


@pytest.mark.asyncio
async def test_error_handling(crawler: DocumentationCrawler):
    """Test crawler error handling."""
    # Test with invalid URL
    target = CrawlTarget(
        url="https://invalid.example.com",
        depth=1,
        max_pages=1
    )
    
    result = await crawler.crawl(target)
    
    assert result.stats.failed_crawls > 0
    assert result.stats.successful_crawls == 0


@pytest.mark.asyncio
async def test_content_processing_pipeline(
    crawler: DocumentationCrawler,
    test_urls: Set[str]
):
    """Test complete content processing pipeline."""
    target = CrawlTarget(
        url=next(iter(test_urls)),
        depth=1,
        max_pages=1
    )
    
    result = await crawler.crawl(target)
    
    assert result.stats.successful_crawls == 1
    assert len(result.documents) == 1
    assert len(result.issues) >= 0  # May have quality issues
    assert result.metrics  # Should have quality metrics


@pytest.mark.asyncio
async def test_cleanup(crawler: DocumentationCrawler):
    """Test crawler cleanup."""
    # Run a crawl
    target = CrawlTarget(
        url="https://example.com/test",
        depth=1,
        max_pages=1
    )
    
    await crawler.crawl(target)
    
    # Verify cleanup
    assert crawler.client_session is not None
    await crawler.cleanup()
    assert crawler.client_session is None


@pytest.mark.asyncio
async def test_max_pages_limit(
    crawler: DocumentationCrawler,
    test_urls: Set[str]
):
    """Test maximum pages limit."""
    max_pages = 2
    target = CrawlTarget(
        url=next(iter(test_urls)),
        depth=3,  # Deep enough to find more pages
        max_pages=max_pages
    )
    
    result = await crawler.crawl(target)
    
    assert result.stats.pages_crawled <= max_pages
    assert len(crawler._crawled_urls) <= max_pages


@pytest.mark.asyncio
async def test_statistics_tracking(
    crawler: DocumentationCrawler,
    test_urls: Set[str]
):
    """Test crawl statistics tracking."""
    target = CrawlTarget(
        url=next(iter(test_urls)),
        depth=1,
        max_pages=len(test_urls)
    )
    
    result = await crawler.crawl(target)
    
    assert result.stats.start_time is not None
    assert result.stats.end_time is not None
    assert result.stats.total_time > 0
    assert result.stats.average_time_per_page > 0
    assert result.stats.pages_crawled == result.stats.successful_crawls + result.stats.failed_crawls


def test_project_type_enum():
    """Test ProjectType enum."""
    # Test all enum values
    assert ProjectType.PACKAGE.value == "package"
    assert ProjectType.FRAMEWORK.value == "framework"
    assert ProjectType.PROGRAM.value == "program"
    assert ProjectType.LIBRARY.value == "library"
    assert ProjectType.CLI_TOOL.value == "cli_tool"
    assert ProjectType.WEB_APP.value == "web_app"
    assert ProjectType.API.value == "api"
    assert ProjectType.UNKNOWN.value == "unknown"


def test_project_identity():
    """Test ProjectIdentity class."""
    # Test basic initialization
    identity = ProjectIdentity(
        name="test-project",
        type=ProjectType.LIBRARY,
        language="python",
        framework="flask",
        repository="https://github.com/test/test-project",
        package_manager="pip",
        main_doc_url="https://test-project.readthedocs.io",
        related_keywords=["web", "api"],
        confidence=0.85
    )
    
    assert identity.name == "test-project"
    assert identity.type == ProjectType.LIBRARY
    assert identity.language == "python"
    assert identity.framework == "flask"
    assert identity.repository == "https://github.com/test/test-project"
    assert identity.package_manager == "pip"
    assert identity.main_doc_url == "https://test-project.readthedocs.io"
    assert identity.related_keywords == ["web", "api"]
    assert identity.confidence == 0.85
    
    # Test default values
    basic_identity = ProjectIdentity(
        name="basic-project",
        type=ProjectType.UNKNOWN
    )
    assert basic_identity.language is None
    assert basic_identity.framework is None
    assert basic_identity.repository is None
    assert basic_identity.package_manager is None
    assert basic_identity.main_doc_url is None
    assert basic_identity.related_keywords == []
    assert basic_identity.confidence == 0.0


def test_project_identifier():
    """Test ProjectIdentifier class."""
    identifier = ProjectIdentifier()
    
    # Test language detection
    files = [
        "setup.py",
        "requirements.txt",
        "src/main.py",
        "tests/test_main.py"
    ]
    
    detected = identifier._detect_language(files)
    assert detected == "python"
    
    # Test framework detection
    python_files = [
        "manage.py",
        "wsgi.py",
        "urls.py",
        "settings.py"
    ]
    
    detected = identifier._detect_framework(python_files, "python")
    assert detected == "django"
    
    # Test doc URL generation
    identity = ProjectIdentity(
        name="test-project",
        type=ProjectType.LIBRARY,
        language="python"
    )
    
    urls = identifier._generate_doc_urls(identity)
    assert "https://test-project.readthedocs.io/en/latest/" in urls
    assert "https://docs.test-project.org/" in urls


@pytest.mark.asyncio
async def test_duckduckgo_search():
    """Test DuckDuckGoSearch class."""
    if not DUCKDUCKGO_AVAILABLE:
        pytest.skip("DuckDuckGo search not available")
    
    search = DuckDuckGoSearch(max_results=5)
    
    # Test basic search
    results = await search.search("python documentation")
    assert len(results) <= 5
    assert all(isinstance(r, str) for r in results)
    assert all("http" in r for r in results)
    
    # Test empty search
    results = await search.search("")
    assert len(results) == 0
    
    # Test cleanup
    await search.close()
    assert search._ddgs is None


@pytest.mark.asyncio
async def test_url_discovery():
    """Test URL discovery mechanisms."""
    crawler = DocumentationCrawler()
    
    # Test basic URL discovery
    target = CrawlTarget(
        url="https://example.com",
        depth=2,
        follow_external=False
    )
    
    discovered = await crawler._discover_urls(target)
    assert isinstance(discovered, set)
    assert all(isinstance(url, str) for url in discovered)
    
    # Test with DuckDuckGo integration
    if DUCKDUCKGO_AVAILABLE:
        target.url = "https://requests.readthedocs.io"
        discovered = await crawler._discover_urls(target)
        assert len(discovered) > 0
        assert any("readthedocs.io" in url for url in discovered)


@pytest.mark.asyncio
async def test_project_type_detection():
    """Test project type detection."""
    crawler = DocumentationCrawler()
    
    # Test Python package detection
    identity = await crawler.project_identifier._identify_project_type(
        "https://requests.readthedocs.io",
        ["setup.py", "requirements.txt"]
    )
    assert identity.type == ProjectType.PACKAGE
    assert identity.language == "python"
    
    # Test web framework detection
    identity = await crawler.project_identifier._identify_project_type(
        "https://flask.palletsprojects.com",
        ["setup.py", "flask/__init__.py"]
    )
    assert identity.type == ProjectType.FRAMEWORK
    assert identity.language == "python"
    
    # Test unknown project
    identity = await crawler.project_identifier._identify_project_type(
        "https://example.com",
        []
    )
    assert identity.type == ProjectType.UNKNOWN