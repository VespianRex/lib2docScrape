"""
Comprehensive GUI tests for lib2docScrape.

This module provides comprehensive test coverage for all GUI components,
interactions, and functionality including the dashboard, forms, navigation,
and real-time updates.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.ui.dashboard import Dashboard, DashboardConfig
from src.ui.search import SearchConfig, SearchInterface
from src.ui.visualizations import VisualizationConfig, Visualizations


class TestDashboardGUI:
    """Test suite for Dashboard GUI components."""

    @pytest.fixture
    def dashboard_config(self):
        """Create dashboard configuration for testing."""
        return DashboardConfig(
            title="Test Dashboard",
            description="Test dashboard for comprehensive testing",
            enable_websockets=True,
            enable_charts=True,
            enable_notifications=True,
            enable_search=True,
            enable_filters=True,
            enable_sorting=True,
            enable_export=True,
            theme="light",
            refresh_interval=5,
            max_items_per_page=20
        )

    @pytest.fixture
    def mock_app(self):
        """Create a mock FastAPI app for testing."""
        from fastapi import FastAPI
        app = FastAPI()
        return app

    @pytest.fixture
    def dashboard(self, mock_app, dashboard_config):
        """Create dashboard instance for testing."""
        return Dashboard(mock_app, config=dashboard_config)

    def test_dashboard_initialization(self, dashboard, dashboard_config):
        """Test dashboard initializes with correct configuration."""
        assert dashboard.config == dashboard_config
        assert dashboard.config.title == "Test Dashboard"
        assert dashboard.config.enable_websockets is True
        assert dashboard.config.enable_charts is True

    def test_dashboard_route_registration(self, dashboard, mock_app):
        """Test that dashboard registers all required routes."""
        # This test will fail until routes are properly implemented
        client = TestClient(mock_app)
        
        # Test main dashboard route
        response = client.get("/")
        assert response.status_code == 200
        assert "Test Dashboard" in response.text

    def test_dashboard_api_endpoints(self, dashboard, mock_app):
        """Test dashboard API endpoints."""
        client = TestClient(mock_app)
        
        # Test status endpoint
        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert "libraries" in data
        assert "documents" in data
        assert "crawls" in data
        assert "uptime" in data

    def test_dashboard_websocket_connection(self, dashboard, mock_app):
        """Test WebSocket connection for real-time updates."""
        client = TestClient(mock_app)
        
        with client.websocket_connect("/ws") as websocket:
            # Test connection established
            data = websocket.receive_json()
            assert data["type"] == "connection"
            assert data["status"] == "connected"

    def test_dashboard_theme_switching(self, dashboard):
        """Test theme switching functionality."""
        # Test light theme
        dashboard.set_theme("light")
        assert dashboard.config.theme == "light"
        
        # Test dark theme
        dashboard.set_theme("dark")
        assert dashboard.config.theme == "dark"
        
        # Test auto theme
        dashboard.set_theme("auto")
        assert dashboard.config.theme == "auto"

    def test_dashboard_data_refresh(self, dashboard):
        """Test dashboard data refresh functionality."""
        with patch.object(dashboard, 'fetch_dashboard_data') as mock_fetch:
            mock_fetch.return_value = {
                "libraries": 10,
                "documents": 50,
                "crawls": 5,
                "uptime": 3600
            }
            
            data = dashboard.refresh_data()
            
            assert data["libraries"] == 10
            assert data["documents"] == 50
            assert data["crawls"] == 5
            assert data["uptime"] == 3600
            mock_fetch.assert_called_once()


class TestSearchInterfaceGUI:
    """Test suite for Search Interface GUI components."""

    @pytest.fixture
    def search_config(self):
        """Create search configuration for testing."""
        return SearchConfig(
            max_results=20,
            min_query_length=2,
            enable_fuzzy_search=True,
            enable_filters=True,
            enable_sorting=True,
            enable_facets=True,
            highlight_results=True,
            search_titles=True,
            search_content=True,
            search_metadata=True
        )

    @pytest.fixture
    def mock_app(self):
        """Create a mock FastAPI app for testing."""
        from fastapi import FastAPI
        app = FastAPI()
        return app

    @pytest.fixture
    def search_interface(self, mock_app, search_config):
        """Create search interface for testing."""
        return SearchInterface(mock_app, config=search_config)

    def test_search_interface_initialization(self, search_interface, search_config):
        """Test search interface initializes correctly."""
        assert search_interface.config == search_config
        assert search_interface.config.enable_advanced_search is True
        assert search_interface.config.enable_filters is True

    def test_search_form_validation(self, search_interface):
        """Test search form validation."""
        # Test valid search query
        result = search_interface.validate_search_query("python documentation")
        assert result.is_valid is True
        assert result.query == "python documentation"
        
        # Test empty query
        result = search_interface.validate_search_query("")
        assert result.is_valid is False
        assert "Query cannot be empty" in result.errors
        
        # Test query too long
        long_query = "a" * 1000
        result = search_interface.validate_search_query(long_query)
        assert result.is_valid is False
        assert "Query too long" in result.errors

    def test_search_autocomplete(self, search_interface):
        """Test search autocomplete functionality."""
        with patch.object(search_interface, 'get_autocomplete_suggestions') as mock_suggestions:
            mock_suggestions.return_value = [
                "python documentation",
                "python tutorial",
                "python api reference"
            ]
            
            suggestions = search_interface.get_autocomplete("python")
            
            assert len(suggestions) == 3
            assert "python documentation" in suggestions
            assert "python tutorial" in suggestions
            assert "python api reference" in suggestions

    def test_search_filters(self, search_interface):
        """Test search filters functionality."""
        filters = {
            "content_type": ["documentation", "tutorial"],
            "language": ["python", "javascript"],
            "date_range": {"start": "2023-01-01", "end": "2023-12-31"}
        }
        
        result = search_interface.apply_filters("test query", filters)
        
        assert result.query == "test query"
        assert result.filters == filters
        assert "documentation" in result.filters["content_type"]
        assert "python" in result.filters["language"]

    def test_search_history(self, search_interface):
        """Test search history functionality."""
        # Add search to history
        search_interface.add_to_history("python documentation")
        search_interface.add_to_history("javascript tutorial")
        
        history = search_interface.get_search_history()
        
        assert len(history) == 2
        assert "python documentation" in history
        assert "javascript tutorial" in history
        
        # Test history limit
        for i in range(50):
            search_interface.add_to_history(f"query {i}")
        
        history = search_interface.get_search_history()
        assert len(history) <= search_interface.config.max_history_items


class TestVisualizationsGUI:
    """Test suite for Visualizations GUI components."""

    @pytest.fixture
    def viz_config(self):
        """Create visualization configuration for testing."""
        return VisualizationConfig(
            enable_charts=True,
            enable_graphs=True,
            enable_maps=True,
            enable_tables=True,
            enable_export=True,
            default_chart_type="bar",
            default_color_scheme="category10",
            max_items_per_chart=100,
            chart_width=800,
            chart_height=400
        )

    @pytest.fixture
    def mock_app(self):
        """Create a mock FastAPI app for testing."""
        from fastapi import FastAPI
        app = FastAPI()
        return app

    @pytest.fixture
    def visualizations(self, mock_app, viz_config):
        """Create visualizations instance for testing."""
        return Visualizations(mock_app, config=viz_config)

    def test_visualizations_initialization(self, visualizations, viz_config):
        """Test visualizations initialize correctly."""
        assert visualizations.config == viz_config
        assert visualizations.config.enable_charts is True
        assert visualizations.config.default_chart_type == "bar"

    def test_chart_generation(self, visualizations):
        """Test chart generation functionality."""
        data = {
            "labels": ["Python", "JavaScript", "Java", "C++"],
            "values": [45, 30, 15, 10]
        }
        
        chart = visualizations.create_chart(
            chart_type="bar",
            data=data,
            title="Programming Languages Usage"
        )
        
        assert chart.chart_type == "bar"
        assert chart.title == "Programming Languages Usage"
        assert chart.data == data
        assert chart.width == visualizations.config.chart_width
        assert chart.height == visualizations.config.chart_height

    def test_data_table_generation(self, visualizations):
        """Test data table generation."""
        data = [
            {"library": "requests", "downloads": 1000000, "rating": 4.8},
            {"library": "numpy", "downloads": 800000, "rating": 4.9},
            {"library": "pandas", "downloads": 600000, "rating": 4.7}
        ]
        
        table = visualizations.create_table(
            data=data,
            columns=["library", "downloads", "rating"],
            title="Popular Python Libraries"
        )
        
        assert table.title == "Popular Python Libraries"
        assert len(table.data) == 3
        assert table.columns == ["library", "downloads", "rating"]
        assert table.data[0]["library"] == "requests"

    def test_export_functionality(self, visualizations):
        """Test export functionality for visualizations."""
        chart_data = {
            "labels": ["A", "B", "C"],
            "values": [10, 20, 30]
        }
        
        chart = visualizations.create_chart("pie", chart_data, "Test Chart")
        
        # Test PNG export
        png_data = visualizations.export_chart(chart, format="png")
        assert png_data is not None
        assert isinstance(png_data, bytes)
        
        # Test SVG export
        svg_data = visualizations.export_chart(chart, format="svg")
        assert svg_data is not None
        assert isinstance(svg_data, str)
        
        # Test JSON export
        json_data = visualizations.export_chart(chart, format="json")
        assert json_data is not None
        data = json.loads(json_data)
        assert data["chart_type"] == "pie"
        assert data["title"] == "Test Chart"


class TestGUIIntegration:
    """Test suite for GUI integration and user workflows."""

    @pytest.fixture
    def integrated_app(self):
        """Create integrated app with all GUI components."""
        from fastapi import FastAPI
        app = FastAPI()
        
        # Add all GUI components
        dashboard = Dashboard(app, DashboardConfig())
        search = SearchInterface(app, SearchConfig())
        viz = Visualizations(app, VisualizationConfig())
        
        return app, dashboard, search, viz

    def test_complete_user_workflow(self, integrated_app):
        """Test complete user workflow through the GUI."""
        app, dashboard, search, viz = integrated_app
        client = TestClient(app)
        
        # 1. User visits dashboard
        response = client.get("/")
        assert response.status_code == 200
        
        # 2. User performs search
        search_data = {"query": "python documentation", "filters": {}}
        response = client.post("/search", json=search_data)
        assert response.status_code == 200
        
        # 3. User views results
        response = client.get("/search/results")
        assert response.status_code == 200
        
        # 4. User exports data
        response = client.get("/export/csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

    def test_error_handling_in_gui(self, integrated_app):
        """Test error handling in GUI components."""
        app, dashboard, search, viz = integrated_app
        client = TestClient(app)
        
        # Test invalid search
        response = client.post("/search", json={"query": ""})
        assert response.status_code == 400
        
        # Test non-existent route
        response = client.get("/nonexistent")
        assert response.status_code == 404
        
        # Test server error handling
        with patch.object(dashboard, 'fetch_dashboard_data', side_effect=Exception("Test error")):
            response = client.get("/api/status")
            assert response.status_code == 500

    def test_responsive_design_elements(self, integrated_app):
        """Test responsive design elements in GUI."""
        app, dashboard, search, viz = integrated_app
        client = TestClient(app)
        
        # Test mobile viewport
        headers = {"User-Agent": "Mobile Browser"}
        response = client.get("/", headers=headers)
        assert response.status_code == 200
        assert "viewport" in response.text
        assert "responsive" in response.text or "mobile" in response.text
        
        # Test desktop viewport
        headers = {"User-Agent": "Desktop Browser"}
        response = client.get("/", headers=headers)
        assert response.status_code == 200
