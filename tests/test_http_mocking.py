import pytest
import aiohttp
import responses
from aioresponses import aioresponses
from bs4 import BeautifulSoup
from tests.fixtures.html_fixtures import html_content_factory, mock_response

# Mark all tests in this module with http_mocking marker
pytestmark = pytest.mark.http_mocking

class TestHTTPMocking:
    """Test suite for HTTP mocking capabilities."""

    @pytest.mark.asyncio
    async def test_aioresponses_success(self):
        """Test successful async HTTP request mocking with aioresponses."""
        url = "https://example.com/api"
        expected_response = {"status": "success", "data": "test"}

        with aioresponses() as m:
            m.get(url, status=200, payload=expected_response)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    assert response.status == 200
                    data = await response.json()
                    assert data == expected_response

    @pytest.mark.asyncio 
    async def test_aioresponses_error(self):
        """Test error handling in async HTTP request mocking."""
        url = "https://example.com/api/error"
        error_response = {"error": "Not Found"}

        with aioresponses() as m:
            m.get(url, status=404, payload=error_response)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    assert response.status == 404
                    data = await response.json()
                    assert data == error_response

    @responses.activate
    def test_responses_success(self):
        """Test successful sync HTTP request mocking with responses."""
        url = "https://example.com/api"
        expected_response = {"status": "success", "data": "test"}
        
        responses.add(
            responses.GET,
            url,
            json=expected_response,
            status=200
        )
        
        import requests
        response = requests.get(url)
        assert response.status_code == 200
        assert response.json() == expected_response

    @responses.activate
    def test_responses_error(self):
        """Test error handling in sync HTTP request mocking."""
        url = "https://example.com/api/error"
        error_response = {"error": "Not Found"}
        
        responses.add(
            responses.GET,
            url,
            json=error_response,
            status=404
        )
        
        import requests
        response = requests.get(url)
        assert response.status_code == 404
        assert response.json() == error_response

    def test_html_parsing_basic(self, html_content_factory):
        """Test basic HTML parsing capabilities with custom HTML content."""
        custom_html = html_content_factory(
            title="Custom Test Page",
            headings=[("h1", "Main Title"), ("h2", "Subtitle")],
            paragraphs=["First paragraph", "Second paragraph"],
            links=[("Home", "/"), ("About", "/about")]
        )
        
        soup = BeautifulSoup(custom_html, 'html.parser')
        
        # Basic structure tests
        assert soup.title.string == "Custom Test Page"
        assert soup.h1.string == "Main Title"
        assert soup.h2.string == "Subtitle"
        assert len(soup.find_all('p')) == 2
        assert len(soup.find_all('a')) == 2

    def test_html_element_extraction(self, html_content_factory):
        """Test extraction of specific HTML elements with complex content."""
        custom_html = html_content_factory(
            headings=[
                ("h1", "API Documentation"),
                ("h2", "Endpoints"),
                ("h3", "GET /users")
            ],
            code_blocks=[
                ("python", "def get_users():\n    return User.query.all()"),
                ("json", '{"status": "success"}')
            ],
            links=[
                ("Users API", "/api/users"),
                ("Auth API", "/api/auth")
            ]
        )
        
        soup = BeautifulSoup(custom_html, 'html.parser')
        
        # Test heading hierarchy
        headings = soup.find_all(['h1', 'h2', 'h3'])
        assert len(headings) == 3
        assert [h.string for h in headings] == ["API Documentation", "Endpoints", "GET /users"]
        
        # Test code blocks
        code_blocks = soup.find_all('code')
        assert len(code_blocks) == 2
        assert "language-python" in code_blocks[0]['class']
        assert "language-json" in code_blocks[1]['class']
        
        # Test links
        links = soup.find_all('a')
        assert len(links) == 2
        assert [link['href'] for link in links] == ["/api/users", "/api/auth"]

    def test_malformed_html_handling(self, html_content_factory):
        """Test handling of malformed HTML content with the factory."""
        malformed_html = html_content_factory(
            title="Malformed Page",
            headings=[("h1", "Unclosed Heading")],
            paragraphs=["Unclosed paragraph"],
            malformed=True,  # This will leave tags unclosed
            include_code=False,  # Don't add code blocks
            include_links=False  # Don't add links
        )
        
        # BeautifulSoup should handle malformed HTML gracefully
        soup = BeautifulSoup(malformed_html, 'html.parser')
        
        # Basic structure should still be parseable
        assert soup.title.string == "Malformed Page"
        assert "Unclosed Heading" in soup.h1.text
        # Content should be found even with unclosed tags
        paragraphs = soup.find_all('p')
        assert len(paragraphs) == 1
        assert "Unclosed paragraph" in paragraphs[0].text

    @pytest.mark.asyncio
    async def test_mixed_content_response(self, mock_response):
        """Test handling of responses with mixed content types."""
        url = "https://example.com/api/docs"
        html_content = """
        <html><body>
        <h1>API Documentation</h1>
        <pre><code class="json">{"version": "1.0"}</code></pre>
        </body></html>
        """
        
        # Create a response with both HTML and a JSON endpoint
        response = mock_response(
            status=200,
            body=html_content,
            headers={"Content-Type": "text/html"}
        )
        
        assert response.status == 200
        assert "text/html" in response.headers["Content-Type"]
        
        # Parse the HTML content
        content = await response.text()
        soup = BeautifulSoup(content, 'html.parser')
        assert soup.h1.string == "API Documentation"
        
        # Extract and parse the embedded JSON
        code_content = soup.find('code', class_='json').string
        import json
        json_data = json.loads(code_content)
        assert json_data["version"] == "1.0"