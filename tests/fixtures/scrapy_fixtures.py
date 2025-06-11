"""Fixtures for ScrapyBackend tests."""

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def html_content_factory():
    """Factory function to generate HTML content for testing."""

    def _factory(title="Test Document", headings=None, paragraphs=None):
        headings = headings or [("h1", "Test Heading")]
        paragraphs = paragraphs or ["This is a test paragraph."]

        heading_html = ""
        for tag, content in headings:
            heading_html += f"<{tag}>{content}</{tag}>\n"

        paragraph_html = ""
        for text in paragraphs:
            paragraph_html += f"<p>{text}</p>\n"

        return f"""
        <html>
            <head>
                <title>{title}</title>
                <meta name="description" content="Test description" />
            </head>
            <body>
                {heading_html}
                {paragraph_html}
                <pre><code>def test():
    pass</code></pre>
                <a href="/test">Test Link</a>
            </body>
        </html>
        """

    return _factory


@pytest.fixture
def mock_aiohttp_session():
    """
    Creates a properly mocked aiohttp ClientSession that can handle async context manager
    patterns and return specified responses.

    Returns a factory function that creates mock sessions.
    """

    def _factory(
        response_body="<html></html>",
        status=200,
        content_type="text/html",
        headers=None,
    ):
        """
        Creates a mock aiohttp session that returns the specified response.

        Args:
            response_body: Body content to return from the response
            status: HTTP status code to return
            content_type: Content-Type header value
            headers: Additional headers to include in the response

        Returns:
            A mock aiohttp ClientSession
        """
        headers = headers or {}
        if content_type and "Content-Type" not in headers:
            headers["Content-Type"] = content_type

        # Create mock response
        mock_response = AsyncMock()
        mock_response.status = status
        mock_response.headers = headers

        # Set up appropriate response methods based on content type
        mock_response.text = AsyncMock(return_value=response_body)
        if content_type == "application/json":
            import json

            try:
                json_data = (
                    json.loads(response_body)
                    if isinstance(response_body, str)
                    else response_body
                )
                mock_response.json = AsyncMock(return_value=json_data)
            except json.JSONDecodeError:
                mock_response.json = AsyncMock(side_effect=ValueError("Invalid JSON"))

        # Create response context manager
        class AsyncContextManagerMock:
            async def __aenter__(self):
                return mock_response

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None

        # Create session mock
        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=AsyncContextManagerMock())
        mock_session.close = AsyncMock()

        return mock_session, mock_response

    return _factory
