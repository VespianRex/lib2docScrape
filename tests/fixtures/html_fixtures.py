"""HTML fixtures for testing."""
import pytest
from typing import List, Tuple, Optional, Callable, Dict, Any


@pytest.fixture
def html_content_factory():
    """Factory function to generate HTML content for testing."""
    def _factory(title: str = "Test Document", 
                headings: Optional[List[Tuple[str, str]]] = None, 
                paragraphs: Optional[List[str]] = None,
                meta_tags: Optional[Dict[str, str]] = None,
                include_code: bool = True,
                include_links: bool = True,
                code_blocks: Optional[List[Tuple[str, str]]] = None,
                links: Optional[List[Tuple[str, str]]] = None,
                malformed: bool = False) -> str:
        """
        Generate HTML content for testing.
        
        Args:
            title: Title of the document
            headings: List of (tag, content) tuples for headings
            paragraphs: List of paragraph text
            meta_tags: Dict of meta name/content pairs
            include_code: Whether to include code blocks
            include_links: Whether to include links
            
        Returns:
            HTML string
        """
        headings = headings or [("h1", "Test Heading")]
        paragraphs = paragraphs or ["This is a test paragraph."]
        meta_tags = meta_tags or {"description": "Test description"}
        code_blocks = code_blocks or []
        links = links or []
        
        # Generate meta tags HTML
        meta_html = ""
        for name, content in meta_tags.items():
            meta_html += f'<meta name="{name}" content="{content}" />\n'
            
        # Generate heading HTML
        heading_html = ""
        for tag, content in headings:
            if malformed:
                heading_html += f"<{tag}>{content}\n"
            else:
                heading_html += f"<{tag}>{content}</{tag}>\n"
            
        # Generate paragraph HTML
        paragraph_html = ""
        for text in paragraphs:
            if malformed:
                paragraph_html += f"<p>{text}\n"
            else:
                paragraph_html += f"<p>{text}</p>\n"
        
        # Generate code blocks
        code_html = ""
        if code_blocks:
            for lang, code in code_blocks:
                code_html += f'<pre><code class="language-{lang}">{code}</code></pre>\n'
        elif include_code:
            code_html = """
            <pre><code class="python">def test():
    pass</code></pre>
            """
        
        # Generate links
        links_html = ""
        if links:
            links_html = '<div class="links">\n'
            for text, href in links:
                links_html += f'<a href="{href}">{text}</a>\n'
            links_html += '</div>\n'
        elif include_links:
            links_html = """
            <div class="links">
                <a href="/test">Test Link</a>
                <a href="https://example.com/external">External Link</a>
                <a href="#section">Fragment Link</a>
            </div>
            """
            
        return f"""
        <!DOCTYPE html>
        <html>
            <head>
                <title>{title}</title>
                {meta_html}
            </head>
            <body>
                {heading_html}
                {paragraph_html}
                {code_html}
                {links_html}
            </body>
        </html>
        """
    return _factory


@pytest.fixture
def mock_response():
    """Factory for mocking HTTP responses."""
    def _factory(status=200, body="", headers=None):
        """Create a mock response object with the given status, body and headers."""
        headers = headers or {"Content-Type": "text/html"}
        
        class MockResponse:
            def __init__(self, status, body, headers):
                self.status = status
                self._body = body
                self.headers = headers
                
            async def text(self):
                return self._body
                
            async def json(self):
                import json
                return json.loads(self._body)
                
            async def read(self):
                return self._body.encode() if isinstance(self._body, str) else self._body
                
            def raise_for_status(self):
                if 400 <= self.status < 600:
                    raise Exception(f"HTTP Error {self.status}")
        
        return MockResponse(status, body, headers)
    
    return _factory
