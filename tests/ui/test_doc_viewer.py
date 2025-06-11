"""
Tests for the documentation viewer.
"""

import os
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src.ui.doc_viewer import DocViewerApp  # Ensure all needed classes are imported


@pytest.fixture
def mock_doc_organizer():
    """Mock document organizer."""
    mock = MagicMock()

    # Mock get_documents
    mock.get_documents.return_value = [
        MagicMock(
            title="Test Document",
            path="test/doc.html",
            url="https://example.com/test/doc.html",
            content_type="text/html",
            format="html",
            last_updated=datetime.now(),
            versions=[MagicMock(version="1.0.0"), MagicMock(version="1.1.0")],
            topics=["test", "example"],
            summary="Test document summary",
        )
    ]

    # Mock get_document
    mock.get_document.return_value = MagicMock(
        title="Test Document",
        path="test/doc.html",
        url="https://example.com/test/doc.html",
        content_type="text/html",
        format="html",
        content="<h1>Test Document</h1><p>This is a test document.</p>",
        last_updated=datetime.now(),
        versions=[MagicMock(version="1.0.0"), MagicMock(version="1.1.0")],
        topics=["test", "example"],
        summary="Test document summary",
    )

    # Mock search
    mock.search.return_value = [
        (
            MagicMock(
                title="Test Document",
                path="test/doc.html",
                url="https://example.com/test/doc.html",
                content_type="text/html",
                format="html",
                library="test-lib",
                version="1.0.0",
                topics=["test", "example"],
                summary="Test document summary",
            ),
            0.95,
            "<em>Test</em> document summary",
        )
    ]

    return mock


@pytest.fixture
def mock_version_tracker():
    """Mock version tracker."""
    mock = MagicMock()

    # Mock get_libraries
    mock.get_libraries.return_value = ["test-lib", "example-lib"]

    # Mock get_versions
    mock.get_versions.return_value = [
        MagicMock(
            version="1.0.0",
            release_date=datetime(2023, 1, 1),
            doc_url="https://example.com/docs/1.0.0",
            crawl_date=datetime.now(),
            changes={"added": 10, "removed": 5, "modified": 3},
        ),
        MagicMock(
            version="1.1.0",
            release_date=datetime(2023, 2, 1),
            doc_url="https://example.com/docs/1.1.0",
            crawl_date=datetime.now(),
            changes={"added": 5, "removed": 2, "modified": 8},
        ),
    ]

    # Mock diff_documents
    mock.diff_documents.return_value = "<div class='diff'>Diff content</div>"

    return mock


@pytest.fixture
def mock_format_handler():
    """Mock format handler."""
    mock = MagicMock()

    # Mock convert
    mock.convert.return_value = "<h1>Converted content</h1>"

    return mock


@pytest.fixture
def app(mock_doc_organizer, mock_version_tracker, mock_format_handler):
    """Create test app."""
    # Create temporary directories for templates and static files
    os.makedirs("test_templates", exist_ok=True)
    os.makedirs("test_static", exist_ok=True)

    # Create app
    app = DocViewerApp(
        doc_organizer=mock_doc_organizer,
        library_tracker=mock_version_tracker,  # Changed from version_tracker to library_tracker
        format_handler=mock_format_handler,
        templates_dir="test_templates",
        static_dir="test_static",
    )

    # Mock templates
    app.templates.TemplateResponse = MagicMock(return_value="Template response")

    return app


@pytest.fixture
def client(app):
    """Test client for the DocViewer app."""
    return TestClient(app.app)


@pytest.mark.asyncio
async def test_get_libraries(app):
    """Test getting libraries."""
    libraries = await app._get_libraries()
    assert libraries == ["test-lib", "example-lib"]
    app.library_tracker.get_libraries.assert_called_once()


@pytest.mark.asyncio
async def test_get_library_versions(app):
    """Test getting library versions."""
    versions = await app._get_library_versions("test-lib")
    assert len(versions) == 2
    assert versions[0].version == "1.0.0"
    assert versions[1].version == "1.1.0"
    app.library_tracker.get_versions.assert_called_once_with("test-lib")


@pytest.mark.asyncio
async def test_get_version_docs(app):
    """Test getting version documents."""
    docs = await app._get_version_docs("test-lib", "1.0.0")
    assert len(docs) == 1
    assert docs[0].title == "Test Document"
    app.doc_organizer.get_documents.assert_called_once_with("test-lib", "1.0.0")


@pytest.mark.asyncio
async def test_get_document(app):
    """Test getting a document."""
    doc = await app._get_document("test-lib", "1.0.0", "test/doc.html")
    assert doc is not None
    assert doc["title"] == "Test Document"
    assert doc["content"] == "<h1>Test Document</h1><p>This is a test document.</p>"
    app.doc_organizer.get_document.assert_called_once_with(
        "test-lib", "1.0.0", "test/doc.html"
    )


@pytest.mark.asyncio
async def test_get_diff(app):
    """Test getting a diff."""
    diff = await app._get_diff("test-lib", "test/doc.html", "1.0.0", "1.1.0")
    assert diff is not None
    assert diff["library"] == "test-lib"
    assert diff["version1"] == "1.0.0"
    assert diff["version2"] == "1.1.0"
    assert diff["diff"] == "<div class='diff'>Diff content</div>"
    app.library_tracker.diff_documents.assert_called_once()


@pytest.mark.asyncio
async def test_search(app):
    """Test searching."""
    results = await app._search("test", library="test-lib")
    assert len(results) == 1
    assert results[0]["title"] == "Test Document"
    assert results[0]["score"] == 0.95
    app.doc_organizer.search.assert_called_once_with(
        "test", library="test-lib", version=None, topics=None, content_type=None
    )


def test_api_libraries(client):
    """Test libraries API endpoint."""
    response = client.get("/api/libraries")
    assert response.status_code == 200
    data = response.json()
    assert "libraries" in data
    assert data["libraries"] == ["test-lib", "example-lib"]


def test_api_versions(client):
    """Test versions API endpoint."""
    response = client.get("/api/library/test-lib/versions")
    assert response.status_code == 200
    data = response.json()
    assert data["library"] == "test-lib"
    assert len(data["versions"]) == 2


def test_api_docs(client):
    """Test docs API endpoint."""
    response = client.get("/api/library/test-lib/version/1.0.0/docs")
    assert response.status_code == 200
    data = response.json()
    assert data["library"] == "test-lib"
    assert data["version"] == "1.0.0"
    assert len(data["docs"]) == 1


def test_api_diff(client):
    """Test diff API endpoint."""
    response = client.post(
        "/api/diff",
        json={
            "library": "test-lib",
            "doc_path": "test/doc.html",
            "version1": "1.0.0",
            "version2": "1.1.0",
            "format": "html",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["library"] == "test-lib"
    assert data["diff"] == "<div class='diff'>Diff content</div>"


def test_api_search(client):
    """Test search API endpoint."""
    response = client.post("/api/search", json={"query": "test", "library": "test-lib"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["title"] == "Test Document"
