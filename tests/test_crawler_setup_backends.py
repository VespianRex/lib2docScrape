# tests/test_crawler_setup_backends.py

from unittest.mock import Mock

import pytest

from src.backends.http_backend import HTTPBackend
from src.backends.selector import BackendCriteria, BackendSelector

# Import the DocumentationCrawler class from the old module for testing
from src.crawler import CrawlerConfig, DocumentationCrawler


def test_setup_backends_no_exception():
    """Test 13.1: Execution without Error"""
    crawler = DocumentationCrawler(config=CrawlerConfig(use_duckduckgo=False))
    try:
        crawler._setup_backends()
    except Exception as e:
        pytest.fail(f"_setup_backends raised an exception: {e}")


def test_setup_backends_registers_http_backend():
    """Test that _setup_backends registers an HTTP backend with the selector."""
    # Create a mock BackendSelector
    mock_selector = Mock(spec=BackendSelector)

    # Create a crawler with the mock selector
    crawler = DocumentationCrawler(backend_selector=mock_selector)

    # Call the method
    crawler._setup_backends()

    # Verify the backend_selector.register_backend was called
    mock_selector.register_backend.assert_called()

    # Get the keyword arguments from the call
    kwargs = mock_selector.register_backend.call_args[1]

    # Check that the backend is an HTTPBackend
    assert isinstance(kwargs["backend"], HTTPBackend)

    # Check that the criteria is a BackendCriteria with expected values
    assert isinstance(kwargs["criteria"], BackendCriteria)
    assert kwargs["criteria"].priority == 1
    assert "text/html" in kwargs["criteria"].content_types
    assert "http://" in kwargs["criteria"].url_patterns
    assert "https://" in kwargs["criteria"].url_patterns


def test_setup_backends_with_custom_config():
    """Test that _setup_backends uses the crawler's config for the HTTP backend."""
    # Create a crawler with custom config
    from src.crawler import CrawlerConfig

    custom_config = CrawlerConfig(
        request_timeout=60.0,
        verify_ssl=False,
        follow_redirects=False,
        headers={"User-Agent": "CustomAgent/1.0"},
    )

    # Create a mock BackendSelector
    mock_selector = Mock(spec=BackendSelector)

    # Create a crawler with the mock selector and custom config
    crawler = DocumentationCrawler(config=custom_config, backend_selector=mock_selector)

    # Call the method
    crawler._setup_backends()

    # Verify the backend_selector.register_backend was called
    mock_selector.register_backend.assert_called()

    # Get the keyword arguments from the call
    kwargs = mock_selector.register_backend.call_args[1]

    # Check that the backend is an HTTPBackend with the expected config
    assert isinstance(kwargs["backend"], HTTPBackend)
    http_backend = kwargs["backend"]

    # Check that the HTTP backend was configured with our custom values
    assert http_backend.config.timeout == 60.0
    assert http_backend.config.verify_ssl is False
    assert http_backend.config.follow_redirects is False
    assert http_backend.config.headers["User-Agent"] == "CustomAgent/1.0"
