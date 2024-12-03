import hashlib
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from ..processors.content_processor import ProcessedContent


class DocumentVersion(BaseModel):
    """Model for document version."""
    version_id: str
    timestamp: datetime
    hash: str
    changes: Dict[str, Any]

    @field_validator('version_id')
    def validate_version_id(cls, v: str) -> str:
        """Validate version ID format."""
        if not v.startswith('v'):
            v = f"v{v}"
        return v


class DocumentMetadata(BaseModel):
    """Model for document metadata."""
    title: str
    url: str
    category: str = "uncategorized"
    tags: List[str] = []
    versions: List[DocumentVersion] = []
    references: Dict[str, List[str]] = {}
    index_terms: List[str] = []
    last_updated: datetime = Field(default_factory=datetime.now)

    def add_version(self, content: Dict[str, Any]) -> None:
        """Add new version if content has changed."""
        version_hash = hashlib.sha256(str(content).encode()).hexdigest()
        
        # Check if content has changed
        if not self.versions or self.versions[-1].hash != version_hash:
            version_num = len(self.versions) + 1
            version = DocumentVersion(
                version_id=f"v{version_num}",
                timestamp=datetime.now(),
                hash=version_hash,
                changes=content
            )
            self.versions.append(version)
            self.last_updated = version.timestamp


class DocumentCollection(BaseModel):
    """Model for a collection of related documents."""
    name: str
    description: str
    documents: List[str]  # List of document IDs
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchIndex(BaseModel):
    """Model for search index entries."""
    term: str
    documents: List[Tuple[str, float]]  # (document_id, relevance_score)
    context: Dict[str, List[str]]  # document_id -> list of context snippets


class OrganizationConfig(BaseModel):
    """Configuration for document organization."""
    min_similarity_score: float = 0.3
    max_versions_to_keep: int = 10
    index_chunk_size: int = 1000
    category_rules: Dict[str, List[str]] = Field(default_factory=dict)
    stop_words: Set[str] = Field(default_factory=set)


