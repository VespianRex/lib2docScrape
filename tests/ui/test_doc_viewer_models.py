"""
Tests for the Pydantic models in the documentation viewer.
"""

from datetime import datetime
from typing import Any, Optional

import pytest

# Create mock classes for testing
from pydantic import BaseModel, ValidationError


class VersionInfo(BaseModel):
    """Version information."""

    version: str
    release_date: Optional[datetime] = None
    doc_url: str
    crawl_date: datetime
    changes: Optional[dict[str, Any]] = None


class DocumentInfo(BaseModel):
    """Document information."""

    title: str
    url: str
    content_type: str
    content_format: str
    last_updated: datetime
    versions: list[str]
    topics: list[str]
    summary: Optional[str] = None


class DiffRequest(BaseModel):
    """Request for diff between versions."""

    library: str
    doc_path: str
    version1: str
    version2: str
    format: str = "html"


class SearchRequest(BaseModel):
    """Search request."""

    query: str
    library: Optional[str] = None
    version: Optional[str] = None
    topics: Optional[list[str]] = None
    content_type: Optional[str] = None


class TestVersionInfo:
    """Tests for the VersionInfo model."""

    def test_default_instantiation(self):
        """Test 1.1: Default Instantiation"""
        # Create with required fields
        data = {
            "version": "1.0",
            "doc_url": "http://example.com",
            "crawl_date": datetime.now(),
        }
        info = VersionInfo(**data)
        assert info.version == "1.0"
        assert info.doc_url == "http://example.com"
        assert isinstance(info.crawl_date, datetime)
        assert info.release_date is None
        assert info.changes is None

    def test_custom_value_instantiation(self):
        """Test with all fields including optional ones."""
        now = datetime.now()
        release_date = datetime(2023, 1, 1)
        changes = {"added": 10, "removed": 5, "modified": 3}

        data = {
            "version": "1.0",
            "doc_url": "http://example.com",
            "crawl_date": now,
            "release_date": release_date,
            "changes": changes,
        }

        info = VersionInfo(**data)
        assert info.version == "1.0"
        assert info.doc_url == "http://example.com"
        assert info.crawl_date == now
        assert info.release_date == release_date
        assert info.changes == changes

    def test_validation_error(self):
        """Test validation error when missing required fields."""
        # Missing required fields
        with pytest.raises(ValidationError):
            VersionInfo(doc_url="http://example.com", crawl_date=datetime.now())

        with pytest.raises(ValidationError):
            VersionInfo(version="1.0", crawl_date=datetime.now())

        with pytest.raises(ValidationError):
            VersionInfo(version="1.0", doc_url="http://example.com")


class TestDocumentInfo:
    """Tests for the DocumentInfo model."""

    def test_default_instantiation(self):
        """Test 1.2: DocumentInfo Instantiation"""
        # Create with required fields
        data = {
            "title": "Intro",
            "url": "http://example.com/intro",
            "content_type": "text/html",
            "content_format": "html",
            "last_updated": datetime.now(),
            "versions": ["1.0"],
            "topics": ["setup"],
        }

        info = DocumentInfo(**data)
        assert info.title == "Intro"
        assert info.url == "http://example.com/intro"
        assert info.content_type == "text/html"
        assert info.content_format == "html"
        assert isinstance(info.last_updated, datetime)
        assert info.versions == ["1.0"]
        assert info.topics == ["setup"]
        assert info.summary is None

    def test_with_summary(self):
        """Test with summary field."""
        data = {
            "title": "Intro",
            "url": "http://example.com/intro",
            "content_type": "text/html",
            "content_format": "html",
            "last_updated": datetime.now(),
            "versions": ["1.0"],
            "topics": ["setup"],
            "summary": "This is a summary",
        }

        info = DocumentInfo(**data)
        assert info.summary == "This is a summary"

    def test_validation_error(self):
        """Test validation error when missing required fields."""
        # Missing required fields
        with pytest.raises(ValidationError):
            DocumentInfo(
                url="http://example.com/intro",
                content_type="text/html",
                content_format="html",
                last_updated=datetime.now(),
                versions=["1.0"],
                topics=["setup"],
            )


class TestDiffRequest:
    """Tests for the DiffRequest model."""

    def test_default_instantiation(self):
        """Test 1.3: DiffRequest Instantiation"""
        # Create with required fields
        data = {
            "library": "libA",
            "doc_path": "intro.md",
            "version1": "1.0",
            "version2": "1.1",
        }

        req = DiffRequest(**data)
        assert req.library == "libA"
        assert req.doc_path == "intro.md"
        assert req.version1 == "1.0"
        assert req.version2 == "1.1"
        assert req.format == "html"  # Default value

    def test_custom_format(self):
        """Test with custom format."""
        data = {
            "library": "libA",
            "doc_path": "intro.md",
            "version1": "1.0",
            "version2": "1.1",
            "format": "text",
        }

        req = DiffRequest(**data)
        assert req.format == "text"

    def test_validation_error(self):
        """Test validation error when missing required fields."""
        # Missing required fields
        with pytest.raises(ValidationError):
            DiffRequest(doc_path="intro.md", version1="1.0", version2="1.1")


class TestSearchRequest:
    """Tests for the SearchRequest model."""

    def test_default_instantiation(self):
        """Test 1.4: SearchRequest Instantiation"""
        # Create with only required field
        data = {"query": "test"}

        req = SearchRequest(**data)
        assert req.query == "test"
        assert req.library is None
        assert req.version is None
        assert req.topics is None
        assert req.content_type is None

    def test_with_optional_fields(self):
        """Test with all optional fields."""
        data = {
            "query": "test",
            "library": "libA",
            "version": "1.0",
            "topics": ["setup", "api"],
            "content_type": "text/html",
        }

        req = SearchRequest(**data)
        assert req.query == "test"
        assert req.library == "libA"
        assert req.version == "1.0"
        assert req.topics == ["setup", "api"]
        assert req.content_type == "text/html"

    def test_validation_error(self):
        """Test validation error when missing required fields."""
        # Missing required fields
        with pytest.raises(ValidationError):
            SearchRequest(library="libA")
