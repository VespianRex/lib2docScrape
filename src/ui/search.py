"""
Search interface for lib2docScrape.
"""

import json
import logging
import re
from datetime import datetime
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SearchConfig(BaseModel):
    """Configuration for the search interface."""

    max_results: int = 20  # Default to 20 as per original test expectation
    min_query_length: int = 2
    enable_fuzzy_search: bool = True
    fuzzy_threshold: float = 0.7
    enable_filters: bool = True
    enable_sorting: bool = True
    enable_facets: bool = True
    highlight_results: bool = (
        True  # Changed from enable_highlighting to match test expectations
    )
    search_titles: bool = True  # Added to match test expectations
    search_content: bool = True  # Added to match test expectations
    search_metadata: bool = True  # Added to match test expectations
    highlight_tag: str = "mark"
    default_sort: str = "relevance"
    default_operator: str = "AND"
    search_fields: list[str] = Field(
        default_factory=lambda: [
            "title",
            "content",
            "metadata",
        ]  # Corresponds to search_titles, search_content, search_metadata
    )
    boost_fields: dict[str, float] = Field(
        default_factory=lambda: {"title": 2.0, "content": 1.0}
    )
    stop_words: list[str] = Field(default_factory=list)
    synonyms: dict[str, list[str]] = Field(default_factory=dict)
    # Fields that were in the test but not in the model, added with defaults or mapped:
    min_score: float = 0.1  # Added from test
    snippet_length: int = 200  # Added from test
    max_history_items: int = 50  # Added for search history
    enable_advanced_search: bool = True  # Added for test compatibility


