import re
import json
import logging
from typing import Optional, List, Dict, Any

# Attempt to import duckduckgo_search and set flag
try:
    from duckduckgo_search import DDGS
    DUCKDUCKGO_AVAILABLE = True
except ImportError:
    DUCKDUCKGO_AVAILABLE = False
    DDGS = None # Define DDGS as None if import fails
    logging.warning("DuckDuckGo search library not found (pip install duckduckgo-search). Search functionality will be disabled.")

# Define SearchError Exception
class SearchError(Exception):
    """Base exception for search-related errors."""
    pass

class DuckDuckGoSearch:
    """DuckDuckGo search implementation using the duckduckgo-search library."""

    def __init__(self, max_results: int = 10):
        """Initialize DuckDuckGo search using the library."""
        self.max_results = max_results
        if not DUCKDUCKGO_AVAILABLE:
            logging.warning("DuckDuckGo search unavailable because library is not installed.")
            self._ddgs = None
        else:
            # Initialize the library instance
            try:
                # DDGS can be initialized without arguments for default settings
                self._ddgs = DDGS()
            except Exception as e:
                logging.error(f"Failed to initialize DDGS library: {e}")
                self._ddgs = None

    # Note: The library handles sessions internally, so _get_session is removed.
    # Note: The library handles VQD tokens internally, so _get_vqd_token is removed.

    async def search(self, query: str, site: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Perform search using the duckduckgo-search library and return results.

        Args:
            query: Search query string
            site: Optional site to limit search to

        Returns:
            List of search result dictionaries

        Raises:
            SearchError: If search fails
        """
        if not self._ddgs:
            logging.warning("DuckDuckGo search unavailable or failed to initialize.")
            return []

        if site:
            query = f"site:{site} {query}"

        try:
            # Use the library's text search function
            # Note: The library's search is synchronous. For a truly async app,
            # this should be run in a thread pool executor using asyncio.to_thread.
            # For simplicity in this context, we call it directly.
            logging.debug(f"Performing DDG search for: {query}")
            # The DDGS().text() returns a generator, convert to list
            library_results = list(self._ddgs.text(query, max_results=self.max_results))

            # Format results to match expected output structure
            formatted_results = []
            for r in library_results:
                # Ensure result is a dictionary before accessing keys
                if isinstance(r, dict):
                    formatted_results.append({
                        'title': r.get('title', ''),
                        'url': r.get('href', ''), # Library uses 'href'
                        'description': r.get('body', ''), # Library uses 'body'
                    })
                else:
                    logging.warning(f"Unexpected result format from DDGS library: {r}")

            logging.debug(f"DDG search returned {len(formatted_results)} results.")
            return formatted_results

        except Exception as e:
            # Catch specific library errors if known, otherwise general error
            logging.error(f"DuckDuckGo library search error: {str(e)}", exc_info=True)
            raise SearchError(f"Search error: {str(e)}")

    # Removed close, __aenter__, __aexit__ as session is managed by DDGS library