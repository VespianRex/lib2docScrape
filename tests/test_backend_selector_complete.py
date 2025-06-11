"""Tests for the backend selector module."""

import logging
from unittest.mock import Mock

from src.backend_selector import BackendCriteria, BackendSelector


class TestBackendCriteria:
    """Tests for the BackendCriteria class."""

    def test_default_initialization(self):
        """Test that BackendCriteria can be initialized with default values."""
        criteria = BackendCriteria()
        assert criteria.priority == 0
        assert criteria.content_types is None
        assert criteria.url_patterns is None
        assert criteria.max_load == 1.0
        assert criteria.min_success_rate == 0.0

    def test_custom_initialization(self):
        """Test that BackendCriteria can be initialized with custom values."""
        criteria = BackendCriteria(
            priority=10,
            content_types=["text/html", "application/json"],
            url_patterns=["docs", "api"],
            max_load=0.8,
            min_success_rate=0.7,
        )
        assert criteria.priority == 10
        assert criteria.content_types == ["text/html", "application/json"]
        assert criteria.url_patterns == ["docs", "api"]
        assert criteria.max_load == 0.8
        assert criteria.min_success_rate == 0.7


class TestBackendSelector:
    """Tests for the BackendSelector class."""

    def test_initialization(self):
        """Test that BackendSelector can be initialized."""
        selector = BackendSelector()
        assert hasattr(selector, "backends")
        assert isinstance(selector.backends, dict)
        assert len(selector.backends) == 0

    def test_register_backend(self):
        """Test that a backend can be registered with criteria."""
        selector = BackendSelector()
        backend = Mock()
        criteria = BackendCriteria(priority=5)

        selector.register_backend(backend, criteria)

        assert len(selector.backends) == 1
        assert backend in selector.backends
        assert selector.backends[backend] == criteria

    def test_register_multiple_backends(self):
        """Test that multiple backends can be registered."""
        selector = BackendSelector()
        backend1 = Mock(name="backend1")
        backend2 = Mock(name="backend2")
        criteria1 = BackendCriteria(priority=5)
        criteria2 = BackendCriteria(priority=10)

        selector.register_backend(backend1, criteria1)
        selector.register_backend(backend2, criteria2)

        assert len(selector.backends) == 2
        assert backend1 in selector.backends
        assert backend2 in selector.backends
        assert selector.backends[backend1] == criteria1
        assert selector.backends[backend2] == criteria2

    def test_select_backend_no_backends(self):
        """Test selecting a backend when no backends are registered."""
        selector = BackendSelector()
        backend = selector.select_backend("https://example.com")
        assert backend is None

    def test_select_backend_url_pattern_match(self):
        """Test selecting a backend based on URL pattern match."""
        selector = BackendSelector()
        backend1 = Mock(name="backend1")
        backend2 = Mock(name="backend2")

        criteria1 = BackendCriteria(priority=5, url_patterns=["docs"])
        criteria2 = BackendCriteria(priority=10, url_patterns=["api"])

        selector.register_backend(backend1, criteria1)
        selector.register_backend(backend2, criteria2)

        # URL matches backend1's pattern
        selected = selector.select_backend("https://example.com/docs/index.html")
        assert selected == backend1

        # URL matches backend2's pattern
        selected = selector.select_backend("https://example.com/api/v1")
        assert selected == backend2

    def test_select_backend_priority(self):
        """Test that the backend with the highest priority is selected when multiple match."""
        selector = BackendSelector()
        backend1 = Mock(name="backend1")
        backend2 = Mock(name="backend2")

        criteria1 = BackendCriteria(priority=5, url_patterns=["example"])
        criteria2 = BackendCriteria(priority=10, url_patterns=["example"])

        selector.register_backend(backend1, criteria1)
        selector.register_backend(backend2, criteria2)

        # Both backends match, but backend2 has higher priority
        selected = selector.select_backend("https://example.com")
        assert selected == backend2

    def test_select_backend_no_match(self):
        """Test that no backend is selected when URL doesn't match any patterns."""
        selector = BackendSelector()
        backend = Mock()
        criteria = BackendCriteria(url_patterns=["docs"])

        selector.register_backend(backend, criteria)

        selected = selector.select_backend("https://example.com/blog")
        assert selected is None

    def test_select_backend_invalid_url(self, caplog):
        """Test handling of invalid URLs."""
        selector = BackendSelector()
        backend = Mock()
        criteria = BackendCriteria(priority=5)

        selector.register_backend(backend, criteria)

        with caplog.at_level(logging.ERROR):
            # Use a URL that will cause urlparse to fail
            selected = selector.select_backend("http://[invalid")
            assert selected is None
            assert "Error selecting backend for http://[invalid" in caplog.text

    def test_select_backend_exception_handling(self, monkeypatch, caplog):
        """Test that exceptions during backend selection are handled gracefully."""
        selector = BackendSelector()
        backend = Mock()
        criteria = BackendCriteria(priority=5)

        selector.register_backend(backend, criteria)

        # Mock urlparse to raise an exception
        def mock_urlparse_error(url):
            raise ValueError("Mocked error")

        monkeypatch.setattr("src.backend_selector.urlparse", mock_urlparse_error)

        with caplog.at_level(logging.ERROR):
            selected = selector.select_backend("https://example.com")
            assert selected is None
            assert "Error selecting backend for https://example.com" in caplog.text
            assert "Mocked error" in caplog.text
