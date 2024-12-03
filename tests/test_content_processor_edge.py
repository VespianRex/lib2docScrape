import pytest
from bs4 import BeautifulSoup
from unittest.mock import patch, MagicMock

from src.processors.content_processor import (
    ContentProcessor,
    ProcessedContent,
    ContentProcessingError
)

def test_empty_content():
    """Test processing of empty content."""
    processor = ContentProcessor()
    
    # Test empty string
    with pytest.raises(ContentProcessingError):
        processor.process("", "https://example.com")
    
    # Test whitespace only
    with pytest.raises(ContentProcessingError):
        processor.process("   \n\t   ", "https://example.com")
    
    # Test None
    with pytest.raises(ContentProcessingError):
        processor.process(None, "https://example.com")

def test_malformed_html():
    """Test processing of malformed HTML."""
    processor = ContentProcessor()
    
    # Test unclosed tags
    content = "<div><p>Test content<div>"
    result = processor.process(content, "https://example.com")
    assert isinstance(result, ProcessedContent)
    assert "Test content" in result.processed_content['main']
    
    # Test mismatched tags
    content = "<div><p>Test content</div></p>"
    result = processor.process(content, "https://example.com")
    assert isinstance(result, ProcessedContent)
    assert "Test content" in result.processed_content['main']
    
    # Test invalid attributes
    content = '<div class="test" <<invalid>>Test content</div>'
    result = processor.process(content, "https://example.com")
    assert isinstance(result, ProcessedContent)
    assert "Test content" in result.processed_content['main']

def test_special_characters():
    """Test processing of content with special characters."""
    processor = ContentProcessor()
    
    # Test Unicode characters
    content = "<div>Test content with Unicode: 你好, Café, 🌟</div>"
    result = processor.process(content, "https://example.com")
    assert "你好" in result.processed_content['main']
    assert "Café" in result.processed_content['main']
    assert "🌟" in result.processed_content['main']
    
    # Test HTML entities
    content = "<div>Test content with entities: &amp; &lt; &gt; &quot; &apos;</div>"
    result = processor.process(content, "https://example.com")
    assert "&" in result.processed_content['main']
    assert "<" in result.processed_content['main']
    assert ">" in result.processed_content['main']
    assert '"' in result.processed_content['main']
    assert "'" in result.processed_content['main']

def test_large_content():
    """Test processing of large content."""
    processor = ContentProcessor()
    
    # Generate large content
    large_content = "<div>" + "Test content. " * 10000 + "</div>"
    
    # Test processing time
    with patch('time.time') as mock_time:
        mock_time.side_effect = [0, 10]  # 10 seconds elapsed
        result = processor.process(large_content, "https://example.com")
        assert isinstance(result, ProcessedContent)
        assert len(result.processed_content['main']) > 1000

def test_nested_structures():
    """Test processing of deeply nested structures."""
    processor = ContentProcessor()
    
    # Create deeply nested content
    nested_content = "<div>" * 100 + "Test content" + "</div>" * 100
    
    result = processor.process(nested_content, "https://example.com")
    assert isinstance(result, ProcessedContent)
    assert "Test content" in result.processed_content['main']

def test_javascript_handling():
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
    result = processor.process(content, "https://example.com")
    assert "alert" not in result.processed_content['main']
    assert "Valid content" in result.processed_content['main']
    assert "var x = 1" not in result.processed_content['main']
    
    # Test event handlers
    content = '<div onclick="alert(\'test\')">Test content</div>'
    result = processor.process(content, "https://example.com")
    assert "onclick" not in result.processed_content['main']
    assert "Test content" in result.processed_content['main']

def test_style_handling():
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
    result = processor.process(content, "https://example.com")
    assert "color: red" not in result.processed_content['main']
    assert "Valid content" in result.processed_content['main']
    assert "background: white" not in result.processed_content['main']
    
    # Test style attributes
    content = '<div style="color: blue;">Test content</div>'
    result = processor.process(content, "https://example.com")
    assert "color: blue" not in result.processed_content['main']
    assert "Test content" in result.processed_content['main']

def test_iframe_handling():
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
    result = processor.process(content, "https://example.com")
    assert "Fallback content" not in result.processed_content['main']
    assert "Main content" in result.processed_content['main']

def test_form_handling():
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
    result = processor.process(content, "https://example.com")
    assert "Main content" in result.processed_content['main']
    # Form elements should be stripped or handled according to requirements
