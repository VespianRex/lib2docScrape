#!/usr/bin/env python3
"""
Semantic Search Engine for Advanced Documentation Search

Provides semantic search capabilities across scraped documentation using
sentence transformers and vector similarity search.
"""

import logging
import pickle
from pathlib import Path
from typing import Any, Optional

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class SemanticSearchEngine:
    """Advanced semantic search engine for documentation content."""

    def __init__(
        self, model_name: str = "all-MiniLM-L6-v2", cache_dir: Optional[str] = None
    ):
        """
        Initialize the semantic search engine.

        Args:
            model_name: Name of the sentence transformer model to use
            cache_dir: Directory to cache embeddings and index
        """
        self.model_name = model_name
        self.cache_dir = Path(cache_dir) if cache_dir else Path("cache/search")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize the sentence transformer model
        try:
            self.model = SentenceTransformer(model_name)
            logger.info(f"Loaded sentence transformer model: {model_name}")
        except Exception as e:
            logger.warning(f"Failed to load model {model_name}, using fallback: {e}")
            # Fallback to a simpler model or mock implementation
            self.model = None

        # Storage for indexed documents
        self.documents = {}  # library_name -> {sections, embeddings, metadata}
        self.document_embeddings = {}
        self.indexed_libraries = set()

    def index_documents(
        self, documentation_content: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Index documentation content for semantic search.

        Args:
            documentation_content: Dictionary mapping library names to their documentation

        Returns:
            Indexing result with status and statistics
        """
        try:
            indexed_count = 0

            for library_name, doc_data in documentation_content.items():
                logger.info(f"Indexing documentation for {library_name}")

                # Extract text content for indexing
                text_chunks = self._extract_text_chunks(doc_data)

                if not text_chunks:
                    logger.warning(f"No text content found for {library_name}")
                    continue

                # Generate embeddings
                if self.model:
                    embeddings = self.model.encode(text_chunks)
                else:
                    # Fallback: use simple text-based features
                    embeddings = self._generate_fallback_embeddings(text_chunks)

                # Store indexed data
                self.documents[library_name] = {
                    "text_chunks": text_chunks,
                    "embeddings": embeddings,
                    "metadata": doc_data,
                    "sections": doc_data.get("sections", []),
                    "tags": doc_data.get("tags", []),
                    "difficulty": doc_data.get("difficulty", "unknown"),
                }

                self.indexed_libraries.add(library_name)
                indexed_count += 1

            # Save index to cache
            self._save_index()

            return {
                "status": "success",
                "indexed_count": indexed_count,
                "indexed_libraries": list(self.indexed_libraries),
                "total_chunks": sum(
                    len(doc["text_chunks"]) for doc in self.documents.values()
                ),
            }

        except Exception as e:
            logger.error(f"Error indexing documents: {e}")
            return {
                "status": "error",
                "error": str(e),
                "indexed_count": 0,
                "indexed_libraries": [],
            }

    def search(
        self, query: str, limit: int = 5, filters: Optional[dict[str, Any]] = None
    ) -> list[dict[str, Any]]:
        """
        Perform semantic search across indexed documentation.

        Args:
            query: Search query string
            limit: Maximum number of results to return
            filters: Optional filters (difficulty, tags, library)

        Returns:
            List of search results with relevance scores
        """
        if not self.documents:
            logger.warning("No documents indexed for search")
            return []

        try:
            # Generate query embedding
            if self.model:
                query_embedding = self.model.encode([query])
            else:
                query_embedding = self._generate_fallback_embeddings([query])

            results = []

            # Search across all indexed libraries
            for library_name, doc_data in self.documents.items():
                # Apply filters
                if filters and not self._matches_filters(
                    library_name, doc_data, filters
                ):
                    continue

                # Calculate similarities
                similarities = cosine_similarity(
                    query_embedding, doc_data["embeddings"]
                )[0]

                # Get top matches for this library
                for i, similarity in enumerate(similarities):
                    if similarity > 0.1:  # Minimum relevance threshold
                        results.append(
                            {
                                "library": library_name,
                                "section": doc_data["sections"][i]
                                if i < len(doc_data["sections"])
                                else {
                                    "title": "Content",
                                    "content": doc_data["text_chunks"][i],
                                },
                                "text_chunk": doc_data["text_chunks"][i],
                                "relevance_score": float(similarity),
                                "tags": doc_data.get("tags", []),
                                "difficulty": doc_data.get("difficulty", "unknown"),
                            }
                        )

            # Sort by relevance and return top results
            results.sort(key=lambda x: x["relevance_score"], reverse=True)
            return results[:limit]

        except Exception as e:
            logger.error(f"Error performing search: {e}")
            return []

    def get_similar_libraries(
        self, library_name: str, limit: int = 3
    ) -> list[dict[str, Any]]:
        """
        Find libraries similar to the given library based on content.

        Args:
            library_name: Name of the reference library
            limit: Maximum number of similar libraries to return

        Returns:
            List of similar libraries with similarity scores
        """
        if library_name not in self.documents:
            logger.warning(f"Library {library_name} not found in index")
            return []

        try:
            reference_doc = self.documents[library_name]
            reference_embedding = np.mean(reference_doc["embeddings"], axis=0).reshape(
                1, -1
            )

            similarities = []

            for other_library, other_doc in self.documents.items():
                if other_library == library_name:
                    continue

                # Calculate average embedding for the library
                other_embedding = np.mean(other_doc["embeddings"], axis=0).reshape(
                    1, -1
                )
                similarity = cosine_similarity(reference_embedding, other_embedding)[0][
                    0
                ]

                # Generate similarity reason
                reason = self._generate_similarity_reason(reference_doc, other_doc)

                similarities.append(
                    {
                        "library": other_library,
                        "similarity_score": float(similarity),
                        "reason": reason,
                        "common_tags": list(
                            set(reference_doc.get("tags", []))
                            & set(other_doc.get("tags", []))
                        ),
                    }
                )

            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x["similarity_score"], reverse=True)
            return similarities[:limit]

        except Exception as e:
            logger.error(f"Error finding similar libraries: {e}")
            return []

    def _extract_text_chunks(self, doc_data: dict[str, Any]) -> list[str]:
        """Extract text chunks from documentation data for indexing."""
        chunks = []

        # Add main content
        if "content" in doc_data:
            chunks.append(doc_data["content"])

        # Add section content
        if "sections" in doc_data:
            for section in doc_data["sections"]:
                if isinstance(section, dict):
                    title = section.get("title", "")
                    content = section.get("content", "")
                    chunks.append(f"{title}. {content}")
                elif isinstance(section, str):
                    chunks.append(section)

        # Add code examples
        if "code_examples" in doc_data:
            for example in doc_data["code_examples"]:
                if isinstance(example, str):
                    chunks.append(f"Code example: {example}")
                elif isinstance(example, dict):
                    chunks.append(f"Code example: {example.get('code', '')}")

        # Add API reference
        if "api_reference" in doc_data:
            api_text = " ".join(doc_data["api_reference"])
            chunks.append(f"API reference: {api_text}")

        return [chunk for chunk in chunks if chunk.strip()]

    def _generate_fallback_embeddings(self, texts: list[str]) -> np.ndarray:
        """Generate simple fallback embeddings when transformer model is not available."""
        # Simple TF-IDF-like approach
        from sklearn.feature_extraction.text import TfidfVectorizer

        if not hasattr(self, "_fallback_vectorizer"):
            self._fallback_vectorizer = TfidfVectorizer(
                max_features=100, stop_words="english"
            )

        try:
            embeddings = self._fallback_vectorizer.fit_transform(texts).toarray()
        except:
            # Ultimate fallback: random embeddings
            embeddings = np.random.rand(len(texts), 50)

        return embeddings

    def _matches_filters(
        self, library_name: str, doc_data: dict[str, Any], filters: dict[str, Any]
    ) -> bool:
        """Check if a document matches the given filters."""
        if "library" in filters and library_name != filters["library"]:
            return False

        if (
            "difficulty" in filters
            and doc_data.get("difficulty") != filters["difficulty"]
        ):
            return False

        if "tags" in filters:
            required_tags = (
                filters["tags"]
                if isinstance(filters["tags"], list)
                else [filters["tags"]]
            )
            doc_tags = doc_data.get("tags", [])
            if not any(tag in doc_tags for tag in required_tags):
                return False

        return True

    def _generate_similarity_reason(
        self, doc1: dict[str, Any], doc2: dict[str, Any]
    ) -> str:
        """Generate a human-readable reason for why two libraries are similar."""
        reasons = []

        # Check common tags
        common_tags = set(doc1.get("tags", [])) & set(doc2.get("tags", []))
        if common_tags:
            reasons.append(f"Common functionality: {', '.join(common_tags)}")

        # Check difficulty level
        if doc1.get("difficulty") == doc2.get("difficulty"):
            reasons.append(
                f"Similar complexity level: {doc1.get('difficulty', 'unknown')}"
            )

        # Default reason
        if not reasons:
            reasons.append("Similar content and usage patterns")

        return "; ".join(reasons)

    def _save_index(self):
        """Save the search index to cache."""
        try:
            index_file = self.cache_dir / "search_index.pkl"
            with open(index_file, "wb") as f:
                pickle.dump(
                    {
                        "documents": self.documents,
                        "indexed_libraries": self.indexed_libraries,
                        "model_name": self.model_name,
                    },
                    f,
                )
            logger.info(f"Search index saved to {index_file}")
        except Exception as e:
            logger.warning(f"Failed to save search index: {e}")

    def load_index(self) -> bool:
        """Load the search index from cache."""
        try:
            index_file = self.cache_dir / "search_index.pkl"
            if index_file.exists():
                with open(index_file, "rb") as f:
                    data = pickle.load(f)

                self.documents = data["documents"]
                self.indexed_libraries = data["indexed_libraries"]
                logger.info(f"Search index loaded from {index_file}")
                return True
        except Exception as e:
            logger.warning(f"Failed to load search index: {e}")

        return False

    def get_search_statistics(self) -> dict[str, Any]:
        """Get statistics about the search index."""
        total_chunks = sum(len(doc["text_chunks"]) for doc in self.documents.values())

        return {
            "indexed_libraries": len(self.indexed_libraries),
            "total_text_chunks": total_chunks,
            "model_name": self.model_name,
            "cache_dir": str(self.cache_dir),
            "libraries": list(self.indexed_libraries),
        }
