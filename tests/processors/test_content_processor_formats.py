"""
Tests for the content processor with different formats.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.processors.content_processor import ContentProcessor, ContentProcessingError
from src.processors.content.format_detector import FormatDetector, ContentTypeDetector
from src.processors.content.format_handlers import (
    HTMLHandler,
    MarkdownHandler,
    ReStructuredTextHandler,
    AsciiDocHandler
)

HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Document</title>
</head>
<body>
    <h1>Test Heading</h1>
    <p>This is a test paragraph.</p>
    <ul>
        <li>Item 1</li>
        <li>Item 2</li>
    </ul>
</body>
</html>
"""

MARKDOWN_CONTENT = """
# Test Heading

This is a test paragraph.

* Item 1
* Item 2

```python
print("Hello, world!")
```
"""

RST_CONTENT = """
Test Heading
===========

This is a test paragraph.

* Item 1
* Item 2

.. code-block:: python

    print("Hello, world!")
"""

ASCIIDOC_CONTENT = """
= Test Heading

This is a test paragraph.

* Item 1
* Item 2

[source,python]
----
print("Hello, world!")
----
"""

@pytest.fixture
def processor():
    """Create a content processor."""
    return ContentProcessor()

@pytest.mark.asyncio
async def test_process_html(processor):
    """Test processing HTML content."""
    # Process HTML content
    result = await processor.process(HTML_CONTENT, "https://example.com", "text/html")
    
    # Check the result
    assert result.title == "Test Document"
    assert "Test Heading" in result.content.get("formatted_content", "")
    assert len(result.headings) > 0
    assert result.headings[0]["text"] == "Test Heading"

@pytest.mark.asyncio
async def test_process_markdown(processor):
    """Test processing Markdown content."""
    # Mock the markdown library
    with patch("markdown.markdown", return_value="<h1>Test Heading</h1><p>This is a test paragraph.</p>"):
        # Process Markdown content
        result = await processor.process(MARKDOWN_CONTENT, "https://example.com", "text/markdown")
        
        # Check the result
        assert "Test Heading" in result.title
        assert "Test Heading" in result.content.get("formatted_content", "")

@pytest.mark.asyncio
async def test_process_rst(processor):
    """Test processing reStructuredText content."""
    # Mock the docutils library
    with patch("src.processors.content.format_handlers.publish_parts", return_value={"html_body": "<h1>Test Heading</h1><p>This is a test paragraph.</p>"}):
        # Process reStructuredText content
        result = await processor.process(RST_CONTENT, "https://example.com", "text/x-rst")
        
        # Check the result
        assert "Test Heading" in result.title
        assert "Test Heading" in result.content.get("formatted_content", "")

@pytest.mark.asyncio
async def test_process_asciidoc(processor):
    """Test processing AsciiDoc content."""
    # Mock the asciidocapi library
    with patch("src.processors.content.format_handlers.asciidocapi.AsciiDocAPI") as mock_asciidoc:
        # Setup the mock
        mock_instance = MagicMock()
        mock_asciidoc.return_value = mock_instance
        
        # Process AsciiDoc content
        result = await processor.process(ASCIIDOC_CONTENT, "https://example.com", "text/asciidoc")
        
        # Check the result
        assert result is not None

@pytest.mark.asyncio
async def test_process_unknown_format(processor):
    """Test processing content with an unknown format."""
    # Process unknown content
    result = await processor.process("Just plain text", "https://example.com", "text/plain")
    
    # Check the result
    assert result is not None
    assert "Just plain text" in result.content.get("formatted_content", "")

@pytest.mark.asyncio
async def test_process_empty_content(processor):
    """Test processing empty content."""
    # Process empty content
    with pytest.raises(ContentProcessingError):
        await processor.process("", "https://example.com")
        
    with pytest.raises(ContentProcessingError):
        await processor.process("   ", "https://example.com")

def test_html_handler():
    """Test HTML handler."""
    # Create a mock processor
    processor = AsyncMock()
    processor.process = AsyncMock(return_value={"formatted_content": "Test"})
    
    # Create handler
    handler = HTMLHandler(processor)
    
    # Test can_handle
    assert handler.can_handle("<html><body>Test</body></html>") is True
    assert handler.can_handle("<div>Test</div>") is True
    assert handler.can_handle("Test") is False
    assert handler.can_handle("", "text/html") is True
    
    # Test get_format_name
    assert handler.get_format_name() == "HTML"

