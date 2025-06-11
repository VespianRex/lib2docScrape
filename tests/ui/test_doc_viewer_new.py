"""
Tests for the document viewer UI module.
"""

from unittest.mock import MagicMock, patch

import pytest

# Use DocViewer from doc_viewer_complete
from src.ui.doc_viewer_complete import DocViewer


def test_doc_viewer_app_initialization():
    """Test DocViewer initialization."""
    # Create mock dependencies
    mock_doc_organizer = MagicMock()
    mock_library_tracker = MagicMock()  # Renamed from version_tracker
    mock_format_handler = MagicMock()

    # Initialize DocViewer
    app = DocViewer(
        doc_organizer=mock_doc_organizer,
        library_tracker=mock_library_tracker,  # Use library_tracker
        format_handler=mock_format_handler,
        templates_dir="test_templates",
        static_dir="test_static",
    )

    # Verify initialization
    assert app.doc_organizer == mock_doc_organizer
    assert app.library_tracker == mock_library_tracker  # Check library_tracker
    assert app.format_handler == mock_format_handler
    assert app.app is not None


@patch("src.ui.doc_viewer_complete.DocumentOrganizer")
@patch("src.ui.doc_viewer_complete.LibraryVersionTracker")
@patch("src.ui.doc_viewer_complete.FormatHandler")
def test_doc_viewer_app_default_dependencies(
    MockFormatHandler, MockLibraryVersionTracker, MockDocumentOrganizer
):
    """Test DocViewer with default dependencies."""
    # Initialize DocViewer with default dependencies
    # Provide dummy directories to satisfy Jinja2Templates and StaticFiles
    app = DocViewer(templates_dir="dummy_templates", static_dir="dummy_static")

    # Verify default dependencies were created
    assert app.doc_organizer is not None
    assert app.library_tracker is not None
    assert app.format_handler is not None
    assert app.app is not None
    assert app.templates is not None
    MockDocumentOrganizer.assert_called_once()
    MockLibraryVersionTracker.assert_called_once()
    MockFormatHandler.assert_called_once()


@patch("src.ui.doc_viewer_complete.Jinja2Templates")
def test_doc_viewer_app_templates(mock_templates):
    """Test DocViewer templates setup."""
    mock_template_instance = MagicMock()
    mock_templates.return_value = mock_template_instance

    # Initialize DocViewer
    app = DocViewer(templates_dir="test_templates", static_dir="test_static")

    # Verify templates were set up
    assert app.templates is mock_template_instance
    mock_templates.assert_called_once_with(directory="test_templates")


@patch("src.ui.doc_viewer_complete.StaticFiles")
@patch("os.path.exists", return_value=True)  # Mock os.path.exists
@patch("os.makedirs")  # Mock os.makedirs
def test_doc_viewer_app_static_files(mock_makedirs, mock_exists, mock_static_files):
    """Test DocViewer static files setup."""
    mock_static_instance = MagicMock()
    mock_static_files.return_value = mock_static_instance

    # Initialize DocViewer
    DocViewer(static_dir="test_static", templates_dir="test_templates")

    # Verify static files were mounted on the app
    # The app should have mount called during initialization
    mock_static_files.assert_called_once_with(directory="test_static")


@patch("os.path.exists", return_value=True)  # Mock os.path.exists
@patch("os.makedirs")  # Mock os.makedirs
def test_doc_viewer_app_routes(mock_makedirs, mock_exists):
    """Test that the DocViewer registers routes."""
    # Initialize DocViewer
    app = DocViewer(templates_dir="test_templates", static_dir="test_static")
    # Check that routes were registered (FastAPI registers routes upon decorator evaluation)
    # We can check if the app's router has routes.
    assert len(app.app.router.routes) > 0


@patch("os.path.exists", return_value=True)  # Mock os.path.exists
@patch("os.makedirs")  # Mock os.makedirs
def test_doc_viewer_app_api_routes(mock_makedirs, mock_exists):
    """Test that the DocViewer registers API routes."""
    # Initialize DocViewer
    app = DocViewer(templates_dir="test_templates", static_dir="test_static")

    api_routes_found = any(
        "/api/" in route.path
        for route in app.app.router.routes
        if hasattr(route, "path")
    )
    assert api_routes_found


@pytest.mark.asyncio
async def test_doc_viewer_app_get_libraries():
    """Test getting libraries from DocViewer."""
    # Create mock library tracker
    mock_library_tracker = MagicMock()
    mock_library_tracker.get_libraries.return_value = ["lib1", "lib2", "lib3"]

    # Initialize DocViewer with mock library tracker
    app = DocViewer(
        library_tracker=mock_library_tracker,
        templates_dir="test_templates",
        static_dir="test_static",
    )

    # Call the method
    libraries = await app._get_libraries()

    # Verify results
    assert libraries == ["lib1", "lib2", "lib3"]
    mock_library_tracker.get_libraries.assert_called_once()
