"""Integration tests for DocViewerApp API endpoints using TestClient."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.ui.doc_viewer_complete import (
    DocViewer,  # Changed from DocViewerApp to DocViewer
)


@pytest.fixture
def mock_doc_organizer():
    """Create a mock DocOrganizer."""
    from src.organizers.doc_organizer import DocumentVersion

    mock = MagicMock()

    # Create mock version with proper structure
    mock_version = DocumentVersion(
        version_id="v1.0.0",
        timestamp=datetime.now(),
        hash="test_hash",
        changes={"content": {"formatted_content": "Test content for lib1"}},
    )

    # Mock document data with library name in URL
    mock.documents = {
        "doc1": MagicMock(
            title="Lib1 Documentation",
            url="http://example.com/lib1/docs/doc1.md",
            category="documentation",
            last_updated=datetime.now(),
            versions=[mock_version],
            tags=["lib1", "documentation"],
        )
    }

    # Mock get_document_versions method
    mock.get_document_versions.return_value = [mock_version]

    return mock


@pytest.fixture
def mock_library_tracker():
    """Create a mock LibraryVersionTracker."""
    mock = MagicMock()

    # Mock libraries list
    mock.get_libraries.return_value = ["lib1", "lib2"]

    # Mock versions list
    mock_version = MagicMock(
        version="1.0.0",
        release_date=datetime(2025, 1, 1),
        doc_url="http://example.com/docs/lib1/1.0.0",
        crawl_date=datetime.now(),
        changes={"summary": "Initial release", "details": []},
    )
    mock.get_versions.return_value = [mock_version]

    return mock


@pytest.fixture
def mock_format_handler():
    """Create a mock FormatHandler."""
    mock = MagicMock()
    mock.convert.return_value = (
        "<h1>Test Document 1</h1>\n<p>This is a test document.</p>"
    )
    return mock


@pytest.fixture
def docviewer_app(mock_doc_organizer, mock_library_tracker, mock_format_handler):
    """Create a DocViewerApp instance with mocked dependencies."""
    # Ensure os.path.exists returns True for template/static dirs to avoid errors
    with patch("os.path.exists", return_value=True):
        app_instance = DocViewer(  # Changed from DocViewerApp to DocViewer
            doc_organizer=mock_doc_organizer,
            library_tracker=mock_library_tracker,
            format_handler=mock_format_handler,
            templates_dir="test_templates",
            static_dir="test_static",
        )

    return app_instance


@pytest.fixture
def test_client(docviewer_app):
    """Create a test client for the DocViewerApp."""
    return TestClient(docviewer_app.app)


# API Endpoint Tests


def test_api_libraries(test_client, mock_library_tracker):
    """Test the /api/libraries endpoint."""
    response = test_client.get("/api/libraries")
    assert response.status_code == 200
    data = response.json()
    assert "libraries" in data
    assert isinstance(data["libraries"], list)


def test_api_library_versions(test_client, mock_library_tracker):
    """Test the /api/library/{library}/versions endpoint."""
    # Test successful request
    response = test_client.get("/api/library/lib1/versions")
    assert response.status_code == 200
    data = response.json()
    assert data["library"] == "lib1"
    assert "versions" in data

    # Test 404 for nonexistent library
    with patch(
        "src.ui.doc_viewer_complete.DocViewer._get_library_versions", return_value=[]
    ):  # Changed DocViewerApp to DocViewer
        response = test_client.get("/api/library/nonexistent/versions")
        assert response.status_code == 404


def test_api_library_version_docs(test_client, mock_doc_organizer):
    """Test the /api/library/{library}/version/{version}/docs endpoint."""
    # Test successful request
    response = test_client.get("/api/library/lib1/version/1.0.0/docs")
    assert response.status_code == 200
    data = response.json()
    assert data["library"] == "lib1"
    assert data["version"] == "1.0.0"
    assert "docs" in data

    # Test 404 for nonexistent version
    with patch(
        "src.ui.doc_viewer_complete.DocViewer._get_version_docs", return_value=[]
    ):  # Changed DocViewerApp to DocViewer
        response = test_client.get("/api/library/lib1/version/nonexistent/docs")
        assert response.status_code == 404


def test_api_diff(test_client):
    """Test the /api/diff endpoint."""
    # Test successful request
    diff_request = {
        "library": "lib1",
        "doc_path": "test/doc1.md",
        "version1": "1.0.0",
        "version2": "2.0.0",
        "format": "side_by_side",
    }

    with patch(
        "src.ui.doc_viewer_complete.DocViewer._get_diff",
        return_value={"diff_html": "<div class='diff'>Test diff content</div>"},
    ):
        response = test_client.post("/api/diff", json=diff_request)
        assert response.status_code == 200
        assert "diff_html" in response.json()

    # Test 404 for failed diff generation
    with patch("src.ui.doc_viewer_complete.DocViewer._get_diff", return_value=None):
        diff_request["library"] = "nonexistent"
        response = test_client.post("/api/diff", json=diff_request)
        assert response.status_code == 404


def test_api_search(test_client):
    """Test the /api/search endpoint."""
    # Test successful request
    search_request = {
        "query": "test",
        "library": "lib1",
        "version": "1.0.0",
        "topics": ["documentation"],
        "content_type": "text/markdown",
    }

    with patch(
        "src.ui.doc_viewer_complete.DocViewer._search",
        return_value=[
            {
                "title": "Search Result 1",
                "url": "http://example.com/test/result1.md",
                "snippet": "This is a <em>test</em> result snippet.",
                "score": 0.95,
            }
        ],
    ):
        response = test_client.post("/api/search", json=search_request)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) > 0

    # Test empty results
    with patch("src.ui.doc_viewer_complete.DocViewer._search", return_value=[]):
        search_request["query"] = "nonexistent"
        response = test_client.post("/api/search", json=search_request)
        assert response.status_code == 200
        assert response.json() == {"results": []}


# HTML Response Endpoint Tests


def test_home_page(test_client):
    """Test the home page endpoint."""
    response = test_client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_library_page(test_client):
    """Test the library page endpoint."""
    # Test successful request
    response = test_client.get("/library/lib1")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

    # Test 404 for nonexistent library
    with patch(
        "src.ui.doc_viewer_complete.DocViewer._get_library_versions", return_value=[]
    ):  # Changed DocViewerApp to DocViewer
        response = test_client.get("/library/nonexistent")
        assert response.status_code == 404


def test_version_page(test_client):
    """Test the version page endpoint."""
    # Test successful request
    response = test_client.get("/library/lib1/version/1.0.0")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

    # Test 404 for nonexistent version
    with patch(
        "src.ui.doc_viewer_complete.DocViewer._get_version_docs", return_value=[]
    ):  # Changed DocViewerApp to DocViewer
        response = test_client.get("/library/lib1/version/nonexistent")
        assert response.status_code == 404


def test_document_page(test_client):
    """Test the document page endpoint."""
    # Test successful request - use path that matches our mock document URL
    response = test_client.get("/library/lib1/version/1.0.0/doc/docs/doc1.md")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

    # Test 404 for nonexistent document
    with patch(
        "src.ui.doc_viewer_complete.DocViewer._get_document", return_value=None
    ):  # Changed DocViewerApp to DocViewer
        response = test_client.get("/library/lib1/version/1.0.0/doc/nonexistent.md")
        assert response.status_code == 404


def test_diff_page(test_client):
    """Test the diff page endpoint."""
    response = test_client.get("/diff")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_search_page(test_client):
    """Test the search page endpoint."""
    response = test_client.get("/search")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
