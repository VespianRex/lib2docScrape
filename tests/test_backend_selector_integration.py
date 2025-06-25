"""
Tests for backend selector integration with performance tracking.

This module tests the integration between BackendSelector and
BackendPerformanceTracker for automatic backend selection based
on performance metrics.
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.backends.base import CrawlerBackend
from src.backends.base import CrawlResult as BackendCrawlResult
from src.backends.selector import BackendCriteria, BackendSelector
from src.performance.backend_tracker import BackendPerformanceTracker


class TestBackendSelectorIntegration:
    """Test suite for BackendSelector integration with performance tracking."""

    @pytest.fixture
    def temp_storage_path(self):
        """Create a temporary file for performance data storage."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = Path(f.name)
        yield temp_path
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

    @pytest.fixture
    def mock_backend(self):
        """Create a mock backend for testing."""
        backend = MagicMock(spec=CrawlerBackend)
        backend.name = "test_backend"
        backend.crawl = AsyncMock(
            return_value=BackendCrawlResult(
                url="https://test.com",
                content={"html": "<html>Test content</html>"},
                metadata={},
                status=200,
            )
        )
        return backend

    @pytest.fixture
    def default_criteria(self):
        """Create default criteria for testing."""
        return BackendCriteria(
            priority=100,
            content_types=["text/html", "*/*"],
            url_patterns=["*"],
            schemes=["http", "https"],
        )

    @pytest.fixture
    def performance_tracker(self, temp_storage_path):
        """Create a performance tracker for testing."""
        return BackendPerformanceTracker(
            storage_path=temp_storage_path, min_samples_for_recommendation=1
        )

    @pytest.fixture
    def backend_selector(self, performance_tracker):
        """Create a backend selector with performance tracking."""
        selector = BackendSelector()
        selector.performance_tracker = performance_tracker
        return selector

    @pytest.mark.asyncio
    async def test_backend_selector_with_performance_tracking(
        self, backend_selector, performance_tracker, mock_backend, default_criteria
    ):
        """Test that backend selector uses performance tracking for selection."""
        # Register a backend with criteria
        backend_selector.register_backend(
            "test_backend", mock_backend, default_criteria
        )

        # Record some performance data
        domain = "test.com"
        await performance_tracker.record_performance(
            "test_backend",
            domain,
            {
                "response_time": 1.0,
                "memory_usage": 50.0,
                "cpu_usage": 15.0,
                "success": True,
                "content_size": 1024,
                "timestamp": 1640995200.0,
            },
        )

        # Test that selector can get performance-optimized backend
        url = "https://test.com/docs"
        backend = await backend_selector.get_backend_with_performance(url)

        assert backend is not None
        assert backend.name == "test_backend"

    @pytest.mark.asyncio
    async def test_performance_based_backend_selection(
        self, backend_selector, performance_tracker, default_criteria
    ):
        """Test selection between multiple backends based on performance."""
        # Create mock backends with different performance characteristics
        fast_backend = MagicMock(spec=CrawlerBackend)
        fast_backend.name = "fast_backend"
        fast_backend.crawl = AsyncMock(
            return_value=BackendCrawlResult(
                url="https://test.com",
                content={"html": "content"},
                metadata={},
                status=200,
            )
        )

        slow_backend = MagicMock(spec=CrawlerBackend)
        slow_backend.name = "slow_backend"
        slow_backend.crawl = AsyncMock(
            return_value=BackendCrawlResult(
                url="https://test.com",
                content={"html": "content"},
                metadata={},
                status=200,
            )
        )

        # Register backends with criteria
        backend_selector.register_backend(
            "fast_backend", fast_backend, default_criteria
        )
        backend_selector.register_backend(
            "slow_backend", slow_backend, default_criteria
        )

        domain = "test.com"

        # Record performance data - fast backend performs better
        await performance_tracker.record_performance(
            "fast_backend",
            domain,
            {
                "response_time": 0.5,
                "memory_usage": 30.0,
                "cpu_usage": 10.0,
                "success": True,
                "content_size": 1024,
                "timestamp": 1640995200.0,
            },
        )

        await performance_tracker.record_performance(
            "slow_backend",
            domain,
            {
                "response_time": 3.0,
                "memory_usage": 150.0,
                "cpu_usage": 50.0,
                "success": True,
                "content_size": 1024,
                "timestamp": 1640995201.0,
            },
        )

        # Get performance-optimized backend
        url = "https://test.com/docs"
        backend = await backend_selector.get_backend_with_performance(url)

        # Should select the fast backend
        assert backend.name == "fast_backend"

    @pytest.mark.asyncio
    async def test_fallback_when_no_performance_data(
        self, backend_selector, performance_tracker, mock_backend, default_criteria
    ):
        """Test fallback to default selection when no performance data exists."""
        # Register a backend with criteria
        backend_selector.register_backend(
            "test_backend", mock_backend, default_criteria
        )

        # No performance data recorded
        url = "https://unknown-domain.com/docs"
        backend = await backend_selector.get_backend_with_performance(url)

        # Should still return a backend (fallback behavior)
        assert backend is not None

    @pytest.mark.asyncio
    async def test_performance_tracking_during_crawl(
        self, backend_selector, performance_tracker, mock_backend, default_criteria
    ):
        """Test that performance is tracked during actual crawling."""
        # Register backend with criteria
        backend_selector.register_backend(
            "test_backend", mock_backend, default_criteria
        )

        # Mock the performance monitoring
        with patch.object(
            performance_tracker, "start_monitoring"
        ) as mock_start, patch.object(
            performance_tracker, "stop_monitoring"
        ) as mock_stop, patch.object(
            performance_tracker, "record_performance"
        ) as mock_record:
            mock_context = MagicMock()
            mock_start.return_value = mock_context
            mock_stop.return_value = {
                "response_time": 1.2,
                "memory_usage": 45.0,
                "cpu_usage": 12.0,
                "success": True,
                "content_size": 1024,
                "timestamp": 1640995200.0,
            }

            # Perform crawl with performance tracking
            url = "https://test.com/docs"
            result = await backend_selector.crawl_with_performance_tracking(url)

            # Verify monitoring was called
            mock_start.assert_called_once()
            mock_stop.assert_called_once_with(mock_context)
            mock_record.assert_called_once()

            # Verify result
            assert result is not None
            assert result.status == 200

    @pytest.mark.asyncio
    async def test_performance_data_persistence(
        self,
        backend_selector,
        performance_tracker,
        mock_backend,
        temp_storage_path,
        default_criteria,
    ):
        """Test that performance data is persisted and loaded correctly."""
        # Register backend and record performance
        backend_selector.register_backend(
            "test_backend", mock_backend, default_criteria
        )

        domain = "test.com"
        await performance_tracker.record_performance(
            "test_backend",
            domain,
            {
                "response_time": 1.0,
                "memory_usage": 50.0,
                "cpu_usage": 15.0,
                "success": True,
                "content_size": 1024,
                "timestamp": 1640995200.0,
            },
        )

        # Save performance data
        await performance_tracker.save_performance_data()

        # Create new tracker and load data
        new_tracker = BackendPerformanceTracker(
            storage_path=temp_storage_path, min_samples_for_recommendation=1
        )
        await new_tracker.load_performance_data()

        # Verify data was loaded
        best_backend = new_tracker.get_best_backend_for_domain(domain)
        assert best_backend == "test_backend"

    @pytest.mark.asyncio
    async def test_adaptive_backend_switching(
        self, backend_selector, performance_tracker, default_criteria
    ):
        """Test adaptive backend switching based on changing performance."""
        # Create two backends
        backend_a = MagicMock(spec=CrawlerBackend)
        backend_a.name = "backend_a"
        backend_b = MagicMock(spec=CrawlerBackend)
        backend_b.name = "backend_b"

        backend_selector.register_backend("backend_a", backend_a, default_criteria)
        backend_selector.register_backend("backend_b", backend_b, default_criteria)

        domain = "adaptive-test.com"

        # Initially, backend_a performs better
        await performance_tracker.record_performance(
            "backend_a",
            domain,
            {
                "response_time": 1.0,
                "memory_usage": 40.0,
                "cpu_usage": 10.0,
                "success": True,
                "content_size": 1024,
                "timestamp": 1640995200.0,
            },
        )

        await performance_tracker.record_performance(
            "backend_b",
            domain,
            {
                "response_time": 2.0,
                "memory_usage": 80.0,
                "cpu_usage": 25.0,
                "success": True,
                "content_size": 1024,
                "timestamp": 1640995201.0,
            },
        )

        # Should recommend backend_a
        best_backend = performance_tracker.get_best_backend_for_domain(domain)
        assert best_backend == "backend_a"

        # Now backend_b improves significantly - add multiple good samples to override the average
        for i in range(3):
            await performance_tracker.record_performance(
                "backend_b",
                domain,
                {
                    "response_time": 0.3,
                    "memory_usage": 15.0,
                    "cpu_usage": 3.0,
                    "success": True,
                    "content_size": 1024,
                    "timestamp": 1640995202.0 + i,
                },
            )

        # Should now recommend backend_b
        best_backend = performance_tracker.get_best_backend_for_domain(domain)
        assert best_backend == "backend_b"

    @pytest.mark.asyncio
    async def test_error_handling_in_performance_tracking(
        self, backend_selector, performance_tracker, mock_backend, default_criteria
    ):
        """Test error handling when performance tracking fails."""
        backend_selector.register_backend(
            "test_backend", mock_backend, default_criteria
        )

        # Mock performance tracking to raise an error
        with patch.object(
            performance_tracker,
            "start_monitoring",
            side_effect=Exception("Monitoring failed"),
        ):
            # Should still be able to crawl without performance tracking
            url = "https://test.com/docs"
            backend = await backend_selector.get_backend_with_performance(url)

            # Should fallback gracefully
            assert backend is not None
