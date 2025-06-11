"""
Tests for the main application API endpoints.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app, library_operations, scraping_results_storage

client = TestClient(app)


@pytest.fixture
def mock_crawl_result():
    """Create a mock crawl result."""
    return {
        "url": "https://example.com",
        "content": {"html": "<html><body>Test content</body></html>"},
        "metadata": {"title": "Test Page"},
        "status": 200,
        "error": None,
        "content_type": "text/html",
        "documents": None,
        "timestamp": datetime.now().isoformat(),
    }


@pytest.fixture
def mock_backend():
    """Create a mock backend."""
    mock = AsyncMock()
    mock.crawl.return_value = [
        MagicMock(model_dump=lambda: {"url": "https://example.com", "status": 200})
    ]
    return mock


def test_store_scraping_results():
    """Test storing scraping results."""
    # Clear any existing results
    scraping_results_storage.clear()

    # Test with provided scraping_id
    results = {
        "scraping_id": "test_id",
        "url": "https://example.com",
        "status": "completed",
        "results": [{"url": "https://example.com", "status": 200}],
    }

    response = client.post("/api/scraping/results", json=results)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["scraping_id"] == "test_id"
    assert "test_id" in scraping_results_storage

    # Test without scraping_id (should generate one)
    results = {
        "url": "https://example2.com",
        "status": "completed",
        "results": [{"url": "https://example2.com", "status": 200}],
    }

    response = client.post("/api/scraping/results", json=results)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "scraping_id" in response.json()
    assert response.json()["scraping_id"] in scraping_results_storage


@patch("src.main.Crawl4AIBackend")
def test_start_crawl_success(mock_backend_class, mock_backend):
    """Test starting a crawl successfully."""
    mock_backend_class.return_value = mock_backend

    response = client.post(
        "/crawl", json={"url": "https://example.com", "backend": "crawl4ai"}
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "scraping_id" in response.json()
    assert "results" in response.json()
    mock_backend.crawl.assert_called_once_with("https://example.com", max_depth=10)


@patch("src.main.Crawl4AIBackend")
def test_start_crawl_no_url(mock_backend_class):
    """Test starting a crawl without a URL."""
    response = client.post("/crawl", json={"backend": "crawl4ai"})

    # The API catches the HTTPException and returns a 200 with error details
    assert response.status_code == 200
    assert response.json()["status"] == "error"
    assert "URL is required" in response.json()["message"]
    mock_backend_class.assert_not_called()


@patch("src.main.Crawl4AIBackend")
def test_start_crawl_invalid_backend(mock_backend_class):
    """Test starting a crawl with an invalid backend."""
    response = client.post(
        "/crawl", json={"url": "https://example.com", "backend": "invalid"}
    )

    # The API catches the HTTPException and returns a 200 with error details
    assert response.status_code == 200
    assert response.json()["status"] == "error"
    assert "Invalid backend type" in response.json()["message"]
    mock_backend_class.assert_not_called()


@patch("src.main.Crawl4AIBackend")
def test_start_crawl_backend_error(mock_backend_class, mock_backend):
    """Test starting a crawl with a backend that raises an error."""
    mock_backend.crawl.side_effect = Exception("Backend error")
    mock_backend_class.return_value = mock_backend

    response = client.post(
        "/crawl", json={"url": "https://example.com", "backend": "crawl4ai"}
    )

    assert response.status_code == 200  # Note: The API returns 200 even for errors
    assert response.json()["status"] == "error"
    assert "Backend error" in response.json()["message"]


@patch("src.main.validate_package_name")
def test_install_library_docs(mock_validate):
    """Test installing library documentation."""
    # Clear any existing operations
    library_operations.clear()

    mock_validate.return_value = True

    # Mock the background task execution to prevent it from running
    with patch("fastapi.BackgroundTasks.add_task") as mock_add_task:
        response = client.post("/api/libraries/test-package")

        assert response.status_code == 200
        assert "operation_id" in response.json()
        assert response.json()["status"] == "pending"

        # Check that the operation was stored
        operation_id = response.json()["operation_id"]
        assert operation_id in library_operations
        assert library_operations[operation_id]["package_name"] == "test-package"
        assert library_operations[operation_id]["operation"] == "install"
        assert library_operations[operation_id]["status"] == "pending"

        # Verify the background task was added
        mock_add_task.assert_called_once()


@patch("src.main.validate_package_name")
def test_install_library_docs_invalid_package(mock_validate):
    """Test installing documentation for an invalid package."""
    mock_validate.return_value = False

    response = client.post("/api/libraries/invalid!package")

    assert response.status_code == 400
    assert "Invalid package name" in response.json()["detail"]


@patch("src.main.validate_package_name")
def test_remove_library_docs(mock_validate):
    """Test removing library documentation."""
    # Clear any existing operations
    library_operations.clear()

    mock_validate.return_value = True

    # Mock the background task execution to prevent it from running
    with patch("fastapi.BackgroundTasks.add_task") as mock_add_task:
        response = client.delete("/api/libraries/test-package")

        assert response.status_code == 200
        assert "operation_id" in response.json()
        assert response.json()["status"] == "pending"

        # Check that the operation was stored
        operation_id = response.json()["operation_id"]
        assert operation_id in library_operations
        assert library_operations[operation_id]["package_name"] == "test-package"
        assert library_operations[operation_id]["operation"] == "uninstall"
        assert library_operations[operation_id]["status"] == "pending"

        # Verify the background task was added
        mock_add_task.assert_called_once()


def test_get_library_operation_status_not_found():
    """Test getting status for a non-existent library operation."""
    response = client.get("/api/libraries/operation/nonexistent")

    assert response.status_code == 404
    assert "Operation not found" in response.json()["detail"]


def test_get_library_operation_status():
    """Test getting status for an existing library operation."""
    # Clear any existing operations
    library_operations.clear()

    # Create a test operation
    operation_id = "test_operation"
    library_operations[operation_id] = {
        "operation_id": operation_id,
        "package_name": "test-package",
        "operation": "install",
        "status": "completed",
        "start_time": datetime.now().isoformat(),
        "end_time": datetime.now().isoformat(),
        "output": "Test output",
        "error": "",
    }

    response = client.get(f"/api/libraries/operation/{operation_id}")

    assert response.status_code == 200
    assert response.json()["operation_id"] == operation_id
    assert response.json()["package_name"] == "test-package"
    assert response.json()["status"] == "completed"
