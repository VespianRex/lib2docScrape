"""
Documentation site verification module.
Helps verify that a URL points to a valid documentation site and identifies the library.
"""
import json
import logging
import re
from typing import Dict, List, Optional, Set, Tuple, Any
from urllib.parse import urlparse

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class DocSitePattern(BaseModel):
    """Pattern for identifying a documentation site."""
    name: str
    url_patterns: List[str]
    content_patterns: List[str] = Field(default_factory=list)
    version_pattern: Optional[str] = None
    doc_paths: List[str] = Field(default_factory=list)
    
class DocSiteVerifier:
    """
    Verifies if a URL points to a valid documentation site.
    Can identify the library and version from the URL or content.
    """
    
    def __init__(self, patterns_file: Optional[str] = None):
        """
        Initialize the documentation site verifier.
        
        Args:
            patterns_file: Optional path to a JSON file with patterns
        """
        self.patterns: List[DocSitePattern] = []
        self.library_urls: Dict[str, str] = {}
        
        # Load default patterns
        self._load_default_patterns()
        
        # Load patterns from file if provided
        if patterns_file:
            self._load_patterns_from_file(patterns_file)
            
    def _load_default_patterns(self) -> None:
        """Load default documentation site patterns."""
        default_patterns = [
            # Python
            DocSitePattern(
                name="python",
                url_patterns=["docs.python.org", "python.org/doc"],
                content_patterns=["Python Documentation", "The Python Standard Library"],
                version_pattern=r"(\d+\.\d+)",
                doc_paths=["library", "reference", "tutorial", "howto"]
            ),
            # Django
            DocSitePattern(
                name="django",
                url_patterns=["docs.djangoproject.com"],
                content_patterns=["Django documentation", "Django Documentation"],
                version_pattern=r"(\d+\.\d+)",
                doc_paths=["intro", "topics", "ref", "howto", "faq"]
            ),
            # Flask
            DocSitePattern(
                name="flask",
                url_patterns=["flask.palletsprojects.com"],
                content_patterns=["Flask Documentation", "Welcome to Flask"],
                version_pattern=r"(\d+\.\d+\.\d+)",
                doc_paths=["quickstart", "tutorial", "patterns", "api"]
            ),
            # React
            DocSitePattern(
                name="react",
                url_patterns=["reactjs.org/docs", "react.dev"],
                content_patterns=["React Documentation", "React Docs"],
                version_pattern=r"(\d+\.\d+\.\d+)",
                doc_paths=["getting-started", "tutorial", "api", "hooks"]
            ),
            # Vue.js
            DocSitePattern(
                name="vue",
                url_patterns=["vuejs.org/guide", "vuejs.org/api"],
                content_patterns=["Vue.js Documentation", "Vue.js Guide"],
                version_pattern=r"v(\d+)",
                doc_paths=["guide", "api", "examples", "cookbook"]
            ),
            # Angular
            DocSitePattern(
                name="angular",
                url_patterns=["angular.io/docs", "angular.io/guide", "angular.io/api"],
                content_patterns=["Angular Documentation", "Angular Docs"],
                version_pattern=r"(\d+)",
                doc_paths=["guide", "api", "tutorial", "cli"]
            ),
            # Node.js
            DocSitePattern(
                name="node",
                url_patterns=["nodejs.org/docs", "nodejs.org/api", "nodejs.dev"],
                content_patterns=["Node.js Documentation", "Node.js API"],
                version_pattern=r"(\d+\.\d+\.\d+)",
                doc_paths=["api", "guides", "dependencies"]
            ),
            # Express.js
            DocSitePattern(
                name="express",
                url_patterns=["expressjs.com"],
                content_patterns=["Express Documentation", "Express API"],
                version_pattern=r"(\d+\.\d+\.\d+)",
                doc_paths=["starter", "guide", "api", "advanced"]
            ),
            # TensorFlow
            DocSitePattern(
                name="tensorflow",
                url_patterns=["tensorflow.org/api_docs", "tensorflow.org/guide"],
                content_patterns=["TensorFlow Documentation", "TensorFlow API"],
                version_pattern=r"(\d+\.\d+)",
                doc_paths=["api_docs", "guide", "tutorials", "examples"]
            ),
            # PyTorch
            DocSitePattern(
                name="pytorch",
                url_patterns=["pytorch.org/docs", "pytorch.org/tutorials"],
                content_patterns=["PyTorch Documentation", "PyTorch Tutorials"],
                version_pattern=r"(\d+\.\d+\.\d+)",
                doc_paths=["docs", "tutorials", "examples"]
            )
        ]
        
        for pattern in default_patterns:
            self.add_pattern(pattern)
            
    def _load_patterns_from_file(self, file_path: str) -> None:
        """
        Load patterns from a JSON file.
        
        Args:
            file_path: Path to the JSON file
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            for pattern_data in data.get("patterns", []):
                pattern = DocSitePattern(**pattern_data)
                self.add_pattern(pattern)
                
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading patterns from {file_path}: {e}")
            
    def add_pattern(self, pattern: DocSitePattern) -> None:
        """
        Add a documentation site pattern.
        
        Args:
            pattern: DocSitePattern to add
        """
        self.patterns.append(pattern)
        
        # Add to library URLs mapping
        for url_pattern in pattern.url_patterns:
            self.library_urls[url_pattern] = pattern.name
            
    def verify_url(self, url: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Verify if a URL points to a known documentation site.
        
        Args:
            url: URL to verify
            
        Returns:
            Tuple of (is_valid, library_name, version)
        """
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        path = parsed_url.path
        
        for pattern in self.patterns:
            # Check if URL matches any pattern
            if any(url_pattern in url for url_pattern in pattern.url_patterns):
                # Try to extract version
                version = None
                if pattern.version_pattern:
                    match = re.search(pattern.version_pattern, url)
                    if match:
                        version = match.group(1)
                        
                return True, pattern.name, version
                
        return False, None, None
        
    def verify_content(self, url: str, content: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Verify if content appears to be from a documentation site.
        
        Args:
            url: URL the content was fetched from
            content: HTML content
            
        Returns:
            Tuple of (is_valid, library_name, version)
        """
        # First check URL
        url_result = self.verify_url(url)
        if url_result[0]:
            return url_result
            
        # Check content patterns
        for pattern in self.patterns:
            if any(content_pattern in content for content_pattern in pattern.content_patterns):
                # Try to extract version from content
                version = None
                if pattern.version_pattern:
                    match = re.search(pattern.version_pattern, content)
                    if match:
                        version = match.group(1)
                        
                return True, pattern.name, version
                
        return False, None, None
        
    def get_library_from_name(self, name: str) -> Optional[DocSitePattern]:
        """
        Get library pattern from name.
        
        Args:
            name: Library name
            
        Returns:
            DocSitePattern or None if not found
        """
        for pattern in self.patterns:
            if pattern.name.lower() == name.lower():
                return pattern
                
        return None
        
    def get_doc_url_from_name(self, name: str, version: Optional[str] = None) -> Optional[str]:
        """
        Get documentation URL from library name.
        
        Args:
            name: Library name
            version: Optional version string
            
        Returns:
            Documentation URL or None if not found
        """
        pattern = self.get_library_from_name(name)
        if not pattern or not pattern.url_patterns:
            return None
            
        # Use the first URL pattern as the base URL
        base_url = pattern.url_patterns[0]
        
        # If it's not a full URL, assume it's a domain
        if not base_url.startswith(('http://', 'https://')):
            base_url = f"https://{base_url}"
            
        # Add version to URL if provided and we have a pattern
        if version and pattern.version_pattern:
            # This is a simplified approach - in a real implementation,
            # you would need more sophisticated URL construction
            if 'docs.python.org' in base_url:
                return f"https://docs.python.org/{version}/"
            elif 'docs.djangoproject.com' in base_url:
                return f"https://docs.djangoproject.com/en/{version}/"
            elif 'flask.palletsprojects.com' in base_url:
                return f"https://flask.palletsprojects.com/en/{version}/"
            # Add more specific URL patterns as needed
            
        return base_url
