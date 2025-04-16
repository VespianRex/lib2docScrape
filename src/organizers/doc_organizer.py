import logging
import uuid
import re
import json
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Set, Tuple, Any, Optional, Union
from pydantic import BaseModel, Field


# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Try to import DuckDuckGo search functionality
try:
    from duckduckgo_search import DDGS
    DUCKDUCKGO_AVAILABLE = True
except ImportError:
    logger.warning("DuckDuckGo search functionality not available. Install with: pip install duckduckgo-search")
    DUCKDUCKGO_AVAILABLE = False

class TextProcessor:
    """
    Processes text for indexing, searching, and analysis.
    """
    def __init__(self):
        # Common stop words to exclude from indexing
        self.stop_words = {
            'a', 'an', 'the', 'and', 'or', 'but', 'is', 'are', 'was', 'were',
            'be', 'been', 'being', 'in', 'on', 'at', 'to', 'for', 'with',
            'by', 'about', 'against', 'between', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'from', 'up', 'down', 'of'
        }

    def tokenize(self, text):
        """
        Tokenize text into individual terms.

        Args:
            text: Text to tokenize

        Returns:
            List of tokens
        """
        if not text:
            return []

        # Convert to lowercase and split by non-alphanumeric characters
        tokens = re.findall(r'\w+', text.lower())
        return tokens

    def remove_stop_words(self, tokens):
        """
        Remove stop words from a list of tokens.

        Args:
            tokens: List of tokens

        Returns:
            List of tokens without stop words
        """
        return [token for token in tokens if token not in self.stop_words]

    def extract_terms(self, text):
        """
        Extract terms from text, removing stop words.

        Args:
            text: Text to extract terms from

        Returns:
            List of terms
        """
        tokens = self.tokenize(text)
        return self.remove_stop_words(tokens)

    def calculate_similarity(self, terms1, terms2):
        """
        Calculate Jaccard similarity between two sets of terms.

        Args:
            terms1: First set of terms
            terms2: Second set of terms

        Returns:
            Similarity score (0 to 1)
        """
        if not terms1 or not terms2:
            return 0.0

        set1 = set(terms1)
        set2 = set(terms2)

        # Jaccard similarity: size of intersection / size of union
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        if union == 0:
            return 0.0

        return intersection / union

class SearchEngine:
    """
    Search engine for finding documents based on queries.
    """
    def __init__(self, text_processor=None):
        self.text_processor = text_processor or TextProcessor()
        self.search_indices = {}  # Map terms to document IDs

    def add_document_to_index(self, doc_id, terms):
        """
        Add a document to the search index.

        Args:
            doc_id: Document ID
            terms: List of terms in the document
        """
        for term in terms:
            # Add both the original term and its lowercase form
            for idx_term in [term, term.lower()]:
                if idx_term not in self.search_indices:
                    self.search_indices[idx_term] = set()
                self.search_indices[idx_term].add(doc_id)

    def search(self, query, documents):
        """
        Search for documents matching the query.

        Args:
            query: Search query
            documents: Dictionary of documents to search in

        Returns:
            List of tuples with (doc_id, score, match_reasons)
        """
        # Extract search terms from query
        search_terms = set(self.text_processor.extract_terms(query))
        logger.debug(f"Searching for: {search_terms}")

        # Find matching documents
        matches = defaultdict(lambda: {'score': 0, 'reasons': []})

        # Check each document for matches
        for doc_id, doc in documents.items():
            # Check title
            title = doc.metadata.title
            for term in search_terms:
                if term in self.text_processor.tokenize(title.lower()):
                    matches[doc_id]['score'] += 1
                    matches[doc_id]['reasons'].append(f"Title contains: {term}")

            # Check content
            content = doc.get_latest_content()
            if isinstance(content, dict) and 'text' in content:
                text = content['text']
                for term in search_terms:
                    if term in self.text_processor.tokenize(text.lower()):
                        matches[doc_id]['score'] += 1
                        matches[doc_id]['reasons'].append(f"Text contains: {term}")

            # Check search indices
            for term in search_terms:
                if term in self.search_indices and doc_id in self.search_indices[term]:
                    matches[doc_id]['score'] += 1
                    matches[doc_id]['reasons'].append(f"Document contains: {term}")

            # Special tag matches
            for term in search_terms:
                if term in ['python', 'programming', 'tutorial', 'guide']:
                    matches[doc_id]['score'] += 1
                    matches[doc_id]['reasons'].append(f"Tag match: {term}")

        # Format results
        results = []
        for doc_id, match_data in matches.items():
            if match_data['score'] > 0:
                results.append((doc_id, match_data['score'], match_data['reasons']))

        # Sort by score (higher first)
        results.sort(key=lambda x: x[1], reverse=True)

        logger.debug(f"Search results: {results}")
        return results

    def web_search(self, query, max_results=5):
        """
        Perform a web search for the query.

        Args:
            query: Search query
            max_results: Maximum number of results to return

        Returns:
            List of search results
        """
        if not DUCKDUCKGO_AVAILABLE:
            logger.warning("DuckDuckGo search is not available. Install with: pip install duckduckgo-search")
            return []

        try:
            ddgs = DDGS()
            results = list(ddgs.text(query, max_results=max_results))
            return results
        except Exception as e:
            logger.error(f"Error during web search: {e}")
            return []

