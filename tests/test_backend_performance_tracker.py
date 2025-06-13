"""
Tests for backend performance tracking system.

This module tests the BackendPerformanceTracker which records metrics
for different backends and automatically selects the most lightweight
backend based on resource and compute performance.
"""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.backends.base import CrawlerBackend
from src.backends.base import CrawlResult as BackendCrawlResult


class TestBackendPerformanceTracker:
    """Test suite for BackendPerformanceTracker."""

    @pytest.fixture
    def temp_storage_path(self):
        """Create a temporary file for performance data storage."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
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
        backend.get_metrics.return_value = {
            "pages_crawled": 10,
            "success_rate": 0.9,
            "average_response_time": 1.5,
            "total_crawl_time": 15.0,
            "min_response_time": 0.5,
            "max_response_time": 3.0,
        }
        return backend

    @pytest.mark.asyncio
    async def test_performance_tracker_initialization(self, temp_storage_path):
        """Test that BackendPerformanceTracker initializes correctly."""
        # This test will fail until we implement BackendPerformanceTracker
        from src.performance.backend_tracker import BackendPerformanceTracker
        
        tracker = BackendPerformanceTracker(storage_path=temp_storage_path)
        
        assert tracker.storage_path == temp_storage_path
        assert tracker.performance_data == {}
        assert tracker.domain_performance == {}

    @pytest.mark.asyncio
    async def test_record_backend_performance(self, temp_storage_path, mock_backend):
        """Test recording backend performance metrics."""
        from src.performance.backend_tracker import BackendPerformanceTracker
        
        tracker = BackendPerformanceTracker(storage_path=temp_storage_path)
        
        # Record performance for a domain
        domain = "docs.python.org"
        metrics = {
            "response_time": 1.2,
            "memory_usage": 50.5,  # MB
            "cpu_usage": 15.3,     # %
            "success": True,
            "content_size": 1024,  # bytes
            "timestamp": 1640995200.0
        }
        
        await tracker.record_performance(mock_backend.name, domain, metrics)
        
        # Verify performance was recorded
        assert domain in tracker.domain_performance
        assert mock_backend.name in tracker.domain_performance[domain]
        
        backend_data = tracker.domain_performance[domain][mock_backend.name]
        assert len(backend_data["history"]) == 1
        assert backend_data["history"][0] == metrics
        assert backend_data["average_response_time"] == 1.2
        assert backend_data["average_memory_usage"] == 50.5
        assert backend_data["average_cpu_usage"] == 15.3
        assert backend_data["success_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_get_best_backend_for_domain(self, temp_storage_path):
        """Test selecting the best backend for a domain based on performance."""
        from src.performance.backend_tracker import BackendPerformanceTracker

        tracker = BackendPerformanceTracker(
            storage_path=temp_storage_path,
            min_samples_for_recommendation=1  # Allow single sample for testing
        )
        
        domain = "docs.python.org"
        
        # Record performance for multiple backends
        await tracker.record_performance("http", domain, {
            "response_time": 2.0,
            "memory_usage": 80.0,
            "cpu_usage": 25.0,
            "success": True,
            "content_size": 1024,
            "timestamp": 1640995200.0
        })
        
        await tracker.record_performance("crawl4ai", domain, {
            "response_time": 1.5,
            "memory_usage": 60.0,
            "cpu_usage": 20.0,
            "success": True,
            "content_size": 1024,
            "timestamp": 1640995201.0
        })
        
        await tracker.record_performance("playwright", domain, {
            "response_time": 3.0,
            "memory_usage": 120.0,
            "cpu_usage": 40.0,
            "success": True,
            "content_size": 1024,
            "timestamp": 1640995202.0
        })
        
        # Get best backend (should be crawl4ai - lowest resource usage)
        best_backend = tracker.get_best_backend_for_domain(domain)
        assert best_backend == "crawl4ai"

    @pytest.mark.asyncio
    async def test_performance_scoring_algorithm(self, temp_storage_path):
        """Test the performance scoring algorithm."""
        from src.performance.backend_tracker import BackendPerformanceTracker
        
        tracker = BackendPerformanceTracker(storage_path=temp_storage_path)
        
        # Test scoring with different weights
        performance_data = {
            "average_response_time": 1.5,
            "average_memory_usage": 60.0,
            "average_cpu_usage": 20.0,
            "success_rate": 0.95,
            "total_requests": 10
        }
        
        score = tracker.calculate_performance_score(performance_data)
        
        # Score should be between 0 and 1, higher is better
        assert 0 <= score <= 1
        assert isinstance(score, float)

    @pytest.mark.asyncio
    async def test_persistence_load_save(self, temp_storage_path):
        """Test saving and loading performance data."""
        from src.performance.backend_tracker import BackendPerformanceTracker
        
        # Create tracker and add some data
        tracker1 = BackendPerformanceTracker(storage_path=temp_storage_path)
        
        domain = "example.com"
        await tracker1.record_performance("http", domain, {
            "response_time": 1.0,
            "memory_usage": 50.0,
            "cpu_usage": 15.0,
            "success": True,
            "content_size": 512,
            "timestamp": 1640995200.0
        })
        
        # Save data
        await tracker1.save_performance_data()
        
        # Create new tracker and load data
        tracker2 = BackendPerformanceTracker(storage_path=temp_storage_path)
        await tracker2.load_performance_data()
        
        # Verify data was loaded correctly
        assert domain in tracker2.domain_performance
        assert "http" in tracker2.domain_performance[domain]
        
        backend_data = tracker2.domain_performance[domain]["http"]
        assert len(backend_data["history"]) == 1
        assert backend_data["average_response_time"] == 1.0

    @pytest.mark.asyncio
    async def test_performance_data_cleanup(self, temp_storage_path):
        """Test cleanup of old performance data."""
        from src.performance.backend_tracker import BackendPerformanceTracker
        
        tracker = BackendPerformanceTracker(
            storage_path=temp_storage_path,
            max_history_days=7
        )
        
        domain = "example.com"
        
        # Add old data (should be cleaned up)
        old_timestamp = 1640995200.0 - (8 * 24 * 60 * 60)  # 8 days ago
        await tracker.record_performance("http", domain, {
            "response_time": 1.0,
            "memory_usage": 50.0,
            "cpu_usage": 15.0,
            "success": True,
            "content_size": 512,
            "timestamp": old_timestamp
        })
        
        # Add recent data (should be kept)
        recent_timestamp = 1640995200.0
        await tracker.record_performance("http", domain, {
            "response_time": 1.2,
            "memory_usage": 55.0,
            "cpu_usage": 18.0,
            "success": True,
            "content_size": 600,
            "timestamp": recent_timestamp
        })
        
        # Trigger cleanup with current time set to recent timestamp
        await tracker.cleanup_old_data(current_time=recent_timestamp)

        # Verify only recent data remains
        backend_data = tracker.domain_performance[domain]["http"]
        assert len(backend_data["history"]) == 1
        assert backend_data["history"][0]["timestamp"] == recent_timestamp

    @pytest.mark.asyncio
    async def test_backend_recommendation_with_fallback(self, temp_storage_path):
        """Test backend recommendation with fallback for unknown domains."""
        from src.performance.backend_tracker import BackendPerformanceTracker
        
        tracker = BackendPerformanceTracker(storage_path=temp_storage_path)
        
        # Test with unknown domain (should return default)
        unknown_domain = "unknown-domain.com"
        best_backend = tracker.get_best_backend_for_domain(unknown_domain)
        
        # Should return a default backend (e.g., "http")
        assert best_backend in ["http", "crawl4ai", "playwright", "scrapy"]

    @pytest.mark.asyncio
    async def test_real_time_performance_monitoring(self, temp_storage_path, mock_backend):
        """Test real-time performance monitoring during crawling."""
        from src.performance.backend_tracker import BackendPerformanceTracker

        tracker = BackendPerformanceTracker(storage_path=temp_storage_path)

        # Mock system resource monitoring
        with patch('src.performance.backend_tracker.PSUTIL_AVAILABLE', True), \
             patch('psutil.Process') as mock_process_class:

            # Create mock process instance
            mock_process = MagicMock()
            mock_process_class.return_value = mock_process

            # Mock memory info for start and stop
            mock_memory_info_start = MagicMock()
            mock_memory_info_start.rss = 50 * 1024 * 1024  # 50MB in bytes
            mock_memory_info_end = MagicMock()
            mock_memory_info_end.rss = 60 * 1024 * 1024  # 60MB in bytes

            mock_process.memory_info.side_effect = [mock_memory_info_start, mock_memory_info_end]
            mock_process.cpu_percent.side_effect = [10.0, 15.5]

            # Start monitoring
            domain = "test.com"
            monitoring_context = await tracker.start_monitoring(mock_backend.name, domain)

            # Simulate some work
            await asyncio.sleep(0.1)

            # Stop monitoring and get metrics
            metrics = await tracker.stop_monitoring(monitoring_context)

            assert "response_time" in metrics
            assert "memory_usage" in metrics
            assert "cpu_usage" in metrics
            assert metrics["response_time"] >= 0.1
            assert metrics["memory_usage"] == 10.0  # 60MB - 50MB = 10MB
            assert metrics["cpu_usage"] == 15.5
