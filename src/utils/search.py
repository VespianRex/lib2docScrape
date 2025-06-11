import logging

# DuckDuckGo Search Integration
try:
    from duckduckgo_search import DDGS

    DUCKDUCKGO_AVAILABLE = True
except ImportError:
    DUCKDUCKGO_AVAILABLE = False
    # Define DDGS as None or a placeholder if not available,
    # so the class definition doesn't break.
    DDGS = None
    logging.warning(
        "DuckDuckGo search functionality not available. Install with: pip install duckduckgo-search"
    )


class DuckDuckGoSearch:
    """DuckDuckGo search integration."""

    def __init__(self, max_results: int = 10):
        self.max_results = max_results
        # Initialize _ddgs only if available and DDGS is not None
        self._ddgs = DDGS() if DUCKDUCKGO_AVAILABLE and DDGS else None

    async def search(self, query: str, site: str = None) -> list[dict]:
        """Search DuckDuckGo for documentation URLs.

        Args:
            query: The search query string
            site: Optional site filter (e.g. 'python.org')

        Returns:
            List of search result dictionaries
        """
        # Check if DDGS was successfully imported and initialized
        if not self._ddgs:
            logging.warning("DuckDuckGo search not available or failed to initialize.")
            return []

        try:
            # Initial empty results list
            results = []

            # Modify query if site filter is provided
            effective_query = query
            if site:
                effective_query = f"site:{site} {query}"
                logging.info(f"Searching with site filter: {effective_query}")

            # Use DuckDuckGo API to search
            logging.info(f"Searching DuckDuckGo for: {effective_query}")
            sync_results = self._ddgs.text(
                effective_query, max_results=self.max_results
            )

            # Transform the results into a standard format for consistency
            for item in sync_results:
                results.append(
                    {
                        "title": item.get("title", ""),
                        "url": item.get("href", ""),
                        "description": item.get("body", ""),
                    }
                )

            logging.info(f"Found {len(results)} results")
            return results
        except Exception as e:
            logging.error(f"DuckDuckGo search error: {str(e)}")
            return []

    async def close(self):
        """Close the search session."""
        pass  # No cleanup needed for DDGS