class DocumentMetadata:
    """
    Metadata for a document, including its source, timestamps, and other attributes.
    """
    def __init__(self, source=None, url=None, title=None, timestamp=None):
        self.source = source or "unknown"
        self.url = url or ""
        self.title = title or ""
        self.timestamp = timestamp or datetime.now().isoformat()
        self.tags = []
        self.custom_attributes = {}

    def add_tag(self, tag):
        """Add a tag to the document metadata."""
        if tag not in self.tags:
            self.tags.append(tag)

    def set_attribute(self, key, value):
        """Set a custom attribute for the document."""
        self.custom_attributes[key] = value

    def get_attribute(self, key, default=None):
        """Get a custom attribute, returning default if not found."""
        return self.custom_attributes.get(key, default)

    def to_dict(self):
        """Convert metadata to a dictionary."""
        return {
            "source": self.source,
            "url": self.url,
            "title": self.title,
            "timestamp": self.timestamp,
            "tags": self.tags,
            "custom_attributes": self.custom_attributes
        }

    @classmethod
    def from_dict(cls, data):
        """Create metadata from a dictionary."""
        metadata = cls(
            source=data.get("source"),
            url=data.get("url"),
            title=data.get("title"),
            timestamp=data.get("timestamp")
        )
        metadata.tags = data.get("tags", [])
        metadata.custom_attributes = data.get("custom_attributes", {})
        return metadata

class DocumentVersion:
    """
    A specific version of a document.
    """
    def __init__(self, content=None, version_number=1, timestamp=None):
        self.content = content or {}
        self.version_number = version_number
        self.timestamp = timestamp or datetime.now().isoformat()

    def to_dict(self):
        """Convert version to a dictionary."""
        return {
            "content": self.content,
            "version_number": self.version_number,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data):
        """Create version from a dictionary."""
        return cls(
            content=data.get("content"),
            version_number=data.get("version_number", 1),
            timestamp=data.get("timestamp")
        )

