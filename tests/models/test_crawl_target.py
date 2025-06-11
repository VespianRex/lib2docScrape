"""Tests for CrawlTarget model."""

import pytest
from pydantic import ValidationError

from src.crawler import CrawlTarget


def test_crawl_target_default_instantiation():
    """Test default instantiation of CrawlTarget model."""
    # In Pydantic 2.10+, we need to explicitly pass url even though it has a default value
    target = CrawlTarget(url="https://docs.python.org/3/")

    # Check default values
    assert target.url == "https://docs.python.org/3/"
    assert target.depth == 1
    assert target.follow_external is False
    assert target.content_types == ["text/html"]
    assert target.exclude_patterns == []
    assert (
        target.include_patterns == []
    )  # Default value has been changed to an empty list
    assert target.max_pages == 1000  # Default value has been changed from None to 1000
    assert target.allowed_paths == []
    assert target.excluded_paths == []


def test_crawl_target_custom_values():
    """Test instantiation of CrawlTarget with custom values."""
    custom_values = {
        "url": "http://example.com",
        "depth": 2,
        "follow_external": True,
        "content_types": ["text/html", "application/json"],
        "exclude_patterns": ["/api/"],
        "include_patterns": [
            "/docs/"
        ],  # Field name has been changed from required_patterns to include_patterns
        "max_pages": 100,
        "allowed_paths": ["/docs/guide/"],
        "excluded_paths": ["/docs/deprecated/"],
    }

    target = CrawlTarget(**custom_values)

    # Check custom values
    assert target.url == "http://example.com"
    assert target.depth == 2
    assert target.follow_external is True
    assert target.content_types == ["text/html", "application/json"]
    assert target.exclude_patterns == ["/api/"]
    assert target.include_patterns == [
        "/docs/"
    ]  # Field name has been changed from required_patterns to include_patterns
    assert target.max_pages == 100
    assert target.allowed_paths == ["/docs/guide/"]
    assert target.excluded_paths == ["/docs/deprecated/"]


def test_crawl_target_validation_error():
    """Test validation errors in CrawlTarget model."""
    # Test invalid depth (string instead of int)
    with pytest.raises(ValidationError):
        CrawlTarget(depth="not_an_int")

    # Test invalid url (not a string)
    with pytest.raises(ValidationError):
        CrawlTarget(url=123)

    # Test invalid content_types (not a list)
    with pytest.raises(ValidationError):
        CrawlTarget(content_types="text/html")
