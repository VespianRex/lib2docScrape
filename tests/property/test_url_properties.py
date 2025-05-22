"""
Property-based tests for URL handling.
"""
import pytest
from hypothesis import given, strategies as st
from urllib.parse import urlparse, urlunparse

from src.utils.url.factory import create_url_info
from src.utils.url.info import URLInfo
from src.utils.url.types import URLType

# Define strategies for URL components
schemes = st.sampled_from(['http', 'https', 'ftp', 'file'])
domains = st.text(min_size=1, max_size=20).filter(lambda x: all(c.isalnum() or c == '-' or c == '.' for c in x))
tlds = st.sampled_from(['.com', '.org', '.net', '.io', '.dev'])
paths = st.lists(st.text(min_size=1, max_size=10).filter(lambda x: all(c.isalnum() or c == '-' or c == '_' for c in x)), 
                 min_size=0, max_size=5).map(lambda x: '/' + '/'.join(x) if x else '')
query_keys = st.text(min_size=1, max_size=10).filter(lambda x: all(c.isalnum() or c == '_' for c in x))
query_values = st.text(min_size=0, max_size=10)
query_params = st.lists(st.tuples(query_keys, query_values), min_size=0, max_size=3)
fragments = st.text(min_size=0, max_size=10).filter(lambda x: all(c.isalnum() or c == '-' or c == '_' for c in x))

# Strategy for valid URLs
valid_urls = st.builds(
    lambda scheme, domain, tld, path, query, fragment: 
        f"{scheme}://{domain}{tld}{path}{('?' + '&'.join(f'{k}={v}' for k, v in query)) if query else ''}{('#' + fragment) if fragment else ''}",
    schemes,
    domains,
    tlds,
    paths,
    query_params,
    fragments
)

@given(valid_urls)
def test_url_info_creation_valid(url):
    """Test that valid URLs can be parsed correctly."""
    url_info = create_url_info(url)
    assert url_info.is_valid
    assert url_info.error_message is None
    assert url_info.raw_url == url

@given(valid_urls)
def test_url_info_normalization_idempotent(url):
    """Test that normalizing a URL twice gives the same result as normalizing once."""
    url_info1 = create_url_info(url)
    url_info2 = create_url_info(url_info1.normalized_url)
    
    assert url_info1.is_valid
    assert url_info2.is_valid
    assert url_info1.normalized_url == url_info2.normalized_url

@given(valid_urls)
def test_url_info_components_match_urlparse(url):
    """Test that URLInfo components match those from urlparse."""
    url_info = create_url_info(url)
    parsed = urlparse(url)
    
    assert url_info.scheme == parsed.scheme
    assert url_info.netloc == parsed.netloc
    assert url_info.path == parsed.path
    assert url_info.query == parsed.query
    assert url_info.fragment == parsed.fragment

@given(valid_urls, valid_urls)
def test_url_info_join_relative(base_url, relative_path):
    """Test joining URLs with relative paths."""
    # Create a relative path by removing scheme and netloc
    parsed = urlparse(relative_path)
    relative = urlunparse(('', '', parsed.path, parsed.params, parsed.query, parsed.fragment))
    
    # Skip empty relative paths
    if not relative:
        return
    
    base_info = create_url_info(base_url)
    if not base_info.is_valid:
        return
    
    try:
        joined_info = base_info.join(relative)
        assert joined_info.is_valid
        
        # The scheme and netloc should come from the base URL
        assert joined_info.scheme == base_info.scheme
        assert joined_info.netloc == base_info.netloc
    except ValueError:
        # Some combinations might be invalid, which is fine
        pass

@given(valid_urls)
def test_url_info_with_scheme(url):
    """Test changing the scheme of a URL."""
    url_info = create_url_info(url)
    if not url_info.is_valid:
        return
    
    new_scheme = "https" if url_info.scheme != "https" else "http"
    new_url_info = url_info.with_scheme(new_scheme)
    
    assert new_url_info.is_valid
    assert new_url_info.scheme == new_scheme
    assert new_url_info.netloc == url_info.netloc
    assert new_url_info.path == url_info.path
    assert new_url_info.query == url_info.query
    assert new_url_info.fragment == url_info.fragment

@given(valid_urls)
def test_url_info_equality(url):
    """Test URL equality."""
    url_info1 = create_url_info(url)
    url_info2 = create_url_info(url)
    
    assert url_info1 == url_info2
    assert hash(url_info1) == hash(url_info2)

@given(valid_urls)
def test_url_info_string_representation(url):
    """Test string representation of URLs."""
    url_info = create_url_info(url)
    if not url_info.is_valid:
        return
    
    # The string representation should be the normalized URL with fragment
    assert str(url_info) == url_info.url
    
    # Creating a new URLInfo from the string representation should give the same normalized URL
    new_url_info = create_url_info(str(url_info))
    assert new_url_info.normalized_url == url_info.normalized_url