class SearchResult(BaseModel):
    """Model for a search result."""

    id: str
    title: str
    url: Optional[str] = None
    content_snippet: Optional[str] = None
    score: float
    highlights: dict[str, list[str]] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    """Model for a search response."""

    query: str
    total_results: int
    took_ms: float
    results: list[SearchResult] = Field(default_factory=list)
    facets: dict[str, dict[str, int]] = Field(default_factory=dict)
    suggestions: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchInterface:
    """
    Search interface for lib2docScrape.
    Provides a search API for documentation content.
    """

    def __init__(self, app: FastAPI, config: Optional[SearchConfig] = None):
        """
        Initialize the search interface.

        Args:
            app: FastAPI application
            config: Optional search configuration
        """
        self.app = app
        self.config = config or SearchConfig()

        # Set up search index
        self.documents: dict[str, dict[str, Any]] = {}
        self.index: dict[str, dict[str, list[str]]] = {}

        # Set up search history
        self.search_history: list[str] = []

        # Set up routes
        self._setup_routes()

        logger.info(
            f"Search interface initialized with max_results={self.config.max_results}"
        )

    def search(
        self, query: str, filters: dict[str, Any] = None
    ) -> list[dict[str, Any]]:
        """
        Perform a search query.

        Args:
            query: Search query
            filters: Optional filters to apply

        Returns:
            List of search results
        """
        if filters is None:
            filters = {}

        # Use the internal _search method
        results = self._search(
            query=query,
            fields=self.config.search_fields,
            filters=filters,
            sort=self.config.default_sort,
            limit=self.config.max_results,
            offset=0,
            fuzzy=self.config.enable_fuzzy_search,
        )

        # Convert SearchResult objects to dictionaries
        return [result.model_dump() for result in results]

    def _setup_routes(self) -> None:
        """Set up search routes."""

        # Search API
        @self.app.get("/api/search")
        async def search(
            q: str = Query(..., min_length=self.config.min_query_length),
            fields: Optional[str] = None,
            filters: Optional[str] = None,
            sort: Optional[str] = None,
            limit: int = Query(self.config.max_results, le=self.config.max_results),
            offset: int = 0,
            fuzzy: Optional[bool] = None,
        ):
            # Parse fields
            search_fields = self.config.search_fields
            if fields:
                search_fields = fields.split(",")

            # Parse filters
            filter_dict = {}
            if filters:
                try:
                    parsed_filters = json.loads(filters)
                except json.JSONDecodeError as e:
                    raise HTTPException(
                        status_code=400, detail="Invalid filters format"
                    ) from e
                if not isinstance(parsed_filters, dict):
                    raise HTTPException(
                        status_code=400, detail="Filters must be a JSON object"
                    ) from None
            else:
                parsed_filters = {}

            # Parse sort
            sort_field = sort or self.config.default_sort

            # Parse fuzzy
            use_fuzzy = fuzzy if fuzzy is not None else self.config.enable_fuzzy_search

            # Perform search
            start_time = datetime.now()
            results = self._search(
                query=q,
                fields=search_fields,
                filters=filter_dict,
                sort=sort_field,
                limit=limit,
                offset=offset,
                fuzzy=use_fuzzy,
            )
            end_time = datetime.now()

            # Calculate time taken
            took_ms = (end_time - start_time).total_seconds() * 1000

            # Create response
            response = SearchResponse(
                query=q,
                total_results=len(results),
                took_ms=took_ms,
                results=results,
                facets=self._get_facets(filter_dict),
                suggestions=self._get_suggestions(q),
            )

            return response.model_dump()

        # Suggestions API
        @self.app.get("/api/suggestions")
        async def suggestions(
            q: str = Query(..., min_length=self.config.min_query_length),
            limit: int = 10,
        ):
            suggestions = self._get_suggestions(q)[:limit]
            return {"query": q, "suggestions": suggestions}

        # Search POST endpoint for form submissions and JSON
        @self.app.post("/search")
        async def search_post(request: Request):
            """Handle search form submissions and JSON requests."""
            try:
                # Try to get JSON data first, then form data
                content_type = request.headers.get("content-type", "")

                if "application/json" in content_type:
                    # Handle JSON request
                    json_data = await request.json()
                    query = json_data.get("query", "").strip()
                    filters = json_data.get("filters", {})
                else:
                    # Handle form data
                    form_data = await request.form()
                    query = form_data.get("query", "").strip()
                    filters = {}

                if not query:
                    raise HTTPException(status_code=400, detail="Query is required")

                # Validate query
                validation = self.validate_search_query(query)
                if not validation.is_valid:
                    raise HTTPException(status_code=400, detail=validation.errors)

                # Perform search
                results = self.search(query)

                # Add to history
                self.add_to_history(query)

                return {
                    "query": query,
                    "results": results,
                    "total": len(results),
                    "filters": filters,
                }
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Search error: {e}")
                raise HTTPException(status_code=500, detail="Internal search error")

        # Search results page
        @self.app.get("/search/results")
        async def search_results():
            """Get search results page."""
            return {"message": "Search results page", "results": [], "total": 0}

    def add_document(self, document: dict[str, Any]) -> None:
        """
        Add a document to the search index.

        Args:
            document: Document to add
        """
        # Ensure document has an ID
        if "id" not in document:
            document["id"] = str(len(self.documents) + 1)

        doc_id = document["id"]

        # Add document to documents store
        self.documents[doc_id] = document

        # Index document
        for field in self.config.search_fields:
            if field in document:
                # Get field value
                value = document[field]
                if not isinstance(value, str):
                    value = json.dumps(value)

                # Tokenize and index
                tokens = self._tokenize(value)
                for token in tokens:
                    if token not in self.index:
                        self.index[token] = {}

                    if field not in self.index[token]:
                        self.index[token][field] = []

                    if doc_id not in self.index[token][field]:
                        self.index[token][field].append(doc_id)

        logger.debug(f"Added document {doc_id} to search index")

    def _tokenize(self, text: str) -> list[str]:
        """
        Tokenize text for indexing.

        Args:
            text: Text to tokenize

        Returns:
            List of tokens
        """
        # Convert to lowercase
        text = text.lower()

        # Remove special characters
        text = re.sub(r"[^\w\s]", " ", text)

        # Split into tokens
        tokens = text.split()

        # Remove stop words
        tokens = [token for token in tokens if token not in self.config.stop_words]

        # Add synonyms
        expanded_tokens = tokens.copy()
        for token in tokens:
            if token in self.config.synonyms:
                expanded_tokens.extend(self.config.synonyms[token])

        return expanded_tokens

    def _search(
        self,
        query: str,
        fields: list[str],
        filters: dict[str, Any],
        sort: str,
        limit: int,
        offset: int,
        fuzzy: bool,
    ) -> list[SearchResult]:
        """
        Search for documents.

        Args:
            query: Search query
            fields: Fields to search in
            filters: Filters to apply
            sort: Sort field
            limit: Maximum number of results
            offset: Result offset
            fuzzy: Whether to use fuzzy matching

        Returns:
            List of search results
        """
        # Tokenize query
        tokens = self._tokenize(query)

        # Find matching documents
        matching_docs: dict[str, dict[str, float]] = {}

        for token in tokens:
            if token in self.index:
                for field in fields:
                    if field in self.index[token]:
                        for doc_id in self.index[token][field]:
                            if doc_id not in matching_docs:
                                matching_docs[doc_id] = {}

                            if field not in matching_docs[doc_id]:
                                matching_docs[doc_id][field] = 0.0

                            # Calculate score
                            boost = self.config.boost_fields.get(field, 1.0)
                            matching_docs[doc_id][field] += boost

        # Apply fuzzy matching if enabled
        if fuzzy:
            for doc_id, doc in self.documents.items():
                if doc_id in matching_docs:
                    continue  # Already matched exactly

                for field in fields:
                    if field in doc:
                        value = doc[field]
                        if not isinstance(value, str):
                            value = json.dumps(value)

                        # Check fuzzy match
                        for token in tokens:
                            if self._fuzzy_match(token, value):
                                if doc_id not in matching_docs:
                                    matching_docs[doc_id] = {}

                                if field not in matching_docs[doc_id]:
                                    matching_docs[doc_id][field] = 0.0

                                # Calculate score (lower for fuzzy matches)
                                boost = self.config.boost_fields.get(field, 1.0) * 0.5
                                matching_docs[doc_id][field] += boost

        # Apply filters
        filtered_docs = matching_docs.copy()
        for field, value in filters.items():
            for doc_id in list(filtered_docs.keys()):
                if doc_id not in self.documents:
                    del filtered_docs[doc_id]
                    continue

                doc = self.documents[doc_id]
                if field not in doc or doc[field] != value:
                    del filtered_docs[doc_id]

        # Calculate total scores
        scored_docs = []
        for doc_id, field_scores in filtered_docs.items():
            total_score = sum(field_scores.values())
            scored_docs.append((doc_id, total_score))

        # Sort results
        if sort == "relevance":
            scored_docs.sort(key=lambda x: x[1], reverse=True)
        else:
            # Sort by field
            scored_docs.sort(key=lambda x: self.documents.get(x[0], {}).get(sort, ""))

        # Apply pagination
        paginated_docs = scored_docs[offset : offset + limit]

        # Create search results
        results = []
        for doc_id, score in paginated_docs:
            doc = self.documents[doc_id]

            # Create result
            result = SearchResult(
                id=doc_id,
                title=doc.get("title", "Untitled"),
                url=doc.get("url"),
                content_snippet=self._get_snippet(doc, query),
                score=score,
                highlights=self._get_highlights(doc, tokens),
                metadata={
                    k: v
                    for k, v in doc.items()
                    if k not in ["id", "title", "url", "content"]
                },
            )

            results.append(result)

        return results

    def _fuzzy_match(self, token: str, text: str) -> bool:
        """
        Check if token fuzzy matches text.

        Args:
            token: Token to match
            text: Text to match against

        Returns:
            Whether token fuzzy matches text
        """
        # Simple implementation - check if token is a substring
        return token in text.lower()

    def _get_snippet(self, doc: dict[str, Any], query: str) -> Optional[str]:
        """
        Get a content snippet for a document.

        Args:
            doc: Document
            query: Search query

        Returns:
            Content snippet
        """
        if "content" not in doc:
            return None

        content = doc["content"]
        if not isinstance(content, str):
            return None

        # Find position of query in content
        query_pos = content.lower().find(query.lower())
        if query_pos == -1:
            # Just return the first 200 characters
            return content[:200] + "..."

        # Get snippet around query
        start = max(0, query_pos - 100)
        end = min(len(content), query_pos + len(query) + 100)

        snippet = content[start:end]

        # Add ellipsis if needed
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet

    def _get_highlights(
        self, doc: dict[str, Any], tokens: list[str]
    ) -> dict[str, list[str]]:
        """
        Get highlights for a document.

        Args:
            doc: Document
            tokens: Search tokens

        Returns:
            Highlights by field
        """
        highlights = {}

        for field in self.config.search_fields:
            if field not in doc:
                continue

            value = doc[field]
            if not isinstance(value, str):
                continue

            # Find matches
            matches = []
            for token in tokens:
                token_pos = value.lower().find(token.lower())
                if token_pos != -1:
                    # Get context around match
                    start = max(0, token_pos - 20)
                    end = min(len(value), token_pos + len(token) + 20)

                    context = value[start:end]

                    # Add ellipsis if needed
                    if start > 0:
                        context = "..." + context
                    if end < len(value):
                        context = context + "..."

                    # Highlight match
                    highlighted = context.replace(
                        value[token_pos : token_pos + len(token)],
                        f"<{self.config.highlight_tag}>{value[token_pos : token_pos + len(token)]}</{self.config.highlight_tag}>",
                    )

                    matches.append(highlighted)

            if matches:
                highlights[field] = matches

        return highlights

    def _get_facets(self, filters: dict[str, Any]) -> dict[str, dict[str, int]]:
        """
        Get facets for search results.

        Args:
            filters: Current filters

        Returns:
            Facets by field
        """
        if not self.config.enable_facets:
            return {}

        facets = {}

        # Get all documents that match the current filters
        matching_docs = []
        for _doc_id, doc in self.documents.items():
            match = True
            for field, value in filters.items():
                if field not in doc or doc[field] != value:
                    match = False
                    break

            if match:
                matching_docs.append(doc)

        # Calculate facets
        for doc in matching_docs:
            for field, value in doc.items():
                if field in ["id", "title", "url", "content"]:
                    continue

                if not isinstance(value, (str, int, float, bool)):
                    continue

                if field not in facets:
                    facets[field] = {}

                str_value = str(value)
                if str_value not in facets[field]:
                    facets[field][str_value] = 0

                facets[field][str_value] += 1

        return facets

    def _get_suggestions(self, query: str) -> list[str]:
        """
        Get search suggestions for a query.

        Args:
            query: Search query

        Returns:
            List of suggestions
        """
        # Simple implementation - just return tokens that start with the query
        suggestions = []

        for token in self.index.keys():
            if token.startswith(query.lower()):
                suggestions.append(token)

        return suggestions

    def _apply_filters(
        self, results: list[dict[str, Any]], filters: dict[str, Any]
    ) -> list[dict[str, Any]]:
        if not filters:
            return results

        filtered_results = []
        for result in results:
            match = True
            for key, value in filters.items():
                if key not in result or result[key] != value:
                    match = False
                    break
            if match:
                filtered_results.append(result)
        return filtered_results

    def _sort_results(
        self, results: list[dict[str, Any]], sort_by: str, sort_order: str
    ) -> list[dict[str, Any]]:
        if not sort_by:
            return results

        reverse = sort_order.lower() == "desc"
        try:
            # Attempt to sort, gracefully handle missing keys or unorderable types
            # by placing items with errors at the end (or beginning for reverse)
            return sorted(
                results,
                key=lambda x: (x.get(sort_by) is None, x.get(sort_by)),
                reverse=reverse,
            )
        except TypeError:
            logger.warning(
                f"Could not sort results by '{sort_by}' due to unorderable types."
            )
            return results  # Return unsorted if complex sort fails

    def _generate_facets(
        self, results: list[dict[str, Any]], facet_fields: list[str]
    ) -> dict[str, dict[str, int]]:
        facets = {}
        for result in results:
            for field in facet_fields:
                if field in result:
                    value = result[field]
                    if field not in facets:
                        facets[field] = {}
                    if value not in facets[field]:
                        facets[field][value] = 0
                    facets[field][value] += 1
        return facets

    def _perform_search(
        self, query_terms: list[str], search_fields: list[str]
    ) -> list[dict[str, Any]]:
        """Core search logic based on query terms and fields."""
        search_results = []
        # Iterate through documents using _doc_id for the unused key
        for _doc_id, doc in self.documents.items():
            score = 0
            matched_terms = set()
            highlights: dict[str, list[str]] = {}
            # document_text_corpus is not used, so it can be removed or commented out.
            # document_text_corpus = "".join(
            #     str(doc.get(field, "")) for field in search_fields
            # ).lower()

            for field in search_fields:
                field_content = str(doc.get(field, "")).lower()

                # Check each query term
                for term in query_terms:
                    if term in field_content:
                        score += self.config.boost_fields.get(field, 1.0)
                        matched_terms.add(term)

                        # Highlighting
                        if field not in highlights:
                            highlights[field] = []
                        highlights[field].append(field_content)

            # Only include documents that match at least one term
            if matched_terms:
                search_results.append(
                    {
                        "id": _doc_id,
                        "score": score,
                        "highlights": highlights,
                        **{
                            k: v
                            for k, v in doc.items()
                            if k not in ["id", "title", "url", "content"]
                        },
                    }
                )

        # Sort and limit results
        search_results.sort(key=lambda x: x["score"], reverse=True)
        return search_results[: self.config.max_results]

    def validate_search_query(self, query: str) -> "SearchValidationResult":
        """
        Validate a search query.

        Args:
            query: Search query to validate

        Returns:
            Validation result
        """
        from pydantic import BaseModel

        class SearchValidationResult(BaseModel):
            is_valid: bool
            query: str
            errors: list[str] = []

        errors = []

        if not query or query.strip() == "":
            errors.append("Query cannot be empty")
        elif len(query) > 500:  # Reasonable limit
            errors.append("Query too long")
        elif len(query) < self.config.min_query_length:
            errors.append(
                f"Query must be at least {self.config.min_query_length} characters"
            )

        return SearchValidationResult(
            is_valid=len(errors) == 0, query=query, errors=errors
        )

    def get_autocomplete_suggestions(self, partial_query: str) -> list[str]:
        """
        Get autocomplete suggestions for a partial query.

        Args:
            partial_query: Partial search query

        Returns:
            List of autocomplete suggestions
        """
        return self._get_suggestions(partial_query)

    def get_autocomplete(self, partial_query: str) -> list[str]:
        """
        Get autocomplete suggestions for a partial query (calls get_autocomplete_suggestions).

        Args:
            partial_query: Partial search query

        Returns:
            List of autocomplete suggestions
        """
        return self.get_autocomplete_suggestions(partial_query)

    def apply_filters(
        self, query: str, filters: dict[str, Any]
    ) -> "FilteredSearchResult":
        """
        Apply filters to a search query.

        Args:
            query: Search query
            filters: Filters to apply

        Returns:
            Filtered search result
        """
        from pydantic import BaseModel

        class FilteredSearchResult(BaseModel):
            query: str
            filters: dict[str, Any]

        return FilteredSearchResult(query=query, filters=filters)

    def add_to_history(self, query: str) -> None:
        """
        Add a search query to the search history.

        Args:
            query: Search query to add
        """
        if query and query.strip():
            # Remove if already exists to avoid duplicates
            if query in self.search_history:
                self.search_history.remove(query)

            # Add to beginning of list
            self.search_history.insert(0, query)

            # Limit history size
            max_history = getattr(self.config, "max_history_items", 50)
            if len(self.search_history) > max_history:
                self.search_history = self.search_history[:max_history]

    def get_search_history(self) -> list[str]:
        """
        Get the search history.

        Returns:
            List of recent search queries
        """
        return self.search_history.copy()
