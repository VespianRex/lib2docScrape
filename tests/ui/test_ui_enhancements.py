"""
Tests for the user interface enhancements.
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from fastapi import FastAPI

# Import the app from main.py
from src.main import app

# Create a test client
client = TestClient(app)

def test_api_endpoints():
    """Test the API endpoints."""
    # Test the root endpoint
    response = client.get("/")
    assert response.status_code == 200
    
    # Test the API version endpoint
    response = client.get("/api/version")
    assert response.status_code == 200
    assert "version" in response.json()
    
    # Test the available backends endpoint
    response = client.get("/api/scraping/backends")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    
    # Test the status endpoint
    response = client.get("/api/status")
    assert response.status_code == 200
    assert "status" in response.json()

def test_library_endpoints():
    """Test the library endpoints."""
    # Mock the LibraryRegistry
    with patch("src.main.LibraryRegistry") as mock_registry:
        # Setup mock
        mock_registry_instance = MagicMock()
        mock_registry_instance.libraries = {
            "test_lib": {
                "name": "test_lib",
                "base_url": "https://docs.test-lib.com",
                "versions": {
                    "1.0.0": {
                        "version": "1.0.0",
                        "documentation_url": "https://docs.test-lib.com/v1.0.0",
                        "is_latest": False
                    },
                    "2.0.0": {
                        "version": "2.0.0",
                        "documentation_url": "https://docs.test-lib.com/v2.0.0",
                        "is_latest": True
                    }
                }
            }
        }
        mock_registry.return_value = mock_registry_instance
        
        # Test the libraries endpoint
        response = client.get("/api/libraries")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        
        # Test the library versions endpoint
        response = client.get("/api/libraries/test_lib/versions")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        
        # Test the library version details endpoint
        response = client.get("/api/libraries/test_lib/versions/1.0.0")
        assert response.status_code == 200
        assert "version" in response.json()
        
        # Test the library version comparison endpoint
        with patch("src.main.LibraryVersionTracker") as mock_tracker:
            # Setup mock
            mock_tracker_instance = MagicMock()
            mock_tracker_instance.compare_versions.return_value = {
                "from_version": "1.0.0",
                "to_version": "2.0.0",
                "added_pages": [],
                "removed_pages": [],
                "modified_pages": []
            }
            mock_tracker.return_value = mock_tracker_instance
            
            response = client.get("/api/libraries/test_lib/compare?from=1.0.0&to=2.0.0")
            assert response.status_code == 200
            assert "from_version" in response.json()
            assert "to_version" in response.json()

def test_visualization_endpoints():
    """Test the visualization endpoints."""
    # Mock the DocumentOrganizer
    with patch("src.main.DocumentOrganizer") as mock_organizer:
        # Setup mock
        mock_organizer_instance = MagicMock()
        mock_organizer_instance.get_document_graph.return_value = {
            "nodes": [
                {"id": "doc1", "label": "Document 1", "type": "document"},
                {"id": "doc2", "label": "Document 2", "type": "document"},
                {"id": "doc3", "label": "Document 3", "type": "document"}
            ],
            "edges": [
                {"source": "doc1", "target": "doc2", "type": "link"},
                {"source": "doc1", "target": "doc3", "type": "link"},
                {"source": "doc2", "target": "doc3", "type": "link"}
            ]
        }
        mock_organizer.return_value = mock_organizer_instance
        
        # Test the document graph endpoint
        response = client.get("/api/visualization/document-graph")
        assert response.status_code == 200
        assert "nodes" in response.json()
        assert "edges" in response.json()
        
        # Test the topic map endpoint
        mock_organizer_instance.get_topic_map.return_value = {
            "topics": [
                {"id": "topic1", "label": "Topic 1", "size": 10},
                {"id": "topic2", "label": "Topic 2", "size": 5},
                {"id": "topic3", "label": "Topic 3", "size": 3}
            ],
            "documents": [
                {"id": "doc1", "label": "Document 1", "topics": ["topic1", "topic2"]},
                {"id": "doc2", "label": "Document 2", "topics": ["topic1", "topic3"]},
                {"id": "doc3", "label": "Document 3", "topics": ["topic2", "topic3"]}
            ]
        }
        
        response = client.get("/api/visualization/topic-map")
        assert response.status_code == 200
        assert "topics" in response.json()
        assert "documents" in response.json()

def test_search_endpoints():
    """Test the search endpoints."""
    # Mock the DocumentOrganizer
    with patch("src.main.DocumentOrganizer") as mock_organizer:
        # Setup mock
        mock_organizer_instance = MagicMock()
        mock_organizer_instance.search.return_value = [
            {
                "id": "doc1",
                "title": "Document 1",
                "url": "https://example.com/doc1",
                "score": 0.95,
                "snippet": "This is a snippet from Document 1"
            },
            {
                "id": "doc2",
                "title": "Document 2",
                "url": "https://example.com/doc2",
                "score": 0.85,
                "snippet": "This is a snippet from Document 2"
            }
        ]
        mock_organizer.return_value = mock_organizer_instance
        
        # Test the search endpoint
        response = client.get("/api/search?q=test")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) > 0
        
        # Test the faceted search endpoint
        mock_organizer_instance.faceted_search.return_value = {
            "results": [
                {
                    "id": "doc1",
                    "title": "Document 1",
                    "url": "https://example.com/doc1",
                    "score": 0.95,
                    "snippet": "This is a snippet from Document 1"
                }
            ],
            "facets": {
                "library": [
                    {"value": "test_lib", "count": 1}
                ],
                "version": [
                    {"value": "1.0.0", "count": 1}
                ],
                "category": [
                    {"value": "api", "count": 1}
                ]
            }
        }
        
        response = client.get("/api/search/faceted?q=test&library=test_lib&version=1.0.0&category=api")
        assert response.status_code == 200
        assert "results" in response.json()
        assert "facets" in response.json()

def test_progress_monitoring_endpoints():
    """Test the progress monitoring endpoints."""
    # Mock the crawler
    with patch("src.main.DocumentationCrawler") as mock_crawler:
        # Setup mock
        mock_crawler_instance = MagicMock()
        mock_crawler_instance.get_progress.return_value = {
            "total_urls": 100,
            "processed_urls": 50,
            "successful_urls": 45,
            "failed_urls": 5,
            "current_url": "https://example.com/page50",
            "elapsed_time": 60.0,
            "estimated_time_remaining": 60.0,
            "status": "running"
        }
        mock_crawler.return_value = mock_crawler_instance
        
        # Test the progress endpoint
        response = client.get("/api/scraping/progress")
        assert response.status_code == 200
        assert "total_urls" in response.json()
        assert "processed_urls" in response.json()
        assert "status" in response.json()
        
        # Test the detailed progress endpoint
        mock_crawler_instance.get_detailed_progress.return_value = {
            "progress": {
                "total_urls": 100,
                "processed_urls": 50,
                "successful_urls": 45,
                "failed_urls": 5,
                "current_url": "https://example.com/page50",
                "elapsed_time": 60.0,
                "estimated_time_remaining": 60.0,
                "status": "running"
            },
            "recent_urls": [
                {"url": "https://example.com/page49", "status": "success", "time": 1.2},
                {"url": "https://example.com/page48", "status": "success", "time": 1.1},
                {"url": "https://example.com/page47", "status": "success", "time": 1.3},
                {"url": "https://example.com/page46", "status": "success", "time": 1.0},
                {"url": "https://example.com/page45", "status": "success", "time": 1.2}
            ],
            "failed_urls": [
                {"url": "https://example.com/page10", "status": "error", "error": "Connection timeout"},
                {"url": "https://example.com/page20", "status": "error", "error": "404 Not Found"},
                {"url": "https://example.com/page30", "status": "error", "error": "500 Internal Server Error"},
                {"url": "https://example.com/page40", "status": "error", "error": "Connection refused"},
                {"url": "https://example.com/page50", "status": "error", "error": "Invalid content type"}
            ]
        }
        
        response = client.get("/api/scraping/progress/detailed")
        assert response.status_code == 200
        assert "progress" in response.json()
        assert "recent_urls" in response.json()
        assert "failed_urls" in response.json()
