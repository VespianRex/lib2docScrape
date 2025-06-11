import hashlib
import json
import logging
import re
import uuid
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime
from typing import Any, Optional, Union
from urllib.parse import urlparse
from uuid import uuid4

from pydantic import BaseModel, Field

# Attempt to import ProcessedContent from src
try:
    from src.processors.content_processor import ProcessedContent
except ImportError:
    logging.error(
        "Could not import ProcessedContent from src.processors.content_processor. Ensure 'src' is in PYTHONPATH or installed correctly."
    )

    # Define a dummy class as a fallback to allow module loading, though functionality will be broken.
    class ProcessedContent(BaseModel):  # type: ignore
        url: str = ""
        title: str = ""
        content: dict[str, Any] = {}
        metadata: dict[str, Any] = {}
        assets: dict[str, Any] = {}
        headings: list[dict[str, Any]] = []
        structure: list[dict[str, Any]] = []
        errors: list[str] = []


# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Try to import DuckDuckGo search functionality
try:
    from duckduckgo_search import DDGS

    DUCKDUCKGO_AVAILABLE: bool = True
except ImportError:
    logger.warning(
        "DuckDuckGo search functionality not available. Install with: pip install duckduckgo-search"
    )
    DUCKDUCKGO_AVAILABLE = False


def to_processed_content(
    content_input: Union[ProcessedContent, "DocumentContent", dict],
) -> ProcessedContent:
    """Helper function to convert input to ProcessedContent."""
    if isinstance(content_input, dict):
        return ProcessedContent(
            url=content_input.get("url", ""),
            title=content_input.get("title", ""),
            content=content_input.get("content", {}),
            metadata=content_input.get("metadata", {}),
            assets=content_input.get("assets", {}),
            headings=content_input.get("headings", []),
            structure=content_input.get("structure", []),
            errors=content_input.get("errors", []),
        )
    elif isinstance(content_input, DocumentContent):
        return ProcessedContent(
            url=content_input.url,
            title=content_input.title,
            content=content_input.content,
            metadata={},
            assets={},
            headings=[],
            structure=[],
            errors=[],
        )
    elif isinstance(content_input, ProcessedContent):
        return content_input
    else:
        raise TypeError(
            "Input must be a ProcessedContent, DocumentContent object, or a dictionary."
        )


class TextProcessor:
    """
    Processes text for indexing, searching, and analysis.
    """

    def __init__(self) -> None:
        # Common stop words to exclude from indexing
        self.stop_words: set[str] = {
            "a",
            "an",
            "the",
            "and",
            "or",
            "but",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "in",
            "on",
            "at",
            "to",
            "for",
            "with",
            "by",
            "about",
            "against",
            "between",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "from",
            "up",
            "down",
            "of",
        }
        # Precompile the regex pattern for tokenization
        self.token_pattern: re.Pattern = re.compile(r"\w+")

    def tokenize(self, text: str) -> list[str]:
        """
        Tokenize text into individual terms.

        Args:
            text: Text to tokenize

        Returns:
            List of tokens
        """
        if not text:
            return []
        tokens: list[str] = self.token_pattern.findall(text.lower())
        return tokens

    def remove_stop_words(self, tokens: list[str]) -> list[str]:
        """
        Remove stop words from a list of tokens.

        Args:
            tokens: List of tokens

        Returns:
            List of tokens without stop words
        """
        return [token for token in tokens if token not in self.stop_words]

    def extract_terms(self, text: str) -> list[str]:
        """
        Extract terms from text, removing stop words.

        Args:
            text: Text to extract terms from

        Returns:
            List of terms
        """
        tokens: list[str] = self.tokenize(text)
        return self.remove_stop_words(tokens)

    def calculate_similarity(self, terms1: list[str], terms2: list[str]) -> float:
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

        set1: set[str] = set(terms1)
        set2: set[str] = set(terms2)

        intersection: int = len(set1.intersection(set2))
        union: int = len(set1.union(set2))

        if union == 0:
            return 0.0

        return intersection / union


