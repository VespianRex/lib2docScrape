import aiohttp
import pytest
import responses
from aioresponses import aioresponses
from bs4 import BeautifulSoup

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

        responses.add(responses.GET, url, json=expected_response, status=200)

        import requests

        response = requests.get(url)
        assert response.status_code == 200
        assert response.json() == expected_response

    @responses.activate
    def test_responses_error(self):
        """Test error handling in sync HTTP request mocking."""
        url = "https://example.com/api/error"
        error_response = {"error": "Not Found"}

        responses.add(responses.GET, url, json=error_response, status=404)

        import requests

        response = requests.get(url)
        assert response.status_code == 404
        assert response.json() == error_response

    def test_html_parsing_basic(self, sample_html_factory):
        """Test basic HTML parsing capabilities with custom HTML content."""
        custom_html = sample_html_factory(
            title="Custom Test Page",
            heading="Main Title",
            paragraph="First paragraph",
            link="/",
        )

        soup = BeautifulSoup(custom_html, "html.parser")

        # Basic structure tests
        assert soup.title.string == "Custom Test Page"
        assert soup.h1.string == "Main Title"
        assert len(soup.find_all("p")) == 1
        assert len(soup.find_all("a")) == 1

    def test_html_element_extraction(self, sample_html_factory):
        """Test extraction of specific HTML elements with complex content."""
        custom_html = sample_html_factory(
            title="API Documentation",
            heading="API Documentation",
            paragraph="This is the API documentation.",
            link="/api/users",
        )

        soup = BeautifulSoup(custom_html, "html.parser")

        # Test heading hierarchy
        headings = soup.find_all(["h1"])
        assert len(headings) == 1
        assert headings[0].string == "API Documentation"

        # Test code blocks
        code_blocks = soup.find_all("code")
        assert len(code_blocks) == 1

        # Test links
        links = soup.find_all("a")
        assert len(links) == 1
        assert links[0]["href"] == "/api/users"

    def test_malformed_html_handling(self):
        """Test handling of malformed HTML content with the factory."""
        # Create malformed HTML manually since sample_html_factory doesn't support malformed option
        malformed_html = """
        <html>
            <head>
                <title>Malformed Page</title>
            </head>
            <body>
                <h1>Unclosed Heading
                <p>Unclosed paragraph
            </body>
        </html>
        """

        # BeautifulSoup should handle malformed HTML gracefully
        soup = BeautifulSoup(malformed_html, "html.parser")

        # Basic structure should still be parseable
        assert soup.title.string == "Malformed Page"
        assert "Unclosed Heading" in soup.h1.text
        # Content should be found even with unclosed tags
        paragraphs = soup.find_all("p")
        assert len(paragraphs) == 1
        assert "Unclosed paragraph" in paragraphs[0].text

    @pytest.mark.asyncio
    async def test_mixed_content_response(self):
        """Test handling of responses with mixed content types."""
        html_content = """
        <html><body>
        <h1>API Documentation</h1>
        <pre><code class="json">{"version": "1.0"}</code></pre>
        </body></html>
        """

        # Create a simple mock response
        class MockResponse:
            def __init__(self, status, body, headers):
                self.status = status
                self._body = body
                self.headers = headers

            async def text(self):
                return self._body

        response = MockResponse(
            status=200, body=html_content, headers={"Content-Type": "text/html"}
        )

        assert response.status == 200
        assert "text/html" in response.headers["Content-Type"]

        # Parse the HTML content
        content = await response.text()
        soup = BeautifulSoup(content, "html.parser")
        assert soup.h1.string == "API Documentation"

        # Extract and parse the embedded JSON
        code_content = soup.find("code", class_="json").string
        import json

        json_data = json.loads(code_content)
        assert json_data["version"] == "1.0"
