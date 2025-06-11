"""Tests for base components of the documentation crawler."""

import time
from typing import Optional

import pytest

from src.backends.base import CrawlerBackend, CrawlResult
from src.backends.selector import BackendCriteria, BackendSelector


class MockCrawlerBackend(CrawlerBackend):
    """Mock crawler backend for testing."""

    def __init__(self, name: Optional[str] = None, success: bool = True):
        super().__init__(name=name)
        self.success = success
        self.crawl_called = False
        self.validate_called = False
        self.process_called = False

    async def crawl(self, url: str, params: dict = None) -> CrawlResult:
        """Mock crawl implementation."""
        self.crawl_called = True
        start_time = time.time()

        try:
            result = CrawlResult(
                url=url,
                content={"html": "<html><body><h1>Test</h1></body></html>"}
                if self.success
                else {},
                metadata={"status": 200} if self.success else {"error": "Mock error"},
                status=200 if self.success else 500,
                error="Mock error" if not self.success else None,
            )

            # Update metrics with crawl time and success status
            await self.update_metrics(time.time() - start_time, result.status == 200)

            return result

        except Exception:
            await self.update_metrics(time.time() - start_time, False)
            # Re-raise unexpected exceptions
            raise

    async def validate(self, content: CrawlResult) -> bool:
        """Mock validate implementation."""
        self.validate_called = True
        return self.success

    async def process(self, content: CrawlResult) -> dict:
        """Mock process implementation."""
        self.process_called = True
        if self.success:
            return {
                "title": "Test Document",
                "content": {"text": "Test content"},
                "metadata": {"type": "test"},
            }
        return {"error": "Processing failed"}


@pytest.mark.asyncio
async def test_crawler_backend_lifecycle():
    """Test crawler backend lifecycle methods."""
    backend = MockCrawlerBackend(name="test_backend")

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
    backend = MockCrawlerBackend(name="error_backend", success=False)

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
    backend = MockCrawlerBackend(name="registration_backend")

    # Register backend with criteria
    criteria = BackendCriteria(
        priority=10, content_types=["text/html"], url_patterns=["example.com"]
    )
    selector.register_backend("registration_backend", backend, criteria)

    # Verify registration
    assert len(selector._backends) == 1  # Only the mock backend should be registered
    assert selector._backends["registration_backend"] == backend
    assert selector.criteria["registration_backend"] == criteria


@pytest.mark.asyncio
async def test_backend_selector_selection():
    """Test backend selection logic."""
    import logging

    logging.getLogger("src.backends.selector").setLevel(logging.DEBUG)
    selector = BackendSelector()
    # Make sure to await async method
    await selector.close_all_backends()  # Clear default backends
    backend1 = MockCrawlerBackend(name="backend1")
    backend2 = MockCrawlerBackend(name="backend2")

    # Register backends with different criteria
    # Use wildcard patterns that match the entire URL
    selector.register_backend(
        "backend1",
        backend1,
        BackendCriteria(
            priority=10,
            content_types=["text/html"],
            url_patterns=[
                "*example.com/docs*"
            ],  # Use wildcard pattern for full URL matching
        ),
    )
    selector.register_backend(
        "backend2",
        backend2,
        BackendCriteria(
            priority=5,
            content_types=["application/json"],
            url_patterns=[
                "*api.example.com*"
            ],  # Use wildcard pattern for full URL matching
        ),
    )

    # Test selection
    selected1 = selector.select_backend_for_url("https://example.com/docs")
    assert selected1 == backend1, "Backend1 should be selected for example.com/docs URL"

    selected2 = selector.select_backend_for_url("https://api.example.com/v1")
    assert selected2 == backend2, "Backend2 should be selected for api.example.com URL"

    selected3 = selector.select_backend_for_url("https://other.com")
    assert selected3 is None, "No backend should be selected for other.com URL"


# test_url_normalization removed as the tested function normalize_url in base.py was removed.
# URL normalization is now handled by URLInfo in src/utils/url_info.py and tested in test_url_handling.py


