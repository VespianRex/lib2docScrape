import pytest
from bs4 import BeautifulSoup
from unittest.mock import patch, MagicMock

from src.processors.content_processor import (
    ContentProcessor,
    ProcessedContent,
    ContentProcessingError
)

@pytest.mark.asyncio
async def test_empty_content():
    """Test processing of empty content."""
    processor = ContentProcessor()
    with pytest.raises(ContentProcessingError):
        await processor.process("", "https://example.com")
    with pytest.raises(ContentProcessingError):
        await processor.process("   \n\t   ", "https://example.com")
    with pytest.raises(ContentProcessingError):
        await processor.process(None, "https://example.com")

@pytest.mark.asyncio
async def test_malformed_html():
    """Test processing of malformed HTML."""
    processor = ContentProcessor()
    
    # Test unclosed tags
    content = "<div><p>Test content<div>" # BeautifulSoup handles this
    result = await processor.process(content, "https://example.com")
    assert isinstance(result, ProcessedContent)
    assert "Test content" in result.content['formatted_content']
    
    # Test mismatched tags
    content = "<div><p>Test content</div></p>" # BeautifulSoup handles this
    result = await processor.process(content, "https://example.com")
    assert isinstance(result, ProcessedContent)
    assert "Test content" in result.content['formatted_content']
    
    # Test invalid attributes - bleach should strip them
    content = '<div class="test" <<invalid>>Test content</div>'
    result = await processor.process(content, "https://example.com")
    assert isinstance(result, ProcessedContent)
    assert "<<invalid>>" not in result.content['formatted_content']
    assert "Test content" in result.content['formatted_content']

@pytest.mark.asyncio
async def test_special_characters():
    """Test processing of content with special characters."""
    processor = ContentProcessor()
    
    # Test Unicode characters
    content = "<div><p>Test content with Unicode: 你好, Café, 🌟</p></div>"
    result = await processor.process(content, "https://example.com")
    assert "你好" in result.content['formatted_content']
    assert "Café" in result.content['formatted_content']
    assert "🌟" in result.content['formatted_content']
    
    # Test HTML entities - markdownify unescapes them
    content = "<div><p>Test content with entities: &amp; &lt; &gt; &quot; &apos;</p></div>"
    result = await processor.process(content, "https://example.com")
    assert "&" in result.content['formatted_content'] # Markdownify unescapes
    assert "<" in result.content['formatted_content']
    assert ">" in result.content['formatted_content']
    assert '"' in result.content['formatted_content']
    assert "'" in result.content['formatted_content']

@pytest.mark.asyncio
async def test_large_content():
    """Test processing of large content."""
    processor = ContentProcessor()
    large_content = "<div><p>" + "Test content. " * 10000 + "</p></div>"
    
    with patch('time.time') as mock_time:
        mock_time.side_effect = [0, 10, 11, 12, 13]
        result = await processor.process(large_content, "https://example.com")
        assert isinstance(result, ProcessedContent)
        assert len(result.content['formatted_content']) > 1000

@pytest.mark.asyncio
async def test_nested_structures():
    """Test processing of deeply nested structures."""
    processor = ContentProcessor()
    nested_content = "<div>" * 100 + "<p>Test content</p>" + "</div>" * 100
    result = await processor.process(nested_content, "https://example.com")
    assert isinstance(result, ProcessedContent)
    assert "Test content" in result.content['formatted_content']

@pytest.mark.asyncio
async def test_javascript_handling():
    """Test handling of JavaScript content."""
    processor = ContentProcessor()
    
    # Test inline scripts - bleach removes script tags
    content = """
    <div>
        <script>alert('test');</script>
        <p>Valid content</p>
        <script>
            var x = 1;
            console.log(x);
        </script>
    </div>
    """
    result = await processor.process(content, "https://example.com")
    assert "alert" not in result.content['formatted_content']
    assert "Valid content" in result.content['formatted_content']
    assert "var x = 1" not in result.content['formatted_content']
    
    # Test event handlers - bleach removes them
    content = '<div onclick="alert(\'test\')"><p>Test content</p></div>'
    result = await processor.process(content, "https://example.com")
    assert "onclick" not in result.content['formatted_content'] 
    assert "Test content" in result.content['formatted_content']

@pytest.mark.asyncio
async def test_style_handling():
    """Test handling of CSS styles."""
    processor = ContentProcessor()
    
    # Test inline styles - bleach removes style tags
    content = """
    <div>
        <style>
            .test { color: red; }
        </style>
        <p>Valid content</p>
        <style>
            body { background: white; }
        </style>
    </div>
    """
    result = await processor.process(content, "https://example.com")
    assert "color: red" not in result.content['formatted_content']
    assert "Valid content" in result.content['formatted_content']
    assert "background: white" not in result.content['formatted_content']
    
    # Test style attributes - bleach removes them by default
    content = '<div style="color: blue;"><p>Test content</p></div>'
    result = await processor.process(content, "https://example.com")
    assert "color: blue" not in result.content['formatted_content'] 
    assert "Test content" in result.content['formatted_content']

@pytest.mark.asyncio
async def test_iframe_handling():
    """Test handling of iframes."""
    processor = ContentProcessor()
    
    content = """
    <div>
        <iframe src="https://example.com/frame">
            Fallback content
        </iframe>
        <p>Main content</p>
    </div>
    """
    result = await processor.process(content, "https://example.com")
    assert "Fallback content" not in result.content['formatted_content']
    assert "Main content" in result.content['formatted_content']

@pytest.mark.asyncio
async def test_form_handling():
    """Test handling of forms and input elements."""
    processor = ContentProcessor()
    
    content = """
    <div>
        <form action="/submit">
            <input type="text" value="test">
            <textarea>Default text</textarea>
            <select>
                <option>Option 1</option>
                <option>Option 2</option>
            </select>
            <button>Submit</button>
        </form>
        <p>Main content</p>
    </div>
    """
    result = await processor.process(content, "https://example.com")
    assert "Main content" in result.content['formatted_content']
    # Depending on markdownify options, form elements might be stripped or represented.
    # For now, we ensure main content is preserved.
    # assert "Default text" not in result.content['formatted_content'] # Example if stripped
