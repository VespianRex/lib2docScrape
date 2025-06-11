"""
Tests for UI components.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.ui.dashboard import Dashboard, DashboardConfig
from src.ui.search import SearchConfig, SearchInterface
from src.ui.visualizations import VisualizationConfig, Visualizations


@pytest.fixture
def app():
    """Create a FastAPI app for testing."""
    return FastAPI()


@pytest.fixture
def dashboard(app):
    """Create a dashboard for testing."""
    config = DashboardConfig(
        title="Test Dashboard",
        description="Test dashboard for testing",
        enable_websockets=False,
        templates_dir="src/ui/templates",
        static_dir="src/ui/static",
    )
    return Dashboard(app, config=config)


@pytest.fixture
def search_interface(app):
    """Create a search interface for testing."""
    config = SearchConfig(max_results=10, min_query_length=2, enable_fuzzy_search=True)
    return SearchInterface(app, config=config)


@pytest.fixture
def visualizations(app):
    """Create visualizations for testing."""
    config = VisualizationConfig(
        enable_charts=True, enable_graphs=True, enable_tables=True
    )
    return Visualizations(app, config=config)


@pytest.fixture
def client(app, dashboard, search_interface, visualizations):
    """Create a test client."""
    return TestClient(app)


def test_dashboard_initialization(dashboard):
    """Test dashboard initialization."""
    assert dashboard.config.title == "Test Dashboard"
    assert dashboard.config.description == "Test dashboard for testing"
    assert dashboard.config.enable_websockets is False


def test_search_interface_initialization(search_interface):
    """Test search interface initialization."""
    assert search_interface.config.max_results == 10
    assert search_interface.config.min_query_length == 2
    assert search_interface.config.enable_fuzzy_search is True


def test_visualizations_initialization(visualizations):
    """Test visualizations initialization."""
    assert visualizations.config.enable_charts is True
    assert visualizations.config.enable_graphs is True
    assert visualizations.config.enable_tables is True


def test_search_add_document(search_interface):
    """Test adding a document to the search index."""
    # Create test document
    doc = {
        "id": "test1",
        "title": "Test Document",
        "content": "This is a test document for testing the search interface.",
        "url": "https://example.com/test1",
        "category": "test",
    }

    # Add document
    search_interface.add_document(doc)

    # Check that document was added
    assert "test1" in search_interface.documents
    assert search_interface.documents["test1"] == doc

    # Check that document was indexed
    assert "test" in search_interface.index
    assert "title" in search_interface.index["test"]
    assert "test1" in search_interface.index["test"]["title"]


def test_search_tokenize(search_interface):
    """Test tokenizing text for search."""
    # Test basic tokenization
    tokens = search_interface._tokenize("This is a test")
    assert "this" in tokens
    assert "is" in tokens
    assert "a" in tokens
    assert "test" in tokens

    # Test with stop words
    search_interface.config.stop_words = ["a", "is"]
    tokens = search_interface._tokenize("This is a test")
    assert "this" in tokens
    assert "is" not in tokens
    assert "a" not in tokens
    assert "test" in tokens

    # Test with synonyms
    search_interface.config.synonyms = {"test": ["exam", "check"]}
    tokens = search_interface._tokenize("This is a test")
    assert "this" in tokens
    assert "test" in tokens
    assert "exam" in tokens
    assert "check" in tokens


def test_visualizations_generate_chart_config(visualizations):
    """Test generating chart configuration."""
    # Create test data
    data = [{"x": "A", "y": 10}, {"x": "B", "y": 20}, {"x": "C", "y": 15}]

    # Generate chart config
    config = visualizations._generate_chart_config("bar", data, {})

    # Check config structure
    assert config["type"] == "bar"
    assert "data" in config
    assert "datasets" in config["data"]
    assert "labels" in config["data"]
    assert len(config["data"]["datasets"]) == 1
    assert config["data"]["datasets"][0]["data"] == [10, 20, 15]  # y values
    assert config["data"]["labels"] == ["A", "B", "C"]  # x values
    assert config["options"]["responsive"] is True
    assert (
        config["options"]["animation"]["duration"]
        == visualizations.config.animation_duration
    )

    # Test with custom options
    custom_options = {"width": 1000, "height": 500, "title": "Custom Chart"}

    config = visualizations._generate_chart_config("line", data, custom_options)

    assert config["type"] == "line"
    assert config["options"]["width"] == 1000
    assert config["options"]["height"] == 500
    assert config["options"]["title"] == "Custom Chart"


def test_visualizations_generate_graph_config(visualizations):
    """Test generating graph configuration."""
    # Create test data
    data = {
        "nodes": [
            {"id": "A", "name": "Node A"},
            {"id": "B", "name": "Node B"},
            {"id": "C", "name": "Node C"},
        ],
        "links": [
            {"source": "A", "target": "B", "value": 1},
            {"source": "B", "target": "C", "value": 2},
            {"source": "C", "target": "A", "value": 3},
        ],
    }

    # Generate graph config
    config = visualizations._generate_graph_config(data, {})

    # Check config structure
    assert config["type"] == "network"  # The actual implementation returns "network"
    assert "data" in config
    assert "nodes" in config["data"]
    assert "links" in config["data"]
    assert len(config["data"]["nodes"]) == 3
    assert len(config["data"]["links"]) == 3
    assert config["options"]["responsive"] is True
    assert config["options"]["nodeSize"] == 10
    assert config["options"]["linkDistance"] == 50

    # Test with custom options
    custom_options = {"nodeSize": 20, "linkWidth": 2, "title": "Custom Graph"}

    config = visualizations._generate_graph_config(data, custom_options)

    assert config["options"]["nodeSize"] == 20
    assert config["options"]["linkWidth"] == 2
    assert config["options"]["title"] == "Custom Graph"


def test_visualizations_generate_table_config(visualizations):
    """Test generating table configuration."""
    # Create test data
    data = [
        {"id": 1, "name": "Item 1", "value": 10},
        {"id": 2, "name": "Item 2", "value": 20},
        {"id": 3, "name": "Item 3", "value": 30},
    ]

    # Generate table config
    config = visualizations._generate_table_config(data, {})

    # Check config structure
    assert config["type"] == "table"
    assert "data" in config
    assert "head" in config["data"]
    assert "body" in config["data"]
    assert len(config["data"]["head"]) == 1  # One header row
    assert len(config["data"]["head"][0]) == 3  # Three columns
    assert len(config["data"]["body"]) == 3  # Three data rows
    assert len(config["options"]["columns"]) == 3
    assert config["options"]["columns"][0]["field"] == "id"
    assert config["options"]["columns"][1]["field"] == "name"
    assert config["options"]["columns"][2]["field"] == "value"
    assert config["options"]["responsive"] is True

    # Test with custom options
    custom_options = {"pageSize": 5, "title": "Custom Table"}

    config = visualizations._generate_table_config(data, custom_options)

    assert config["options"]["pageSize"] == 5
    assert config["options"]["title"] == "Custom Table"