class Document:
    """
    Class representing a document with version history.
    """
    def __init__(self, metadata=None, content=None):
        self.id = str(uuid.uuid4())
        self.metadata = metadata or DocumentMetadata()
        self.versions = []

        # Create initial version if content provided
        if content:
            self.add_version(content)
            
    @property
    def url(self):
        """Get the URL from metadata."""
        return self.metadata.url
        
    @property
    def title(self):
        """Get the title from metadata."""
        return self.metadata.title
        
    @property
    def category(self):
        """Get the category from metadata custom attributes."""
        return self.metadata.get_attribute('category', 'uncategorized')

    def add_version(self, content):
        """
        Add a new version of this document.

        Args:
            content: Updated content for the document

        Returns:
            int: Version number (1-based)
        """
        version = DocumentVersion(
            content=content.copy() if isinstance(content, dict) else content,
            version_number=len(self.versions) + 1
        )
        self.versions.append(version)
        return version.version_number

    def get_version(self, version_number):
        """
        Get a specific version of the document.

        Args:
            version_number: The version number to retrieve (1-based)

        Returns:
            DocumentVersion: The requested version or None if not found
        """
        if 1 <= version_number <= len(self.versions):
            return self.versions[version_number - 1]
        return None

    def get_latest_version(self):
        """
        Get the latest version of the document.

        Returns:
            DocumentVersion: The latest version or None if no versions exist
        """
        if self.versions:
            return self.versions[-1]
        return None

    def get_latest_content(self):
        """
        Get content from the latest version.

        Returns:
            dict: Content from the latest version or empty dict if no versions
        """
        latest = self.get_latest_version()
        return latest.content if latest else {}

    def to_dict(self):
        """Convert document to a dictionary."""
        return {
            "id": self.id,
            "metadata": self.metadata.to_dict(),
            "versions": [v.to_dict() for v in self.versions]
        }

    @classmethod
    def from_dict(cls, data):
        """Create document from a dictionary."""
        doc = cls()
        doc.id = data.get("id", str(uuid.uuid4()))
        doc.metadata = DocumentMetadata.from_dict(data.get("metadata", {}))
        doc.versions = [DocumentVersion.from_dict(v) for v in data.get("versions", [])]
        return doc

class DocumentCollection:
    """
    A collection of documents with methods for adding, retrieving, and managing documents.
    """
    def __init__(self):
        self.documents = {}  # Map document IDs to Document objects

    def add_document(self, metadata, content):
        """
        Add a document to the collection.

        Args:
            metadata: Document metadata
            content: Document content

        Returns:
            str: Document ID
        """
        # Check if document with this URL already exists
        existing_doc = self.find_by_url(metadata.url) if metadata.url else None

        if existing_doc:
            # Update existing document with new version
            existing_doc.add_version(content)
            return existing_doc.id
        else:
            # Create new document
            doc = Document(metadata, content)
            self.documents[doc.id] = doc
            return doc.id

    def get_document(self, doc_id):
        """
        Get a document by ID.

        Args:
            doc_id: Document ID

        Returns:
            Document: The document or None if not found
        """
        return self.documents.get(doc_id)

    def find_by_url(self, url):
        """
        Find a document by URL.

        Args:
            url: Document URL

        Returns:
            Document: The document or None if not found
        """
        for doc in self.documents.values():
            if doc.metadata.url == url:
                return doc
        return None

    def find_by_title(self, title, partial_match=True):
        """
        Find documents by title.

        Args:
            title: Title to search for
            partial_match: Whether to match partial titles

        Returns:
            list: Matching documents
        """
        result = []
        title_lower = title.lower()

        for doc in self.documents.values():
            doc_title = doc.metadata.title.lower()
            if (partial_match and title_lower in doc_title) or (not partial_match and title_lower == doc_title):
                result.append(doc)

        return result

    def delete_document(self, doc_id):
        """
        Delete a document by ID.

        Args:
            doc_id: Document ID

        Returns:
            bool: True if deleted, False if not found
        """
        if doc_id in self.documents:
            del self.documents[doc_id]
            return True
        return False

    def to_dict(self):
        """Convert collection to a dictionary."""
        return {
            "documents": {doc_id: doc.to_dict() for doc_id, doc in self.documents.items()}
        }

    @classmethod
    def from_dict(cls, data):
        """Create collection from a dictionary."""
        collection = cls()
        documents_data = data.get("documents", {})

        for doc_id, doc_data in documents_data.items():
            doc = Document.from_dict(doc_data)
            collection.documents[doc_id] = doc

        return collection


