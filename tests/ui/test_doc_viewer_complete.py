"""Tests for the doc_viewer_complete module."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import fastapi  # Ensure fastapi is imported
import pytest
from fastapi.testclient import TestClient

from src.ui.doc_viewer_complete import (
    DocViewer,
    DocViewerConfig,
)
from src.ui.doc_viewer_complete import (
    app as doc_viewer_app,
)


@pytest.fixture
def doc_viewer():
    """Create a test instance of DocViewer."""
    config = DocViewerConfig()
    doc_organizer_mock = MagicMock()
    library_tracker_mock = MagicMock()
    format_handler_mock = MagicMock()

    # Create a DocViewer instance with the correct parameters
    viewer = DocViewer(
        config=config,
        doc_organizer=doc_organizer_mock,
        library_tracker=library_tracker_mock,
        format_handler=format_handler_mock,
        templates_dir="test_templates",
        static_dir="test_static",
    )

    # Add attributes needed for tests
    viewer.config.docs_dir = "test_docs_dir"

    # Set up the mocks to return test values
    doc_organizer_mock.get_document_list.return_value = [
        {"id": "doc1", "title": "Document 1", "updated": datetime.now()}
    ]

    doc_organizer_mock.get_document.return_value = {
        "id": "doc1",
        "title": "Document 1",
        "content": "Test content",
        "format": "markdown",
    }

    library_tracker_mock.get_version_history.return_value = [
        {"version": "1.0.0", "date": datetime.now()}
    ]

    # Set the version_tracker attribute
    viewer.version_tracker = library_tracker_mock

    return viewer


@pytest.fixture
def test_client(doc_viewer):
    """Create a test client for the FastAPI app."""
    # Use the existing app instance
    return TestClient(doc_viewer_app)


def test_docviewer_init(doc_viewer):
    """Test DocViewer initialization."""
    assert doc_viewer.templates_dir == "test_templates"
    assert doc_viewer.static_dir == "test_static"


def test_get_app():
    """Test app instance."""
    # Test the existing app instance
    assert doc_viewer_app is not None
    assert isinstance(doc_viewer_app, fastapi.FastAPI)


@patch("os.path.exists")
def test_docviewer_get_document_list(mock_exists, doc_viewer):
    """Test get_document_list method."""
    mock_exists.return_value = True

    # The mock is already set up in the fixture
    result = doc_viewer.get_document_list()
    assert len(result) == 1
    assert result[0]["id"] == "doc1"


@patch("os.path.exists")
def test_docviewer_get_document(mock_exists, doc_viewer):
    """Test get_document method."""
    mock_exists.return_value = True

    # The mock is already set up in the fixture
    result = doc_viewer.get_document("doc1")
    assert result["id"] == "doc1"
    assert result["content"] == "Test content"


@patch("os.path.exists")
def test_docviewer_get_version_history(mock_exists, doc_viewer):
    """Test get_version_history method."""
    mock_exists.return_value = True

    # The mock is already set up in the fixture
    result = doc_viewer.get_version_history("doc1")
    assert len(result) == 1
    assert result[0]["version"] == "1.0.0"
