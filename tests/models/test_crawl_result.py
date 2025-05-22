"""Tests for CrawlResult model."""

import pytest
from pydantic import ValidationError
from src.crawler.models import CrawlResult, CrawlTarget, CrawlStats, QualityIssue
from datetime import datetime, timezone

# Mock data for testing
mock_target = CrawlTarget(url="http://example.com")
mock_stats = CrawlStats()

def test_crawl_result_default_instantiation():
    """Test 3.1: Instantiation with Required Fields and default factory usage."""
    result = CrawlResult(
        target=mock_target,
        stats=mock_stats,
        documents=[],
        issues=[],
        metrics={}
    )
    assert result.target == mock_target
    assert result.stats == mock_stats
    assert result.documents == []
    assert result.issues == []
    assert isinstance(result.metrics, dict)
    assert result.failed_urls == []  # Check default factory
    assert result.errors == {}       # Check default factory
    assert result.processed_url is None

def test_crawl_result_custom_values():
    """Test instantiation with all fields, including optional ones."""
    doc1 = {"url": "http://example.com/doc1", "title": "Doc 1", "content": "Content 1", "content_type": "text/html", "depth": 1}
    
    # Fixed issue1 to include required level field
    issue1 = QualityIssue(type="general", level="warning", message="Issue 1")
    
    metrics_data = {"total_urls_processed": 10, "http_status_counts": {200: 5, 404: 1}}
    
    exception_obj = ValueError("A test error occurred")
    
    result = CrawlResult(
        target=mock_target,
        stats=mock_stats,
        documents=[doc1],
        issues=[issue1],
        metrics=metrics_data,
        # Fixed structure to be a list instead of a dict
        structure=[{"type": "root", "children": []}],
        processed_url="http://example.com/processed",
        failed_urls=["http://example.com/failed"],
        errors={"http://example.com/error": exception_obj},
        # Fixed crawled_pages to be a dict instead of an int
        crawled_pages={"http://example.com": {"status": 200}}
    )
    assert result.documents == [doc1]
    assert result.issues[0].message == "Issue 1"
    assert result.issues[0].level == "warning"
    assert result.metrics["total_urls_processed"] == 10
    assert result.failed_urls == ["http://example.com/failed"]
    assert result.errors == {"http://example.com/error": exception_obj}
    assert isinstance(result.crawled_pages, dict)
    assert isinstance(result.structure, list)
    assert len(result.structure) == 1
    assert result.structure[0]["type"] == "root"
    assert result.processed_url == "http://example.com/processed"

def test_crawl_result_arbitrary_types_allowed_for_errors():
    """Test 3.2: `arbitrary_types_allowed` for `Exception` in `errors`."""
    my_exception = ValueError("Test error for arbitrary type")
    result = CrawlResult(
        target=mock_target,
        stats=mock_stats,
        documents=[],
        issues=[],
        metrics={},
        errors={"http://example.com/exception_url": my_exception}
    )
    assert result.errors["http://example.com/exception_url"] == my_exception
    assert isinstance(result.errors["http://example.com/exception_url"], ValueError)

def test_crawl_result_pydantic_validation_missing_required():
    """Test Pydantic validation for missing required fields."""
    with pytest.raises(ValidationError) as excinfo:
        CrawlResult(target=mock_target, documents=[]) # Missing stats, issues, metrics
    
    error_str = str(excinfo.value)
    assert "validation errors for CrawlResult" in error_str
    assert "stats" in error_str
    assert "issues" in error_str
    assert "metrics" in error_str

def test_crawl_result_pydantic_validation_invalid_type():
    """Test Pydantic validation for invalid field types."""
    with pytest.raises(ValidationError) as excinfo:
        CrawlResult(
            target=mock_target,
            stats=mock_stats,
            documents="not_a_list", # Invalid type
            issues=[],
            metrics={}
        )
    assert "Input should be a valid list" in str(excinfo.value)
    assert "documents" in str(excinfo.value)

    with pytest.raises(ValidationError) as excinfo:
         CrawlResult(
            target=mock_target,
            stats="not_crawl_stats", # Invalid type
            documents=[], 
            issues=[],
            metrics={}
        )
    assert "Input should be a valid instance of CrawlStats" in str(excinfo.value)
    assert "stats" in str(excinfo.value)
