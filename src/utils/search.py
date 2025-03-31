"""Search utility module for documentation crawler."""

import json
import logging
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus

DUCKDUCKGO_AVAILABLE = True

class SearchError(Exception):
    """Base exception for search-related errors."""
    pass

class DuckDuckGoSearch:
    """DuckDuckGo search implementation."""
    
    BASE_URL = "https://duckduckgo.com/"
    SEARCH_URL = "https://links.duckduckgo.com/d.js"
    
    def __init__(self, max_results: int = 10, timeout: float = 10.0):
        """Initialize DuckDuckGo search."""
        self.max_results = max_results
        self.timeout = timeout
        self.session = None
        self.vqd_token = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
        return self.session
        
    async def _get_vqd_token(self, query: str) -> str:
        """Get vqd token required for search."""
        if self.vqd_token:
            return self.vqd_token
            
        session = await self._get_session()
        params = {'q': query}
        
        try:
            async with session.get(self.BASE_URL, params=params) as response:
                if response.status != 200:
                    raise SearchError(f"Failed to get vqd token: {response.status}")
                    
                text = await response.text()
                vqd_match = text.find('vqd="')
                if vqd_match == -1:
                    raise SearchError("Could not find vqd token")
                    
                vqd_start = vqd_match + 5
                vqd_end = text.find('"', vqd_start)
                if vqd_end == -1:
                    raise SearchError("Malformed vqd token")
                    
                self.vqd_token = text[vqd_start:vqd_end]
                return self.vqd_token
                
        except asyncio.TimeoutError:
            raise SearchError("Timeout while getting vqd token")
        except Exception as e:
            raise SearchError(f"Error getting vqd token: {str(e)}")
            
    async def search(self, query: str, site: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Perform search and return results.
        
        Args:
            query: Search query string
            site: Optional site to limit search to
            
        Returns:
            List of search result dictionaries
            
        Raises:
            SearchError: If search fails
        """
        if site:
            query = f"site:{site} {query}"
            
        encoded_query = quote_plus(query)
        vqd_token = await self._get_vqd_token(query)
        session = await self._get_session()
        
        params = {
            'q': encoded_query,
            'vqd': vqd_token,
            'l': 'us-en',
            'o': 'json',
            'p': '1',
            's': '0',
        }
        
        try:
            async with session.get(self.SEARCH_URL, params=params) as response:
                if response.status != 200:
                    raise SearchError(f"Search failed with status: {response.status}")
                    
                data = await response.json()
                results = []
                
                for result in data.get('results', [])[:self.max_results]:
                    results.append({
                        'title': result.get('title', ''),
                        'url': result.get('url', ''),
                        'description': result.get('description', ''),
                    })
                    
                return results
                
        except asyncio.TimeoutError:
            raise SearchError("Search timeout")
        except json.JSONDecodeError:
            raise SearchError("Invalid JSON response")
        except Exception as e:
            raise SearchError(f"Search error: {str(e)}")
            
    async def close(self):
        """Close resources."""
        if self.session:
            await self.session.close()
            self.session = None

    async def __aenter__(self):
        """Async context manager enter."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()