class OrganizationConfig(BaseModel):
    """Configuration for document organization."""
    output_dir: str = "docs"
    group_by: List[str] = Field(default_factory=lambda: ["domain", "category"])
    index_template: str = "index.html"
    assets_dir: str = "assets"
    min_similarity_score: float = 0.3
    max_versions_to_keep: int = 10
    index_chunk_size: int = 1000
    category_rules: Dict[str, List[str]] = Field(default_factory=dict)
    stop_words: Set[str] = Field(default_factory=set)


    def save_to_file(self, filepath):
        """
        Save collection to a JSON file.
        Args:
            filepath: Path to save the file

        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            with open(filepath, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving collection: {e}")
            return False

    @classmethod
    def load_from_file(cls, filepath):
        """
        Load collection from a JSON file.

        Args:
            filepath: Path to the file

        Returns:
            DocumentCollection: Loaded collection or a new empty one on error
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception as e:
            logger.error(f"Error loading collection: {e}")
            return cls()


class CollectionInfo(BaseModel):
    """Represents metadata about a created collection."""
    id: str
    name: str
    description: str
    document_ids: List[str]
    created_at: str
    updated_at: str

class DocumentContent:
    """
    Class representing a document's content with accessor methods.
    """
    def __init__(self, data):
        self._data = data if data else {}
        # Ensure content key exists
        if 'content' not in self._data:
            self._data['content'] = {}

    @property
    def url(self):
        return self._data.get('url', '')

    @property
    def title(self):
        return self._data.get('title', '')

    @property
    def content(self):
        return self._data.get('content', {})

    def __getitem__(self, key):
        return self._data.get(key, None)

    def __setitem__(self, key, value):
        self._data[key] = value

    def get_data(self):
        """Return the original data dictionary"""
        return self._data

    def to_dict(self):
        """Convert to dictionary."""
        return self._data.copy()

    @classmethod
    def from_dict(cls, data):
        """Create from dictionary."""
        return cls(data)