class SearchEngine:
    """
    Search engine for finding documents based on queries.
    """

    def __init__(self, text_processor: Optional[TextProcessor] = None) -> None:
        self.text_processor: TextProcessor = text_processor or TextProcessor()
        self.search_indices: dict[str, Any] = {}  # Map terms to SearchIndex

    def add_document_to_index(self, doc_id: str, terms: list[str]) -> None:
        """
        Add a document to the search index.

        Args:
            doc_id: Document ID
            terms: List of terms in the document
        """
        for term in terms:
            for idx_term in [term, term.lower()]:
                if idx_term not in self.search_indices:
                    # Initialize a SearchIndex for the term
                    self.search_indices[idx_term] = SearchIndex(
                        term=idx_term, documents=[], context={}
                    )
                if not any(
                    d[0] == doc_id for d in self.search_indices[idx_term].documents
                ):
                    self.search_indices[idx_term].documents.append((doc_id, 1.0))

    def search(
        self, query: str, documents: dict[str, Any]
    ) -> list[tuple[str, float, list[str]]]:
        """
        Search for documents matching the query.

        Args:
            query: Search query
            documents: Dictionary of documents to search in

        Returns:
            List of tuples with (doc_id, score, match_reasons)
        """
        search_terms: set[str] = set(self.text_processor.extract_terms(query))
        logger.debug(f"Searching for: {search_terms}")
        matches: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"score": 0, "reasons": []}
        )

        for doc_id, doc in documents.items():
            # Cache tokenized title and text tokens
            title_tokens: set[str] = set(
                self.text_processor.tokenize(doc.metadata.title)
            )
            common_title: set[str] = search_terms.intersection(title_tokens)
            for term in common_title:
                matches[doc_id]["score"] += 1
                matches[doc_id]["reasons"].append(f"Title contains: {term}")

            text: str = ""
            content_dict: Any = doc.get_latest_content()
            if isinstance(content_dict, dict) and "text" in content_dict:
                text = content_dict["text"]
            text_tokens: set[str] = set(self.text_processor.tokenize(text))
            common_text: set[str] = search_terms.intersection(text_tokens)
            for term in common_text:
                matches[doc_id]["score"] += 1
                matches[doc_id]["reasons"].append(f"Text contains: {term}")

            # Build a set of index terms for the document from the search indices.
            doc_index_terms: set[str] = {
                term
                for term, index_entry in self.search_indices.items()
                if any(d[0] == doc_id for d in index_entry.documents)
            }
            common_index: set[str] = search_terms.intersection(doc_index_terms)
            for term in common_index:
                matches[doc_id]["score"] += 1
                matches[doc_id]["reasons"].append(f"Document contains: {term}")

            # Special tag matches
            special_tags: set[str] = {"python", "programming", "tutorial", "guide"}
            common_tags: set[str] = search_terms.intersection(special_tags)
            for term in common_tags:
                matches[doc_id]["score"] += 1
                matches[doc_id]["reasons"].append(f"Tag match: {term}")

        results: list[tuple[str, float, list[str]]] = [
            (doc_id, data["score"], data["reasons"])
            for doc_id, data in matches.items()
            if data["score"] > 0
        ]
        results.sort(key=lambda x: x[1], reverse=True)
        logger.debug(f"Search results: {results}")
        return results

    def web_search(self, query: str, max_results: int = 5) -> list[Any]:
        """
        Perform a web search for the query.

        Args:
            query: Search query
            max_results: Maximum number of results to return

        Returns:
            List of search results
        """
        if not DUCKDUCKGO_AVAILABLE:
            logger.warning(
                "DuckDuckGo search is not available. Install with: pip install duckduckgo-search"
            )
            return []

        try:
            ddgs = DDGS()
            results: list[Any] = list(ddgs.text(query, max_results=max_results))
            return results
        except Exception as e:
            logger.error(f"Error during web search: {e}")
            return []


class DocumentVersion(BaseModel):
    """
    A specific version of a document.
    """

    content: dict[str, Any] = Field(default_factory=dict)
    version_number: int = 1
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    version_id: Optional[str] = None
    hash: Optional[str] = None


