"""
Tests for the format handlers.
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.processors.content.format_detector import ContentTypeDetector, FormatDetector
from src.processors.content.format_handlers import (
    AsciiDocHandler,
    HTMLHandler,
    MarkdownHandler,
    ReStructuredTextHandler,
)


@pytest.fixture
def html_processor():
    """Create a mock HTML processor."""
    processor = AsyncMock()
    processor.process = AsyncMock(
        return_value={
            "formatted_content": "<html><body>Test</body></html>",
            "structure": [{"type": "heading", "level": 1, "title": "Test"}],
            "headings": [{"level": 1, "text": "Test", "id": "", "type": "heading"}],
            "metadata": {"title": "Test"},
            "assets": [],
        }
    )
    return processor


@pytest.fixture
def html_handler(html_processor):
    """Create an HTML handler."""
    return HTMLHandler(html_processor)


@pytest.fixture
def markdown_handler():
    """Create a Markdown handler."""
    return MarkdownHandler()


@pytest.fixture
def rst_handler():
    """Create a reStructuredText handler."""
    return ReStructuredTextHandler()


@pytest.fixture
def asciidoc_handler():
    """Create an AsciiDoc handler."""
    return AsciiDocHandler()


@pytest.fixture
def format_detector(html_handler, markdown_handler, rst_handler, asciidoc_handler):
    """Create a format detector with all handlers registered."""
    detector = FormatDetector()
    detector.register_handler(html_handler)
    detector.register_handler(markdown_handler)
    detector.register_handler(rst_handler)
    detector.register_handler(asciidoc_handler)
    return detector


def test_html_handler_can_handle(html_handler):
    """Test HTML handler can_handle method."""
    # Test with content type
    assert html_handler.can_handle("", "text/html") is True
    assert html_handler.can_handle("", "application/xhtml+xml") is True
    assert html_handler.can_handle("", "text/plain") is False

    # Test with content
    assert html_handler.can_handle("<html><body>Test</body></html>") is True
    assert html_handler.can_handle("<div>Test</div>") is True
    assert html_handler.can_handle("<p>Test</p>") is True
    assert html_handler.can_handle("<h1>Test</h1>") is True
    assert html_handler.can_handle("Test") is False


@pytest.mark.asyncio
async def test_html_handler_process(html_handler, html_processor):
    """Test HTML handler process method."""
    result = await html_handler.process(
        "<html><body>Test</body></html>", "https://example.com"
    )

    # Check that the HTML processor was called
    html_processor.process.assert_called_once_with(
        "<html><body>Test</body></html>", "https://example.com"
    )

    # Check the result
    assert result["formatted_content"] == "<html><body>Test</body></html>"
    assert result["structure"] == [{"type": "heading", "level": 1, "title": "Test"}]
    assert result["headings"] == [
        {"level": 1, "text": "Test", "id": "", "type": "heading"}
    ]
    assert result["metadata"] == {"title": "Test"}
    assert result["assets"] == []


def test_markdown_handler_can_handle(markdown_handler):
    """Test Markdown handler can_handle method."""
    # Test with content type
    assert markdown_handler.can_handle("", "text/markdown") is True
    assert markdown_handler.can_handle("", "text/md") is True
    assert markdown_handler.can_handle("", "text/plain") is False

    # Test with content
    assert markdown_handler.can_handle("# Heading\n\nParagraph") is True
    assert markdown_handler.can_handle("Heading\n=======\n\nParagraph") is True
    assert markdown_handler.can_handle("```python\nprint('Hello')\n```") is True
    assert markdown_handler.can_handle("* Item 1\n* Item 2") is True
    assert markdown_handler.can_handle("[Link](https://example.com)") is True
    assert markdown_handler.can_handle("Just plain text") is False


@pytest.mark.asyncio
async def test_markdown_handler_process(markdown_handler):
    """Test Markdown handler process method."""
    # Mock the markdown library
    with patch("markdown.markdown", return_value="<h1>Heading</h1><p>Paragraph</p>"):
        # Mock the ContentProcessor
        with patch(
            "src.processors.content_processor.ContentProcessor"
        ) as mock_processor_class:
            mock_processor = AsyncMock()
            mock_processor.process = AsyncMock(
                return_value={
                    "formatted_content": "# Heading\n\nParagraph",
                    "structure": [{"type": "heading", "level": 1, "title": "Heading"}],
                }
            )
            mock_processor_class.return_value = mock_processor

            result = await markdown_handler.process(
                "# Heading\n\nParagraph", "https://example.com"
            )

            # Check the result
            assert result["formatted_content"] == "# Heading\n\nParagraph"
            assert result["structure"] == [
                {"type": "heading", "level": 1, "title": "Heading"}
            ]


def test_rst_handler_can_handle(rst_handler):
    """Test reStructuredText handler can_handle method."""
    # Test with content type
    assert rst_handler.can_handle("", "text/x-rst") is True
    assert rst_handler.can_handle("", "text/restructuredtext") is True
    assert rst_handler.can_handle("", "text/plain") is False

    # Test with content
    assert rst_handler.can_handle("=======\nHeading\n=======\n\nParagraph") is True
    assert rst_handler.can_handle(".. directive:: value") is True
    assert rst_handler.can_handle(".. [1] Footnote") is True
    assert rst_handler.can_handle(".. _target:") is True
    assert rst_handler.can_handle(":role:`value`") is True
    assert rst_handler.can_handle("::\n\n    code block") is True
    assert rst_handler.can_handle("Just plain text") is False


def test_asciidoc_handler_can_handle(asciidoc_handler):
    """Test AsciiDoc handler can_handle method."""
    # Test with content type
    assert asciidoc_handler.can_handle("", "text/asciidoc") is True
    assert asciidoc_handler.can_handle("", "text/plain") is False

    # Test with content
    assert asciidoc_handler.can_handle("= Document Title") is True
    assert asciidoc_handler.can_handle("== Section Title") is True
    assert (
        asciidoc_handler.can_handle("[source,python]\n----\nprint('Hello')\n----")
        is True
    )
    assert asciidoc_handler.can_handle("[NOTE]\n====\nThis is a note\n====") is True
    assert asciidoc_handler.can_handle("Just plain text") is False


def test_format_detector_detect_format(format_detector):
    """Test format detector detect_format method."""
    # Test with content type
    assert format_detector.detect_format("", "text/html").get_format_name() == "HTML"
    assert (
        format_detector.detect_format("", "text/markdown").get_format_name()
        == "Markdown"
    )
    assert (
        format_detector.detect_format("", "text/x-rst").get_format_name()
        == "reStructuredText"
    )
    assert (
        format_detector.detect_format("", "text/asciidoc").get_format_name()
        == "AsciiDoc"
    )

    # Test with content
    assert (
        format_detector.detect_format(
            "<html><body>Test</body></html>"
        ).get_format_name()
        == "HTML"
    )
    assert (
        format_detector.detect_format("# Heading\n\nParagraph").get_format_name()
        == "Markdown"
    )
    # Use a more specific RST pattern that won't be confused with Markdown
    assert (
        format_detector.detect_format(".. directive:: value").get_format_name()
        == "reStructuredText"
    )
    assert (
        format_detector.detect_format("= Document Title").get_format_name()
        == "AsciiDoc"
    )

    # Test with unknown format
    assert format_detector.detect_format("Just plain text") is None


def test_content_type_detector():
    """Test content type detector."""
    # Test detect_from_filename
    assert ContentTypeDetector.detect_from_filename("document.html") == "text/html"
    assert ContentTypeDetector.detect_from_filename("document.md") == "text/markdown"
    assert ContentTypeDetector.detect_from_filename("document.rst") == "text/x-rst"
    assert ContentTypeDetector.detect_from_filename("document.adoc") == "text/asciidoc"
    assert ContentTypeDetector.detect_from_filename("document.txt") == "text/plain"
    assert ContentTypeDetector.detect_from_filename("document") is None

    # Test detect_from_content
    assert (
        ContentTypeDetector.detect_from_content(
            "<!DOCTYPE html><html><body>Test</body></html>"
        )
        == "text/html"
    )
    assert (
        ContentTypeDetector.detect_from_content("# Heading\n\nParagraph")
        == "text/markdown"
    )
    assert (
        ContentTypeDetector.detect_from_content(
            "=======\nHeading\n=======\n\nParagraph"
        )
        == "text/x-rst"
    )
    assert (
        ContentTypeDetector.detect_from_content("= Document Title") == "text/asciidoc"
    )
    assert (
        ContentTypeDetector.detect_from_content("<root><element>Test</element></root>")
        == "application/xml"
    )
    assert (
        ContentTypeDetector.detect_from_content('{"key": "value"}')
        == "application/json"
    )
    assert (
        ContentTypeDetector.detect_from_content("---\nkey: value\n")
        == "application/yaml"
    )
    assert ContentTypeDetector.detect_from_content("Just plain text") == "text/plain"
