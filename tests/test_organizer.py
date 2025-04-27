"""Tests for the document organizer component."""

from datetime import datetime, timedelta
from typing import Dict, List

import pytest

from src.organizers.doc_organizer import (DocumentCollection, DocumentMetadata,
                                       DocumentOrganizer, DocumentVersion,
                                       OrganizationConfig, SearchEngine)
from src.processors.content_processor import ProcessedContent
from tests.test_helpers import create_test_content




def test_document_organizer_initialization():
    """Test document organizer initialization and configuration."""
    # Test with default config
    organizer = DocumentOrganizer()
    assert organizer.config is not None
    assert len(organizer.documents) == 0
    assert len(organizer.collections) == 0
    assert len(organizer.search_indices) == 0
    
    # Test with custom config
    custom_config = OrganizationConfig(
        min_similarity_score=0.4,
        max_versions_to_keep=3,
        index_chunk_size=500,
        category_rules={
            "test": ["test", "example"]
        }
    )
    organizer = DocumentOrganizer(config=custom_config)
    assert organizer.config == custom_config
    assert organizer.config.max_versions_to_keep == 3


def test_document_version_management():
    """Test document version creation and management."""
    organizer = DocumentOrganizer()
    
    # Add initial version
    content = create_test_content(
        url="https://example.com/doc",
        title="Test Document",
        content={"text": "Version 1"}
    )
    doc_id = organizer.add_document(content)
    
    assert doc_id in organizer.documents
    assert len(organizer.documents[doc_id].versions) == 1
    
    # Add new version
    content.content["text"] = "Version 2"
    organizer.add_document(content)
    
    assert len(organizer.documents[doc_id].versions) == 2
    assert organizer.documents[doc_id].versions[-1].version_id == "v2"
    
    # Test version limit
    for i in range(10):  # Add more versions than max_versions_to_keep
        content.content["text"] = f"Version {i+3}"
        organizer.add_document(content)
    
    assert len(organizer.documents[doc_id].versions) == organizer.config.max_versions_to_keep


def test_document_categorization():
    """Test document categorization logic."""
    organizer = DocumentOrganizer(
        config=OrganizationConfig(
            category_rules={
                "api": ["api", "reference"],
                "guide": ["guide", "tutorial"],
                "example": ["example", "sample"]
            }
        )
    )
    
    # Test API category
    api_content = create_test_content(
        url="https://example.com/api/v1",
        title="API Reference",
        content={"text": "API documentation"}
    )
    api_doc_id = organizer.add_document(api_content)
    assert organizer.documents[api_doc_id].category == "api"
    
    # Test guide category
    guide_content = create_test_content(
        url="https://example.com/guide",
        title="User Guide",
        content={"text": "Tutorial content"}
    )
    guide_doc_id = organizer.add_document(guide_content)
    assert organizer.documents[guide_doc_id].category == "guide"
    
    # Test uncategorized
    misc_content = create_test_content(
        url="https://example.com/misc",
        title="Miscellaneous",
        content={"text": "Random content"}
    )
    misc_doc_id = organizer.add_document(misc_content)
    assert organizer.documents[misc_doc_id].category is None


def test_reference_extraction():
    """Test cross-reference extraction."""
    organizer = DocumentOrganizer()
    
    # Create content with various references
    content = create_test_content(
        url="https://example.com/doc",
        title="Test Document",
        content={
            "links": [
                {"url": "https://example.com/internal", "type": "internal"},
                {"url": "https://external.com", "type": "external"}
            ],
            "code_blocks": [
                {"language": "python", "content": "import test"}
            ]
        }
    )
    
    doc_id = organizer.add_document(content)
    references = organizer.documents[doc_id].references
    
    assert "internal" in references
    assert "external" in references
    assert "code" in references
    assert len(references["internal"]) == 1
    assert len(references["external"]) == 1


