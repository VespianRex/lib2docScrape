"""Tests for CrawlConfig model."""

import pytest
from pydantic import ValidationError

from src.crawler.models import CrawlConfig


def test_crawl_config_default_instantiation():
    """Test default instantiation of CrawlConfig model."""
    config = CrawlConfig()

    # Check default values
    assert config.max_depth == 3
    assert config.max_pages == 1000
    assert config.follow_external is False
    assert config.content_types == ["text/html"]
    assert config.exclude_patterns == []
    assert config.include_patterns == []
    assert config.rate_limit == 0.5
    assert config.timeout == 30
    assert config.retry_count == 3
    assert config.user_agent == "lib2docScrape/1.0"


def test_crawl_config_custom_values():
    """Test setting and getting custom values for CrawlConfig model."""
    custom_values = {
        "max_depth": 5,
        "max_pages": 100,
        "follow_external": True,
        "content_types": ["text/html", "text/plain"],
        "exclude_patterns": ["/api/", "/internal/"],
        "include_patterns": ["/docs/"],
        "rate_limit": 2.0,
        "timeout": 60,
        "retry_count": 5,
        "user_agent": "Custom User Agent",
    }

    config = CrawlConfig(**custom_values)

    # Verify all custom values are set correctly
    assert config.max_depth == 5
    assert config.max_pages == 100
    assert config.follow_external is True
    assert config.content_types == ["text/html", "text/plain"]
    assert config.exclude_patterns == ["/api/", "/internal/"]
    assert config.include_patterns == ["/docs/"]
    assert config.rate_limit == 2.0
    assert config.timeout == 60
    assert config.retry_count == 5
    assert config.user_agent == "Custom User Agent"


def test_crawl_config_validation_errors():
    """Test validation errors in CrawlConfig model."""
    # Test invalid types
    with pytest.raises(ValidationError) as excinfo:
        CrawlConfig(max_depth="not_an_int")
    assert "Input should be" in str(excinfo.value)

    with pytest.raises(ValidationError) as excinfo:
        CrawlConfig(content_types="not_a_list")
    assert "Input should be a valid list" in str(excinfo.value)

    with pytest.raises(ValidationError) as excinfo:
        CrawlConfig(follow_external="not_a_bool")
    assert "Input should be" in str(excinfo.value)

    with pytest.raises(ValidationError) as excinfo:
        CrawlConfig(timeout="not_an_int")
    assert "Input should be" in str(excinfo.value)
