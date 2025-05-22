"""
Search interface for lib2docScrape.
"""
import logging
import os
import json
import re
from typing import Dict, List, Optional, Any, Union, Callable
from datetime import datetime

from pydantic import BaseModel, Field
from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

logger = logging.getLogger(__name__)

class SearchConfig(BaseModel):
    """Configuration for the search interface."""
    max_results: int = 100
    min_query_length: int = 2
    enable_fuzzy_search: bool = True
    fuzzy_threshold: float = 0.7
    enable_filters: bool = True
    enable_sorting: bool = True
    enable_facets: bool = True
    enable_highlighting: bool = True
    highlight_tag: str = "mark"
    default_sort: str = "relevance"
    default_operator: str = "AND"
    search_fields: List[str] = Field(default_factory=lambda: ["title", "content", "metadata"])
    boost_fields: Dict[str, float] = Field(default_factory=lambda: {"title": 2.0, "content": 1.0})
    stop_words: List[str] = Field(default_factory=list)
    synonyms: Dict[str, List[str]] = Field(default_factory=dict)

class SearchResult(BaseModel):
    """Model for a search result."""
    id: str
    title: str
    url: Optional[str] = None
    content_snippet: Optional[str] = None
    score: float
    highlights: Dict[str, List[str]] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SearchResponse(BaseModel):
    """Model for a search response."""
    query: str
    total_results: int
    took_ms: float
    results: List[SearchResult] = Field(default_factory=list)
    facets: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    suggestions: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

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
        
        # Set up routes
        self._setup_routes()
        
        # Set up search index
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.index: Dict[str, Dict[str, List[str]]] = {}
        
        logger.info(f"Search interface initialized with max_results={self.config.max_results}")
        
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
            fuzzy: Optional[bool] = None
        ):
            # Parse fields
            search_fields = self.config.search_fields
            if fields:
                search_fields = fields.split(",")
                
            # Parse filters
            filter_dict = {}
            if filters:
                try:
                    filter_dict = json.loads(filters)
                except json.JSONDecodeError:
                    raise HTTPException(status_code=400, detail="Invalid filters format")
                    
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
                fuzzy=use_fuzzy
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
                suggestions=self._get_suggestions(q)
            )
            
            return response.model_dump()
            
        # Suggestions API
        @self.app.get("/api/suggestions")
        async def suggestions(
            q: str = Query(..., min_length=self.config.min_query_length),
            limit: int = 10
        ):
            suggestions = self._get_suggestions(q)[:limit]
            return {"query": q, "suggestions": suggestions}
            
    def add_document(self, document: Dict[str, Any]) -> None:
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
        
    def _tokenize(self, text: str) -> List[str]:
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
        text = re.sub(r'[^\w\s]', ' ', text)
        
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
        fields: List[str],
        filters: Dict[str, Any],
        sort: str,
        limit: int,
        offset: int,
        fuzzy: bool
    ) -> List[SearchResult]:
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
        matching_docs: Dict[str, Dict[str, float]] = {}
        
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
        paginated_docs = scored_docs[offset:offset+limit]
        
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
                metadata={k: v for k, v in doc.items() if k not in ["id", "title", "url", "content"]}
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
        
    def _get_snippet(self, doc: Dict[str, Any], query: str) -> Optional[str]:
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
        
    def _get_highlights(self, doc: Dict[str, Any], tokens: List[str]) -> Dict[str, List[str]]:
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
                        value[token_pos:token_pos+len(token)],
                        f"<{self.config.highlight_tag}>{value[token_pos:token_pos+len(token)]}</{self.config.highlight_tag}>"
                    )
                    
                    matches.append(highlighted)
                    
            if matches:
                highlights[field] = matches
                
        return highlights
        
    def _get_facets(self, filters: Dict[str, Any]) -> Dict[str, Dict[str, int]]:
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
        for doc_id, doc in self.documents.items():
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
        
    def _get_suggestions(self, query: str) -> List[str]:
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
