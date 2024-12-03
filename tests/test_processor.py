"""Tests for the content processor component."""

import pytest
from bs4 import BeautifulSoup

from src.processors.content_processor import (ContentProcessor, ProcessedContent,
                                           ProcessorConfig, URLInfo)


def test_content_processor_initialization():
    """Test content processor initialization and configuration."""
    # Test with default config
    processor = ContentProcessor()
    assert processor.config is not None
    assert len(processor.config.allowed_tags) > 0
    
    # Test with custom config
    custom_config = ProcessorConfig(
        allowed_tags=["p", "a"],
        preserve_whitespace=True,
        code_languages=["python"],
        max_heading_level=2,
        max_content_length=500,
        min_content_length=10
    )
    processor = ContentProcessor(config=custom_config)
    assert processor.config == custom_config
    assert processor.config.max_heading_level == 2


def test_clean_text_processing(content_processor: ContentProcessor):
    """Test text cleaning functionality."""
    # Test basic cleaning
    text = "  Multiple   spaces   and\nlines\n"
    cleaned = content_processor._clean_text(text)
    assert cleaned == "Multiple spaces and lines"
    
    # Test with regex cleaning
    text = "Text with <tags> and {symbols}"
    cleaned = content_processor._clean_text(
        text,
        clean_regex=r'[<{}>]'
    )
    assert cleaned == "Text with tags and symbols"


def test_code_language_detection(content_processor: ContentProcessor):
    """Test programming language detection in code blocks."""
    # Create mock elements
    python_element = BeautifulSoup(
        '<pre><code class="language-python">def test(): pass</code></pre>',
        'html.parser'
    ).code
    
    js_element = BeautifulSoup(
        '<pre><code class="lang-javascript">function test() {}</code></pre>',
        'html.parser'
    ).code
    
    plain_element = BeautifulSoup(
        '<pre><code>plain text</code></pre>',
        'html.parser'
    ).code
    
    # Test language detection
    assert content_processor._extract_code_language(python_element) == "python"
    assert content_processor._extract_code_language(js_element) == "javascript"
    assert content_processor._extract_code_language(plain_element) == "text"


def test_code_block_processing(content_processor: ContentProcessor, soup: BeautifulSoup):
    """Test code block processing."""
    # Add a code block with language class
    code = soup.new_tag('code', attrs={'class': 'language-python'})
    code.string = 'print("Hello, World!")'
    pre = soup.new_tag('pre')
    pre.append(code)
    soup.body.append(pre)
    
    code_blocks = content_processor._process_code_blocks(soup)
    
    assert len(code_blocks) > 0
    first_block = code_blocks[0]
    
    assert "language" in first_block
    assert "content" in first_block
    assert first_block["language"] == "python"
    assert "Hello, World!" in first_block["content"]


def test_link_processing(content_processor: ContentProcessor, soup: BeautifulSoup):
    """Test link processing and validation."""
    base_url = "https://example.com"
    links = content_processor._process_links(soup, base_url)
    
    assert len(links) > 0
    first_link = links[0]
    
    assert "url" in first_link
    assert "text" in first_link
    assert "title" in first_link
    assert first_link["url"].startswith(("http://", "https://", "/"))


def test_metadata_extraction(content_processor: ContentProcessor, soup: BeautifulSoup):
    """Test metadata extraction from content."""
    metadata = content_processor._extract_metadata(soup)
    
    assert "meta_tags" in metadata
    assert "description" in metadata["meta_tags"]
    assert "keywords" in metadata["meta_tags"]
    assert metadata["meta_tags"]["description"] == "Sample description"


def test_asset_collection(content_processor: ContentProcessor, soup: BeautifulSoup):
    """Test asset URL collection."""
    base_url = "https://example.com"
    assets = content_processor._collect_assets(soup, base_url)
    
    assert "images" in assets
    assert len(assets["images"]) > 0
    assert assets["images"][0].endswith("image.jpg")


def test_full_content_processing(content_processor: ContentProcessor, sample_html: str):
    """Test complete content processing pipeline."""
    processed = content_processor.process(sample_html, "https://example.com/test")
    
    assert isinstance(processed, ProcessedContent)
    assert processed.url == "https://example.com/test"
    assert processed.title == "Sample Document"
    assert len(processed.content.get("headings", [])) > 0
    assert len(processed.content.get("code_blocks", [])) > 0
    assert len(processed.content.get("links", [])) > 0
    assert len(processed.assets.get("images", [])) > 0


def test_content_size_limits(content_processor: ContentProcessor):
    """Test content size limit handling."""
    # Test content too large
    large_content = "x" * (content_processor.config.max_content_length + 1)
    large_html = f"<html><body><p>{large_content}</p></body></html>"
    
    processed = content_processor.process(large_html, "https://example.com")
    assert not processed.content  # Should be empty due to size limit
    assert "Content exceeds maximum size limit" in processed.errors
    assert processed.metadata["error"] == "Content exceeds maximum size limit"
    
    # Test content too small
    small_content = "x" * (content_processor.config.min_content_length - 1)
    small_html = f"<html><body><p>{small_content}</p></body></html>"
    
    processed = content_processor.process(small_html, "https://example.com")
    assert not processed.content  # Should be empty due to size limit
    assert "Content below minimum size limit" in processed.errors
    assert processed.metadata["error"] == "Content below minimum size limit"


def test_malformed_html_handling(content_processor: ContentProcessor):
    """Test handling of malformed HTML."""
    # Test unclosed tags
    malformed_html = "<html><body><p>Unclosed paragraph<div>Nested</p></div></body></html>"
    processed = content_processor.process(malformed_html, "https://example.com")
    assert processed.content  # Should still process despite malformed HTML
    
    # Test invalid nesting
    invalid_html = "<html><body><h1><p>Invalid nesting</h1></p></body></html>"
    processed = content_processor.process(invalid_html, "https://example.com")
    assert processed.content  # Should handle invalid nesting


def test_special_content_handling(content_processor: ContentProcessor):
    """Test handling of special content cases."""
    # Test content with scripts and styles
    html_with_scripts = """
    <html>
        <head>
            <script>alert('test');</script>
            <style>body { color: red; }</style>
        </head>
        <body>
            <h1>Test</h1>
            <script>console.log('test');</script>
        </body>
    </html>
    """
    processed = content_processor.process(html_with_scripts, "https://example.com")
    assert "alert" not in str(processed.content)  # Scripts should be removed
    assert "color: red" not in str(processed.content)  # Styles should be removed
    
    # Test content with comments
    html_with_comments = """
    <html>
        <body>
            <!-- Comment -->
            <h1>Test</h1>
            <!-- Another comment -->
        </body>
    </html>
    """
    processed = content_processor.process(html_with_comments, "https://example.com")
    assert "Comment" not in str(processed.content)  # Comments should be removed


def test_content_structure_preservation(content_processor: ContentProcessor):
    """Test preservation of content structure."""
    html = """
    <html>
        <body>
            <h1>Title</h1>
            <p>First paragraph</p>
            <h2>Subtitle</h2>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
            </ul>
        </body>
    </html>
    """
    processed = content_processor.process(html, "https://example.com")
    
    # Check structure preservation
    headings = processed.content.get("headings", [])
    assert len(headings) == 2
    assert headings[0]["level"] == 1
    assert headings[1]["level"] == 2
    
    # Check content order
    content_text = " ".join(str(v) for v in processed.content.values())
    title_pos = content_text.find("Title")
    subtitle_pos = content_text.find("Subtitle")
    assert title_pos < subtitle_pos  # Original order should be preserved