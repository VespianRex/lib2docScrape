"""Tests for base components of the documentation crawler."""

import asyncio
import time
from typing import Dict

import pytest
from bs4 import BeautifulSoup

from src.backends.base import CrawlerBackend, CrawlResult
from src.backends.selector import BackendCriteria, BackendSelector
from src.processors.content_processor import ProcessedContent
from src.utils.helpers import URLProcessor, URLInfo


class MockCrawlerBackend(CrawlerBackend):
    """Mock crawler backend for testing."""
    
    def __init__(self, success: bool = True):
        super().__init__()
        self.success = success
        self.crawl_called = False
        self.validate_called = False
        self.process_called = False

    async def crawl(self, url: str, params: Dict = None) -> CrawlResult:
        """Mock crawl implementation."""
        self.crawl_called = True
        start_time = time.time()
        
        try:
            if self.success:
                result = CrawlResult(
                    url=url,
                    content={"html": "<html><body><h1>Test</h1></body></html>"},
                    metadata={"status": 200},
                    status=200
                )
            else:
                result = CrawlResult(
                    url=url,
                    content={},
                    metadata={"error": "Mock error"},
                    status=500,
                    error="Mock error"
                )
            
            # Update metrics with crawl time and success status
            await self.update_metrics(
                time.time() - start_time, 
                result.status == 200
            )
            
            return result
        
        except Exception as e:
            await self.update_metrics(
                time.time() - start_time, 
                False
            )
            raise

    async def validate(self, content: CrawlResult) -> bool:
        """Mock validate implementation."""
        self.validate_called = True
        return self.success

    async def process(self, content: CrawlResult) -> Dict:
        """Mock process implementation."""
        self.process_called = True
        if self.success:
            return {
                "title": "Test Document",
                "content": {"text": "Test content"},
                "metadata": {"type": "test"}
            }
        return {"error": "Processing failed"}


@pytest.mark.asyncio
async def test_crawler_backend_lifecycle():
    """Test crawler backend lifecycle methods."""
    backend = MockCrawlerBackend()
    
    # Test crawl
    result = await backend.crawl("https://example.com")
    assert backend.crawl_called
    assert result.url == "https://example.com"
    assert result.status == 200
    assert "html" in result.content
    
    # Test validate
    valid = await backend.validate(result)
    assert backend.validate_called
    assert valid is True
    
    # Test process
    processed = await backend.process(result)
    assert backend.process_called
    assert processed["title"] == "Test Document"
    assert processed["content"]["text"] == "Test content"
    assert processed["metadata"]["type"] == "test"


@pytest.mark.asyncio
async def test_crawler_backend_error_handling():
    """Test crawler backend error handling."""
    backend = MockCrawlerBackend(success=False)
    
    # Test crawl failure
    result = await backend.crawl("https://example.com")
    assert result.status == 500
    assert result.error == "Mock error"
    
    # Test validate failure
    valid = await backend.validate(result)
    assert valid is False
    
    # Test process failure
    processed = await backend.process(result)
    assert "error" in processed


@pytest.mark.asyncio
async def test_backend_selector_registration():
    """Test backend selector registration and criteria."""
    selector = BackendSelector()
    backend = MockCrawlerBackend()
    
    # Register backend with criteria
    criteria = BackendCriteria(
        domains=["example.com"],
        paths=["/docs", "/api"],
        content_types=["text/html"]
    )
    selector.register_backend(backend, criteria)
    
    # Verify registration
    assert len(selector.backends) == 1
    assert selector.backends[0][0] == backend
    assert selector.backends[0][1] == criteria


