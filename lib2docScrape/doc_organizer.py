import logging
import uuid
import re
from collections import defaultdict
from typing import Dict, List, Set, Any, Optional, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Document:
    """
    Class representing a document with versioning support.
    """
    def __init__(self, data: Dict[str, Any]):
        """
        Initialize a document with its data and create the first version.
        
        Args:
            data: Dictionary containing document data (url, title, content)
        """
        self.url = data.get('url', '')
        self.title = data.get('title', '')
        self.content = data.get('content', {})
        self.versions = []
        
        # Create initial version
        self.add_version(self.content)
    
    def add_version(self, content: Dict[str, Any]) -> int:
        """
        Add a new version of this document.
        
        Args:
            content: Updated content for the document
            
        Returns:
            int: Version number (1-based)
        """
        timestamp = datetime.now().isoformat()
        version = {
            'content': content.copy(),
            'timestamp': timestamp,
            'version_number': len(self.versions) + 1
        }
        
        self.versions.append(version)
        
        # Update current content
        self.content = content.copy()
        
        return version['version_number']
    
    def get_version(self, version_number: int) -> Dict[str, Any]:
        """
        Get a specific version of the document.
        
        Args:
            version_number: The version number to retrieve (1-based)
            
        Returns:
            Dict[str, Any]: The requested version or None if not found
        """
        if 1 <= version_number <= len(self.versions):
            return self.versions[version_number - 1]
        return None
    
    def get_latest_version(self) -> Dict[str, Any]:
        """
        Get the latest version of the document.
        
        Returns:
            Dict[str, Any]: The latest version or None if no versions exist
        """
        if self.versions:
            return self.versions[-1]
        return None

