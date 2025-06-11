from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.backends.base import CrawlResult
from src.main import ConnectionManager, app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def connection_manager():
    """Create a connection manager."""
    return ConnectionManager()


def test_home_page(client):
    """Test home page returns successfully."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_crawl_request(client):
    """Test crawl request endpoint."""
    test_url = "https://example.com"
    with patch("src.main.Crawl4AIBackend.crawl", new_callable=AsyncMock) as mock_crawl:
        mock_result_obj = CrawlResult(
            url=test_url,
            content={"text": "Mocked content", "title": "Mock Title"},
            metadata={},
            status=200,
        )

        async def mock_side_effect(*args, **kwargs):
            return [mock_result_obj]

        mock_crawl.side_effect = mock_side_effect

        response = client.post("/crawl", json={"url": test_url})
        assert response.status_code == 200
        response_json = response.json()
        assert response_json["status"] == "success"
        assert len(response_json["results"]) == 1
        assert response_json["results"][0]["url"] == test_url
        assert response_json["results"][0]["status"] == 200


def test_connection_manager():
    """Test connection manager functionality."""
    manager = ConnectionManager()
    assert manager.scraping_metrics["pages_scraped"] == 0
    assert manager.scraping_metrics["current_depth"] == 0
    assert manager.scraping_metrics["successful_requests"] == 0
    assert manager.scraping_metrics["failed_requests"] == 0


def test_get_available_backends(client):
    """Test retrieving available backend types."""
    response = client.get("/api/scraping/backends")
    assert response.status_code == 200
    backends = response.json()
    assert isinstance(backends, list)
    assert "crawl4ai" in backends
    assert "file" in backends


def test_get_scraping_status(client):
    """Test retrieving scraping status."""
    response = client.get("/api/scraping/status")
    assert response.status_code == 200
    status = response.json()
    assert isinstance(status, dict)
    assert "is_running" in status
    assert "current_url" in status
    assert "progress" in status


@pytest.mark.asyncio
async def test_websocket_scraping_updates():
    """Test WebSocket updates for scraping."""
    with TestClient(app) as client:
        with client.websocket_connect("/ws/scraping") as websocket:
            # Test connection establishment
            data = websocket.receive_json()
            assert "type" in data
            assert data["type"] == "connection_established"

            # Test status update
            test_update = {
                "type": "scraping_progress",
                "data": {
                    "is_running": True,
                    "current_url": "https://example.com",
                    "progress": 50,
                },
            }
            websocket.send_json(test_update)
            response = websocket.receive_json()
            assert response["type"] == "scraping_progress"
            assert response["data"]["progress"] == 50


def test_store_scraping_results(client):
    """Test storing and retrieving scraping results."""
    scraping_results = {
        "scraping_id": "scrape123",
        "timestamp": "2025-05-14T15:30:00",
        "results": [
            {"url": "https://example.com", "content": "Test content", "status": 200}
        ],
    }

    # Store results
    response = client.post("/api/scraping/results", json=scraping_results)
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # Retrieve results
    response = client.get("/api/scraping/results/scrape123")
    assert response.status_code == 200
    stored_results = response.json()
    assert stored_results["scraping_id"] == "scrape123"
    assert len(stored_results["results"]) == 1
    assert stored_results["results"][0]["status"] == 200


def test_scraping_dashboard_template(client):
    """Test the scraping dashboard HTML template."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    content = response.text
    assert "Backend Selection" in content
    assert "Scraping Configuration" in content
    assert "Scraping Status" in content
    assert "Results" in content


def test_library_operations(client):
    """Test library management operations."""
    # Test installing a package
    response = client.post("/api/libraries/test-package")
    assert response.status_code == 200
    operation = response.json()
    assert "operation_id" in operation

    # Test operation status
    response = client.get(f"/api/libraries/operation/{operation['operation_id']}")
    assert response.status_code == 200
    status = response.json()
    assert status["operation"] == "install"
    assert status["package_name"] == "test-package"

    # Test uninstalling a package
    response = client.delete("/api/libraries/test-package")
    assert response.status_code == 200
    operation = response.json()
    assert "operation_id" in operation