@pytest.mark.asyncio
async def test_backend_selector_selection():
    """Test backend selection logic."""
    selector = BackendSelector()
    backend1 = MockCrawlerBackend()
    backend2 = MockCrawlerBackend()
    
    # Register backends with different criteria
    selector.register_backend(
        backend1,
        BackendCriteria(
            domains=["example.com"],
            paths=["/docs"],
            content_types=["text/html"]
        )
    )
    selector.register_backend(
        backend2,
        BackendCriteria(
            domains=["api.example.com"],
            paths=["/v1"],
            content_types=["application/json"]
        )
    )
    
    # Test selection
    selected1 = await selector.select_backend("https://example.com/docs")
    assert selected1 == backend1
    
    selected2 = await selector.select_backend("https://api.example.com/v1")
    assert selected2 == backend2
    
    selected3 = await selector.select_backend("https://other.com")
    assert selected3 is None


@pytest.mark.asyncio
async def test_url_normalization():
    """Test URL normalization."""
    test_cases = [
        ("http://example.com", "http://example.com/"),
        ("http://example.com/path", "http://example.com/path"),
        ("http://example.com/path/", "http://example.com/path/"),
        ("http://example.com/path?q=1", "http://example.com/path?q=1"),
        ("http://example.com/path/?q=1", "http://example.com/path/?q=1"),
        ("http://example.com/path/#fragment", "http://example.com/path/"),
        ("http://example.com/path?q=1#fragment", "http://example.com/path?q=1")
    ]
    
    for input_url, expected_url in test_cases:
        assert URLProcessor(input_url).url == expected_url


@pytest.mark.asyncio
async def test_processed_content_validation():
    """Test processed content validation."""
    # Valid content
    valid_content = ProcessedContent(
        title="Test Document",
        content={
            "text": "Test content",
            "headings": [{"level": 1, "text": "Test"}],
            "links": [{"url": "https://example.com", "text": "Link"}]
        },
        metadata={
            "type": "test",
            "language": "en"
        }
    )
    assert valid_content.is_valid()
    
    # Invalid content (missing required fields)
    invalid_content = ProcessedContent(
        title="",
        content={},
        metadata={}
    )
    assert not invalid_content.is_valid()


@pytest.mark.asyncio
async def test_concurrent_backend_operations():
    """Test concurrent backend operations."""
    backend = MockCrawlerBackend()
    urls = [
        "https://example.com/1",
        "https://example.com/2",
        "https://example.com/3"
    ]
    
    # Test concurrent crawls
    tasks = [backend.crawl(url) for url in urls]
    results = await asyncio.gather(*tasks)
    
    assert len(results) == 3
    assert all(result.status == 200 for result in results)
    
    # Test concurrent processing
    tasks = [backend.process(result) for result in results]
    processed = await asyncio.gather(*tasks)
    
    assert len(processed) == 3
    assert all("title" in result for result in processed)


@pytest.mark.asyncio
async def test_backend_metrics_update():
    """Test backend metrics updating."""
    backend = MockCrawlerBackend()
    
    # Successful request
    await backend.crawl("https://example.com/success")
    assert backend.metrics.total_requests == 1
    assert backend.metrics.successful_requests == 1
    assert backend.metrics.failed_requests == 0
    assert backend.metrics.average_response_time > 0
    
    # Failed request
    backend.success = False
    await backend.crawl("https://example.com/failure")
    assert backend.metrics.total_requests == 2
    assert backend.metrics.successful_requests == 1
    assert backend.metrics.failed_requests == 1


@pytest.mark.asyncio
async def test_backend_selector_error_handling():
    """Test backend selector error handling."""
    selector = BackendSelector()
    backend = MockCrawlerBackend(success=False)
    
    # Register backend
    selector.register_backend(
        backend,
        BackendCriteria(
            domains=["example.com"],
            paths=["/docs"],
            content_types=["text/html"]
        )
    )
    
    # Test invalid URL
    with pytest.raises(ValueError):
        await selector.select_backend("not_a_url")
    
    # Test URL with no matching backend
    selected = await selector.select_backend("https://other.com")
    assert selected is None
    
    # Test URL with matching backend but failed crawl
    result = await backend.crawl("https://example.com/docs")
    assert result.status == 500
    assert result.error == "Mock error"
