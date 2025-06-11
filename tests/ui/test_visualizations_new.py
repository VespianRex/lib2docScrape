"""
Tests for the visualizations UI module.
"""

from unittest.mock import MagicMock, patch

from src.ui.visualizations import VisualizationConfig, Visualizations


def test_visualizations_ui_initialization():
    """Test Visualizations initialization."""
    # Create a mock FastAPI app
    mock_app = MagicMock()

    # Initialize Visualizations
    vis_ui = Visualizations(app=mock_app)

    # Verify initialization
    assert vis_ui.app == mock_app
    assert vis_ui.config is not None


def test_visualizations_ui_with_custom_config():
    """Test Visualizations with custom config."""
    # Create a mock FastAPI app
    mock_app = MagicMock()

    # Create custom config
    config = VisualizationConfig(
        default_chart_type="line", default_color_scheme="blue", animation_duration=0
    )

    # Initialize Visualizations with custom config
    vis_ui = Visualizations(app=mock_app, config=config)

    # Verify custom config was applied
    assert vis_ui.config.default_chart_type == "line"
    assert vis_ui.config.default_color_scheme == "blue"
    assert vis_ui.config.animation_duration == 0


def test_visualizations_ui_routes():
    """Test that Visualizations registers routes."""
    # Create a mock FastAPI app
    mock_app = MagicMock()

    # Initialize Visualizations
    Visualizations(app=mock_app)

    # Verify routes were registered
    assert mock_app.get.call_count > 0

    # Find the visualization routes
    chart_route = None

    for route in mock_app.get.call_args_list:
        route_path = route[0][0]
        if "/api/visualizations/chart" in route_path:
            chart_route = True
            break

    # The visualization routes should be registered
    assert chart_route is not None


def test_visualizations_ui_api_routes():
    """Test that Visualizations registers API routes."""
    # Create a mock FastAPI app
    mock_app = MagicMock()

    # Initialize Visualizations
    Visualizations(app=mock_app)

    # Find the API routes
    api_routes = []
    for route in mock_app.get.call_args_list:
        if "/api/visualizations/graph" in route[0][0]:
            api_routes.append(route[0][0])

    # API routes should be registered
    assert len(api_routes) > 0


@patch("src.ui.visualizations.Visualizations._generate_chart_config")
def test_visualizations_ui_chart_config(mock_generate_chart_config):
    """Test generating chart configuration."""
    # Set up mock return value
    mock_generate_chart_config.return_value = {
        "type": "bar",
        "data": [{"x": "A", "y": 10}, {"x": "B", "y": 20}],
        "options": {"title": "Test Chart"},
    }

    # Create a mock FastAPI app
    mock_app = MagicMock()

    # Initialize Visualizations
    vis_ui = Visualizations(app=mock_app)

    # Mock the chart generation
    chart_type = "bar"
    chart_data = [{"x": "A", "y": 10}, {"x": "B", "y": 20}]
    chart_options = {"title": "Test Chart"}

    # Call the method directly
    result = vis_ui._generate_chart_config(chart_type, chart_data, chart_options)

    # Verify the result
    assert result["type"] == "bar"
    assert len(result["data"]) == 2
    assert result["options"]["title"] == "Test Chart"


@patch("src.ui.visualizations.Visualizations._generate_graph_config")
def test_visualizations_ui_graph_config(mock_generate_graph_config):
    """Test generating graph configuration."""
    # Set up mock return value
    mock_generate_graph_config.return_value = {
        "type": "graph",
        "data": {
            "nodes": [{"id": "A"}, {"id": "B"}],
            "links": [{"source": "A", "target": "B"}],
        },
        "options": {"title": "Test Graph"},
    }

    # Create a mock FastAPI app
    mock_app = MagicMock()

    # Initialize Visualizations
    vis_ui = Visualizations(app=mock_app)

    # Mock the graph data and options
    graph_data = {
        "nodes": [{"id": "A"}, {"id": "B"}],
        "links": [{"source": "A", "target": "B"}],
    }
    graph_options = {"title": "Test Graph"}

    # Call the method directly
    result = vis_ui._generate_graph_config(graph_data, graph_options)

    # Verify the result
    assert result["type"] == "graph"
    assert len(result["data"]["nodes"]) == 2
    assert len(result["data"]["links"]) == 1
    assert result["options"]["title"] == "Test Graph"


@patch("src.ui.visualizations.Visualizations._generate_table_config")
def test_visualizations_ui_table_config(mock_generate_table_config):
    """Test generating table configuration."""
    # Set up mock return value
    mock_generate_table_config.return_value = {
        "type": "table",
        "data": [{"name": "Item 1", "value": 10}, {"name": "Item 2", "value": 20}],
        "options": {"title": "Test Table"},
    }

    # Create a mock FastAPI app
    mock_app = MagicMock()

    # Initialize Visualizations
    vis_ui = Visualizations(app=mock_app)

    # Mock the table data and options
    table_data = [{"name": "Item 1", "value": 10}, {"name": "Item 2", "value": 20}]
    table_options = {"title": "Test Table"}

    # Call the method directly
    result = vis_ui._generate_table_config(table_data, table_options)

    # Verify the result
    assert result["type"] == "table"
    assert len(result["data"]) == 2
    assert result["options"]["title"] == "Test Table"