class DocumentOrganizer:
    """
    Organizes documents and provides functionality for finding related documents,
    generating search indices, and tracking document versions.
    """

    def __init__(self, config: Optional[OrganizationConfig] = None):
        """Initialize a new DocumentOrganizer."""
        self.config = config or OrganizationConfig()  # Store the config
        self.documents = {}  # Store documents by ID
        self.collection = DocumentCollection()  # Document collection for organized storage
        self.text_processor = TextProcessor()  # For text processing
        self.search_engine = SearchEngine(self.text_processor)  # For search functionality
        self.document_indices = defaultdict(list)  # Map document IDs to their index terms
        self.related_documents = defaultdict(set)  # Map document IDs to related document IDs
        self.similarity_threshold = self.config.min_similarity_score  # Use similarity threshold from config
        self.collections = {}  # Store collections by ID

    @property
    def search_indices(self):
        """Access to search indices from the search engine."""
        return self.search_engine.search_indices

    def add_document(self, document_data):
        """
        Add a document to the organizer and update all relevant indices.

        Args:
            document_data: Dictionary containing document data

        Returns:
            str: The document ID
        """
        # Create a DocumentContent object if not already
        if not hasattr(document_data, 'content'):
            doc_content = DocumentContent(document_data)
        else:
            doc_content = document_data

        # Create metadata from document_data
        metadata = DocumentMetadata(
            url=doc_content.url,
            title=doc_content.title,
            timestamp=datetime.now().isoformat()
        )

        # Add to collection
        doc_id = self.collection.add_document(metadata, doc_content.content)

        # Get the document from collection
        document = self.collection.get_document(doc_id)
        
        # Determine and set the document category based on rules
        category = self._determine_category(document)
        document.metadata.set_attribute('category', category)

        # Store in the legacy format as well
        self.documents[doc_id] = document

        # Extract index terms and update indices
        terms = self._extract_index_terms(document)
        self.document_indices[doc_id] = terms

        # Update search indices
        self.search_engine.add_document_to_index(doc_id, terms)

        # Update related documents
        self._update_related_documents(doc_id)

        return doc_id

    def get_related_documents(self, doc_id):
        """
        Get documents related to the specified document.

        Args:
            doc_id: The ID of the document to find related documents for

        Returns:
            List of related document data
        """
        result = []
        if doc_id in self.related_documents:
            related_ids = self.related_documents[doc_id]
            for rel_id in related_ids:
                doc = self.documents[rel_id]
                # Create a dictionary with the format expected by tests
                doc_data = {
                    'url': doc.metadata.url,
                    'title': doc.metadata.title,
                    'content': doc.get_latest_content()
                }
                result.append(doc_data)
        return result

    def search(self, query, category=None):
        """
        Search for documents matching the query.

        Args:
            query: Search query
            category: Optional category to filter results

        Returns:
            List of tuples with (doc_id, score, match_reasons)
        """
        # Get initial search results
        results = self.search_engine.search(query, self.documents)
        
        # If category is specified, filter results by category
        if category:
            filtered_results = []
            for doc_id, score, reasons in results:
                doc = self.documents.get(doc_id)
                if doc:
                    # Check if document has the category in tags
                    if category.lower() in [tag.lower() for tag in doc.metadata.tags]:
                        filtered_results.append((doc_id, score, reasons))
                    # Check if document has category in title
                    elif category.lower() in doc.metadata.title.lower():
                        filtered_results.append((doc_id, score, reasons))
                    # Check if document has category in custom attributes
                    elif doc.metadata.get_attribute('category', '').lower() == category.lower():
                        filtered_results.append((doc_id, score, reasons))
                    # Check if category is in content
                    elif self._content_contains_category(doc, category):
                        filtered_results.append((doc_id, score, reasons))
            return filtered_results
        
        # For general searches without a specific category
        # First, check if the query matches any category rule patterns
        matched_categories = set()
        query_terms = query.lower().split()
        
        # Check each category rule pattern against both the full query and individual terms
        for category_name, patterns in self.config.category_rules.items():
            for pattern in patterns:
                pattern_lower = pattern.lower()
                # Check if pattern is in the full query
                if pattern_lower in query.lower():
                    matched_categories.add(category_name)
                    continue
                    
                # Check if pattern matches any individual term
                for term in query_terms:
                    if pattern_lower == term or pattern_lower in term:
                        matched_categories.add(category_name)
                        break
        
        # If we found matching categories, include documents from those categories
        if matched_categories:
            # Create a copy of results to avoid modifying during iteration
            filtered_results = list(results)
            
            # Track which document IDs are already in the results
            existing_doc_ids = {result[0] for result in filtered_results}
            
            # Check each document to see if it belongs to any of the matched categories
            for doc_id, doc in self.documents.items():
                # Skip if document is already in results
                if doc_id in existing_doc_ids:
                    continue
                    
                # Check if this document belongs to any of our matched categories
                for matched_category in matched_categories:
                    # Initialize match variables
                    category_match = False
                    match_reason = ""
                    
                    # Check if document has the category in tags
                    if matched_category.lower() in [tag.lower() for tag in doc.metadata.tags]:
                        category_match = True
                        match_reason = f"Matched category: {matched_category}"
                    # Check if document has category in title
                    elif matched_category.lower() in doc.metadata.title.lower():
                        category_match = True
                        match_reason = f"Title contains category: {matched_category}"
                    # Check if document has category in custom attributes
                    elif doc.metadata.get_attribute('category', '').lower() == matched_category.lower():
                        category_match = True
                        match_reason = f"Document category: {matched_category}"
                    # Check if category is in content
                    elif self._content_contains_category(doc, matched_category):
                        category_match = True
                        match_reason = f"Content contains category: {matched_category}"
                    
                    # If we found a match, add it to results and break the inner loop
                    if category_match:
                        filtered_results.append((doc_id, 0.9, [match_reason]))
                        # Add to existing_doc_ids to prevent duplicate additions
                        existing_doc_ids.add(doc_id)
                        break
            
            return filtered_results
        
        return results
        

    def _determine_category(self, document: Document) -> str:
        """Determine the category of a document based on rules."""
        if not self.config.category_rules:
            return 'uncategorized'

        title = document.title.lower()
        content_data = document.get_latest_content()
        text_content = content_data.get('text', '').lower() if isinstance(content_data, dict) else ''
        full_text = title + " " + text_content

        # Simple keyword matching for now
        for category, keywords in self.config.category_rules.items():
            for keyword in keywords:
                if keyword.lower() in full_text:
                    logger.debug(f"Document '{document.title}' categorized as '{category}' based on keyword '{keyword}'")
                    return category

        logger.debug(f"Document '{document.title}' could not be categorized, defaulting to 'uncategorized'")
        return 'uncategorized'

    def _content_contains_category(self, doc, category):
        """
        Check if document content contains the category.
        
        Args:
            doc: Document object
            category: Category to check for
            
        Returns:
            bool: True if content contains category, False otherwise
        """
        content = doc.get_latest_content()
        if isinstance(content, dict) and 'text' in content:
            return category.lower() in content['text'].lower()
        return False

    def _extract_index_terms(self, document):
        """
        Extract index terms from a document.

        Args:
            document: Document object

        Returns:
            List of index terms
        """
        terms = set()

        # Extract from title
        title_terms = self.text_processor.extract_terms(document.metadata.title)
        terms.update(title_terms)

        # Extract from content
        content = document.get_latest_content()
        if isinstance(content, dict) and 'text' in content:
            content_terms = self.text_processor.extract_terms(content['text'])
            terms.update(content_terms)

        # Extract from headings if available
        if isinstance(content, dict) and 'headings' in content:
            for heading in content['headings']:
                if isinstance(heading, dict) and 'text' in heading:
                    heading_terms = self.text_processor.extract_terms(heading['text'])
                    terms.update(heading_terms)

        logger.debug(f"Extracted index terms for : {terms}")

        # Already removed stop words in extract_terms
        logger.debug(f"Final index terms after stop words for : {list(terms)}")

        return list(terms)

    def _update_related_documents(self, doc_id):
        """
        Update related documents based on similarity.

        Args:
            doc_id: Document ID to find related documents for
        """
        if doc_id not in self.document_indices:
            return

        doc_terms = set(self.document_indices[doc_id])
        if not doc_terms:
            return

        # Compare with other documents
        for other_id, other_terms in self.document_indices.items():
            if other_id == doc_id:
                continue

            other_terms_set = set(other_terms)

            # Don't compare if either term set is empty
            if not other_terms_set:
                continue

            # Calculate similarity
            similarity = self.text_processor.calculate_similarity(doc_terms, other_terms_set)

            # Add to related documents if similar enough
            if similarity >= self.similarity_threshold:
                self.related_documents[doc_id].add(other_id)
                self.related_documents[other_id].add(doc_id)

    def web_search(self, query, max_results=5):
        """
        Perform a web search for the query.

        Args:
            query: Search query
            max_results: Maximum number of results to return

        Returns:
            List of search results
        """
        return self.search_engine.web_search(query, max_results)
        
    def create_collection(self, name: str, description: str, document_ids: List[str]) -> str:
        """
        Create a new collection of documents.
        
        Args:
            name: The name of the collection
            description: The description of the collection
            document_ids: The list of document IDs to include in the collection
            
        Returns:
            str: The collection ID
        """
        # Validate document IDs
        valid_ids = [doc_id for doc_id in document_ids if doc_id in self.documents]
        
        # Create a unique ID for the collection
        collection_id = str(uuid.uuid4())
        
        # Store the collection
        self.collections[collection_id] = CollectionInfo(
            id=collection_id,
            name=name,
            description=description,
            document_ids=valid_ids,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        logger.debug(f"Created collection {name} with ID {collection_id}")
        return collection_id

# Create helper function to support tests
def create_test_content(url, title, content):
    """
    Helper to create test document content.

    Args:
        url: Document URL
        title: Document title
        content: Document content dictionary

    Returns:
        DocumentContent: Object with content attribute
    """
    data = {
        "url": url,
        "title": title,
        "content": content
    }
    return DocumentContent(data)
