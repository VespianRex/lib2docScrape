"""Backend selector for choosing appropriate backend for a URL."""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class BackendCriteria:
    """Criteria for selecting a backend."""
    priority: int = 0
    content_types: List[str] = None
    url_patterns: List[str] = None
    max_load: float = 1.0
    min_success_rate: float = 0.0


class BackendSelector:
    """Select appropriate backend based on URL and criteria."""
    
    def __init__(self):
        """Initialize the backend selector."""
        self.backends: Dict[object, BackendCriteria] = {}
        
    def register_backend(self, backend: object, criteria: BackendCriteria):
        """Register a backend with its selection criteria."""
        self.backends[backend] = criteria
        
    def select_backend(self, url: str) -> Optional[object]:
        """Select the most appropriate backend for a URL."""
        try:
            parsed_url = urlparse(url)
            hostname = parsed_url.netloc.lower()
            
            best_backend = None
            best_priority = -1
            
            for backend, criteria in self.backends.items():
                # Check URL patterns
                if criteria.url_patterns:
                    matches = False
                    for pattern in criteria.url_patterns:
                        if pattern.lower() in url.lower():
                            matches = True
                            break
                    if not matches:
                        continue
                        
                # Check priority
                if criteria.priority > best_priority:
                    best_backend = backend
                    best_priority = criteria.priority
                    
            return best_backend
            
        except Exception as e:
            logging.error(f"Error selecting backend for {url}: {str(e)}")
            return None