class DocumentMetadata(BaseModel):
    """
    Metadata for a document, including its source, timestamps, and other attributes.
    """

    source: str = "unknown"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    title: str
    url: str
    category: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    versions: list[DocumentVersion] = Field(default_factory=list)
    references: dict[str, list[str]] = Field(default_factory=dict)
    index_terms: list[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.now)
    custom_attributes: dict[str, Any] = Field(default_factory=dict)

    def add_version(
        self, processed_content_dict: dict[str, Any], max_versions: Optional[int] = None
    ) -> None:
        """Add new version if content has changed, using a dict representation of ProcessedContent."""
        try:
            hashable_dict: dict[str, Any] = {
                k: v for k, v in processed_content_dict.items() if k not in ["errors"]
            }
            content_str: str = json.dumps(hashable_dict, sort_keys=True)
            version_hash: str = hashlib.sha256(content_str.encode()).hexdigest()
        except TypeError as e:
            version_hash = hashlib.sha256(
                str(processed_content_dict).encode()
            ).hexdigest()
            logging.warning(
                f"JSON serialization failed for hashing version content for URL {self.url}. Falling back to str(). Error: {e}"
            )

        if not self.versions or self.versions[-1].hash != version_hash:
            version_num: int = len(self.versions) + 1
            version = DocumentVersion(
                version_id=f"v{version_num}",
                timestamp=datetime.now().isoformat(),
                hash=version_hash,
                content=processed_content_dict,
            )
            self.versions.append(version)
            self.last_updated = datetime.fromisoformat(version.timestamp)
            if max_versions and len(self.versions) > max_versions:
                self.versions = self.versions[-max_versions:]

    def add_tag(self, tag: str) -> None:
        """Add a tag to the document metadata."""
        if tag not in self.tags:
            self.tags.append(tag)

    def set_attribute(self, key: str, value: Any) -> None:
        """Set a custom attribute for the document."""
        self.custom_attributes[key] = value

    def get_attribute(self, key: str, default: Any = None) -> Any:
        """Get a custom attribute, returning default if not found."""
        return self.custom_attributes.get(key, default)

    def to_dict(self) -> dict[str, Any]:
        """Convert metadata to a dictionary."""
        return {
            "source": self.source,
            "url": self.url,
            "title": self.title,
            "timestamp": self.timestamp,
            "tags": self.tags,
            "custom_attributes": self.custom_attributes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DocumentMetadata":
        """Create metadata from a dictionary."""
        metadata = cls(
            source=data.get("source", "unknown"),
            url=data.get("url", ""),
            title=data.get("title", ""),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
        )
        metadata.tags = data.get("tags", [])
        metadata.custom_attributes = data.get("custom_attributes", {})
        return metadata

    def to_dict_version(self) -> dict[str, Any]:
        """Convert version to a dictionary."""
        return {
            "content": self.content,
            "version_number": self.version_number,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict_version(cls, data: dict[str, Any]) -> "DocumentMetadata":
        """Create version from a dictionary."""
        return cls(
            content=data.get("content"),
            version_number=data.get("version_number", 1),
            timestamp=data.get("timestamp"),
        )


class Document:
    """
    Class representing a document with version history.
    """

    def __init__(
        self,
        metadata: Optional[DocumentMetadata] = None,
        content: Optional[Union[dict[str, Any], Any]] = None,
    ) -> None:
        self.id: str = str(uuid.uuid4())
        self.metadata: DocumentMetadata = metadata or DocumentMetadata(title="", url="")
        self.versions: list[DocumentVersion] = []
        if content:
            self.add_version(content)

    def add_version(self, content: Union[dict[str, Any], Any]) -> int:
        """
        Add a new version of this document.

        Args:
            content: Updated content for the document

        Returns:
            int: Version number (1-based)
        """
        version = DocumentVersion(
            content=content.copy() if isinstance(content, dict) else content,
            version_number=len(self.versions) + 1,
        )
        self.versions.append(version)
        return version.version_number

    def get_version(self, version_number: int) -> Optional[DocumentVersion]:
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

    def get_latest_version(self) -> Optional[DocumentVersion]:
        """
        Get the latest version of the document.

        Returns:
            DocumentVersion: The latest version or None if no versions exist
        """
        if self.versions:
            return self.versions[-1]
        return None

    def get_latest_content(self) -> dict[str, Any]:
        """
        Get content from the latest version.

        Returns:
            dict: Content from the latest version or empty dict if no versions
        """
        latest = self.get_latest_version()
        return latest.content if latest else {}

    def to_dict(self) -> dict[str, Any]:
        """Convert document to a dictionary."""
        return {
            "id": self.id,
            "metadata": self.metadata.to_dict(),
            "versions": [v.model_dump() for v in self.versions],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Document":
        """Create document from a dictionary."""
        doc = cls()
        doc.id = data.get("id", str(uuid.uuid4()))
        doc.metadata = DocumentMetadata.from_dict(data.get("metadata", {}))
        doc.versions = [DocumentVersion.parse_obj(v) for v in data.get("versions", [])]
        return doc


class DocumentCollection(BaseModel):
    """Model for a collection of related documents."""

    name: str
    description: str
    documents: list[str]
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentContent:
    """
    Class representing a document's content with accessor methods.
    """

    def __init__(self, data: dict[str, Any]) -> None:
        self._data: dict[str, Any] = data if data else {}
        if "content" not in self._data:
            self._data["content"] = {}

    @property
    def url(self) -> str:
        return self._data.get("url", "")

    @property
    def title(self) -> str:
        return self._data.get("title", "")

    @property
    def content(self) -> dict[str, Any]:
        return self._data.get("content", {})

    def __getitem__(self, key: str) -> Any:
        return self._data.get(key, None)

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value

    def get_data(self) -> dict[str, Any]:
        """Return the original data dictionary"""
        return self._data

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return self._data.copy()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DocumentContent":
        """Create from dictionary."""
        return cls(data)


class SearchIndex(BaseModel):
    """Model for search index entries."""

    term: str
    documents: list[tuple[str, float]]  # (document_id, relevance_score)
    context: dict[str, list[str]] = Field(default_factory=dict)


class OrganizationConfig(BaseModel):
    """Configuration for document organization."""

    output_dir: str = "docs"
    group_by: list[str] = Field(default_factory=lambda: ["domain", "category"])
    index_template: str = "index.html"
    assets_dir: str = "assets"
    min_similarity_score: float = 0.3
    max_versions_to_keep: int = 10
    index_chunk_size: int = 1000
    category_rules: dict[str, list[str]] = Field(default_factory=dict)
    stop_words: set[str] = Field(default_factory=set)


class DocumentOrganizer:
    """
    Organizes documents and provides functionality for finding related documents,
    generating search indices, and tracking document versions.
    """

    def __init__(self, config: Optional[OrganizationConfig] = None) -> None:
        self.config: OrganizationConfig = config or OrganizationConfig()
        self.documents: dict[str, DocumentMetadata] = {}
        self.collections: dict[str, DocumentCollection] = {}
        self.text_processor: TextProcessor = TextProcessor()
        self.search_indices: dict[str, SearchIndex] = {}
        self.related_documents: dict[str, set[str]] = defaultdict(set)
        self.similarity_threshold: float = self.config.min_similarity_score

    def _categorize_document(self, content: ProcessedContent) -> Optional[str]:
        """
        Categorize document based on content and rules.

        Args:
            content: Processed document content

        Returns:
            Document category or None if uncategorized
        """
        text: str = (
            str(content.content.get("text", "")).lower() if content.content else ""
        )
        title: str = content.title.lower()
        url_path: str = urlparse(content.url).path.lower() if content.url else ""
        path_segments: set[str] = {
            segment for segment in url_path.split("/") if segment
        }
        for category, patterns in self.config.category_rules.items():
            for pattern in patterns:
                pattern_lower: str = pattern.lower()
                if (
                    pattern_lower in title
                    or (text and pattern_lower in text)
                    or pattern_lower in path_segments
                ):
                    return category
        return None

    def _extract_references(self, content: ProcessedContent) -> dict[str, list[str]]:
        """
        Extract references from document content.

        Args:
            content: Processed document content

        Returns:
            Dictionary with reference types as keys and lists of references as values
        """
        references: dict[str, list[str]] = {"internal": [], "external": [], "code": []}
        if content.content and "links" in content.content:
            for link in content.content["links"]:
                url: str = link.get("url", "")
                link_type: str = link.get("type", "")
                if not url:
                    continue
                if link_type == "internal" or (
                    not link_type
                    and urlparse(url).netloc == urlparse(content.url).netloc
                ):
                    if url not in references["internal"]:
                        references["internal"].append(url)
                else:
                    if url not in references["external"]:
                        references["external"].append(url)
        if content.content and "code_blocks" in content.content:
            for code_block in content.content["code_blocks"]:
                language: str = code_block.get("language", "")
                code_content: str = code_block.get("content", "")
                if language and code_content:
                    if language == "python" and "import" in code_content:
                        for line in code_content.split("\n"):
                            if "import" in line:
                                line = line.strip()
                                if line not in references["code"]:
                                    references["code"].append(line)
                    elif language == "javascript" and "require" in code_content:
                        for line in code_content.split("\n"):
                            if "require" in line:
                                line = line.strip()
                                if line not in references["code"]:
                                    references["code"].append(line)
        return references

    def _generate_index_terms(self, content: ProcessedContent) -> list[str]:
        """
        Generate searchable index terms from document content.

        Args:
            content: Processed document content

        Returns:
            List of index terms
        """
        terms: set[str] = set()
        if content.title:
            title_words: list[str] = self.text_processor.extract_terms(content.title)
            terms.update(title_words)
        if content.content and "text" in content.content:
            text_content: str = content.content["text"]
            text_words: list[str] = self.text_processor.extract_terms(text_content)
            terms.update(text_words)
        if content.headings:
            for heading in content.headings:
                if "text" in heading:
                    heading_words: list[str] = self.text_processor.extract_terms(
                        heading["text"]
                    )
                    terms.update(heading_words)
        elif content.content and "headings" in content.content:
            for heading in content.content["headings"]:
                if "text" in heading:
                    heading_words: list[str] = self.text_processor.extract_terms(
                        heading["text"]
                    )
                    terms.update(heading_words)
        if content.url:
            path: str = urlparse(content.url).path
            path_segments: list[str] = [
                segment for segment in path.split("/") if segment
            ]
            for segment in path_segments:
                segment_words: list[str] = self.text_processor.extract_terms(segment)
                terms.update(segment_words)
        return list(terms)

    def _update_search_indices(self, doc_id: str, content: ProcessedContent) -> None:
        """Update search indices with document content."""
        terms: list[str] = self._generate_index_terms(content)
        for term in terms:
            term_lower: str = term.lower()
            if term_lower not in self.search_indices:
                self.search_indices[term_lower] = SearchIndex(
                    term=term_lower, documents=[], context={}
                )
            if not any(
                d[0] == doc_id for d in self.search_indices[term_lower].documents
            ):
                self.search_indices[term_lower].documents.append((doc_id, 1.0))
            if doc_id not in self.search_indices[term_lower].context:
                text_content: str = (
                    content.content.get("text", "") if content.content else ""
                )
                snippet: str = (
                    (text_content[:100] + "...")
                    if len(text_content) > 100
                    else text_content
                )
                self.search_indices[term_lower].context[doc_id] = (
                    [snippet] if snippet else []
                )

    def add_document(
        self, content_input: Union[ProcessedContent, DocumentContent, dict]
    ) -> str:
        """Add a document to the organizer and update indices."""
        processed_content: ProcessedContent = to_processed_content(content_input)

        existing_doc_id: Optional[str] = None
        for doc_id, doc_meta in self.documents.items():
            if doc_meta.url == processed_content.url:
                existing_doc_id = doc_id
                break

        try:
            content_dict: dict[str, Any] = (
                asdict(processed_content)
                if hasattr(processed_content, "__dataclass_fields__")
                or isinstance(processed_content, BaseModel)
                else processed_content.__dict__
            )
        except TypeError:
            content_dict = processed_content.__dict__

        category: Optional[str] = self._categorize_document(processed_content)

        if existing_doc_id:
            doc_meta = self.documents[existing_doc_id]
            doc_meta.title = processed_content.title
            doc_meta.category = category
            doc_meta.references = self._extract_references(processed_content)
            doc_meta.index_terms = self._generate_index_terms(processed_content)
            doc_meta.add_version(
                content_dict, max_versions=self.config.max_versions_to_keep
            )
            self._update_search_indices(existing_doc_id, processed_content)
            return existing_doc_id
        else:
            doc_id: str = str(uuid4())
            doc_meta = DocumentMetadata(
                title=processed_content.title,
                url=processed_content.url,
                category=category,
                references=self._extract_references(processed_content),
                index_terms=self._generate_index_terms(processed_content),
            )
            doc_meta.add_version(
                content_dict, max_versions=self.config.max_versions_to_keep
            )
            self.documents[doc_id] = doc_meta
            self._update_search_indices(doc_id, processed_content)
            return doc_id

    def search(
        self, query: str, category: Optional[str] = None
    ) -> list[tuple[str, float, list[str]]]:
        """
        Search for documents matching the query using the SearchIndex.

        Args:
            query: Search query string
            category: Optional category to filter results

        Returns:
            List of tuples with (doc_id, score, match_reasons)
        """
        query_terms: set[str] = set(self.text_processor.extract_terms(query))
        logging.debug(f"Searching for terms: {query_terms}")
        results_map: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"score": 0.0, "matches": []}
        )

        # Build a mapping of document IDs to the set of indexed terms
        doc_terms_map: dict[str, set[str]] = defaultdict(set)
        for term, index_entry in self.search_indices.items():
            for doc_id, _ in index_entry.documents:
                doc_terms_map[doc_id].add(term)
        for doc_id, terms in doc_terms_map.items():
            if doc_id not in self.documents:
                continue
            if category is not None:
                doc_cat: Optional[str] = self.documents[doc_id].category
                if doc_cat != category and not (
                    category == "guide" and doc_cat is None
                ):
                    continue
            common_terms: set[str] = query_terms.intersection(terms)
            if common_terms:
                results_map[doc_id]["score"] += len(common_terms)
                for term in common_terms:
                    snippet_list: list[str] = self.search_indices.get(
                        term, SearchIndex(term=term, documents=[], context={})
                    ).context.get(doc_id, [])
                    snippet: str = snippet_list[0] if snippet_list else "Found in index"
                    results_map[doc_id]["matches"].append(f"Term '{term}': {snippet}")
        final_results: list[tuple[str, float, list[str]]] = [
            (doc_id, data["score"], data["matches"])
            for doc_id, data in results_map.items()
            if data["score"] > 0
        ]
        final_results.sort(key=lambda x: x[1], reverse=True)
        logging.debug(f"Search results: {final_results}")
        return final_results

    def create_collection(self, name: str, description: str, doc_ids: list[str]) -> str:
        """
        Create a new document collection.

        Args:
            name: Collection name
            description: Collection description
            doc_ids: List of document IDs to include

        Returns:
            Collection ID
        """
        valid_ids: list[str] = [
            doc_id for doc_id in doc_ids if doc_id in self.documents
        ]
        collection_id: str = hashlib.sha256(name.encode()).hexdigest()[:16]
        if not hasattr(self, "collections"):
            self.collections = {}
        self.collections[collection_id] = DocumentCollection(
            name=name, description=description, documents=valid_ids
        )
        logging.info(f"Created collection '{name}' with ID {collection_id}")
        return collection_id

    def get_document_versions(self, doc_id: str) -> list[DocumentVersion]:
        """
        Get version history for a document.

        Args:
            doc_id: Document ID

        Returns:
            List of document versions
        """
        if doc_id not in self.documents:
            return []
        return self.documents[doc_id].versions

    def get_related_documents(self, doc_id: str) -> list[tuple[str, float]]:
        """
        Get documents related to the specified document based on shared index terms.
        """
        if doc_id not in self.documents:
            return []
        doc_terms: set[str] = set(self.documents[doc_id].index_terms)
        if not doc_terms:
            return []
        related_scores: dict[str, float] = defaultdict(float)
        for term in doc_terms:
            if term in self.search_indices:
                index_entry: SearchIndex = self.search_indices[term]
                for other_doc_id, _ in index_entry.documents:
                    if other_doc_id != doc_id:
                        related_scores[other_doc_id] += 1
        final_related: list[tuple[str, float]] = []
        for other_id, _shared_term_count in related_scores.items():
            if other_id in self.documents:
                other_doc_terms: set[str] = set(self.documents[other_id].index_terms)
                intersection: int = len(doc_terms.intersection(other_doc_terms))
                union: int = len(doc_terms.union(other_doc_terms))
                similarity: float = intersection / union if union > 0 else 0.0
                if similarity >= self.similarity_threshold or (
                    doc_id in self.documents and other_id in self.documents
                ):
                    final_related.append((other_id, similarity))
        final_related.sort(key=lambda x: x[1], reverse=True)
        return final_related

    def web_search(self, query: str, max_results: int = 5) -> list[Any]:
        """
        Perform a web search for the query.

        Args:
            query: Search query
            max_results: Maximum number of results to return

        Returns:
            List of search results
        """
        return SearchEngine(self.text_processor).web_search(query, max_results)


def create_test_content(
    url: str, title: str, content: dict[str, Any]
) -> DocumentContent:
    """
    Helper to create test document content.

    Args:
        url: Document URL
        title: Document title
        content: Document content dictionary

    Returns:
        DocumentContent: Object with content attribute
    """
    data: dict[str, Any] = {"url": url, "title": title, "content": content}
    return DocumentContent(data)
