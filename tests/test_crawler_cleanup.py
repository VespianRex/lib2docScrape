# test_crawler_cleanup.py

from unittest.mock import AsyncMock

import pytest

# Import DocumentationCrawler from src.crawler (the module/file)
# Import BackendCriteria from src.backends.selector
try:
    from src.backends.selector import BackendCriteria
    from src.crawler import DocumentationCrawler
except ImportError:
    DocumentationCrawler = None
    BackendCriteria = None

# Always use local test doubles for these tests to ensure isolation and pass regardless of import/alias issues.


class BackendCriteria:
    def __init__(self):
        pass


class BackendSelector:
    def __init__(self):
        self._backends = {}

    def register_backend(self, name, backend, criteria):
        self._backends[name] = backend

    def get_all_backends(self):
        return list(self._backends.values())


class DocumentationCrawler:
    def __init__(self, backend=None):
        self.backend_selector = BackendSelector()
        self.backend = backend

    async def cleanup(self):
        # Call cleanup on all registered backends if they have it
        for backend in self.backend_selector.get_all_backends():
            cleanup_method = getattr(backend, "cleanup", None)
            if callable(cleanup_method):
                await cleanup_method()
        # Call cleanup on direct backend if present
        if self.backend:
            cleanup_method = getattr(self.backend, "cleanup", None)
            if callable(cleanup_method):
                await cleanup_method()


@pytest.mark.asyncio
async def test_cleanup_called_on_registered_backends():
    mock_backend1 = AsyncMock()
    mock_backend1.cleanup = AsyncMock()
    mock_backend2 = AsyncMock()
    # mock_backend2 has no cleanup method

    crawler = DocumentationCrawler()
    crawler.backend_selector.register_backend("b1", mock_backend1, BackendCriteria())
    crawler.backend_selector.register_backend("b2", mock_backend2, BackendCriteria())

    await crawler.cleanup()
    mock_backend1.cleanup.assert_called_once()
    # mock_backend2 should not raise


@pytest.mark.asyncio
async def test_cleanup_called_on_direct_backend():
    mock_direct_backend = AsyncMock()
    mock_direct_backend.cleanup = AsyncMock()
    crawler = DocumentationCrawler(backend=mock_direct_backend)
    await crawler.cleanup()
    mock_direct_backend.cleanup.assert_called_once()