@pytest.mark.asyncio
async def test_backend_selector_advanced_selection():
    """Test advanced backend selection logic."""
    selector = BackendSelector()
    # Make sure to await async method
    await selector.close_all_backends()  # Clear default backends
    backend1 = MockCrawlerBackend(name="backend1")
    backend2 = MockCrawlerBackend(name="backend2")
    backend3 = MockCrawlerBackend(name="backend3")
    backend4 = MockCrawlerBackend(name="backend4")

    # Backend 1: Domain and Path specific
    selector.register_backend(
        "backend1",
        backend1,
        BackendCriteria(
            priority=10,
            url_patterns=["*"],
            domains=["example.com"],
            paths=["/docs/api"],
            content_types=["text/html"],
        ),
    )

    # Backend 2: Content type specific, lower priority
    selector.register_backend(
        "backend2",
        backend2,
        BackendCriteria(
            priority=5, url_patterns=["*"], content_types=["application/json"]
        ),
    )

    # Backend 3: Fallback backend, lowest priority
    selector.register_backend(
        "backend3",
        backend3,
        BackendCriteria(
            priority=1,
            url_patterns=["*"],  # Matches all URLs
            content_types=["text/html"],
        ),
    )

    # Backend 4: Higher priority for same domain but different path
    selector.register_backend(
        "backend4",
        backend4,
        BackendCriteria(
            priority=15,
            url_patterns=["*"],
            domains=["example.com"],
            paths=["/special"],
            content_types=["text/html"],
        ),
    )

    # Test selection based on domain and path
    print(f"Test: backend1 ID is {id(backend1)}")  # Diagnostic print
    selected1 = selector.select_backend_for_url("https://example.com/docs/api/endpoint")
    assert selected1 == backend1

    # Test selection based on content type
    selected2 = selector.select_backend_for_url(
        "https://api.example.com/data", content_type="application/json"
    )
    assert selected2 == backend2

    # Test no backend match
    selected3 = selector.select_backend_for_url("https://other.com/page")
    assert selected3.name == backend3.name  # Should select fallback

    # When requesting a specific unknown content type, we expect the highest priority backend to be used,
    # which in this case is backend2 (even though backend3 is the "fallback" with text/html content type)
    selected4 = selector.select_backend_for_url(
        "https://other.com/page", content_type="application/xml"
    )
    assert (
        selected4 is not None
    ), "A backend should be selected for unknown content type"

    # For the specific test case of "application/xml", the backend4 will be used since it has the highest priority
    # (15) among all backends when falling back for unknown content types
    assert (
        selected4.name == "backend4"
    ), "Backend4 should be selected by priority (highest priority: 15)"

    # Test priority selection (backend4 should be selected over backend1 for /special path)
    selected5 = selector.select_backend_for_url("https://example.com/special/page")
    assert selected5 == backend4

    # Test backend1 still selected for /docs/api path
    selected6 = selector.select_backend_for_url("https://example.com/docs/api/page")
    assert selected6 == backend1

    # Test no match, fallback backend should be selected
    selected7 = selector.select_backend_for_url("https://nomatch.com/page")
    assert selected7 == backend3


@pytest.mark.asyncio
async def test_mock_crawler_backend_edge_cases():
    """Test MockCrawlerBackend edge cases and error handling."""
    backend = MockCrawlerBackend(name="edge_case_backend")

    # Test crawl method returning error result
    backend.success = False
    error_result_1 = await backend.crawl("https://example.com/error")
    assert error_result_1.status != 200
    assert error_result_1.error is not None

    backend.success = True  # Reset success

    # Test validate method returning False
    backend.success = False
    result = await backend.crawl("https://example.com/validate_fail")
    valid = await backend.validate(result)
    assert valid is False
    assert backend.validate_called

    backend.success = True  # Reset success

    # Test process method returning error dict
    backend.success = False
    result = await backend.crawl("https://example.com/process_fail")
    processed = await backend.process(result)
    assert "error" in processed
    assert backend.process_called

    backend.success = True  # Reset success

    # Test metrics update on crawl failure (returning error result)
    backend_error_metrics = MockCrawlerBackend(
        name="error_metrics_backend", success=False
    )  # Set to fail
    # Call crawl and check the error result
    error_result = await backend_error_metrics.crawl(
        "https://example.com/error_result"
    )  # Changed URL slightly for clarity
    assert error_result.status != 200
    assert error_result.error is not None
    assert backend_error_metrics.metrics["pages_crawled"] == 1
    assert (
        backend_error_metrics.metrics["success_rate"] == 0.0
    )  # Should be 0 as crawl failed
    assert backend_error_metrics.metrics["average_response_time"] > 0

    # Test crawl with parameters (though mock backend ignores them)
    params = {"param1": "value1", "param2": "value2"}
    crawl_result = await backend.crawl("https://example.com/params", params=params)
    assert crawl_result.url == "https://example.com/params"
    assert backend.crawl_called
