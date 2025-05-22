"""Tests for the backend_selector module."""

import pytest
from unittest.mock import MagicMock

from src.backend_selector import BackendSelector, BackendCriteria


class TestBackendCriteria:
    """Tests for the BackendCriteria class."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        criteria = BackendCriteria()
        assert criteria.priority == 0
        assert criteria.content_types is None
        assert criteria.url_patterns is None
        assert criteria.max_load == 1.0
        assert criteria.min_success_rate == 0.0

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        criteria = BackendCriteria(
            priority=10,
            content_types=["text/html", "application/json"],
            url_patterns=["docs", "api"],
            max_load=0.8,
            min_success_rate=0.7
        )
        assert criteria.priority == 10
        assert criteria.content_types == ["text/html", "application/json"]
        assert criteria.url_patterns == ["docs", "api"]
        assert criteria.max_load == 0.8
        assert criteria.min_success_rate == 0.7


class TestBackendSelector:
    """Tests for the BackendSelector class."""

    def test_init(self):
        """Test initialization."""
        selector = BackendSelector()
        assert selector.backends == {}

    def test_register_backend(self):
        """Test registering a backend."""
        selector = BackendSelector()
        backend = MagicMock()
        criteria = BackendCriteria(priority=10)
        
        selector.register_backend(backend, criteria)
        
        assert backend in selector.backends
        assert selector.backends[backend] == criteria

    def test_select_backend_with_url_pattern_match(self):
        """Test selecting a backend with matching URL pattern."""
        selector = BackendSelector()
        
        # Create mock backends
        backend1 = MagicMock(name="backend1")
        backend2 = MagicMock(name="backend2")
        
        # Register backends with criteria
        selector.register_backend(
            backend1, 
            BackendCriteria(priority=10, url_patterns=["docs"])
        )
        selector.register_backend(
            backend2, 
            BackendCriteria(priority=5, url_patterns=["api"])
        )
        
        # Test URL that matches backend1
        selected = selector.select_backend("https://example.com/docs/index.html")
        assert selected == backend1
        
        # Test URL that matches backend2
        selected = selector.select_backend("https://example.com/api/v1")
        assert selected == backend2

    def test_select_backend_priority(self):
        """Test selecting a backend based on priority."""
        selector = BackendSelector()
        
        # Create mock backends
        backend1 = MagicMock(name="backend1")
        backend2 = MagicMock(name="backend2")
        
        # Register backends with criteria
        selector.register_backend(
            backend1, 
            BackendCriteria(priority=10, url_patterns=["docs"])
        )
        selector.register_backend(
            backend2, 
            BackendCriteria(priority=20, url_patterns=["docs"])
        )
        
        # Test URL that matches both backends, but backend2 has higher priority
        selected = selector.select_backend("https://example.com/docs/index.html")
        assert selected == backend2

    def test_select_backend_no_match(self):
        """Test selecting a backend with no matching URL pattern."""
        selector = BackendSelector()
        
        # Create mock backend
        backend = MagicMock()
        
        # Register backend with criteria
        selector.register_backend(
            backend, 
            BackendCriteria(priority=10, url_patterns=["docs"])
        )
        
        # Test URL that doesn't match any backend
        selected = selector.select_backend("https://example.com/blog/index.html")
        assert selected is None

    def test_select_backend_with_invalid_url(self):
        """Test selecting a backend with an invalid URL."""
        selector = BackendSelector()
        
        # Create mock backend
        backend = MagicMock()
        
        # Register backend with criteria
        selector.register_backend(
            backend, 
            BackendCriteria(priority=10, url_patterns=["docs"])
        )
        
        # Test with invalid URL
        selected = selector.select_backend("invalid-url")
        assert selected is None

    def test_select_backend_with_multiple_patterns(self):
        """Test selecting a backend with multiple URL patterns."""
        selector = BackendSelector()
        
        # Create mock backend
        backend = MagicMock()
        
        # Register backend with multiple URL patterns
        selector.register_backend(
            backend, 
            BackendCriteria(priority=10, url_patterns=["docs", "api", "blog"])
        )
        
        # Test URLs matching different patterns
        assert selector.select_backend("https://example.com/docs/index.html") == backend
        assert selector.select_backend("https://example.com/api/v1") == backend
        assert selector.select_backend("https://example.com/blog/post") == backend
        assert selector.select_backend("https://example.com/about") is None
