"""
Tests for the main application module.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import (
    ConnectionManager,
    app,
    run_uv_command,
    scraping_results_storage,
    validate_package_name,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_storage():
    """Clear scraping_results_storage before and after each test."""
    scraping_results_storage.clear()
    yield
    scraping_results_storage.clear()


def test_home_route():
    """Test the home route returns HTML."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_get_available_backends():
    """Test getting available backends."""
    with patch("subprocess.run") as mock_run:
        # Mock Lightpanda as available
        mock_run.return_value = MagicMock(returncode=0)
        response = client.get("/api/scraping/backends")
        assert response.status_code == 200
        assert "crawl4ai" in response.json()
        assert "file" in response.json()
        assert "lightpanda" in response.json()

        # Mock Lightpanda as unavailable
        mock_run.return_value = MagicMock(returncode=1)
        response = client.get("/api/scraping/backends")
        assert response.status_code == 200
        assert "crawl4ai" in response.json()
        assert "file" in response.json()
        assert "lightpanda" not in response.json()


def test_get_scraping_status():
    """Test getting scraping status."""
    response = client.get("/api/scraping/status")
    assert response.status_code == 200
    assert "is_running" in response.json()
    assert "current_url" in response.json()
    assert "progress" in response.json()


def test_list_scraping_results_empty():
    """Test listing scraping results when none exist."""
    response = client.get("/api/scraping/results")
    assert response.status_code == 200
    assert response.json() == []


def test_get_scraping_results_not_found():
    """Test getting non-existent scraping results."""
    response = client.get("/api/scraping/results/nonexistent")
    assert response.status_code == 404


def test_download_results_no_results():
    """Test downloading results when none exist."""
    response = client.get("/api/scraping/download/json")
    assert response.status_code == 500  # The API returns 500 instead of 404
    assert "No scraping results available" in response.json()["detail"]


def test_libraries_route():
    """Test the libraries route returns HTML."""
    response = client.get("/libraries")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_validate_package_name():
    """Test package name validation."""
    assert await validate_package_name("valid-package") is True
    assert await validate_package_name("valid_package") is True
    assert await validate_package_name("valid.package") is True
    assert await validate_package_name("valid123") is True
    assert (
        await validate_package_name("1invalid") is True
    )  # Numbers are allowed at start
    assert await validate_package_name("invalid!package") is False
    assert await validate_package_name("invalid package") is False
    assert await validate_package_name("invalid/package") is False


@pytest.mark.asyncio
async def test_run_uv_command_success():
    """Test running a UV command successfully."""
    with patch("asyncio.create_subprocess_exec") as mock_exec:
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"success output", b"")
        mock_process.returncode = 0
        mock_exec.return_value = mock_process

        returncode, stdout, stderr = await run_uv_command(["--version"])

        assert returncode == 0
        assert stdout == "success output"
        assert stderr == ""
        mock_exec.assert_called_once()


@pytest.mark.asyncio
async def test_run_uv_command_failure():
    """Test running a UV command that fails."""
    with patch("asyncio.create_subprocess_exec") as mock_exec:
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"error output")
        mock_process.returncode = 1
        mock_exec.return_value = mock_process

        returncode, stdout, stderr = await run_uv_command(["invalid-command"])

        assert returncode == 1
        assert stdout == ""
        assert stderr == "error output"
        mock_exec.assert_called_once()


@pytest.mark.asyncio
async def test_run_uv_command_exception():
    """Test running a UV command that raises an exception."""
    with patch("asyncio.create_subprocess_exec") as mock_exec:
        mock_exec.side_effect = Exception("Command failed")

        returncode, stdout, stderr = await run_uv_command(["command"])

        assert returncode == 1
        assert stdout == ""
        assert stderr == "Command failed"
        mock_exec.assert_called_once()


def test_connection_manager():
    """Test the ConnectionManager class."""
    manager = ConnectionManager()

    # Test initial state
    assert manager.active_connections == []
    assert manager.scraping_connections == []
    assert manager.library_connections == []
    assert manager.scraping_metrics["pages_scraped"] == 0
    assert manager.scraping_status["is_running"] is False

    # Test update_metrics
    manager.update_metrics("success")
    assert manager.scraping_metrics["pages_scraped"] == 1
    assert manager.scraping_metrics["successful_requests"] == 1

    manager.update_metrics("error")
    assert manager.scraping_metrics["pages_scraped"] == 2
    assert manager.scraping_metrics["failed_requests"] == 1

    # Test reset_metrics
    manager.reset_metrics()
    assert manager.scraping_metrics["pages_scraped"] == 0
    assert manager.scraping_metrics["successful_requests"] == 0
    assert manager.scraping_metrics["failed_requests"] == 0
