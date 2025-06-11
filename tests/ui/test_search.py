"""
Tests for the search UI module.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.ui.search import (
    SearchConfig,
    SearchInterface,
    SearchResult,
)

# Create a test app with search interface for testing
test_app = FastAPI()
search_interface = SearchInterface(test_app)
client = TestClient(test_app)


def test_search_config_defaults():
    """Test SearchConfig default values."""
    config = SearchConfig()
    assert config.max_results == 20
    assert config.highlight_results is True
    assert config.search_titles is True
    assert config.search_content is True
    assert config.search_metadata is True
    assert config.enable_filters is True
    assert config.enable_sorting is True
    assert config.min_score == 0.1
    assert config.snippet_length == 200


def test_search_config_custom():
    """Test SearchConfig with custom values."""
    config = SearchConfig(
        max_results=50,
        highlight_results=False,
        search_titles=False,
        search_content=False,
        search_metadata=False,
        enable_filters=False,
        enable_sorting=False,
        min_score=0.5,
        snippet_length=100,
    )
    assert config.max_results == 50
    assert config.highlight_results is False
    assert config.search_titles is False
    assert config.search_content is False
    assert config.search_metadata is False
    assert config.enable_filters is False
    assert config.enable_sorting is False
    assert config.min_score == 0.5
    assert config.snippet_length == 100


def test_search_result_model():
    """Test SearchResult model."""
    result = SearchResult(
        id="test-id",  # Added id field
        title="Test Document",
        url="/docs/test",
        content_snippet="This is a test document...",  # Renamed from snippet
        score=0.95,
        # Removed library, version, doc_type, last_updated as they are not in the model
        # highlights and metadata can be tested separately if needed, using default factory here
    )
    assert result.id == "test-id"
    assert result.title == "Test Document"
    assert result.url == "/docs/test"
    assert result.content_snippet == "This is a test document..."
    assert result.score == 0.95


# Remove tests that instantiate SearchUI directly as it's not how it's used.
# Tests should interact with the search functionality via API endpoints.


def test_search_api_basic_query():
    """Test basic search API query."""
    # Add a test document to the search interface
    search_interface.add_document(
        {
            "id": "test-doc-1",
            "title": "Test Document",
            "content": "This is a test document with some content",
            "url": "/docs/test",
        }
    )

    response = client.get("/api/search?q=test")
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "test"
    assert "results" in data
    assert "total_results" in data


def test_search_api_with_limit():
    """Test search API with limit parameter."""
    # Add multiple test documents
    for i in range(10):
        search_interface.add_document(
            {
                "id": f"doc-{i}",
                "title": f"Document {i}",
                "content": f"This is document number {i} with some content",
                "url": f"/docs/doc-{i}",
            }
        )

    response = client.get("/api/search?q=document&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) <= 5


def test_search_api_empty_query():
    """Test search API with an empty query (should fail based on min_length)."""
    # Assuming SearchConfig default min_query_length is > 0
    response = client.get("/api/search?q=")
    assert response.status_code == 422  # FastAPI validation error for query params


def test_suggestions_api():
    """Test suggestions API."""
    # Add a test document for suggestions
    search_interface.add_document(
        {
            "id": "doc-suggestion",
            "title": "Documentation Guide",
            "content": "This is a documentation guide",
            "url": "/docs/guide",
        }
    )

    response = client.get("/api/suggestions?q=doc")
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "doc"
    assert "suggestions" in data


# Further tests would involve:
# - Setting up SearchInterface with known documents.
# - Testing different query parameters (fields, filters, sort, fuzzy).
# - Verifying the content of search results, snippets, and highlights.
# - This might require a fixture that initializes SearchInterface with test data
#   or mocking the _search method of SearchInterface for controlled results.

# Example of how you might test adding a document and then searching,
# if you had a way to access the SearchInterface instance used by the app:
# (This is illustrative and might not work directly without more setup)
# @patch('src.ui.search.SearchInterface.add_document')
# def test_add_document_and_search(mock_add_document):
#     # This test would be more of an integration test for SearchInterface itself
#     # rather than just the API endpoint.
#     pass
