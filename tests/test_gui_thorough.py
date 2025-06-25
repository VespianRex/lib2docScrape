from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from run_gui import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.mark.asyncio
async def test_scraping_dashboard_loads_successfully(client):
    """Test that the scraping dashboard page loads correctly."""
    response = client.get("/test-dashboard")
    assert response.status_code == 200
    assert "Scraping Dashboard" in response.text


@pytest.mark.asyncio
async def test_websocket_connection_and_initial_message(client):
    """Test WebSocket connection and initial message exchange."""
    with client.websocket_connect("/ws/scraping") as websocket:
        # Send a sample message to start scraping
        websocket.send_json({"type": "start_scraping", "urls": ["https://example.com"]})
        # Wait for a response from the server
        data = websocket.receive_json()
        # Assert that the server sends a progress update
        assert data["type"] == "progress"
        assert "Processing URL 1/1" in data["message"]


@pytest.mark.asyncio
async def test_form_submission_and_scraping_start(client):
    """Test that submitting the scraping form starts the scraping process."""
    with patch(
        "run_gui.handle_scraping_background", new_callable=AsyncMock
    ) as mock_handle_scraping:
        response = client.post(
            "/api/scraping/start", json={"urls": ["https://example.com"]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "Scraping started" in data["message"]
        mock_handle_scraping.assert_called_once()


@pytest.mark.asyncio
async def test_stop_scraping_endpoint(client):
    """Test the endpoint for stopping an ongoing scraping process."""
    # First, start a task to be stopped
    with patch(
        "run_gui.handle_scraping_background", new_callable=AsyncMock
    ) as mock_handle_scraping:
        start_response = client.post(
            "/api/scraping/start", json={"urls": ["https://example.com"]}
        )
        task_id = start_response.json()["task_id"]

        # Now, stop the task
        stop_response = client.post("/api/scraping/stop", json={"task_id": task_id})
        assert stop_response.status_code == 200
        data = stop_response.json()
        assert data["status"] == "success"
        assert "Scraping task" in data["message"]
        assert "stopped" in data["message"]


@pytest.mark.asyncio
async def test_websocket_progress_and_completion_messages(client):
    """Test that the WebSocket sends progress and completion messages correctly."""
    with client.websocket_connect("/ws/scraping") as websocket:
        websocket.send_json(
            {
                "type": "start_scraping",
                "urls": ["https://example.com", "https://example.org"],
            }
        )

        # Check for progress messages
        progress_count = 0
        completion_message = None
        while True:
            try:
                data = websocket.receive_json()
                if data["type"] == "progress":
                    progress_count += 1
                elif data["type"] == "complete":
                    completion_message = data
                    break
            except WebSocketDisconnect:
                break

        assert progress_count > 0
        assert completion_message is not None
        assert completion_message["total_processed"] == 2
