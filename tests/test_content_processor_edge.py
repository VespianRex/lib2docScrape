import pytest
from bs4 import BeautifulSoup
from unittest.mock import patch, MagicMock

from src.processors.content_processor import (
    ContentProcessor,
    ProcessedContent,
    ContentProcessingError
)

@pytest.mark.asyncio # Mark test as async
async def test_empty_content(): # Make test async
    """Test processing of empty content."""
    processor = ContentProcessor()
    
    # Test empty string
    with pytest.raises(ContentProcessingError):
        await processor.process("", "https://example.com") # Add await
    
    # Test whitespace only
    with pytest.raises(ContentProcessingError):
        await processor.process("   \n\t   ", "https://example.com") # Add await
    
    # Test None
    with pytest.raises(ContentProcessingError):
        await processor.process(None, "https://example.com") # Ensure await is present

@pytest.mark.asyncio # Mark test as async
async def test_malformed_html(): # Make test async
    """Test processing of malformed HTML."""
    processor = ContentProcessor()
    
    # Test unclosed tags
    content = "<div><p>Test content<div>"
    result = await processor.process(content, "https://example.com") # Add await
    assert isinstance(result, ProcessedContent)
    assert "Test content" in result.content['formatted_content'] # Check 'formatted_content' key
    
    # Test mismatched tags
    content = "<div><p>Test content</div></p>"
    result = await processor.process(content, "https://example.com") # Add await
    assert isinstance(result, ProcessedContent)
    assert "Test content" in result.content['formatted_content'] # Check 'formatted_content' key
    
    # Test invalid attributes
    content = '<div class="test" <<invalid>>Test content</div>'
    result = await processor.process(content, "https://example.com") # Add await
    assert isinstance(result, ProcessedContent)
    assert "<<invalid>>" not in result.content['formatted_content'] # Check that the invalid attribute part is removed
    assert "Test content" in result.content['formatted_content'] # Check that the valid content remains (even if prefixed with >)

@pytest.mark.asyncio # Mark test as async
async def test_special_characters(): # Make test async
    """Test processing of content with special characters."""
    processor = ContentProcessor()
    
    # Test Unicode characters
    content = "<div><p>Test content with Unicode: 你好, Café, 🌟</p></div>" # Wrap in <p>
    result = await processor.process(content, "https://example.com") # Add await
    assert "你好" in result.content['formatted_content'] # Check 'formatted_content' key
    assert "Café" in result.content['formatted_content'] # Check 'formatted_content' key
    assert "🌟" in result.content['formatted_content'] # Check 'formatted_content' key
    
    # Test HTML entities
    content = "<div><p>Test content with entities: &amp; &lt; &gt; &quot; &apos;</p></div>" # Wrap in <p>
    result = await processor.process(content, "https://example.com") # Add await
    assert "&" in result.content['formatted_content'] # Check 'formatted_content' key
    assert "<" in result.content['formatted_content'] # Check 'formatted_content' key
    assert ">" in result.content['formatted_content'] # Check 'formatted_content' key
    assert '"' in result.content['formatted_content'] # Check 'formatted_content' key
    assert "'" in result.content['formatted_content'] # Check 'formatted_content' key

@pytest.mark.asyncio # Mark test as async
async def test_large_content(): # Make test async
    """Test processing of large content."""
    processor = ContentProcessor()
    
    # Generate large content
    large_content = "<div><p>" + "Test content. " * 10000 + "</p></div>" # Wrap content in <p>
    
    # Test processing time
    with patch('time.time') as mock_time:
        mock_time.side_effect = [0, 10, 11, 12, 13] # Provide more values
        result = await processor.process(large_content, "https://example.com") # Add await
        assert isinstance(result, ProcessedContent)
        assert len(result.content['formatted_content']) > 1000 # Check 'formatted_content' key

@pytest.mark.asyncio # Mark test as async
async def test_nested_structures(): # Make test async
    """Test processing of deeply nested structures."""
    processor = ContentProcessor()
    
    # Create deeply nested content
    nested_content = "<div>" * 100 + "<p>Test content</p>" + "</div>" * 100 # Wrap in <p>
    
    result = await processor.process(nested_content, "https://example.com") # Add await
    assert isinstance(result, ProcessedContent)
    assert "Test content" in result.content['formatted_content'] # Check 'formatted_content' key

@pytest.mark.asyncio # Mark test as async
async def test_javascript_handling(): # Make test async
    """Test handling of JavaScript content."""
    processor = ContentProcessor()
    
    # Test inline scripts
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
    result = await processor.process(content, "https://example.com") # Add await
    assert "alert" not in result.content['formatted_content'] # Check 'formatted_content' key
    assert "Valid content" in result.content['formatted_content'] # Check 'formatted_content' key
    assert "var x = 1" not in result.content['formatted_content'] # Check 'formatted_content' key
    
    # Test event handlers
    content = '<div onclick="alert(\'test\')"><p>Test content</p></div>' # Wrap in <p>
    result = await processor.process(content, "https://example.com") # Add await
    assert "onclick" not in result.content['formatted_content'] # Check 'formatted_content' key
    assert "Test content" in result.content['formatted_content'] # Check 'formatted_content' key

@pytest.mark.asyncio # Mark test as async
async def test_style_handling(): # Make test async
    """Test handling of CSS styles."""
    processor = ContentProcessor()
    
    # Test inline styles
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
    result = await processor.process(content, "https://example.com") # Add await
    assert "color: red" not in result.content['formatted_content'] # Corrected key
    assert "Valid content" in result.content['formatted_content'] # Corrected key
    assert "background: white" not in result.content['formatted_content'] # Corrected key
    
    # Test style attributes
    content = '<div style="color: blue;"><p>Test content</p></div>' # Wrap in <p>
    result = await processor.process(content, "https://example.com") # Add await
    assert "color: blue" not in result.content['formatted_content'] # Corrected key
    assert "Test content" in result.content['formatted_content'] # Corrected key

@pytest.mark.asyncio # Mark test as async
async def test_iframe_handling(): # Make test async
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
    result = await processor.process(content, "https://example.com") # Add await
    assert "Fallback content" not in result.content['formatted_content'] # Corrected key
    assert "Main content" in result.content['formatted_content'] # Already corrected, ensuring consistency

@pytest.mark.asyncio # Mark test as async
async def test_form_handling(): # Make test async
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
    result = await processor.process(content, "https://example.com") # Add await
    assert "Main content" in result.content['formatted_content'] # Corrected key
    # Form elements should be stripped or handled according to requirements
