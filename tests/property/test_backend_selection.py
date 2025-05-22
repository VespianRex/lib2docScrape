"""
Property-based tests for backend selection.
"""
import pytest
from hypothesis import given, strategies as st
from unittest.mock import MagicMock, AsyncMock
import asyncio

from src.backends.selector import BackendSelector, BackendCriteria
from src.backends.base import CrawlerBackend

# Define strategies for backend criteria
priorities = st.integers(min_value=1, max_value=100)
content_types = st.lists(
    st.sampled_from(['text/html', 'text/plain', 'application/json', 'application/xml', 'text/*', '*/*']),
    min_size=1,
    max_size=3
)
url_patterns = st.lists(
    st.sampled_from(['*example.com*', '*docs*', '*api*', '*github*', '*']),
    min_size=1,
    max_size=3
)
schemes = st.lists(
    st.sampled_from(['http', 'https', 'ftp', 'file']),
    min_size=1,
    max_size=4
)
domains = st.lists(
    st.sampled_from(['example.com', 'docs.example.com', 'api.example.com', 'github.com']),
    min_size=0,
    max_size=3
)
paths = st.lists(
    st.sampled_from(['/docs', '/api', '/reference', '/guide']),
    min_size=0,
    max_size=3
)

# Strategy for backend criteria
backend_criteria = st.builds(
    BackendCriteria,
    priority=priorities,
    content_types=content_types,
    url_patterns=url_patterns,
    schemes=schemes,
    domains=domains,
    paths=paths
)

# Strategy for URLs
urls = st.sampled_from([
    'https://example.com',
    'https://docs.example.com',
    'https://api.example.com',
    'https://example.com/docs',
    'https://example.com/api',
    'https://github.com',
    'http://example.org'
])

# Strategy for content types
content_type_values = st.sampled_from([
    'text/html',
    'application/json',
    'text/plain',
    None
])

class MockBackend(CrawlerBackend):
    """Mock backend for testing."""
    
    def __init__(self, name):
        super().__init__(name=name)
        self.crawl = AsyncMock()
        self.validate = AsyncMock(return_value=True)
        self.process = AsyncMock(return_value={})

@given(st.lists(backend_criteria, min_size=1, max_size=5), urls, content_type_values)
def test_backend_selection_properties(criteria_list, url, content_type):
    """Test properties of backend selection."""
    selector = BackendSelector()
    
    # Register backends with criteria
    backends = []
    for i, criteria in enumerate(criteria_list):
        backend = MockBackend(f"backend{i}")
        selector.register_backend(f"backend{i}", backend, criteria)
        backends.append(backend)
    
    # Select a backend
    selected = selector.select_backend_for_url(url, content_type)
    
    # If a backend was selected, it should be one of the registered backends
    if selected is not None:
        assert selected in backends
        
        # The selected backend should have criteria that match the URL
        backend_name = selected.name
        backend_criteria = selector.criteria[backend_name]
        
        # Check that the URL matches the criteria
        parsed_url = url.split('://', 1)[1] if '://' in url else url
        domain = parsed_url.split('/', 1)[0] if '/' in parsed_url else parsed_url
        
        # If domains are specified, the URL domain should match one of them
        if backend_criteria.domains:
            assert domain in backend_criteria.domains or any(domain.endswith(f".{d}") for d in backend_criteria.domains)
        
        # If content_type is specified, it should match one of the backend's content types
        if content_type and backend_criteria.content_types:
            assert content_type in backend_criteria.content_types or any(
                ct.endswith('*') and content_type.startswith(ct[:-1]) 
                for ct in backend_criteria.content_types
            )

@given(st.lists(backend_criteria, min_size=2, max_size=5), urls)
def test_backend_selection_priority(criteria_list, url):
    """Test that backend selection respects priority."""
    selector = BackendSelector()
    
    # Sort criteria by priority (highest first)
    sorted_criteria = sorted(criteria_list, key=lambda c: c.priority, reverse=True)
    
    # Register backends with criteria
    for i, criteria in enumerate(sorted_criteria):
        # Make all backends match all URLs by setting url_patterns to ['*']
        criteria.url_patterns = ['*']
        backend = MockBackend(f"backend{i}")
        selector.register_backend(f"backend{i}", backend, criteria)
    
    # Select a backend
    selected = selector.select_backend_for_url(url)
    
    # The selected backend should be the one with the highest priority
    if selected is not None:
        assert selected.name == "backend0"

@given(backend_criteria)
def test_backend_criteria_validation(criteria):
    """Test that backend criteria validation works correctly."""
    # Validation should happen automatically when the BackendCriteria is created
    assert isinstance(criteria.priority, int)
    assert all(isinstance(ct, str) for ct in criteria.content_types)
    assert all(isinstance(up, str) for up in criteria.url_patterns)
    assert all(isinstance(s, str) for s in criteria.schemes)
    assert all(isinstance(d, str) for d in criteria.domains)
    assert all(isinstance(p, str) for p in criteria.paths)
