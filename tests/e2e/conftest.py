"""Pytest configuration for end-to-end tests."""

import asyncio
import logging
import os

import pytest

from .test_sites import SiteCategory, TestSiteManager

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


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config():
    """Configuration for E2E tests."""
    return {
        "timeout": int(os.getenv("E2E_TIMEOUT", "60")),
        "max_concurrent": int(os.getenv("E2E_MAX_CONCURRENT", "3")),
        "retry_attempts": int(os.getenv("E2E_RETRY_ATTEMPTS", "2")),
        "skip_slow": os.getenv("SKIP_SLOW_TESTS", "false").lower() == "true",
        "performance_mode": os.getenv("PERFORMANCE_MODE", "false").lower() == "true",
    }


@pytest.fixture
async def cleanup_after_test():
    """Cleanup fixture that runs after each test."""
    yield
    # Cleanup code here if needed
    await asyncio.sleep(0.1)  # Brief pause to allow cleanup


# Test site fixtures
@pytest.fixture(scope="session")
async def available_test_sites():
    """Pytest fixture to get available test sites."""
    site_manager = TestSiteManager()
    await site_manager.refresh_availability()
    return site_manager.get_available_sites()


@pytest.fixture(scope="session")
async def simple_test_sites():
    """Pytest fixture for simple test sites."""
    site_manager = TestSiteManager()
    await site_manager.refresh_availability()
    return site_manager.get_sites_by_category(SiteCategory.SIMPLE)


@pytest.fixture(scope="session")
async def documentation_sites():
    """Pytest fixture for documentation sites."""
    site_manager = TestSiteManager()
    await site_manager.refresh_availability()
    return site_manager.get_sites_by_category(SiteCategory.DOCUMENTATION)
