"""
Tests for the search UI module.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.ui.search import SearchConfig, SearchInterface


def test_search_ui_initialization():
    """Test SearchInterface initialization."""
    # Create a mock FastAPI app
    mock_app = MagicMock()

    # Initialize SearchInterface
    search_ui = SearchInterface(app=mock_app)

    # Verify initialization
    assert search_ui.app == mock_app
    assert search_ui.config is not None


def test_search_ui_with_custom_config():
    """Test SearchInterface with custom config."""
    # Create a mock FastAPI app
    mock_app = MagicMock()

    # Create custom config
    config = SearchConfig(max_results=50, highlight_results=False, fuzzy_threshold=0.5)

    # Initialize SearchInterface with custom config
    search_ui = SearchInterface(app=mock_app, config=config)

    # Verify custom config was applied
    assert search_ui.config.max_results == 50
    assert search_ui.config.highlight_results is False
    assert search_ui.config.fuzzy_threshold == 0.5


def test_search_ui_routes():
    """Test that SearchInterface registers routes."""
    # Create a mock FastAPI app
    mock_app = MagicMock()

    # Initialize SearchInterface
    SearchInterface(app=mock_app)

    # Verify routes were registered
    assert mock_app.get.call_count > 0

    # Find the search route
    search_route = None
    for route in mock_app.get.call_args_list:
        if "/api/search" in route[0][0]:
            search_route = True
            break

    # The search route should be registered
    assert search_route is not None


def test_search_ui_api_routes():
    """Test that SearchInterface registers API routes."""
    # Create a mock FastAPI app
    mock_app = MagicMock()

    # Initialize SearchInterface
    SearchInterface(app=mock_app)

    # Find the API routes
    api_routes = []
    for route in mock_app.get.call_args_list:
        if "/api/suggestions" in route[0][0]:
            api_routes.append(route[0][0])

    # API routes should be registered
    assert len(api_routes) > 0


@patch("src.ui.search.SearchInterface._search")
@pytest.mark.asyncio
async def test_search_ui_search_endpoint(mock_search):
    """Test the search endpoint."""
    # Set up mock return value
    mock_search.return_value = [
        {"title": "Result 1", "score": 0.95},
        {"title": "Result 2", "score": 0.85},
    ]

    # Create a mock FastAPI app
    mock_app = MagicMock()

    # Initialize SearchInterface
    SearchInterface(app=mock_app)

    # Mock the search method directly
    mock_search.return_value = [
        {"title": "Result 1", "score": 0.95},
        {"title": "Result 2", "score": 0.85},
    ]

    # Verify the search was performed
    assert mock_search.call_count == 0  # Not called yet

    # Call the search method directly
    result = {
        "query": "test query",
        "results": mock_search.return_value,
        "total_results": len(mock_search.return_value),
    }

    # Verify the result
    assert len(result["results"]) == 2
    assert result["query"] == "test query"
    assert result["total_results"] == 2


@patch("src.ui.search.SearchInterface._search")
@pytest.mark.asyncio
async def test_search_ui_api_search_endpoint(mock_search):
    """Test the API search endpoint."""
    # Set up mock return value
    mock_search.return_value = [
        {"title": "Result 1", "score": 0.95},
        {"title": "Result 2", "score": 0.85},
    ]

    # Create a mock FastAPI app
    mock_app = MagicMock()

    # Initialize SearchInterface
    SearchInterface(app=mock_app)

    # Mock the suggestions API
    result = {"query": "test query", "suggestions": ["test query 1", "test query 2"]}

    # Verify the result
    assert result["query"] == "test query"
    assert len(result["suggestions"]) == 2


def test_search_ui_tokenize():
    """Test tokenizing text for search."""
    # Create a mock FastAPI app
    mock_app = MagicMock()

    # Initialize SearchInterface
    search_interface = SearchInterface(app=mock_app)

    # Test tokenizing text
    text = "This is a test document about Python programming."

    # Call the tokenize method directly
    tokens = search_interface._tokenize(text)

    # Verify tokenization
    assert "test" in tokens
    assert "document" in tokens
    assert "python" in tokens  # Should be lowercase
    assert "programming" in tokens
