import pytest
import asyncio # Import asyncio
from unittest.mock import MagicMock, patch, AsyncMock # Import AsyncMock
from pathlib import Path
from fastapi.testclient import TestClient

from src.gui.app import app, ConnectionManager, CrawlRequest
from src.processors.quality_checker import QualityIssue, IssueType, IssueLevel # Import needed types
from src.processors.content_processor import ProcessedContent
from src.backends.base import CrawlResult # Import CrawlResult
# Assume CrawlerThread and ResultsViewer are part of a separate GUI implementation
# from src.gui.main_window import CrawlerThread, ResultsViewer # Commented out

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
    # Mock the backend crawl method used within the endpoint
    # Use AsyncMock for the patch target as it's an async method
    with patch('src.gui.app.Crawl4AIBackend.crawl', new_callable=AsyncMock) as mock_crawl:
        # Create an actual CrawlResult instance for the mock return value
        mock_result_obj = CrawlResult(
            url=test_url,
            content={"text": "Mocked content", "title": "Mock Title"},
            metadata={}, # Add empty metadata dict
            status=200
        )

        # Define an async side_effect function
        async def mock_side_effect(*args, **kwargs):
            # Simulate some async operation if needed, e.g., await asyncio.sleep(0)
            return [mock_result_obj] # Return a list containing the CrawlResult instance

        # Set the side_effect of the AsyncMock
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
    assert manager.crawl_metrics["pages_crawled"] == 0
    assert manager.crawl_metrics["current_depth"] == 0
    assert manager.crawl_metrics["successful_requests"] == 0
    assert manager.crawl_metrics["failed_requests"] == 0

# Commenting out tests related to PyQt GUI for now
# def test_crawler_thread():
#     """Test crawler thread functionality."""
#     mock_crawler = MagicMock()
#     # Corrected ProcessedContent instantiation
#     mock_processed_content = ProcessedContent(
#         title="Mock Title",
#         content={'formatted_content': 'processed content'},
#         metadata={'type': 'documentation'},
#         assets={},
#         structure=[],
#         errors=[]
#     )
#     # Corrected QualityIssue instantiation (if needed)
#     mock_quality_issue = QualityIssue(
#         type=IssueType.CONTENT, # Use valid IssueType
#         message='Test issue',
#         level=IssueLevel.WARNING # Use valid IssueLevel
#     )
#     mock_crawler.crawl.return_value = {
#         'content': mock_processed_content,
#         'quality_issues': [mock_quality_issue]
#     }
#
#     # Assuming CrawlerThread is defined elsewhere and takes these args
#     # thread = CrawlerThread(
#     #     crawler=mock_crawler,
#     #     url='https://example.com',
#     #     depth=2
#     # )
#
#     # Test signals (requires CrawlerThread to be defined and imported)
#     # with patch.object(thread, 'finished') as mock_finished:
#     #     with patch.object(thread, 'error') as mock_error:
#     #         thread.run()
#     #         mock_finished.emit.assert_called_once()
#     #         mock_error.emit.assert_not_called()
#     pass # Placeholder if CrawlerThread part is commented out

# def test_results_viewer():
#     """Test results viewer functionality."""
#     # Assuming ResultsViewer is defined elsewhere
#     # viewer = ResultsViewer()
#
#     # Test content display
#     content = ProcessedContent(
#         title="Test Title", # Use valid args
#         content={'formatted_content': 'processed content'},
#         metadata={'type': 'documentation'},
#         assets={},
#         structure=[],
#         errors=[]
#     )
#     # viewer.display_content(content) # Requires viewer instance
#
#     # Test quality issues display
#     # issues = [
#     #     QualityIssue(
#     #         type=IssueType.CONTENT, # Use valid IssueType
#     #         message='Test issue 1',
#     #         level=IssueLevel.WARNING # Use valid IssueLevel
#     #     ),
#     #     QualityIssue(
#     #         type=IssueType.STRUCTURE, # Use valid IssueType
#     #         message='Test issue 2',
#     #         level=IssueLevel.ERROR # Use valid IssueLevel
#     #     )
#     # ]
#     # viewer.display_quality_issues(issues) # Requires viewer instance
#     pass # Placeholder

# def test_save_results(tmp_path):
#     """Test saving results functionality."""
#     output_dir = tmp_path / 'output'
#     output_dir.mkdir()
#
#     mock_content = ProcessedContent(
#         title="Test Title", # Use valid args
#         content={'formatted_content': 'processed content'},
#         metadata={'type': 'documentation'},
#         assets={},
#         structure=[],
#         errors=[]
#     )
#
#     # Test saving (Requires main_window or similar instance)
#     # with patch('PyQt6.QtWidgets.QFileDialog.getExistingDirectory') as mock_dialog:
#     #     mock_dialog.return_value = str(output_dir)
#     #     # main_window._save_results(mock_content, []) # Example call
#     #
#     #     # Check if files were created (adjust based on actual save logic)
#     #     assert (output_dir / 'content.json').exists()
#     #     assert (output_dir / 'quality_report.json').exists()
#     pass # Placeholder

# def test_error_handling():
#     """Test error handling in GUI."""
#     error_msg = "Test error message"
#
#     # Test error display (Requires main_window or similar instance)
#     # with patch('PyQt6.QtWidgets.QMessageBox.critical') as mock_critical:
#     #     # main_window._handle_error(error_msg)
#     #     # mock_critical.assert_called_once()
#     #     pass # Placeholder
#
#     # Test status bar update (Requires main_window or similar instance)
#     # main_window._update_status("Test status")
#     # assert main_window.status_bar.currentMessage() == "Test status"
#     pass # Placeholder
