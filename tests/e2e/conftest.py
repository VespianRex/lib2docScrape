"""Pytest configuration for end-to-end tests.

Environment Variables:
    E2E_FAST_MODE: Enable fast mode with mocked backends (default: true)
    E2E_MOCK_NETWORK: Use mock network responses (default: true)
    E2E_TIMEOUT: Test timeout in seconds (default: 60)
    E2E_MAX_CONCURRENT: Max concurrent tests (default: 3)
    SKIP_REAL_WORLD_TESTS: Skip real network tests (default: false)
    SKIP_SLOW_TESTS: Skip slow tests (default: false)

Usage:
    # Fast mode (default) - uses mocks, very quick
    pytest tests/e2e/

    # Real mode - actual network requests, slower but more realistic
    E2E_FAST_MODE=false E2E_MOCK_NETWORK=false pytest tests/e2e/

    # Parallel execution for faster real-world tests
    E2E_FAST_MODE=false pytest tests/e2e/ -n 2
"""

import asyncio
import logging
import os
from unittest.mock import AsyncMock, patch

import pytest

from .test_sites import SiteCategory, SiteManager, SiteConfig, TechStack

# Configure logging for E2E tests
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Disable verbose logging from external libraries
logging.getLogger("aiohttp").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


def pytest_configure(config):
    """Configure pytest for E2E tests."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "real_world: mark test as real-world integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance benchmark"
    )
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers and skip conditions."""
    # Skip real-world tests if running in CI without network access
    skip_real_world = pytest.mark.skip(reason="Real-world tests disabled in CI")

    for item in items:
        # Add slow marker to all E2E tests
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.slow)

        # Skip real-world tests if SKIP_REAL_WORLD_TESTS is set
        if "real_world" in item.keywords and os.getenv("SKIP_REAL_WORLD_TESTS"):
            item.add_marker(skip_real_world)


# Removed deprecated event_loop fixture - use pytest-asyncio's default instead


@pytest.fixture(scope="session")
def test_config():
    """Configuration for E2E tests."""
    return {
        "timeout": int(os.getenv("E2E_TIMEOUT", "60")),
        "max_concurrent": int(os.getenv("E2E_MAX_CONCURRENT", "3")),
        "retry_attempts": int(os.getenv("E2E_RETRY_ATTEMPTS", "2")),
        "skip_slow": os.getenv("SKIP_SLOW_TESTS", "false").lower() == "true",
        "performance_mode": os.getenv("PERFORMANCE_MODE", "false").lower() == "true",
        "fast_mode": os.getenv("E2E_FAST_MODE", "false").lower() == "true",  # Default to real mode
        "mock_network": os.getenv("E2E_MOCK_NETWORK", "false").lower() == "true",  # Default to real network
    }


@pytest.fixture
async def cleanup_after_test():
    """Cleanup fixture that runs after each test."""
    yield
    # Cleanup code here if needed
    await asyncio.sleep(0.1)  # Brief pause to allow cleanup


@pytest.fixture
async def mock_fast_backend(test_config):
    """Mock backend that returns fast fake responses for testing."""
    if not test_config["mock_network"]:
        return None

    from src.backends.base import CrawlResult as BackendCrawlResult

    class FastMockBackend:
        """Ultra-fast mock backend for e2e testing."""

        def __init__(self):
            self.name = "fast_mock"
            self.crawl_count = 0

        async def crawl(self, url_info, **kwargs):
            """Return instant mock response."""
            self.crawl_count += 1

            # Simulate very brief processing time
            await asyncio.sleep(0.01)

            return BackendCrawlResult(
                url=url_info.normalized_url,
                content={
                    "html": f"<html><head><title>Mock Page {self.crawl_count}</title></head>"
                           f"<body><h1>Mock Content</h1><p>This is mock content for {url_info.normalized_url}</p>"
                           f"<a href='/page{self.crawl_count + 1}'>Next Page</a></body></html>"
                },
                status=200,
                content_type="text/html",
                metadata={"mock": True, "crawl_count": self.crawl_count},
                documents=[
                    {
                        "url": url_info.normalized_url,
                        "title": f"Mock Page {self.crawl_count}",
                        "content": f"Mock content for testing. Page {self.crawl_count}.",
                        "headings": [{"level": 1, "text": "Mock Content"}],
                        "links": [{"text": "Next Page", "url": f"/page{self.crawl_count + 1}"}],
                    }
                ],
            )

    return FastMockBackend()


@pytest.fixture
def fast_crawler_config(test_config):
    """Fast crawler configuration for e2e tests."""
    from src.crawler.models import CrawlConfig

    if test_config["fast_mode"]:
        # Ultra-fast configuration for testing
        return CrawlConfig(
            max_depth=2,
            max_pages=5,
            rate_limit=0.01,  # Very fast - 0.01 seconds between requests
            timeout=5,  # Short timeout
            retry_count=1,  # Minimal retries
            use_duckduckgo=False,  # Disable DuckDuckGo for speed
            concurrent_requests=5,
            user_agent="lib2docScrape-E2E-Test/1.0",
        )
    else:
        # Real-world configuration but still optimized
        return CrawlConfig(
            max_depth=3,
            max_pages=10,
            rate_limit=0.1,  # Faster than default 0.5s
            timeout=15,  # Shorter than default 30s
            retry_count=2,
            use_duckduckgo=False,  # Disable DuckDuckGo for e2e tests
            concurrent_requests=3,
            user_agent="lib2docScrape-E2E-Test/1.0",
        )


# Mock test sites for fast testing
MOCK_SITES = [
    SiteConfig(
        name="Mock Simple Site",
        url="http://localhost:8000/mock-simple",
        category=SiteCategory.SIMPLE,
        tech_stack=TechStack.STATIC_HTML,
        expected_pages=3,
        max_depth=1,
        description="Mock site for fast testing",
    ),
    SiteConfig(
        name="Mock Documentation Site",
        url="http://localhost:8000/mock-docs",
        category=SiteCategory.DOCUMENTATION,
        tech_stack=TechStack.SPHINX,
        expected_pages=5,
        max_depth=2,
        description="Mock documentation site for fast testing",
    ),
]


# Test site fixtures
@pytest.fixture(scope="function")
async def available_test_sites(test_config):
    """Pytest fixture to get available test sites."""
    if test_config["fast_mode"]:
        return MOCK_SITES

    site_manager = SiteManager()
    await site_manager.refresh_availability()
    return site_manager.get_available_sites()


@pytest.fixture(scope="function")
async def simple_test_sites(test_config):
    """Pytest fixture for simple test sites."""
    if test_config["fast_mode"]:
        return [site for site in MOCK_SITES if site.category == SiteCategory.SIMPLE]

    site_manager = SiteManager()
    await site_manager.refresh_availability()
    return site_manager.get_sites_by_category(SiteCategory.SIMPLE)


@pytest.fixture(scope="function")
async def documentation_sites(test_config):
    """Pytest fixture for documentation sites."""
    if test_config["fast_mode"]:
        return [site for site in MOCK_SITES if site.category == SiteCategory.DOCUMENTATION]

    site_manager = SiteManager()
    await site_manager.refresh_availability()
    return site_manager.get_sites_by_category(SiteCategory.DOCUMENTATION)