class DocumentOrganizer:
    """
    Organizes documents and provides functionality for finding related documents,
    tracking document versions, and generating search indices.
    """
    
    def __init__(self):
        """Initialize a new DocumentOrganizer."""
        self.documents = {}  # Store documents by ID
        self.document_indices = {}  # Map document IDs to their index terms
        self.search_indices = {}  # Map terms to document IDs
        self.related_documents = defaultdict(set)  # Map document IDs to related document IDs
        self.similarity_threshold = 0.3  # Similarity threshold for relatedness
        
        # Common stop words to exclude from indexing
        self.stop_words = {
            'a', 'an', 'the', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 
            'be', 'been', 'being', 'in', 'on', 'at', 'to', 'for', 'with', 
            'by', 'about', 'against', 'between', 'into', 'through', 'during', 
            'before', 'after', 'above', 'below', 'from', 'up', 'down', 'of'
        }
    
    def add_document(self, document_data: Dict[str, Any]) -> str:
        """
        Add a document to the organizer and update all relevant indices.
        
        Args:
            document_data: Dictionary containing document data (url, title, content)
            
        Returns:
            str: The generated document ID
        """
        # Check if this document is a new version of an existing one
        url = document_data.get('url', '')
        existing_id = self._find_document_by_url(url)
        
        if existing_id:
            # Update existing document with a new version
            document = self.documents[existing_id]
            document.add_version(document_data.get('content', {}))
            doc_id = existing_id
        else:
            # Generate a unique ID for the new document
            doc_id = str(uuid.uuid4())
            
            # Create and store the document
            document = Document(document_data)
            self.documents[doc_id] = document
        
        # Extract index terms
        terms = self._extract_index_terms(document)
        
        # Store index terms for this document
        self.document_indices[doc_id] = terms
        
        # Update search indices
        self._update_search_indices(doc_id, terms)
        
        # Update related documents based on similarity
        self._update_related_documents(doc_id)
        
        return doc_id
    
    def get_related_documents(self, doc_id: str) -> List[Dict[str, Any]]:
        """
        Get documents related to the specified document.
        
        Args:
            doc_id: The ID of the document to find related documents for
            
        Returns:
            List[Dict[str, Any]]: List of related documents
        """
        if doc_id not in self.related_documents:
            return []
        
        related_ids = self.related_documents[doc_id]
        # Return document data in the format expected by tests
        return [
            {
                'url': self.documents[rel_id].url,
                'title': self.documents[rel_id].title,
                'content': self.documents[rel_id].content
            } 
            for rel_id in related_ids
        ]
    
    def _find_document_by_url(self, url: str) -> Optional[str]:
        """
        Find a document by its URL.
        
        Args:
            url: The URL to search for
            
        Returns:
            Optional[str]: The document ID if found, None otherwise
        """
        for doc_id, document in self.documents.items():
            if document.url == url:
                return doc_id
        return None
    
    def _extract_index_terms(self, document: Document) -> List[str]:
        """
        Extract index terms from a document.
        
        Args:
            document: The document to extract terms from
            
        Returns:
            List[str]: List of extracted terms
        """
        terms = set()
        
        # Extract terms from title
        title_terms = self._tokenize_text(document.title)
        terms.update(title_terms)
        
        # Extract terms from content text
        if 'text' in document.content:
            content_terms = self._tokenize_text(document.content['text'])
            terms.update(content_terms)
        
        # Extract terms from headings if available
        if 'headings' in document.content:
            for heading in document.content['headings']:
                heading_terms = self._tokenize_text(heading['text'])
                terms.update(heading_terms)
        
        logger.debug(f"Extracted index terms for : {terms}")
        
        # Remove stop words
        final_terms = [term for term in terms if term not in self.stop_words]
        logger.debug(f"Final index terms after stop words for : {final_terms}")
        
        return final_terms
    
    def _tokenize_text(self, text: str) -> List[str]:
        """
        Tokenize text into individual terms.
        
        Args:
            text: The text to tokenize
            
        Returns:
            List[str]: List of tokens
        """
        # Convert to lowercase and split by non-alphanumeric characters
        tokens = re.findall(r'\w+', text.lower())
        return tokens
    
    def _update_search_indices(self, doc_id: str, terms: List[str]) -> None:
        """
        Update search indices with the terms from a document.
        
        Args:
            doc_id: The document ID
            terms: List of terms extracted from the document
        """
        for term in terms:
            # Add both the original term and lowercase version
            if term not in self.search_indices:
                self.search_indices[term] = set()
            self.search_indices[term].add(doc_id)
            
            # Ensure the term is also indexed in lowercase
            term_lower = term.lower()
            if term_lower not in self.search_indices:
                self.search_indices[term_lower] = set()
            self.search_indices[term_lower].add(doc_id)
    
    def _update_related_documents(self, doc_id: str) -> None:
        """
        Update related documents for a given document based on similarity.
        
        Args:
            doc_id: The document ID to update relationships for
        """
        # Skip if this document doesn't have index terms
        if doc_id not in self.document_indices:
            return
            
        new_doc_terms = set(self.document_indices[doc_id])
        
        # Compare with all other documents
        for other_id, other_terms in self.document_indices.items():
            if other_id == doc_id:
                continue
            
            other_terms_set = set(other_terms)
            
            # Calculate Jaccard similarity
            similarity = self._calculate_similarity(new_doc_terms, other_terms_set)
            
            # If similar enough, mark as related
            if similarity >= self.similarity_threshold:
                self.related_documents[doc_id].add(other_id)
                self.related_documents[other_id].add(doc_id)
    
    def _calculate_similarity(self, terms1: Set[str], terms2: Set[str]) -> float:
        """
        Calculate similarity between two sets of terms using Jaccard similarity.
        
        Args:
            terms1: First set of terms
            terms2: Second set of terms
            
        Returns:
            float: Similarity score between 0 and 1
        """
        if not terms1 or not terms2:
            return 0.0
        
        intersection = len(terms1.intersection(terms2))
        union = len(terms1.union(terms2))
        
        return intersection / union if union > 0 else 0.0