def test_search_functionality():
    """Test document search functionality."""
    organizer = DocumentOrganizer()
    
    # Add documents with different content
    doc1 = create_test_content(
        url="https://example.com/doc1",
        title="Python Programming",
        content={
            "text": "Guide to Python programming language",
            "code_blocks": [{"language": "python", "content": "print('Hello')"}]
        }
    )
    doc2 = create_test_content(
        url="https://example.com/doc2",
        title="JavaScript Tutorial",
        content={
            "text": "Learn JavaScript programming",
            "code_blocks": [{"language": "javascript", "content": "console.log('Hello')"}]
        }
    )
    
    organizer.add_document(doc1)
    organizer.add_document(doc2)
    
    # Search for Python-related content
    python_results = organizer.search("python programming")
    assert len(python_results) > 0
    assert any("python" in r[2][0].lower() for r in python_results)
    
    # Search with category filter
    js_results = organizer.search("javascript", category="guide")
    assert len(js_results) > 0
    assert any("javascript" in r[2][0].lower() for r in js_results)


def test_collection_management():
    """Test document collection management."""
    organizer = DocumentOrganizer()
    
    # Create test documents
    docs = [
        create_test_content(
            url=f"https://example.com/doc{i}",
            title=f"Document {i}",
            content={"text": f"Content {i}"}
        )
        for i in range(3)
    ]
    
    doc_ids = [organizer.add_document(doc) for doc in docs]
    
    # Create collection
    collection_id = organizer.create_collection(
        "Test Collection",
        "Test collection description",
        doc_ids
    )
    
    assert collection_id in organizer.collections
    assert len(organizer.collections[collection_id].documents) == 3
    assert organizer.collections[collection_id].name == "Test Collection"



def test_document_similarity():
    """Test document similarity detection."""
    organizer = DocumentOrganizer()
    
    # Create similar documents
    doc1 = create_test_content(
        url="https://example.com/doc1",
        title="Python Guide",
        content={"text": "Guide to Python programming basics and fundamentals"}
    )
    
    doc2 = create_test_content(
        url="https://example.com/doc2",
        title="Python Tutorial",
        content={"text": "Tutorial about Python programming basics"}
    )
    
    id1 = organizer.add_document(doc1)
    id2 = organizer.add_document(doc2)
    
    # Find related documents
    related = organizer.get_related_documents(id1)
    assert len(related) > 0
    assert id2 in [doc_id for doc_id, _ in related]


def test_version_tracking():
    """Test document version tracking."""
    organizer = DocumentOrganizer()
    
    # Create initial version
    content = create_test_content(
        url="https://example.com/doc",
        title="Test Document",
        content={"text": "Initial version"}
    )
    doc_id = organizer.add_document(content)
    
    # Create multiple versions
    versions = []
    for i in range(3):
        content.content["text"] = f"Version {i+1}"
        organizer.add_document(content)
        versions.append(content.content["text"])
    
    # Check version history
    doc_versions = organizer.get_document_versions(doc_id)
    assert len(doc_versions) > 0
    assert all(isinstance(v, DocumentVersion) for v in doc_versions)
    
    # Verify version order
    assert doc_versions[-1].version_id > doc_versions[0].version_id


def test_search_index_generation():
    """Test search index generation and updates."""
    organizer = DocumentOrganizer()
    
    # Add document with searchable content
    content = create_test_content(
        url="https://example.com/doc",
        title="Python Programming Guide",
        content={
            "text": "Comprehensive guide to Python programming",
            "headings": [
                {"level": 1, "text": "Python Basics"},
                {"level": 2, "text": "Variables and Types"}
            ]
        }
    )
    
    organizer.add_document(content)
    
    # Check search indices
    assert len(organizer.search_indices) > 0
    assert any("python" in idx.lower() for idx in organizer.search_indices.keys())
    
    # Verify index structure
    for term, index in organizer.search_indices.items():
        assert isinstance(index, SearchIndex)
        assert index.term == term
        assert len(index.documents) > 0
        assert isinstance(index.context, dict)