@pytest.mark.asyncio
async def test_markdown_handler():
    """Test Markdown handler."""
    # Create handler
    handler = MarkdownHandler()
    
    # Test can_handle
    assert handler.can_handle("# Heading\n\nParagraph") is True
    assert handler.can_handle("Test") is False
    assert handler.can_handle("", "text/markdown") is True
    
    # Test get_format_name
    assert handler.get_format_name() == "Markdown"
    
    # Test process with markdown library
    with patch("markdown.markdown", return_value="<h1>Heading</h1><p>Paragraph</p>"):
        # Mock the ContentProcessor
        with patch("src.processors.content_processor.ContentProcessor") as mock_processor_class:
            mock_processor = AsyncMock()
            mock_processor.process = AsyncMock(return_value={"formatted_content": "# Heading\n\nParagraph"})
            mock_processor_class.return_value = mock_processor
            
            result = await handler.process("# Heading\n\nParagraph")
            assert result["formatted_content"] == "# Heading\n\nParagraph"
            
    # Test process without markdown library
    with patch("src.processors.content.format_handlers.markdown", None):
        with patch.dict("sys.modules", {"markdown": None}):
            result = await handler.process("# Heading\n\nParagraph")
            assert "structure" in result

def test_rst_handler():
    """Test reStructuredText handler."""
    # Create handler
    handler = ReStructuredTextHandler()
    
    # Test can_handle
    assert handler.can_handle("=======\nHeading\n=======\n\nParagraph") is True
    assert handler.can_handle("Test") is False
    assert handler.can_handle("", "text/x-rst") is True
    
    # Test get_format_name
    assert handler.get_format_name() == "reStructuredText"

def test_asciidoc_handler():
    """Test AsciiDoc handler."""
    # Create handler
    handler = AsciiDocHandler()
    
    # Test can_handle
    assert handler.can_handle("= Heading\n\nParagraph") is True
    assert handler.can_handle("Test") is False
    assert handler.can_handle("", "text/asciidoc") is True
    
    # Test get_format_name
    assert handler.get_format_name() == "AsciiDoc"

def test_format_detector():
    """Test format detector."""
    # Create detector
    detector = FormatDetector()
    
    # Create handlers
    html_handler = HTMLHandler(AsyncMock())
    markdown_handler = MarkdownHandler()
    rst_handler = ReStructuredTextHandler()
    asciidoc_handler = AsciiDocHandler()
    
    # Register handlers
    detector.register_handler(html_handler)
    detector.register_handler(markdown_handler)
    detector.register_handler(rst_handler)
    detector.register_handler(asciidoc_handler)
    
    # Test detect_format with content type
    assert detector.detect_format("", "text/html") == html_handler
    assert detector.detect_format("", "text/markdown") == markdown_handler
    assert detector.detect_format("", "text/x-rst") == rst_handler
    assert detector.detect_format("", "text/asciidoc") == asciidoc_handler
    assert detector.detect_format("", "text/plain") is None
    
    # Test detect_format with content
    assert detector.detect_format("<html><body>Test</body></html>") == html_handler
    assert detector.detect_format("# Heading\n\nParagraph") == markdown_handler
    assert detector.detect_format("=======\nHeading\n=======\n\nParagraph") == rst_handler
    assert detector.detect_format("= Heading\n\nParagraph") == asciidoc_handler
    assert detector.detect_format("Test") is None
    
    # Test get_handler_for_format
    assert detector.get_handler_for_format("HTML") == html_handler
    assert detector.get_handler_for_format("Markdown") == markdown_handler
    assert detector.get_handler_for_format("reStructuredText") == rst_handler
    assert detector.get_handler_for_format("AsciiDoc") == asciidoc_handler
    assert detector.get_handler_for_format("Unknown") is None

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
    assert ContentTypeDetector.detect_from_content(HTML_CONTENT) == "text/html"
    assert ContentTypeDetector.detect_from_content(MARKDOWN_CONTENT) == "text/markdown"
    assert ContentTypeDetector.detect_from_content(RST_CONTENT) == "text/x-rst"
    assert ContentTypeDetector.detect_from_content(ASCIIDOC_CONTENT) == "text/asciidoc"
    assert ContentTypeDetector.detect_from_content("<root><element>Test</element></root>") == "application/xml"
    assert ContentTypeDetector.detect_from_content('{"key": "value"}') == "application/json"
    assert ContentTypeDetector.detect_from_content("---\nkey: value\n") == "application/yaml"
    assert ContentTypeDetector.detect_from_content("Just plain text") == "text/plain"
