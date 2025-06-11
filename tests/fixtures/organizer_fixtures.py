"""Organization testing fixtures."""

from datetime import datetime, timedelta
from typing import Optional

import pytest

from src.organizers.doc_organizer import (
    DocumentCollection,
    DocumentMetadata,
    DocumentVersion,
    SearchIndex,
)
from src.processors.content_processor import ProcessedContent


@pytest.fixture
def create_test_content():
    """Factory to create test content for organizer tests."""

    def _factory(
        url: str = "https://example.com/doc",
        title: str = "Test Document",
        content_type: str = "text/html",
        headings: Optional[list[dict]] = None,
        paragraphs: Optional[list[str]] = None,
        code_blocks: Optional[list[dict]] = None,
        metadata: Optional[dict] = None,
        timestamp: Optional[datetime] = None,
        content: Optional[dict] = None,
    ) -> ProcessedContent:
        """
        Create test content for organizer tests.

        Args:
            url: Document URL
            title: Document title
            content_type: Content MIME type
            headings: List of heading dictionaries
            paragraphs: List of paragraph text
            code_blocks: List of code block dictionaries
            metadata: Additional metadata
            timestamp: Document timestamp

        Returns:
            ProcessedContent object
        """
        headings = headings or [
            {"level": 1, "text": "Main Heading"},
            {"level": 2, "text": "Subheading 1"},
            {"level": 2, "text": "Subheading 2"},
        ]

        paragraphs = paragraphs or [
            "This is the first paragraph of test content.",
            "This is the second paragraph with some more text.",
        ]

        code_blocks = code_blocks or [
            {"language": "python", "code": "def test():\n    return True"},
            {
                "language": "javascript",
                "code": "function test() {\n    return true;\n}",
            },
        ]

        metadata = metadata or {
            "author": "Test Author",
            "description": "Test description for document",
            "keywords": ["test", "document", "example"],
        }

        timestamp = timestamp or datetime.now()

        # Use provided content if given, otherwise build the default structure
        if content is None:
            content = {
                "title": title,
                "headings": headings,
                "content_sections": [
                    {"type": "heading", "content": headings[0]},
                    {"type": "paragraph", "content": paragraphs[0]},
                    {"type": "heading", "content": headings[1]},
                    {"type": "paragraph", "content": paragraphs[1]},
                    {"type": "code", "content": code_blocks[0]},
                    {"type": "heading", "content": headings[2]},
                    {"type": "code", "content": code_blocks[1]},
                ],
                "links": [
                    {
                        "url": "https://example.com/related",
                        "text": "Related Doc",
                        "type": "internal",
                    },
                    {
                        "url": "https://external.com/reference",
                        "text": "External Reference",
                        "type": "external",
                    },
                ],
            }

        # Build the processed content object
        processed_content = ProcessedContent(
            url=url,  # Use the passed url parameter
            title=title,
            content_type=content_type,
            content=content,
            metadata=metadata,
            raw=f"<html><head><title>{title}</title></head><body><p>{paragraphs[0]}</p></body></html>",
            text="\n".join(paragraphs),
            markdown=f"# {title}\n\n{paragraphs[0]}\n\n## {headings[1]['text']}\n\n{paragraphs[1]}",
            timestamp=timestamp,
        )

        return processed_content

    return _factory


@pytest.fixture
def document_version_factory(create_test_content):
    """Factory to create document versions for testing."""

    def _factory(
        url: str = "https://example.com/doc", version_number: int = 1, days_ago: int = 0
    ) -> DocumentVersion:
        """
        Create a document version for testing.

        Args:
            url: Document URL
            version_number: Version number
            days_ago: Number of days ago this version was created

        Returns:
            DocumentVersion object
        """
        timestamp = datetime.now() - timedelta(days=days_ago)
        content = create_test_content(url=url, timestamp=timestamp)

        version = DocumentVersion(
            version=version_number,
            content=content,
            timestamp=timestamp,
            changes={
                "added": ["New section added"] if version_number > 1 else [],
                "removed": ["Removed outdated section"] if version_number > 1 else [],
                "modified": ["Updated code examples"] if version_number > 1 else [],
            },
        )

        return version

    return _factory


@pytest.fixture
def document_collection_factory(document_version_factory):
    """Factory to create document collections for testing."""

    def _factory(
        url: str = "https://example.com/doc",
        num_versions: int = 3,
        category: str = "api",
    ) -> DocumentCollection:
        """
        Create a document collection with versions for testing.

        Args:
            url: Document URL
            num_versions: Number of versions to create
            category: Document category

        Returns:
            DocumentCollection object
        """
        versions = []
        for i in range(num_versions):
            version_num = i + 1
            days_ago = (num_versions - i) * 5  # Spread versions out by 5 days
            versions.append(
                document_version_factory(
                    url=url, version_number=version_num, days_ago=days_ago
                )
            )

        metadata = DocumentMetadata(
            url=url,
            title=versions[0].content.title,
            category=category,
            first_seen=versions[-1].timestamp,
            last_updated=versions[0].timestamp,
            access_count=10,
            importance_score=0.75,
        )

        collection = DocumentCollection(
            metadata=metadata,
            versions=versions,
            related_documents=[f"{url}/related1", f"{url}/related2"],
        )

        return collection

    return _factory


@pytest.fixture
def search_index_factory(document_collection_factory):
    """Factory to create search indices for testing."""

    def _factory(num_documents: int = 5) -> SearchIndex:
        """
        Create a search index with documents for testing.

        Args:
            num_documents: Number of documents to add to the index

        Returns:
            SearchIndex object
        """
        index = SearchIndex()

        for i in range(num_documents):
            url = f"https://example.com/doc{i + 1}"
            category = ["api", "tutorial", "reference", "guide", "faq"][i % 5]
            collection = document_collection_factory(url=url, category=category)

            # Add document text to the index
            doc_text = collection.versions[0].content.text
            index.add_document(url, doc_text)

        return index

    return _factory