class DocumentOrganizer:
    """Organizes and manages documentation content."""

    def __init__(self, config: Optional[OrganizationConfig] = None) -> None:
        """
        Initialize the document organizer.
        
        Args:
            config: Optional organization configuration
        """
        self.config = config or OrganizationConfig()
        self.documents: Dict[str, DocumentMetadata] = {}
        self.collections: Dict[str, DocumentCollection] = {}
        self.search_indices: Dict[str, Dict[str, str]] = {}
        self._setup_default_categories()

    def _setup_default_categories(self) -> None:
        """Setup default category rules."""
        if not self.config.category_rules:
            self.config.category_rules = {
                "api": ["api", "endpoint", "rest", "graphql"],
                "guide": ["guide", "tutorial", "how-to", "howto"],
                "reference": ["reference", "doc", "documentation"],
                "example": ["example", "sample", "demo"],
                "concept": ["concept", "overview", "introduction"]
            }

    def _generate_document_id(self, url: str, content: str) -> str:
        """
        Generate a unique document ID.
        
        Args:
            url: Document URL
            content: Document content
            
        Returns:
            Unique document ID
        """
        combined = f"{url}:{content}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def _calculate_content_hash(self, content: Dict[str, Any]) -> str:
        """
        Calculate hash of document content.
        
        Args:
            content: Document content
            
        Returns:
            Content hash
        """
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()

    def _categorize_document(self, content: ProcessedContent) -> str:
        """
        Categorize document based on content and rules.
        
        Args:
            content: Processed document content
            
        Returns:
            Document category
        """
        # Get text content for matching
        text = str(content.content.get("text", "")).lower()
        title = content.title.lower()
        url = content.url.lower()
        
        # Check each category's rules
        for category, patterns in self.config.category_rules.items():
            for pattern in patterns:
                pattern = pattern.lower()
                if (pattern in url or 
                    pattern in title or 
                    pattern in text):
                    return category
        
        # Default to uncategorized if no rules match
        return "uncategorized"

    def _extract_references(self, content: ProcessedContent) -> Dict[str, List[str]]:
        """
        Extract references from content.
        
        Args:
            content: Processed document content
            
        Returns:
            Dictionary of reference types and their values
        """
        references = {
            "internal": [],
            "external": [],
            "code": []
        }
        
        # Extract links
        for link in content.content.get("links", []):
            if isinstance(link, dict) and "url" in link:
                url = link["url"]
                if url.startswith(("http://", "https://")):
                    if urlparse(url).netloc == urlparse(content.url).netloc:
                        references["internal"].append(url)
                    else:
                        references["external"].append(url)
                        
        # Extract code references
        for block in content.content.get("code_blocks", []):
            if isinstance(block, dict) and "content" in block:
                code = block["content"].strip()
                if code:
                    references["code"].append(code)
                
        return references

    def _generate_index_terms(self, content: ProcessedContent) -> List[str]:
        """
        Generate search index terms from content.
        
        Args:
            content: Processed document content
            
        Returns:
            List of index terms
        """
        terms = set()
        
        # Add title terms
        terms.update(self._tokenize(content.title))
        
        # Add heading terms
        for heading in content.content.get("headings", []):
            terms.update(self._tokenize(heading["text"]))
        
        # Add code terms
        for code_block in content.content.get("code_blocks", []):
            if code_block.get("language"):
                terms.add(f"lang:{code_block['language']}")
        
        # Add metadata terms
        for key, value in content.metadata.get("meta_tags", {}).items():
            if isinstance(value, str):
                terms.update(self._tokenize(f"{key}:{value}"))
        
        return list(terms - self.config.stop_words)

    def _tokenize(self, text: str) -> Set[str]:
        """
        Tokenize text into terms.
        
        Args:
            text: Text to tokenize
            
        Returns:
            Set of tokens
        """
        # Convert to lowercase and split on non-alphanumeric
        tokens = re.findall(r'\w+', text.lower())
        return set(tokens) - self.config.stop_words

    def _update_search_indices(self, doc_id: str, content: ProcessedContent):
        """Update search indices with document content."""
        # Initialize indices if they don't exist
        if not hasattr(self, 'search_indices'):
            self.search_indices = {}

        # Create text index from title and content
        text_content = f"{content.title} {content.content.get('formatted_content', '')}"
        self.search_indices['text'] = self.search_indices.get('text', {})
        self.search_indices['text'][doc_id] = text_content

        # Create headings index
        headings = content.content.get('headings', [])
        self.search_indices['headings'] = self.search_indices.get('headings', {})
        self.search_indices['headings'][doc_id] = [h['text'] for h in headings]

        # Create code index
        code_blocks = content.content.get('code_blocks', [])
        self.search_indices['code'] = self.search_indices.get('code', {})
        self.search_indices['code'][doc_id] = [block['content'] for block in code_blocks]

    def add_document(self, content: ProcessedContent) -> str:
        """Add a document to the organizer and update indices."""
        doc_id = str(uuid4())
        doc = DocumentMetadata(
            title=content.title,
            url=content.url,
            category=self._categorize_document(content),
            tags=self._extract_tags(content),
            versions=[],
            references=self._extract_references(content),
            index_terms=self._extract_index_terms(content)
        )
        self.documents[doc_id] = doc
        
        # Update search indices
        self._update_search_indices(doc_id, content)
        
        return doc_id

    def create_collection(self, name: str, description: str, doc_ids: List[str]) -> str:
        """
        Create a new document collection.
        
        Args:
            name: Collection name
            description: Collection description
            doc_ids: List of document IDs to include
            
        Returns:
            Collection ID
        """
        collection_id = hashlib.sha256(name.encode()).hexdigest()[:16]
        
        self.collections[collection_id] = DocumentCollection(
            name=name,
            description=description,
            documents=[doc_id for doc_id in doc_ids if doc_id in self.documents]
        )
        
        return collection_id

    def search(self, query: str, category: str = None) -> List[Tuple[str, float, List[str]]]:
        """Search for documents matching the query."""
        results = []
        query_terms = self._tokenize_text(query.lower())
        
        for doc_id, metadata in self.documents.items():
            if category and metadata.category != category:
                continue
            
            # Get latest version content
            if not metadata.versions:
                continue
            
            latest = metadata.versions[-1]
            content = latest.changes
            
            # Calculate relevance score
            score = 0
            matches = []
            
            # Check title
            title_terms = self._tokenize_text(metadata.title.lower())
            title_matches = set(query_terms) & set(title_terms)
            if title_matches:
                score += len(title_matches) * 2
                matches.extend([f"Title: {metadata.title}"])
            
            # Check content
            if isinstance(content, dict):
                # Check text content
                if 'text' in content:
                    content_terms = self._tokenize_text(content['text'].lower())
                    content_matches = set(query_terms) & set(content_terms)
                    if content_matches:
                        score += len(content_matches)
                        matches.extend([f"Content: ...{self._get_context(content['text'], term)}..." 
                                      for term in content_matches])
                
                # Check code blocks
                if 'code_blocks' in content:
                    for block in content['code_blocks']:
                        if isinstance(block, dict) and 'content' in block:
                            code_terms = self._tokenize_text(block['content'].lower())
                            code_matches = set(query_terms) & set(code_terms)
                            if code_matches:
                                score += len(code_matches) * 1.5
                                matches.extend([f"Code: {block.get('language', 'unknown')}: {block['content'][:50]}"])
            
            if score > 0:
                results.append((doc_id, score, matches))
        
        # Sort by relevance score
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def _tokenize_text(self, text: str) -> List[str]:
        """Tokenize text into words."""
        return re.findall(r'\w+', text)

    def _get_context(self, text: str, term: str, context_size: int = 50) -> str:
        """Get context around a matching term."""
        index = text.lower().find(term.lower())
        if index == -1:
            return ""
        start = max(0, index - context_size)
        end = min(len(text), index + len(term) + context_size)
        return text[start:end]

    def get_document_versions(self, doc_id: str) -> List[DocumentVersion]:
        """Get all versions of a document."""
        if doc_id not in self.documents:
            return []
        return self.documents[doc_id].versions

    def get_related_documents(self, doc_id: str) -> List[Tuple[str, float]]:
        """
        Find related documents based on content similarity.
        
        Args:
            doc_id: Document ID
            
        Returns:
            List of (related_doc_id, similarity_score) tuples
        """
        if doc_id not in self.documents:
            return []
            
        source_doc = self.documents[doc_id]
        related: List[Tuple[str, float]] = []
        
        # Compare with other documents
        for other_id, other_doc in self.documents.items():
            if other_id != doc_id:
                # Calculate similarity based on shared index terms
                source_terms = set(source_doc.index_terms)
                other_terms = set(other_doc.index_terms)
                
                if source_terms and other_terms:
                    similarity = len(source_terms & other_terms) / len(source_terms | other_terms)
                    
                    if similarity >= self.config.min_similarity_score:
                        related.append((other_id, similarity))
        
        return sorted(related, key=lambda x: x[1], reverse=True)

    def _compute_hash(self, content: ProcessedContent) -> str:
        """Compute a hash of the document content."""
        import hashlib
        content_str = str(content.content)
        return hashlib.sha256(content_str.encode()).hexdigest()

    def _determine_category(self, content: ProcessedContent) -> str:
        """
        Determine document category based on content and rules.
        
        Args:
            content: Processed document content
            
        Returns:
            Document category
        """
        # Check URL first
        url_lower = content.url.lower()
        for category, patterns in self.config.category_rules.items():
            if any(pattern in url_lower for pattern in patterns):
                return category

        # Check title
        title_lower = content.title.lower()
        for category, patterns in self.config.category_rules.items():
            if any(pattern in title_lower for pattern in patterns):
                return category

        # Check content text
        if isinstance(content.content, dict) and "text" in content.content:
            text_lower = content.content["text"].lower()
            for category, patterns in self.config.category_rules.items():
                if any(pattern in text_lower for pattern in patterns):
                    return category

        # If no patterns match, return uncategorized
        return "uncategorized"

    def _extract_tags(self, content: ProcessedContent) -> List[str]:
        """Extract tags from content."""
        tags = set()
        
        # Extract from title
        title_words = content.title.lower().split()
        tags.update(w for w in title_words if len(w) > 3 and w not in self.config.stop_words)
        
        # Extract from content text
        if "text" in content.content:
            text_words = content.content["text"].lower().split()
            tags.update(w for w in text_words if len(w) > 3 and w not in self.config.stop_words)
            
        return list(tags)

    def _extract_references(self, content: ProcessedContent) -> Dict[str, List[str]]:
        """Extract references from content."""
        references = {
            "internal": [],
            "external": [],
            "code": []  # Add code references
        }
        
        # Extract links
        if "links" in content.content:
            for link in content.content["links"]:
                if isinstance(link, dict) and "url" in link:
                    url = link["url"]
                    if url.startswith(("http://", "https://")):
                        if content.url.split("/")[2] in url:
                            references["internal"].append(url)
                        else:
                            references["external"].append(url)
                            
        # Extract code references
        if "code_blocks" in content.content:
            for block in content.content["code_blocks"]:
                if isinstance(block, dict) and "content" in block:
                    references["code"].append(block["content"])
                    
        return references

    def _extract_index_terms(self, content: ProcessedContent) -> List[str]:
        """Extract index terms from content."""
        terms = set()
        
        # Add title terms
        terms.update(content.title.lower().split())
        
        # Add heading terms
        if "headings" in content.content:
            for heading in content.content["headings"]:
                if isinstance(heading, dict) and "text" in heading:
                    terms.update(heading["text"].lower().split())
                    
        # Add code terms
        if "code_blocks" in content.content:
            for block in content.content["code_blocks"]:
                if isinstance(block, dict) and "language" in block:
                    terms.add(block["language"].lower())
                    
        # Remove stop words and short terms
        return [term for term in terms if len(term) > 3 and term not in self.config.stop_words]

    def _compute_hash(self, content: ProcessedContent) -> str:
        """Compute hash of document content."""
        content_str = json.dumps(content.content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()