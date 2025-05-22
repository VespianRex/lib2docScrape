import hashlib
import json
import logging

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import asdict
from urllib.parse import urlparse

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

    def add_version(self, processed_content_dict: Dict[str, Any]) -> None:
        """Add new version if content has changed, using a dict representation of ProcessedContent."""
        # Hash based on the structured content for better change detection
        # Use json.dumps for consistent hashing of the dictionary
        try:
            # Exclude fields that might change without semantic difference (like errors) for hashing
            hashable_dict = {k: v for k, v in processed_content_dict.items() if k not in ['errors']}
            content_str = json.dumps(hashable_dict, sort_keys=True)
            version_hash = hashlib.sha256(content_str.encode()).hexdigest()
        except TypeError as e:
            # Fallback if json serialization fails (e.g., non-serializable objects)
            version_hash = hashlib.sha256(str(processed_content_dict).encode()).hexdigest()
            logging.warning(f"JSON serialization failed for hashing version content for URL {self.url}. Falling back to str(). Error: {e}")

        # Check if content has changed
        if not self.versions or self.versions[-1].hash != version_hash:
            version_num = len(self.versions) + 1
            version = DocumentVersion(
                version_id=f"v{version_num}",
                timestamp=datetime.now(),
                hash=version_hash,
                changes=processed_content_dict # Store the whole dict
            )
            self.versions.append(version)
            # Enforce max_versions_to_keep (assuming config is accessible or passed)
            # This requires passing the config limit to this method or accessing it differently.
            # For now, let's assume a default or pass it. We'll adjust the call site later if needed.
            # Let's postpone this fix until we confirm how config is accessed here.
            # TODO: Implement version limiting based on config.max_versions_to_keep
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
        self.documents: Dict[str, DocumentMetadata] = {} # doc_id -> metadata
        self.url_to_doc_id: Dict[str, str] = {} # url -> doc_id mapping
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
        
        # Prioritize more specific categories first
        priority_categories = ["api", "guide", "reference", "concept"]
        other_categories = [cat for cat in self.config.category_rules if cat not in priority_categories]

        # Check priority categories
        for category in priority_categories:
            if category in self.config.category_rules:
                patterns = self.config.category_rules[category]
                for pattern in patterns:
                    pattern = pattern.lower()
                    # Prioritize title and text matches for specific categories
                    if pattern in title or pattern in text:
                        return category
                    # Check URL as lower priority for specific categories
                    if pattern in url:
                         return category

        # Check other categories (like 'example') - prioritize title/text
        for category in other_categories:
             if category in self.config.category_rules:
                patterns = self.config.category_rules[category]
                for pattern in patterns:
                    pattern = pattern.lower()
                    if pattern in title or pattern in text:
                         return category
                    # Only check URL for less specific categories if title/text didn't match
                    # if pattern in url: # Avoid matching 'example' in domain too easily
                    #     return category

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
        return set(tokens) # Return all tokens, filter later

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
        """
        Add or update a document in the organizer. If a document with the same URL
        exists, a new version is added if the content hash differs. Otherwise, a new
        document entry is created. Updates search indices accordingly.
        """
        normalized_url = content.url # Assuming content.url is already normalized

        # Check if document with this URL already exists
        existing_doc_id = self.url_to_doc_id.get(normalized_url)

        if existing_doc_id and existing_doc_id in self.documents:
            # Document exists, add a new version if content changed
            doc = self.documents[existing_doc_id]
            # Convert ProcessedContent to dict before adding version
            content_dict = asdict(content)
            # Store previous version count to check if a new one was added
            prev_version_count = len(doc.versions)
            doc.add_version(content_dict)
            # If a new version was added, update search index
            if len(doc.versions) > prev_version_count:
                 logging.info(f"Added new version {doc.versions[-1].version_id} for existing document: {normalized_url} (ID: {existing_doc_id})")
                 # Trim old versions if limit exceeded
                 if len(doc.versions) > self.config.max_versions_to_keep:
                     num_to_trim = len(doc.versions) - self.config.max_versions_to_keep
                     logging.debug(f"Trimming {num_to_trim} old versions for {normalized_url}. Count before: {len(doc.versions)}, Max: {self.config.max_versions_to_keep}")
                     doc.versions = doc.versions[num_to_trim:]
                     logging.debug(f"Version count after trimming: {len(doc.versions)}")
                 self._update_search_indices(existing_doc_id, content) # Update index even if only version was added
            else:
                 logging.info(f"Content unchanged for existing document: {normalized_url} (ID: {existing_doc_id}). No new version added.")
            return existing_doc_id
        else:
            # Document does not exist, create a new entry
            doc_id = str(uuid4())
            logging.info(f"Creating new document entry for: {normalized_url} (ID: {doc_id})")
            doc = DocumentMetadata(
                title=content.title,
                url=normalized_url, # Store normalized URL
                category=self._categorize_document(content),
                tags=self._extract_tags(content),
                versions=[],
                references=self._extract_references(content),
                index_terms=self._extract_index_terms(content)
            )
            # Add the initial version using the dictionary representation
            content_dict = asdict(content)
            doc.add_version(content_dict)
            self.documents[doc_id] = doc
            self.url_to_doc_id[normalized_url] = doc_id # Add to URL lookup map

            # Update search indices for the new document
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
        """
        Search for documents matching the query.
        
        Args:
            query: Search query string
            category: Optional category to filter results
            
        Returns:
            List of (doc_id, score, context_matches) tuples
        """
        results = []
        query_lower = query.lower()
        query_terms = self._tokenize(query)
        
        # Create a set of multi-word phrases to check
        query_phrases = []
        words = query_lower.split()
        if len(words) > 1:
            # Add the complete phrase
            query_phrases.append(query_lower)
            # Add adjacent word pairs
            for i in range(len(words) - 1):
                query_phrases.append(f"{words[i]} {words[i+1]}")
        
        for doc_id, metadata in self.documents.items():
            if category and metadata.category != category:
                continue
            
            score = 0
            matches = []
            
            # Check for exact index term matches
            index_term_matches = set(query_terms) & set(metadata.index_terms)
            if index_term_matches:
                # Score based on matching terms
                score += len(index_term_matches) * 2  # Weight exact matches higher
                matches.extend([f"Matched Term: {term}" for term in index_term_matches])
            
            # Check for phrase matches in title
            title_lower = metadata.title.lower()
            for phrase in query_phrases:
                if phrase in title_lower:
                    score += 3  # Weight title matches even higher
                    matches.append(f"Title contains: {phrase}")
            
            # Check for individual term matches in title
            for term in query_terms:
                if term in title_lower:
                    score += 1
                    matches.append(f"Title contains term: {term}")
            
            # Check for category relevance
            if query_lower in metadata.category.lower():
                score += 1
                matches.append(f"Category match: {metadata.category}")
            
            # Check for tag matches
            tag_matches = [tag for tag in metadata.tags if any(term in tag.lower() for term in query_terms)]
            if tag_matches:
                score += len(tag_matches)
                matches.extend([f"Tag match: {tag}" for tag in tag_matches])
                
            # Check for matches in document versions (especially headings)
            if metadata.versions:
                latest_version = metadata.versions[-1]
                if 'headings' in latest_version.changes:
                    for heading in latest_version.changes['headings']:
                        if isinstance(heading, dict) and 'title' in heading:
                            heading_lower = heading['title'].lower()
                            # Check for exact phrase match in headings
                            for phrase in query_phrases:
                                if phrase in heading_lower:
                                    score += 4  # Highest weight for heading matches
                                    matches.append(f"Heading contains: {phrase}")
                            # Check for individual term matches in headings
                            for term in query_terms:
                                if term in heading_lower:
                                    score += 2
                                    matches.append(f"Heading contains term: {term}")
                
                # Check for matches in content text
                if 'content' in latest_version.changes and isinstance(latest_version.changes['content'], dict):
                    content_dict = latest_version.changes['content']
                    # Check formatted content
                    if 'formatted_content' in content_dict:
                        formatted_content = content_dict['formatted_content'].lower()
                        for phrase in query_phrases:
                            if phrase in formatted_content:
                                score += 2
                                matches.append(f"Content contains: {phrase}")
                    
                    # Check text content
                    if 'text' in content_dict:
                        text_content = content_dict['text'].lower()
                        for phrase in query_phrases:
                            if phrase in text_content:
                                score += 2
                                matches.append(f"Content contains: {phrase}")
            
            # If we have any matches or the document has relevant content, include it
            if score > 0 or index_term_matches:
                results.append((doc_id, score, matches))
        
        # Sort by relevance score
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    # _tokenize_text method is now redundant and can be removed
    # def _tokenize_text(self, text: str) -> List[str]:
    #     """Tokenize text into words."""
    #     return re.findall(r'\w+', text)

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
                        logging.debug(f"Comparing {doc_id} ({source_terms}) and {other_id} ({other_terms})")
                        logging.debug(f"Intersection: {source_terms & other_terms}, Union: {source_terms | other_terms}")
                        logging.debug(f"Similarity: {similarity:.4f}, Threshold: {self.config.min_similarity_score}")

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
        terms.update(self._tokenize(content.title))
        
        # Add heading terms (accessing the correct attribute)
        if content.headings:
            for heading in content.headings:
                if isinstance(heading, dict) and "title" in heading: # Headings use 'title' key
                    terms.update(self._tokenize(heading["title"])) # Use _tokenize for headings
                    # Add terms from main content
                    if 'formatted_content' in content.content:
                        terms.update(self._tokenize(content.content['formatted_content']))
                        
        # Add terms from code blocks found in the structure
        if content.structure: # Check if structure exists
            code_terms = set()
            def find_code_terms(element):
                if isinstance(element, dict):
                    if element.get('type') == 'code':
                        # Add language if present
                        lang = element.get('language')
                        if lang:
                            code_terms.add(lang.lower()) # Add the language itself as a term
                        # Add tokenized content
                        code_content = element.get('content')
                        if code_content:
                            code_terms.update(self._tokenize(code_content))
                    # Recurse into values
                    for value in element.values():
                        if isinstance(value, (dict, list)):
                             find_code_terms(value)
                elif isinstance(element, list):
                    # Recurse into list items
                    for item in element:
                         find_code_terms(item)
            find_code_terms(content.structure)
            terms.update(code_terms)

        logging.debug(f"Extracted index terms for {content.url}: {terms}")

        # Remove stop words and log final terms
        final_terms = [term for term in terms if term not in self.config.stop_words] # Remove length filter
        logging.debug(f"Final index terms after stop words for {content.url}: {final_terms}")
        return final_terms

    def _compute_hash(self, content: ProcessedContent) -> str:
        """Compute hash of document content."""
        content_str = json.dumps(content.content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()