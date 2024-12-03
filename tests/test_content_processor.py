import pytest
from bs4 import BeautifulSoup, Comment
from src.processors.content_processor import ContentProcessor, ProcessorConfig, ProcessedContent
from dataclasses import dataclass
import re

# --------------------
# Helper Functions
# --------------------

def assert_metadata(metadata, key, expected):
    """Helper function to assert metadata values."""
    assert metadata.get(key) == expected, (
        f"Metadata '{key}' expected to be '{expected}' but got '{metadata.get(key)}'"
    )

def assert_asset(assets, asset_type, url):
    """Helper function to assert asset URLs."""
    assert url in assets.get(asset_type, []), (
        f"Asset URL '{url}' not found in '{asset_type}'"
    )

# --------------------
# Pytest Fixtures
# --------------------

@pytest.fixture
def processor():
    """Fixture to provide a ContentProcessor instance for tests."""
    return ContentProcessor()

# --------------------
# Test Classes
# --------------------

class TestBasicFunctionality:
    """Tests for basic content extraction and processing."""

    def test_extract_text_basic(self, processor):
        """Test basic text extraction from HTML."""
        html = "<html><body><h1>Title</h1><p>This is a paragraph.</p></body></html>"
        result = processor.process(html)
        
        assert result.title == "Title"
        assert "This is a paragraph." in result.content["formatted_content"]

    def test_process_basic(self, processor):
        """Test processing of basic HTML content."""
        html = "<html><head><title>Test Document</title></head><body><p>Content here.</p></body></html>"
        result = processor.process(html)
        
        assert result.title == "Test Document"
        assert "Content here." in result.content["formatted_content"]
        assert not result.errors

    def test_format_as_markdown(self, processor):
        """Test markdown formatting functionality."""
        html = "<html><body><h1>Title</h1><p>Paragraph.</p></body></html>"
        result = processor.process(html)
        
        expected_markdown = "# Title\n\nParagraph."
        assert result.content["formatted_content"] == expected_markdown

    def test_extract_text_with_nested_content(self, processor):
        """Test text extraction from deeply nested HTML structures."""
        html = """
        <div>
            <div>
                <div>
                    <p>Deeply nested paragraph.</p>
                </div>
            </div>
        </div>
        """
        result = processor.process(html)
        
        assert "Deeply nested paragraph." in result.content["formatted_content"]

    def test_extract_text_with_special_characters(self, processor):
        """Test text extraction handling special HTML entities."""
        html = """
        <html>
            <body>
                <p>Special characters: &amp;, &lt;, &gt;, &quot;, &#39;</p>
            </body>
        </html>
        """
        result = processor.process(html)
        
        assert "Special characters: &, <, >, \", '" in result.content["formatted_content"]

    def test_extract_text_with_complex_content(self, processor):
        """Test text extraction from HTML with complex nested structures."""
        html = """
        <html>
            <body>
                <div>
                    <section>
                        <article>
                            <h2>Article Title</h2>
                            <p>Article content.</p>
                        </article>
                    </section>
                </div>
            </body>
        </html>
        """
        result = processor.process(html)
        
        assert "Article Title" in result.content["formatted_content"]
        assert "Article content." in result.content["formatted_content"]

    def test_extract_text_with_mixed_content_types(self, processor):
        """Test text extraction from HTML with mixed content types."""
        html = """
        <html>
            <body>
                <h1>Main Title</h1>
                <p>Paragraph text.</p>
                <ul>
                    <li>Unordered list item</li>
                </ul>
                <ol>
                    <li>Ordered list item</li>
                </ol>
                <pre><code class="python">print("Hello")</code></pre>
                <table>
                    <tr><th>Header</th></tr>
                    <tr><td>Data</td></tr>
                </table>
                <a href="https://example.com">External Link</a>
            </body>
        </html>
        """
        result = processor.process(html)
        
        assert "Main Title" in result.content["formatted_content"]
        assert "- Unordered list item" in result.content["formatted_content"]
        assert "1. Ordered list item" in result.content["formatted_content"]
        assert "```python\nprint(\"Hello\")\n```" in result.content["formatted_content"]
        assert "| Header |\n| --- |\n| Data |" in result.content["formatted_content"]
        assert "[External Link](https://example.com)" in result.content["formatted_content"]

class TestScriptHandling:
    """Tests for handling script tags in HTML."""

    def test_extract_text_with_scripts(self, processor):
        """Test text extraction while ignoring scripts."""
        html = """
        <html>
            <head>
                <script type="text/javascript">var a = 1;</script>
            </head>
            <body>
                <p>Visible text.</p>
            </body>
        </html>
        """
        result = processor.process(html)
        
        assert "var a = 1;" not in result.content["formatted_content"]
        assert "Visible text." in result.content["formatted_content"]

    def test_script_tags_non_json_ld(self, processor):
        """Test that script tags with non-JSON-LD are removed."""
        html = """
        <html>
            <head>
                <title>Script Test</title>
                <script>alert('Hello');</script>
            </head>
            <body>
                <p>Content here.</p>
            </body>
        </html>
        """
        result = processor.process(html)
        
        assert "Content here." in result.content["formatted_content"]
        assert "alert('Hello');" not in result.content["formatted_content"]

    def test_script_tags_with_invalid_json(self, processor):
        """Test that script tags with invalid JSON do not break processing."""
        html = """
        <html>
            <head>
                <title>Invalid JSON-LD</title>
                <script type="application/ld+json">
                { invalid json }
                </script>
            </head>
            <body>
                <p>Content here.</p>
            </body>
        </html>
        """
        result = processor.process(html)
        
        assert result.title == "Invalid JSON-LD"
        assert "Content here." in result.content["formatted_content"]
        assert "invalid json" not in result.metadata

    def test_script_tags_with_different_types(self, processor):
        """Test that script tags with different types are handled correctly."""
        html = """
        <html>
            <head>
                <script type="text/javascript">
                    console.log('JS Script');
                </script>
                <script type="application/json">
                    {"key": "value"}
                </script>
            </head>
            <body>
                <p>Content here.</p>
            </body>
        </html>
        """
        result = processor.process(html)
        
        # JSON script should not be processed as JSON-LD
        assert "console.log('JS Script');" not in result.metadata
        assert "key" not in result.metadata
        assert "Content here." in result.content["formatted_content"]

    def test_scripts_with_data_attributes(self, processor):
        """Test that script tags with data attributes are handled correctly."""
        html = """
        <html>
            <body>
                <script src="app.js" data-role="admin"></script>
                <script src="user.js" data-role="user"></script>
            </body>
        </html>
        """
        result = processor.process(html, base_url='https://example.com/scripts/')
        
        assert "https://example.com/scripts/app.js" in result.assets["scripts"]
        assert "https://example.com/scripts/user.js" in result.assets["scripts"]

class TestCodeBlockExtraction:
    """Tests for extraction and formatting of code blocks."""

    @pytest.mark.parametrize("language,code,expected", [
        ("javascript", 'console.log("Hello, World!");', '```javascript\nconsole.log("Hello, World!");\n```'),
        ("python", 'print("Hello, World!")', '```python\nprint("Hello, World!")\n```'),
        ("ruby", 'puts "Hello, Ruby!"', '```ruby\nputs "Hello, Ruby!"\n```'),
        (None, 'Inline code', '`Inline code`'),
    ])
    def test_extract_code_blocks(self, processor, language, code, expected):
        """Test extraction of code blocks with language information."""
        if language:
            html = f'<pre><code class="language-{language}">{code}</code></pre>'
        else:
            html = f'<code>{code}</code>'
        result = processor.process(html)
        
        assert expected in result.content["formatted_content"]

    def test_extract_code_blocks_with_attributes(self, processor):
        """Test extraction of code blocks with various attributes."""
        html = """
        <html>
            <body>
                <pre><code class="language-python">print("Hello, World!")</code></pre>
                <pre><code class="language-java">System.out.println("Hello, World!");</code></pre>
            </body>
        </html>
        """
        result = processor.process(html)
        
        assert "```python\nprint(\"Hello, World!\")\n```" in result.content["formatted_content"]
        # Assuming 'java' is not in allowed languages, it should not be processed
        assert "```java\nSystem.out.println(\"Hello, World!\");\n```" not in result.content["formatted_content"]

    def test_extract_code_blocks_with_nested_content(self, processor):
        """Test extraction of code blocks containing nested HTML elements."""
        html = """
        <html>
            <body>
                <pre><code class="language-python">
    def foo():
        return "<div>HTML Content</div>"
                </code></pre>
            </body>
        </html>
        """
        result = processor.process(html)
        
        expected_code = "def foo():\n    return \"<div>HTML Content</div>\""
        assert f"```python\n{expected_code}\n```" in result.content["formatted_content"]

    def test_code_blocks_with_disallowed_languages(self, processor):
        """Test that code blocks with disallowed languages are not processed."""
        html = """
        <html>
            <body>
                <pre><code class="language-go">package main</code></pre>
                <pre><code class="language-python">print("Hello, Python!")</code></pre>
            </body>
        </html>
        """
        config = {
            'code_languages': ['python']
        }
        processor.configure(config)
        result = processor.process(html)
        
        assert "```go\npackage main\n```" not in result.content["formatted_content"]
        assert "```python\nprint(\"Hello, Python!\")\n```" in result.content["formatted_content"]

class TestContentStructureExtraction:
    """Tests for extraction of content structure like headings."""

    def test_extract_content_structure(self, processor):
        """Test extraction of content structure with headings and content."""
        html = """
        <html>
            <body>
                <h1>Main Title</h1>
                <p>Introduction paragraph.</p>
                <h2>Section 1</h2>
                <p>Content of section 1.</p>
                <h3>Subsection 1.1</h3>
                <p>Content of subsection 1.1.</p>
            </body>
        </html>
        """
        result = processor.process(html)
        
        structure = result.content["structure"]
        assert len(structure) == 3  # h1, h2, h3
        assert structure[0]["title"] == "Main Title"
        assert structure[1]["title"] == "Section 1"
        assert structure[2]["title"] == "Subsection 1.1"

    def test_extract_headings_hierarchy(self, processor):
        """Test extraction of headings hierarchy."""
        html = """
        <html>
            <body>
                <h1>Top Level</h1>
                <h2>Second Level</h2>
                <h3>Third Level</h3>
                <h4>Fourth Level</h4>
            </body>
        </html>
        """
        result = processor.process(html)
        
        headings = result.content["headings"]
        assert len(headings) == 3  # h1, h2, h3 (h4 is beyond max_heading_level=3)
        assert any(h["text"] == "Top Level" and h["level"] == 1 for h in headings)
        assert any(h["text"] == "Second Level" and h["level"] == 2 for h in headings)
        assert any(h["text"] == "Third Level" and h["level"] == 3 for h in headings)
        assert not any(h["text"] == "Fourth Level" for h in headings)

class TestMetadataExtraction:
    """Tests for extraction of various metadata tags."""

    def test_extract_metadata(self, processor):
        """Test extraction of various metadata tags."""
        html = """
        <html>
            <head>
                <title>Meta Test</title>
                <meta name="description" content="A test description.">
                <meta property="og:title" content="OG Meta Title">
            </head>
            <body>
                <p>Content here.</p>
            </body>
        </html>
        """
        result = processor.process(html)
        
        assert_metadata(result.metadata, "title", "Meta Test")
        assert_metadata(result.metadata, "description", "A test description.")
        assert_metadata(result.metadata, "og:title", "OG Meta Title")

    def test_extract_metadata_with_complex_metadata(self, processor):
        """Test processing of HTML with complex metadata structures."""
        html = """
        <html>
            <head>
                <title>Complex Meta</title>
                <meta name="description" content="A complex description.">
                <meta name="dc.title" content="Dublin Core Title">
                <meta property="og:type" content="website">
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "WebSite",
                    "name": "Example Site",
                    "url": "https://example.com"
                }
                </script>
            </head>
            <body>
                <p>Some content.</p>
            </body>
        </html>
        """
        result = processor.process(html)
        
        # Check basic metadata
        assert_metadata(result.metadata, "title", "Complex Meta")
        assert_metadata(result.metadata, "description", "A complex description.")
        assert_metadata(result.metadata, "dc.title", "Dublin Core Title")
        assert_metadata(result.metadata, "og:type", "website")
        
        # Check JSON-LD metadata
        assert_metadata(result.metadata, "name", "Example Site")
        assert_metadata(result.metadata, "url", "https://example.com")

    def test_extract_metadata_with_duplicates(self, processor):
        """Test metadata extraction with duplicate meta tags."""
        html = """
        <html>
            <head>
                <title>First Title</title>
                <title>Second Title</title>
                <meta name="description" content="First description">
                <meta name="description" content="Second description">
                <meta property="og:title" content="First OG title">
                <meta property="og:title" content="Second OG title">
            </head>
        </html>
        """
        result = processor.process(html)
        
        # Should use first occurrence of duplicate tags
        assert_metadata(result.metadata, "title", "First Title")
        assert_metadata(result.metadata, "description", "First description")
        assert_metadata(result.metadata, "og:title", "First OG title")

    def test_extract_metadata_with_invalid_html(self, processor):
        """Test metadata extraction with invalid HTML structure."""
        html = """
        <html>
            <title>Outside head</title>
            <meta name="description" content="Outside head">
            <head>
                <title>Inside head</title>
                <meta name="keywords" content="inside, head">
            </head>
            <body>
                <title>Inside body</title>
                <meta name="author" content="Inside body">
            </body>
        </html>
        """
        result = processor.process(html)
        
        # Should prioritize metadata from <head> section
        assert_metadata(result.metadata, "title", "Inside head")
        assert_metadata(result.metadata, "keywords", "inside, head")
        assert_metadata(result.metadata, "description", "Outside head")
        assert_metadata(result.metadata, "author", "Inside body")

    def test_extract_metadata_with_missing_values(self, processor):
        """Test metadata extraction with empty or missing attribute values."""
        html = """
        <html>
            <head>
                <title></title>
                <meta name="empty-content" content="">
                <meta name="no-content">
                <meta name="" content="no-name">
                <meta content="no-name-or-property">
                <meta property="" content="empty-property">
            </head>
        </html>
        """
        result = processor.process(html)
        
        # 'title' should default to "Untitled Document"
        assert_metadata(result.metadata, "title", "Untitled Document")
        
        # Check other meta tags
        assert_metadata(result.metadata, "empty-content", "")
        assert_metadata(result.metadata, "no-content", "")
        assert "no-name" not in result.metadata
        assert "no-name-or-property" not in result.metadata
        assert_metadata(result.metadata, "empty-property", "")

    def test_extract_metadata_with_schema_org_json_ld(self, processor):
        """Test metadata extraction with Schema.org JSON-LD markup."""
        html = """
        <html>
            <head>
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "Article",
                    "headline": "Article Title",
                    "author": {
                        "@type": "Person",
                        "name": "Author Name"
                    },
                    "description": "Article description"
                }
                </script>
            </head>
            <body>
                <div itemscope itemtype="https://schema.org/Product">
                    <meta itemprop="name" content="Product Name">
                    <meta itemprop="description" content="Product description">
                </div>
            </body>
        </html>
        """
        result = processor.process(html)
        
        # Microdata
        assert_metadata(result.metadata, "name", "Product Name")
        assert_metadata(result.metadata, "description", "Product description")
        
        # JSON-LD
        assert_metadata(result.metadata, "headline", "Article Title")
        assert_metadata(result.metadata, "author", {"@type": "Person", "name": "Author Name"})
        # Note: 'description' is overwritten by microdata 'description'

    def test_extract_metadata_with_all_types(self, processor):
        """Test metadata extraction with all supported types."""
        html = """
        <html>
            <head>
                <!-- Standard meta tags -->
                <title>Page Title</title>
                <meta name="description" content="Page description">
                <meta name="keywords" content="key1, key2, key3">
                <meta name="author" content="Author Name">

                <!-- OpenGraph meta tags -->
                <meta property="og:title" content="OG Title">
                <meta property="og:description" content="OG description">
                <meta property="og:image" content="https://example.com/image.jpg">
                <meta property="og:url" content="https://example.com/page">

                <!-- Twitter Card meta tags -->
                <meta name="twitter:card" content="summary">
                <meta name="twitter:title" content="Twitter Title">
                <meta name="twitter:description" content="Twitter description">
                <meta name="twitter:image" content="https://example.com/twitter.jpg">

                <!-- Dublin Core meta tags -->
                <meta name="dc.title" content="DC Title">
                <meta name="dc.creator" content="DC Creator">
                <meta name="dc.subject" content="DC Subject">

                <!-- Custom meta tags -->
                <meta name="custom-tag" content="Custom value">
                <meta property="custom:property" content="Property value">
            </head>
            <body>
                <h1>Page Content</h1>
                <p>Content here.</p>
            </body>
        </html>
        """
        result = processor.process(html)
    
        # Check standard meta
        assert_metadata(result.metadata, "title", "Page Title")
        assert_metadata(result.metadata, "description", "Page description")
        assert "key1" in result.metadata["keywords"].split(", ")
        assert_metadata(result.metadata, "author", "Author Name")
        
        # Check OpenGraph
        assert_metadata(result.metadata, "og:title", "OG Title")
        assert_metadata(result.metadata, "og:description", "OG description")
        assert_metadata(result.metadata, "og:image", "https://example.com/image.jpg")
        assert_metadata(result.metadata, "og:url", "https://example.com/page")
        
        # Check Twitter Card
        assert_metadata(result.metadata, "twitter:card", "summary")
        assert_metadata(result.metadata, "twitter:title", "Twitter Title")
        assert_metadata(result.metadata, "twitter:description", "Twitter description")
        assert_metadata(result.metadata, "twitter:image", "https://example.com/twitter.jpg")
        
        # Check Dublin Core
        assert_metadata(result.metadata, "dc.title", "DC Title")
        assert_metadata(result.metadata, "dc.creator", "DC Creator")
        assert_metadata(result.metadata, "dc.subject", "DC Subject")
        
        # Check Custom meta
        assert_metadata(result.metadata, "custom-tag", "Custom value")
        assert_metadata(result.metadata, "custom:property", "Property value")

class TestAssetCollection:
    """Tests for collection of various asset URLs."""

    def test_collect_assets(self, processor):
        """Test collection of various asset URLs."""
        html = """
        <html>
            <head>
                <link rel="stylesheet" href="styles.css">
                <script src="app.js"></script>
            </head>
            <body>
                <img src="image.png" alt="Image">
                <video src="video.mp4"></video>
                <audio src="audio.mp3"></audio>
                <source src="media.webm" type="video/webm">
            </body>
        </html>
        """
        result = processor.process(html)
        
        assert_asset(result.assets, "stylesheets", "styles.css")
        assert_asset(result.assets, "scripts", "app.js")
        assert_asset(result.assets, "images", "image.png")
        assert_asset(result.assets, "media", "video.mp4")
        assert_asset(result.assets, "media", "audio.mp3")
        assert_asset(result.assets, "media", "media.webm")

    def test_images_with_data_urls(self, processor):
        """Test extraction of images with data URLs."""
        html = """
        <html>
            <body>
                <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..." alt="Embedded Image">
                <img src="https://example.com/image.jpg" alt="External Image">
                <img src="/images/local.png" alt="Local Image">
            </body>
        </html>
        """
        result = processor.process(html)
        
        assert "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..." in result.assets["images"]
        assert "https://example.com/image.jpg" in result.assets["images"]
        assert "/images/local.png" in result.assets["images"]

    def test_extract_assets_with_invalid_urls(self, processor):
        """Test that invalid asset URLs are sanitized or ignored."""
        html = """
        <html>
            <body>
                <img src="javascript:alert('XSS')" alt="Bad Image">
                <script src="javascript:alert('XSS')"></script>
                <link rel="stylesheet" href="styles.css">
            </body>
        </html>
        """
        result = processor.process(html, base_url='https://example.com')
        
        assert "styles.css" in result.assets["stylesheets"]
        assert "javascript:alert('XSS')" not in result.assets["images"]
        assert "javascript:alert('XSS')" not in result.assets["scripts"]

class TestLinkHandling:
    """Tests for handling of links within content."""

    def test_extract_links_with_invalid_urls(self, processor):
        """Test that invalid URLs are filtered out."""
        html = """
        <html>
            <body>
                <a href="javascript:alert('XSS')">Bad Link</a>
                <a href="https://valid.com">Good Link</a>
            </body>
        </html>
        """
        result = processor.process(html)
        
        assert "[Good Link](https://valid.com)" in result.content["formatted_content"]
        assert "[Bad Link](#)" not in result.content["formatted_content"]  # JavaScript links are sanitized

    def test_extract_links_with_relative_paths(self, processor):
        """Test extraction and resolution of relative link URLs."""
        html = """
        <html>
            <head>
                <base href="https://example.com/subdir/">
            </head>
            <body>
                <a href="page.html">Relative Link</a>
                <a href="/absolute.html">Absolute Link</a>
            </body>
        </html>
        """
        result = processor.process(html)
        
        assert "[Relative Link](https://example.com/subdir/page.html)" in result.content["formatted_content"]
        assert "[Absolute Link](https://example.com/absolute.html)" in result.content["formatted_content"]

    def test_links_with_query_parameters(self, processor):
        """Test that links with query parameters are correctly formatted."""
        html = """
        <html>
            <body>
                <a href="https://example.com/page?name=John Doe&age=30">John's Page</a>
            </body>
        </html>
        """
        result = processor.process(html)
        
        assert "[John's Page](https://example.com/page?name=John Doe&age=30)" in result.content["formatted_content"]

    def test_links_with_anchors(self, processor):
        """Test that links with anchors are correctly formatted."""
        html = """
        <html>
            <body>
                <a href="https://example.com/page#section1">Section 1</a>
                <a href="#section2">Section 2</a>
            </body>
        </html>
        """
        result = processor.process(html, base_url='https://example.com/page')
        
        assert "[Section 1](https://example.com/page#section1)" in result.content["formatted_content"]
        assert "[Section 2](https://example.com/page#section2)" in result.content["formatted_content"]

    def test_anchor_tags_without_href(self, processor):
        """Test that anchor tags without href attributes are handled gracefully."""
        html = """
        <html>
            <body>
                <a>Link without href</a>
                <a href="">Empty href link</a>
            </body>
        </html>
        """
        result = processor.process(html)
        
        # Links without href or empty href might be rendered as plain text or with empty links
        assert "[Link without href](#)" in result.content["formatted_content"]
        assert "[Empty href link](#)" in result.content["formatted_content"]

    def test_links_with_various_protocols(self, processor):
        """Test that links with various protocols are handled correctly."""
        html = """
        <html>
            <body>
                <a href="https://example.com">HTTPS Link</a>
                <a href="http://example.com">HTTP Link</a>
                <a href="mailto:test@example.com">Email Link</a>
                <a href="ftp://example.com/file">FTP Link</a>
            </body>
        </html>
        """
        result = processor.process(html, base_url='https://example.com')
        
        assert "[HTTPS Link](https://example.com)" in result.content["formatted_content"]
        assert "[HTTP Link](http://example.com)" in result.content["formatted_content"]
        assert "[Email Link](mailto:test@example.com)" in result.content["formatted_content"]
        assert "[FTP Link](ftp://example.com/file)" in result.content["formatted_content"]

    def test_multiple_links_in_paragraph(self, processor):
        """Test that multiple links within a paragraph are correctly formatted."""
        html = """
        <html>
            <body>
                <p>Visit <a href="https://example.com/page1">Page 1</a> and <a href="https://example.com/page2">Page 2</a>.</p>
            </body>
        </html>
        """
        result = processor.process(html)
        
        assert "[Page 1](https://example.com/page1)" in result.content["formatted_content"]
        assert "[Page 2](https://example.com/page2)" in result.content["formatted_content"]

    def test_links_with_no_text(self, processor):
        """Test that links without text are handled correctly."""
        html = """
        <html>
            <body>
                <a href="https://example.com"></a>
            </body>
        </html>
        """
        result = processor.process(html)
        
        # Link with no text might appear as empty or with placeholder
        assert "[](https://example.com)" in result.content["formatted_content"]

class TestImageHandling:
    """Tests for handling of image tags within content."""

    def test_extract_images_with_no_alt(self, processor):
        """Test that images without alt attributes are handled correctly."""
        html = """
        <html>
            <body>
                <img src="image.jpg">
            </body>
        </html>
        """
        result = processor.process(html, base_url='https://example.com')
        
        formatted_content = result.content["formatted_content"]
        # Image with no alt text should have empty alt in Markdown
        assert "[](" in formatted_content
        assert "![Image](https://example.com/image.jpg)" not in formatted_content  # No alt text

    def test_images_with_alt_texts(self, processor):
        """Test that images have correct alt texts."""
        html = """
        <html>
            <body>
                <img src="image1.jpg" alt="Image One">
                <img src="image2.jpg" alt="Image Two">
            </body>
        </html>
        """
        result = processor.process(html, base_url='https://example.com')
        
        formatted_content = result.content["formatted_content"]
        assert "![Image One](https://example.com/image1.jpg)" in formatted_content
        assert "![Image Two](https://example.com/image2.jpg)" in formatted_content

    def test_images_with_data_uris(self, processor):
        """Test that images with data URIs are correctly handled."""
        html = """
        <html>
            <body>
                <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..." alt="Embedded Image">
                <img src="https://example.com/image.jpg" alt="External Image">
            </body>
        </html>
        """
        result = processor.process(html)
        
        assert "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..." in result.assets["images"]
        assert "https://example.com/image.jpg" in result.assets["images"]

    def test_multiple_images_same_src(self, processor):
        """Test that multiple images with the same src are handled correctly."""
        html = """
        <html>
            <body>
                <img src="image.jpg" alt="Image">
                <img src="image.jpg" alt="Duplicate Image">
            </body>
        </html>
        """
        result = processor.process(html, base_url='https://example.com')
        
        assets = result.assets
        # Images should be collected twice
        assert assets["images"].count("https://example.com/image.jpg") == 2
        formatted_content = result.content["formatted_content"]
        assert "![Image](https://example.com/image.jpg)" in formatted_content
        assert "![Duplicate Image](https://example.com/image.jpg)" in formatted_content

class TestTableHandling:
    """Tests for handling of table tags within content."""

    def test_convert_table_to_markdown_with_custom_attributes(self, processor):
        """Test table conversion with colspan, rowspan, and complex content."""
        html = """
        <table class="custom-table">
            <thead>
                <tr>
                    <th colspan="2">Merged Header</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td rowspan="2">Spanned Cell</td>
                    <td><strong>Bold Text</strong></td>
                </tr>
                <tr>
                    <td><em>Italic Text</em></td>
                </tr>
            </tbody>
        </table>
        """
        markdown = processor._convert_table_to_markdown(BeautifulSoup(html, 'html.parser').find('table'))
        assert "| Merged Header |" in markdown
        assert "| --- | --- |" in markdown
        assert "| Spanned Cell | Bold Text |" in markdown
        assert "| Italic Text |" in markdown

    def test_nested_tables(self, processor):
        """Test that nested tables are correctly converted to Markdown."""
        html = """
        <html>
            <body>
                <table>
                    <tr>
                        <th>Main Header</th>
                        <th>Subtable</th>
                    </tr>
                    <tr>
                        <td>Data 1</td>
                        <td>
                            <table>
                                <tr><th>Nested Header</th></tr>
                                <tr><td>Nested Data</td></tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """
        result = processor.process(html)
        
        formatted_content = result.content["formatted_content"]
        # Check main table headers
        assert "| Main Header | Subtable |" in formatted_content
        assert "| --- | --- |" in formatted_content
        # Check main table data
        assert "| Data 1 | " in formatted_content
        # Check nested table
        assert "| Nested Header |" in formatted_content
        assert "| --- |" in formatted_content
        assert "| Nested Data |" in formatted_content

    def test_tables_with_no_content(self, processor):
        """Test that tables without content are handled gracefully."""
        html = """
        <html>
            <body>
                <table></table>
            </body>
        </html>
        """
        result = processor.process(html)
        
        formatted_content = result.content["formatted_content"]
        # Empty table should not appear
        assert "|" not in formatted_content

class TestListHandling:
    """Tests for handling of list tags within content."""

    def test_nested_list_formatting(self, processor):
        """Test markdown formatting of nested lists."""
        html = """
        <html>
            <body>
                <ul>
                    <li>First level 1
                        <ul>
                            <li>Second level 1</li>
                            <li>Second level 2
                                <ul>
                                    <li>Third level 1</li>
                                </ul>
                            </li>
                        </ul>
                    </li>
                    <li>First level 2</li>
                </ul>
                <ol>
                    <li>Numbered item 1
                        <ol>
                            <li>Sub first</li>
                            <li>Sub second</li>
                        </ol>
                    </li>
                    <li>Numbered item 2</li>
                </ol>
                <ul>
                    <li>Mixed content:
                        <ol>
                            <li>Numbered in unordered</li>
                        </ol>
                    </li>
                </ul>
            </body>
        </html>
        """
        result = processor.process(html)
        
        content = result.content["formatted_content"]
        
        # Check unordered lists
        assert "- First level 1" in content
        assert "  - Second level 1" in content
        assert "  - Second level 2" in content
        assert "    - Third level 1" in content
        assert "- First level 2" in content
    
        # Check ordered lists
        assert "1. Numbered item 1" in content
        assert "   1. Sub first" in content
        assert "   2. Sub second" in content
        assert "2. Numbered item 2" in content
    
        # Check mixed content
        assert "- Mixed content:" in content
        assert "  1. Numbered in unordered" in content

    def test_unordered_lists_with_mixed_content(self, processor):
        """Test that unordered lists containing various types of content are correctly formatted."""
        html = """
        <html>
            <body>
                <ul>
                    <li>Item 1 with <strong>bold</strong> text.</li>
                    <li>Item 2 with a <a href="https://example.com">link</a>.</li>
                    <li>Item 3 with <em>italic</em> text.</li>
                </ul>
            </body>
        </html>
        """
        result = processor.process(html)
        
        content = result.content["formatted_content"]
        assert "- Item 1 with **bold** text." in content
        assert "- Item 2 with a [link](https://example.com)." in content
        assert "- Item 3 with _italic_ text." in content

    def test_ordered_lists_without_items(self, processor):
        """Test that ordered lists without list items are handled correctly."""
        html = """
        <html>
            <body>
                <ol>
                </ol>
            </body>
        </html>
        """
        result = processor.process(html)
        
        content = result.content["formatted_content"]
        # Empty ordered list should not appear
        assert "1. " not in content

    def test_lists_with_mixed_item_types(self, processor):
        """Test that lists with mixed item types are correctly formatted."""
        html = """
        <html>
            <body>
                <ul>
                    <li>Item 1</li>
                    <li>Item 2
                        <ol>
                            <li>Subitem 1</li>
                            <li>Subitem 2</li>
                        </ol>
                    </li>
                </ul>
            </body>
        </html>
        """
        result = processor.process(html)
        
        content = result.content["formatted_content"]
        assert "- Item 1" in content
        assert "- Item 2" in content
        assert "  1. Subitem 1" in content
        assert "  2. Subitem 2" in content

class TestAbbreviationHandling:
    """Tests for handling of abbreviation tags within content."""

    def test_process_with_abbreviations(self, processor):
        """Test processing of HTML with abbreviation tags."""
        html = """
        <html>
            <body>
                <p>The <abbr title="World Health Organization">WHO</abbr> was founded in 1948.</p>
            </body>
        </html>
        """
        result = processor.process(html)
        
        # Abbreviations are converted to markdown or plain text
        assert "The WHO (World Health Organization) was founded in 1948." in result.content["formatted_content"]

    def test_abbreviations_missing_title(self, processor):
        """Test that abbreviations without title attributes are handled gracefully."""
        html = """
        <html>
            <body>
                <p>The <abbr>NASA</abbr> was established in 1958.</p>
            </body>
        </html>
        """
        result = processor.process(html)
        
        # Without title, abbreviation might just be the text
        assert "The NASA was established in 1958." in result.content["formatted_content"]

    def test_multiple_abbreviations_in_paragraph(self, processor):
        """Test that multiple abbreviation tags within a paragraph are correctly formatted."""
        html = """
        <html>
            <body>
                <p>The <abbr title="World Health Organization">WHO</abbr> and <abbr title="United Nations">UN</abbr> collaborate globally.</p>
            </body>
        </html>
        """
        result = processor.process(html)
        
        assert "The WHO (World Health Organization) and UN (United Nations) collaborate globally." in result.content["formatted_content"]

    def test_multiple_abbreviations(self, processor):
        """Test that multiple abbreviation tags are correctly formatted."""
        html = """
        <html>
            <body>
                <p>The <abbr title="National Aeronautics and Space Administration">NASA</abbr> and <abbr title="Federal Bureau of Investigation">FBI</abbr> collaborate globally.</p>
            </body>
        </html>
        """
        result = processor.process(html)
        
        assert "The NASA (National Aeronautics and Space Administration) and FBI (Federal Bureau of Investigation) collaborate globally." in result.content["formatted_content"]

class TestFootnoteHandling:
    """Tests for handling of footnotes within content."""

    def test_process_with_footnotes(self, processor):
        """Test processing of HTML with footnotes."""
        html = """
        <html>
            <body>
                <p>Here is a footnote.<sup id="fnref1"><a href="#fn1">1</a></sup></p>
                <div class="footnotes">
                    <ol>
                        <li id="fn1">
                            <p>Footnote content. <a href="#fnref1">↩</a></p>
                        </li>
                    </ol>
                </div>
            </body>
        </html>
        """
        result = processor.process(html)
        
        # Assuming footnotes are converted to markdown references or plain text
        assert "Here is a footnote.[1]" in result.content["formatted_content"]
        assert "1. Footnote content." in result.content["formatted_content"]

    def test_multiple_footnotes(self, processor):
        """Test processing of HTML with multiple footnotes."""
        html = """
        <html>
            <body>
                <p>First footnote.<sup id="fnref1"><a href="#fn1">1</a></sup></p>
                <p>Second footnote.<sup id="fnref2"><a href="#fn2">2</a></sup></p>
                <div class="footnotes">
                    <ol>
                        <li id="fn1">
                            <p>First footnote content. <a href="#fnref1">↩</a></p>
                        </li>
                        <li id="fn2">
                            <p>Second footnote content. <a href="#fnref2">↩</a></p>
                        </li>
                    </ol>
                </div>
            </body>
        </html>
        """
        result = processor.process(html)
        
        formatted_content = result.content["formatted_content"]
        assert "First footnote.[1]" in formatted_content
        assert "Second footnote.[2]" in formatted_content
        assert "1. First footnote content." in formatted_content
        assert "2. Second footnote content." in formatted_content

class TestCommentHandling:
    """Tests for handling of HTML comments within content."""

    def test_extract_text_with_comments(self, processor):
        """Test that HTML comments are ignored in text extraction."""
        html = """
        <html>
            <body>
                <!-- This is a comment -->
                <p>Visible text.</p>
            </body>
        </html>
        """
        result = processor.process(html)
        
        assert "This is a comment" not in result.content["formatted_content"]
        assert "Visible text." in result.content["formatted_content"]

    def test_process_with_comments_extraction_enabled(self, processor):
        """Test that comments are extracted when extraction is enabled."""
        config = {
            'extract_comments': True
        }
        processor.configure(config)
    
        html = """
        <html>
            <body>
                <!-- This is a comment -->
                <p>Visible text.</p>
            </body>
        </html>
        """
        result = processor.process(html)
        
        # Comments should be present in the formatted content
        assert "<!-- This is a comment -->" in result.content["formatted_content"]
        assert "Visible text." in result.content["formatted_content"]

    def test_process_with_conditional_comments(self, processor):
        """Test that conditional comments are ignored in content extraction."""
        html = """
        <html>
            <!--[if IE]>
                <p>IE specific content.</p>
            <![endif]-->
            <p>Regular content.</p>
        </html>
        """
        result = processor.process(html)
        
        assert "IE specific content." not in result.content["formatted_content"]
        assert "Regular content." in result.content["formatted_content"]

class TestProcessorConfiguration:
    """Tests for processor configuration and custom settings."""

    def test_processor_with_custom_config(self, processor):
        """Test content processor with custom configuration."""
        config = {
            'allowed_tags': ['p', 'a', 'strong'],
            'max_heading_level': 3,
            'preserve_whitespace_elements': ['pre', 'code'],
            'code_languages': ['python', 'javascript'],
            'sanitize_urls': True,
            'metadata_prefixes': ['custom:', 'app:'],
            'extract_comments': False
        }
    
        processor.configure(config)
    
        html = """
        <div>
            <h1>Level 1</h1>
            <h4>Level 4</h4>
            <p>Paragraph <strong>bold</strong> <em>italic</em></p>
            <pre><code class="python">def test(): pass</code></pre>
            <pre><code class="ruby">def test; end</code></pre>
            <a href="/relative">Link</a>
            <!-- Comment -->
            <meta name="custom:key" content="value">
            <meta name="other:key" content="value">
        </div>
        """
        result = processor.process(html, base_url='https://example.com')
    
        # Check heading levels
        headings = result.content["headings"]
        assert any(h["text"] == "Level 1" and h["level"] == 1 for h in headings)
        assert not any(h["text"] == "Level 4" for h in headings)
    
        # Check allowed tags
        assert "**bold**" in result.content["formatted_content"]
        assert "_italic_" not in result.content["formatted_content"]  # 'em' tag is not allowed
    
        # Check code blocks
        assert "```python\ndef test(): pass\n```" in result.content["formatted_content"]
        assert "```ruby\ndef test; end\n```" not in result.content["formatted_content"]  # 'ruby' not allowed
    
        # Check URL sanitization
        assert "[Link](https://example.com/relative)" in result.content["formatted_content"]
    
        # Check metadata prefixes
        assert_metadata(result.metadata, "custom:key", "value")
        assert "other:key" not in result.metadata  # 'other:key' does not match metadata_prefixes
    
        # Check that comments are not extracted
        assert "<!-- Comment -->" not in result.content["formatted_content"]

    def test_processor_with_multiple_custom_configurations(self, processor):
        """Test processor with multiple custom configurations."""
        config = {
            'allowed_tags': ['p', 'a', 'strong', 'em', 'code'],
            'max_heading_level': 5,
            'preserve_whitespace_elements': ['pre', 'code'],
            'code_languages': ['python', 'javascript'],
            'sanitize_urls': True,
            'metadata_prefixes': ['custom:', 'app:'],
            'extract_comments': True
        }
        processor.configure(config)
    
        html = """
        <html>
            <head>
                <title>Custom Config Test</title>
                <meta name="custom:meta" content="Custom Meta Value">
            </head>
            <body>
                <h1>Heading 1</h1>
                <h5>Heading 5</h5>
                <p>Paragraph with <strong>bold</strong> and <em>italic</em> text.</p>
                <pre><code class="python">print("Hello, Python!")</code></pre>
                <pre><code class="ruby">puts "Hello, Ruby!"</code></pre>
                <a href="https://example.com">Valid Link</a>
                <a href="javascript:alert('XSS')">Bad Link</a>
                <!-- Extracted Comment -->
            </body>
        </html>
        """
        result = processor.process(html, base_url='https://example.com')
    
        # Check headings
        headings = result.content["headings"]
        assert any(h["text"] == "Heading 1" and h["level"] == 1 for h in headings)
        assert any(h["text"] == "Heading 5" and h["level"] == 5 for h in headings)
    
        # Check allowed tags
        assert "**bold**" in result.content["formatted_content"]
        assert "_italic_" in result.content["formatted_content"]
    
        # Check code blocks
        assert "```python\nprint(\"Hello, Python!\")\n```" in result.content["formatted_content"]
        assert "```ruby\nputs \"Hello, Ruby!\"\n```" not in result.content["formatted_content"]  # 'ruby' not allowed
    
        # Check URL sanitization
        assert "[Bad Link](#)" in result.content["formatted_content"]
        assert "[Valid Link](https://example.com)" in result.content["formatted_content"]
    
        # Check metadata prefixes
        assert_metadata(result.metadata, "custom:meta", "Custom Meta Value")
    
        # Check comments extraction
        assert "<!-- Extracted Comment -->" in result.content["formatted_content"]

class TestProcessorEdgeCases:
    """Tests for various edge cases and malformed HTML."""

    def test_process_with_invalid_html(self, processor):
        """Test processing of HTML with invalid structure."""
        html = """
        <html>
            <title>Outside head</title>
            <meta name="description" content="Outside head">
            <head>
                <title>Inside head</title>
                <meta name="keywords" content="inside, head">
            </head>
            <body>
                <title>Inside body</title>
                <meta name="author" content="Inside body">
            </body>
        </html>
        """
        result = processor.process(html)
        
        # Should prioritize metadata from <head> section
        assert_metadata(result.metadata, "title", "Inside head")
        assert_metadata(result.metadata, "keywords", "inside, head")
        assert_metadata(result.metadata, "description", "Outside head")
        assert_metadata(result.metadata, "author", "Inside body")

    def test_process_with_large_content(self, processor):
        """Test processing of very large HTML content."""
        config = ProcessorConfig(
            max_content_length=5000,
            min_content_length=10
        )
        processor = ContentProcessor(config)
        
        # Create large HTML content
        large_text = "<p>" + "A" * 6000 + "</p>"
        html = f"<html><head><title>Large Content</title></head><body>{large_text}</body></html>"
        
        result = processor.process(html)
        
        assert result.title == "Content Too Large"
        assert len(result.errors) == 1
        assert "exceeds maximum limit" in result.errors[0]
        assert not result.content["formatted_content"]

    def test_process_with_invalid_nesting(self, processor):
        """Test processing of HTML with invalid nesting of tags."""
        html = """
        <html>
            <body>
                <p>Paragraph with <strong>bold <em>and italic</strong> text</em>.</p>
            </body>
        </html>
        """
        result = processor.process(html)
        
        # Depending on how BeautifulSoup handles invalid nesting
        assert "Paragraph with **bold and italic** text." in result.content["formatted_content"]

    def test_process_with_malformed_attributes(self, processor):
        """Test processing of HTML with malformed attributes."""
        html = """
        <html>
            <body>
                <a href='https://example.com" onclick="alert(1)'>Link</a>
                <img src='https://example.com/image.jpg" alt="Image'>
            </body>
        </html>
        """
        result = processor.process(html)
        
        # Ensure that attributes are sanitized
        assert "[Link](https://example.com)" in result.content["formatted_content"]
        assert "![Image](https://example.com/image.jpg)" in result.content["formatted_content"]

    def test_process_with_empty_html(self, processor):
        """Test processing of empty HTML."""
        html = ""
        result = processor.process(html)
        
        assert result.title == "Untitled Document"
        assert not result.content.get("formatted_content", "")
        assert not result.metadata
        assert not result.assets
        assert not result.errors

    def test_html_without_body(self, processor):
        """Test processing of HTML without a body tag."""
        html = """
        <html>
            <head>
                <title>Title Only</title>
            </head>
        </html>
        """
        result = processor.process(html)
        
        formatted_content = result.content.get("formatted_content", "")
        assert not formatted_content
        assert_metadata(result.metadata, "title", "Title Only")

    def test_empty_paragraphs(self, processor):
        """Test that empty paragraphs are handled correctly."""
        html = """
        <html>
            <body>
                <p></p>
                <p>Non-empty paragraph.</p>
                <p></p>
            </body>
        </html>
        """
        result = processor.process(html)
        
        assert "Non-empty paragraph." in result.content["formatted_content"]
        # No content from empty paragraphs
        assert result.content["formatted_content"].count("<p></p>") == 0

class TestInlineStyleHandling:
    """Tests for removal of inline styles from content."""

    def test_processor_with_inline_styles(self, processor):
        """Test that inline styles are removed from content."""
        html = """
        <html>
            <body>
                <p style="color:red;">Red text.</p>
                <p style="font-size:20px;">Large text.</p>
            </body>
        </html>
        """
        result = processor.process(html)
        
        # Inline styles should be removed, text should remain
        assert "Red text." in result.content["formatted_content"]
        assert "Large text." in result.content["formatted_content"]
        assert 'style="color:red;"' not in result.content["formatted_content"]
        assert 'style="font-size:20px;"' not in result.content["formatted_content"]

    def test_inline_styles_within_allowed_tags(self, processor):
        """Test that inline styles within allowed tags are removed but content remains."""
        html = """
        <html>
            <body>
                <p style="color:blue;">Blue text.</p>
                <strong style="font-weight:normal;">Normal Weight</strong>
            </body>
        </html>
        """
        result = processor.process(html)
        
        formatted_content = result.content["formatted_content"]
        assert "Blue text." in formatted_content
        assert "**Normal Weight**" in formatted_content
        assert 'style="color:blue;"' not in formatted_content
        assert 'style="font-weight:normal;"' not in formatted_content

class TestMediaHandling:
    """Tests for handling of media elements like video and audio."""

    def test_collect_media_assets(self, processor):
        """Test collection of media assets like video and audio."""
        html = """
        <html>
            <body>
                <video src="video.mp4" controls></video>
                <audio src="audio.mp3" controls></audio>
                <source src="source.mp4" type="video/mp4">
            </body>
        </html>
        """
        result = processor.process(html, base_url='https://example.com')
        
        assets = result.assets
        assert "https://example.com/video.mp4" in assets["media"]
        assert "https://example.com/audio.mp3" in assets["media"]
        assert "https://example.com/source.mp4" in assets["media"]

    def test_embedded_media_handling(self, processor):
        """Test that embedded media like videos and audios are correctly collected."""
        html = """
        <html>
            <body>
                <video src="video.mp4" controls></video>
                <audio src="audio.mp3" controls></audio>
                <source src="source.mp4" type="video/mp4">
            </body>
        </html>
        """
        result = processor.process(html, base_url='https://example.com')
        
        assets = result.assets
        assert "https://example.com/video.mp4" in assets["media"]
        assert "https://example.com/audio.mp3" in assets["media"]
        assert "https://example.com/source.mp4" in assets["media"]

    def test_embedded_videos_without_src(self, processor):
        """Test that embedded videos without src attributes are handled gracefully."""
        html = """
        <html>
            <body>
                <video controls></video>
                <audio controls></audio>
            </body>
        </html>
        """
        result = processor.process(html)
        
        assets = result.assets
        # Video without src should not be collected
        assert not assets["media"]
        
        formatted_content = result.content["formatted_content"]
        # Video without src should not appear
        assert "![video](#)" not in formatted_content

class TestInlineEventHandlers:
    """Tests for removal of inline event handlers to prevent XSS."""

    def test_inline_event_handlers_removal(self, processor):
        """Test that inline event handlers are removed from tags."""
        html = """
        <html>
            <body>
                <p onmouseover="alert('XSS')">Hover over me!</p>
                <a href="https://example.com" onclick="alert('XSS')">Example Link</a>
            </body>
        </html>
        """
        result = processor.process(html)
        
        formatted_content = result.content["formatted_content"]
        # Inline event handlers should be removed
        assert 'onmouseover="alert(\'XSS\')"' not in formatted_content
        assert 'onclick="alert(\'XSS\')"' not in formatted_content
        # Links should remain sanitized if needed
        assert "[Example Link](https://example.com)" in formatted_content

    def test_process_with_xss_attempts(self, processor):
        """Test that XSS attempts are sanitized in content."""
        html = """
        <html>
            <body>
                <p onclick="alert('XSS')">Click me!</p>
                <a href="javascript:alert('XSS')">Bad Link</a>
                <img src="javascript:alert('XSS')" alt="Bad Image">
            </body>
        </html>
        """
        result = processor.process(html)
        
        # Inline event handlers should be removed
        assert 'onclick="alert(\'XSS\')"' not in result.content["formatted_content"]
        
        # Bad link should be sanitized
        assert "[Bad Link](#)" in result.content["formatted_content"]
        
        # Images with javascript: are sanitized or removed
        assert "![Bad Image](#)" not in result.content["formatted_content"]  # Assuming images with invalid src are removed

class TestAdvancedFeatures:
    """Tests for advanced features like custom extractors and filters."""

    def test_processor_with_custom_extractors(self, processor):
        """Test content processor with custom content extractors."""
        def custom_tag_extractor(soup):
            return [{"type": "custom", "content": tag.text}
                    for tag in soup.find_all("custom-tag")]
        
        def custom_metadata_extractor(soup):
            return {"custom_meta_" + tag["name"]: tag["content"]
                    for tag in soup.find_all("meta", {"name": re.compile("^custom-")})}
        
        processor.add_content_extractor("custom_tags", custom_tag_extractor)
        processor.add_metadata_extractor(custom_metadata_extractor)
        
        html = """
        <div>
            <custom-tag>Custom content 1</custom-tag>
            <custom-tag>Custom content 2</custom-tag>
            <meta name="custom-key1" content="value1">
            <meta name="custom-key2" content="value2">
        </div>
        """
        result = processor.process(html)
        
        # Check custom content extraction
        assert "Custom content 1" in result.content["formatted_content"]
        assert "Custom content 2" in result.content["formatted_content"]
        assert len(result.content.get("custom_tags", [])) == 2
        
        # Check custom metadata extraction
        assert_metadata(result.metadata, "custom_meta_key1", "value1")
        assert_metadata(result.metadata, "custom_meta_key2", "value2")

    def test_processor_with_custom_filters(self, processor):
        """Test content processor with custom content filters."""
        def custom_content_filter(content):
            # Remove content containing specific keywords
            if isinstance(content, str):
                return not any(kw in content.lower()
                             for kw in ["forbidden", "restricted"])
            return True
        
        def custom_url_filter(url):
            # Only allow specific domains
            allowed_domains = ["example.com", "trusted.org"]
            return any(domain in url.lower() for domain in allowed_domains)
        
        processor.add_content_filter(custom_content_filter)
        processor.add_url_filter(custom_url_filter)
        
        html = """
        <div>
            <p>Normal content</p>
            <p>Content with forbidden word</p>
            <p>Content with restricted access</p>
            <a href="https://example.com/page">Valid link</a>
            <a href="https://untrusted.com/page">Invalid link</a>
            <img src="https://trusted.org/image.jpg">
            <img src="https://malicious.com/image.jpg">
        </div>
        """
        result = processor.process(html)
        
        # Check content filtering
        assert "Normal content" in result.content["formatted_content"]
        assert "Content with forbidden word" not in result.content["formatted_content"]
        assert "Content with restricted access" not in result.content["formatted_content"]
        
        # Check URL filtering
        assert "[Valid link](https://example.com/page)" in result.content["formatted_content"]
        assert "[Invalid link](https://untrusted.com/page)" not in result.content["formatted_content"]
        assert "https://trusted.org/image.jpg" in result.assets["images"]
        assert "https://malicious.com/image.jpg" not in result.assets["images"]

    def test_custom_content_extraction(self, processor):
        """Test that custom content extractors work as expected."""
        def custom_extractor(soup):
            return [tag.get_text(strip=True) for tag in soup.find_all("custom-element")]
        
        processor.add_content_extractor("custom_elements", custom_extractor)
        
        html = """
        <html>
            <body>
                <custom-element>Custom Data 1</custom-element>
                <custom-element>Custom Data 2</custom-element>
            </body>
        </html>
        """
        result = processor.process(html)
        
        assert "Custom Data 1" in result.content["custom_elements"]
        assert "Custom Data 2" in result.content["custom_elements"]

# --------------------
# Security Tests
# --------------------

class TestSecurity:
    """Tests to ensure that malicious content is sanitized."""

    def test_process_with_xss_attempts(self, processor):
        """Test that XSS attempts are sanitized in content."""
        html = """
        <html>
            <body>
                <p onclick="alert('XSS')">Click me!</p>
                <a href="javascript:alert('XSS')">Bad Link</a>
                <img src="javascript:alert('XSS')" alt="Bad Image">
            </body>
        </html>
        """
        result = processor.process(html)
        
        # Inline event handlers should be removed
        assert 'onclick="alert(\'XSS\')"' not in result.content["formatted_content"]
        
        # Bad link should be sanitized
        assert "[Bad Link](#)" in result.content["formatted_content"]
        
        # Images with javascript: are sanitized or removed
        assert "![Bad Image](#)" not in result.content["formatted_content"]  # Assuming images with invalid src are removed

    def test_safe_content_sanitization(self, processor):
        """Test that content is sanitized to prevent XSS."""
        html = """
        <html>
            <body>
                <p>Safe content.</p>
                <p onclick="alert('XSS')">Unsafe content.</p>
                <a href="javascript:alert('XSS')">Bad Link</a>
            </body>
        </html>
        """
        result = processor.process(html)
        
        # Safe content should remain
        assert "Safe content." in result.content["formatted_content"]
        
        # Unsafe content should have the event handler removed
        assert "Unsafe content." in result.content["formatted_content"]
        assert 'onclick="alert(\'XSS\')"' not in result.content["formatted_content"]
        
        # Bad link should be sanitized
        assert "[Bad Link](#)" in result.content["formatted_content"]

# --------------------
# Other Specific Tests
# --------------------

class TestEdgeCases:
    """Tests for various edge cases and uncommon scenarios."""

    def test_empty_content(self, processor):
        """Test that empty content is handled gracefully."""
        html = """
        <html>
            <head>
                <title>Empty Content Test</title>
            </head>
            <body>
            </body>
        </html>
        """
        result = processor.process(html)
        
        assert_metadata(result.metadata, "title", "Empty Content Test")
        assert not result.content.get("formatted_content", "")
        assert not result.assets
        assert not result.errors

    def test_meta_redirects_handling(self, processor):
        """Test that meta refresh redirects are correctly extracted and recorded."""
        html = """
        <html>
            <head>
                <meta http-equiv="refresh" content="0; url=https://example.com/redirect">
                <title>Redirect Page</title>
            </head>
            <body>
                <p>If you are not redirected, <a href="https://example.com/redirect">click here</a>.</p>
            </body>
        </html>
        """
        result = processor.process(html)
        
        # Assuming meta redirects are stored in metadata
        assert_metadata(result.metadata, "meta_redirects", ["https://example.com/redirect"])
        formatted_content = result.content["formatted_content"]
        assert "[click here](https://example.com/redirect)" in formatted_content

    def test_duplicate_metadata_handling(self, processor):
        """Test that duplicate metadata tags retain the first occurrence."""
        html = """
        <html>
            <head>
                <title>First Title</title>
                <meta name="description" content="First description">
                <meta name="description" content="Second description">
            </head>
        </html>
        """
        result = processor.process(html)
        
        assert_metadata(result.metadata, "title", "First Title")
        assert_metadata(result.metadata, "description", "First description")  # First occurrence retained

    def test_metadata_extraction_with_case_sensitivity(self, processor):
        """Test that metadata keys are case-insensitive and stored in lowercase."""
        html = """
        <html>
            <head>
                <title>Case Sensitivity Test</title>
                <meta name="Description" content="Uppercase Description">
                <meta property="OG:Title" content="Uppercase OG Title">
            </head>
            <body>
                <p>Content here.</p>
            </body>
        </html>
        """
        result = processor.process(html)
        
        # Metadata keys should be in lowercase
        assert_metadata(result.metadata, "description", "Uppercase Description")
        assert_metadata(result.metadata, "og:title", "Uppercase OG Title")

    def test_process_with_multiple_json_ld_scripts(self, processor):
        """Test processing of HTML with multiple JSON-LD scripts."""
        html = """
        <html>
            <head>
                <title>Multiple JSON-LD</title>
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "Person",
                    "name": "John Doe",
                    "jobTitle": "Developer"
                }
                </script>
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "Organization",
                    "name": "Example Corp",
                    "url": "https://example.com"
                }
                </script>
            </head>
            <body>
                <p>Content here.</p>
            </body>
        </html>
        """
        result = processor.process(html)
    
        # Check Person metadata
        assert_metadata(result.metadata, "name", "John Doe")
        assert_metadata(result.metadata, "jobtitle", "Developer")
        
        # Check Organization metadata
        assert_metadata(result.metadata, "organization", {"@context": "https://schema.org", "@type": "Organization", "name": "Example Corp", "url": "https://example.com"})
        
        # Depending on implementation, JSON-LD may overwrite or merge metadata

    def test_multiple_custom_metadata_prefixes(self, processor):
        """Test that custom metadata prefixes are handled correctly."""
        html = """
        <html>
            <head>
                <title>Custom Prefixes Test</title>
                <meta name="custom:author" content="Jane Doe">
                <meta name="app:version" content="1.0.0">
            </head>
            <body>
                <p>Content here.</p>
            </body>
        </html>
        """
        result = processor.process(html)
        
        assert_metadata(result.metadata, "custom:author", "Jane Doe")
        assert_metadata(result.metadata, "app:version", "1.0.0")

    def test_extract_metadata_with_microdata(self, processor):
        """Test processing of HTML with microdata."""
        html = """
        <html>
            <head>
                <title>Microdata Test</title>
                <meta name="description" content="Testing microdata extraction.">
            </head>
            <body>
                <div itemscope itemtype="https://schema.org/Person">
                    <meta itemprop="name" content="John Doe">
                    <meta itemprop="jobTitle" content="Software Engineer">
                    <p>About John Doe.</p>
                </div>
            </body>
        </html>
        """
        result = processor.process(html)
        
        assert_metadata(result.metadata, "name", "John Doe")
        assert_metadata(result.metadata, "jobtitle", "Software Engineer")
        assert "About John Doe." in result.content["formatted_content"]

    def test_extract_metadata_with_meta_redirects(self, processor):
        """Test metadata extraction of meta refresh redirects."""
        html = """
        <html>
            <head>
                <meta http-equiv="refresh" content="5; URL='https://example.com/redirected-page'">
                <meta http-equiv="refresh" content="10; URL='https://example.com/another-page'">
            </head>
            <body>
                <p>Redirecting...</p>
            </body>
        </html>
        """
        result = processor.process(html)
        
        redirects = result.metadata.get("meta_redirects", [])
        assert "https://example.com/redirected-page" in redirects
        assert "https://example.com/another-page" in redirects

class TestCustomFilters:
    """Tests for custom content and URL filters."""

    def test_processor_with_custom_content_filters(self, processor):
        """Test that custom content filters work as expected."""
        def custom_content_filter(content):
            # Remove content containing specific keywords
            if isinstance(content, str):
                return not any(kw in content.lower() for kw in ["forbidden", "restricted"])
            return True
        
        processor.add_content_filter(custom_content_filter)
        
        html = """
        <html>
            <body>
                <p>Normal content</p>
                <p>Content with forbidden word</p>
                <p>Content with restricted access</p>
            </body>
        </html>
        """
        result = processor.process(html)
        
        # Check content filtering
        assert "Normal content" in result.content["formatted_content"]
        assert "Content with forbidden word" not in result.content["formatted_content"]
        assert "Content with restricted access" not in result.content["formatted_content"]

    def test_processor_with_custom_url_filters(self, processor):
        """Test that custom URL filters work as expected."""
        def custom_url_filter(url):
            # Only allow specific domains
            allowed_domains = ["example.com", "trusted.org"]
            return any(domain in url.lower() for domain in allowed_domains)
        
        processor.add_url_filter(custom_url_filter)
        
        html = """
        <html>
            <body>
                <a href="https://example.com/page">Valid Link</a>
                <a href="https://untrusted.com/page">Invalid Link</a>
                <img src="https://trusted.org/image.jpg">
                <img src="https://malicious.com/image.jpg">
            </body>
        </html>
        """
        result = processor.process(html)
        
        # Check URL filtering
        assert "[Valid Link](https://example.com/page)" in result.content["formatted_content"]
        assert "[Invalid Link](https://untrusted.com/page)" not in result.content["formatted_content"]
        assert "https://trusted.org/image.jpg" in result.assets["images"]
        assert "https://malicious.com/image.jpg" not in result.assets["images"]

# --------------------
# Comprehensive Test Cases
# --------------------

class TestComprehensiveScenarios:
    """Comprehensive tests covering multiple functionalities together."""

    def test_complex_nested_html(self, processor):
        """Test that deeply nested HTML elements are processed correctly."""
        html = """
        <html>
            <body>
                <div>
                    <section>
                        <article>
                            <div>
                                <p>Deeply nested paragraph.</p>
                            </div>
                        </article>
                    </section>
                </div>
            </body>
        </html>
        """
        result = processor.process(html)
        
        assert "Deeply nested paragraph." in result.content["formatted_content"]

    def test_processor_with_multiple_custom_configurations(self, processor):
        """Test processor with multiple custom configurations."""
        config = {
            'allowed_tags': ['p', 'a', 'strong', 'em', 'code'],
            'max_heading_level': 5,
            'preserve_whitespace_elements': ['pre', 'code'],
            'code_languages': ['python', 'javascript'],
            'sanitize_urls': True,
            'metadata_prefixes': ['custom:', 'app:'],
            'extract_comments': True
        }
        processor.configure(config)
    
        html = """
        <html>
            <head>
                <title>Custom Config Test</title>
                <meta name="custom:meta" content="Custom Meta Value">
            </head>
            <body>
                <h1>Heading 1</h1>
                <h5>Heading 5</h5>
                <p>Paragraph with <strong>bold</strong> and <em>italic</em> text.</p>
                <pre><code class="python">print("Hello, Python!")</code></pre>
                <pre><code class="ruby">puts "Hello, Ruby!"</code></pre>
                <a href="https://example.com">Valid Link</a>
                <a href="javascript:alert('XSS')">Bad Link</a>
                <!-- Extracted Comment -->
            </body>
        </html>
        """
        result = processor.process(html, base_url='https://example.com')
    
        # Check headings
        headings = result.content["headings"]
        assert any(h["text"] == "Heading 1" and h["level"] == 1 for h in headings)
        assert any(h["text"] == "Heading 5" and h["level"] == 5 for h in headings)
    
        # Check allowed tags
        assert "**bold**" in result.content["formatted_content"]
        assert "_italic_" in result.content["formatted_content"]
    
        # Check code blocks
        assert "```python\nprint(\"Hello, Python!\")\n```" in result.content["formatted_content"]
        assert "```ruby\nputs \"Hello, Ruby!\"\n```" not in result.content["formatted_content"]  # 'ruby' not allowed
    
        # Check URL sanitization
        assert "[Bad Link](#)" in result.content["formatted_content"]
        assert "[Valid Link](https://example.com)" in result.content["formatted_content"]
    
        # Check metadata prefixes
        assert_metadata(result.metadata, "custom:meta", "Custom Meta Value")
    
        # Check comments extraction
        assert "<!-- Extracted Comment -->" in result.content["formatted_content"]

    def test_processor_with_multiple_custom_configurations(self, processor):
        """Test processor with multiple custom configurations."""
        config = {
            'allowed_tags': ['p', 'a', 'strong', 'em', 'code'],
            'max_heading_level': 5,
            'preserve_whitespace_elements': ['pre', 'code'],
            'code_languages': ['python', 'javascript'],
            'sanitize_urls': True,
            'metadata_prefixes': ['custom:', 'app:'],
            'extract_comments': True
        }
        processor.configure(config)
    
        html = """
        <html>
            <head>
                <title>Custom Config Test</title>
                <meta name="custom:meta" content="Custom Meta Value">
            </head>
            <body>
                <h1>Heading 1</h1>
                <h5>Heading 5</h5>
                <p>Paragraph with <strong>bold</strong> and <em>italic</em> text.</p>
                <pre><code class="python">print("Hello, Python!")</code></pre>
                <pre><code class="ruby">puts "Hello, Ruby!"</code></pre>
                <a href="https://example.com">Valid Link</a>
                <a href="javascript:alert('XSS')">Bad Link</a>
                <!-- Extracted Comment -->
            </body>
        </html>
        """
        result = processor.process(html, base_url='https://example.com')
    
        # Check headings
        headings = result.content["headings"]
        assert any(h["text"] == "Heading 1" and h["level"] == 1 for h in headings)
        assert any(h["text"] == "Heading 5" and h["level"] == 5 for h in headings)
    
        # Check allowed tags
        assert "**bold**" in result.content["formatted_content"]
        assert "_italic_" in result.content["formatted_content"]
    
        # Check code blocks
        assert "```python\nprint(\"Hello, Python!\")\n```" in result.content["formatted_content"]
        assert "```ruby\nputs \"Hello, Ruby!\"\n```" not in result.content["formatted_content"]  # 'ruby' not allowed
    
        # Check URL sanitization
        assert "[Bad Link](#)" in result.content["formatted_content"]
        assert "[Valid Link](https://example.com)" in result.content["formatted_content"]
    
        # Check metadata prefixes
        assert_metadata(result.metadata, "custom:meta", "Custom Meta Value")
    
        # Check comments extraction
        assert "<!-- Extracted Comment -->" in result.content["formatted_content"]

class TestUnicodeHandling:
    """Tests for handling of Unicode characters within content."""

    def test_process_with_unicode_content(self, processor):
        """Test processing of HTML with Unicode characters."""
        html = """
        <html>
            <head>
                <title>Unicode Test</title>
            </head>
            <body>
                <p>Unicode content: 😊, 🚀, and 🌟</p>
            </body>
        </html>
        """
        result = processor.process(html)
        
        assert_metadata(result.metadata, "title", "Unicode Test")
        assert "Unicode content: 😊, 🚀, and 🌟" in result.content["formatted_content"]

    def test_extract_text_with_mixed_encodings(self, processor):
        """Test processing of HTML with mixed character encodings."""
        html = """
        <html>
            <head>
                <meta charset="UTF-8">
                <title>Mixed Encodings</title>
            </head>
            <body>
                <p>Normal text.</p>
                <p>Emoji: 😊🚀🌟</p>
                <p>Accented characters: café, naïve, résumé</p>
            </body>
        </html>
        """
        result = processor.process(html)
        
        assert_metadata(result.metadata, "title", "Mixed Encodings")
        assert "Normal text." in result.content["formatted_content"]
        assert "Emoji: 😊🚀🌟" in result.content["formatted_content"]
        assert "Accented characters: café, naïve, résumé" in result.content["formatted_content"]

class TestMediaAssetsCollection:
    """Tests for collection of various media assets like video and audio."""

    def test_media_assets_collection(self, processor):
        """Test that media assets like video and audio are collected."""
        html = """
        <html>
            <body>
                <video src="video.mp4" controls></video>
                <audio src="audio.mp3" controls></audio>
                <source src="source.mp4" type="video/mp4">
            </body>
        </html>
        """
        result = processor.process(html, base_url='https://example.com')
        
        assets = result.assets
        assert "https://example.com/video.mp4" in assets["media"]
        assert "https://example.com/audio.mp3" in assets["media"]
        assert "https://example.com/source.mp4" in assets["media"]

class TestMultipleJSONLD:
    """Tests for processing of multiple JSON-LD scripts within HTML."""

    def test_process_with_multiple_json_ld_scripts(self, processor):
        """Test processing of HTML with multiple JSON-LD scripts."""
        html = """
        <html>
            <head>
                <title>Multiple JSON-LD</title>
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "Person",
                    "name": "John Doe",
                    "jobTitle": "Developer"
                }
                </script>
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "Organization",
                    "name": "Example Corp",
                    "url": "https://example.com"
                }
                </script>
            </head>
            <body>
                <p>Content here.</p>
            </body>
        </html>
        """
        result = processor.process(html)
    
        # Check Person metadata
        assert_metadata(result.metadata, "name", "John Doe")
        assert_metadata(result.metadata, "jobtitle", "Developer")
        
        # Check Organization metadata
        assert_metadata(result.metadata, "organization", {"@context": "https://schema.org", "@type": "Organization", "name": "Example Corp", "url": "https://example.com"})
        
        # Depending on implementation, JSON-LD may overwrite or merge metadata

class TestMetaRedirects:
    """Tests for handling of meta refresh redirects."""

    def test_process_with_meta_redirects_and_valid_content(self, processor):
        """Test processing of HTML with meta redirects and valid content."""
        html = """
        <html>
            <head>
                <title>Redirect Test</title>
                <meta http-equiv="refresh" content="0; URL='https://example.com/home'">
            </head>
            <body>
                <p>You are being redirected.</p>
            </body>
        </html>
        """
        result = processor.process(html)
        
        assert_metadata(result.metadata, "title", "Redirect Test")
        redirects = result.metadata.get("meta_redirects", [])
        assert "https://example.com/home" in redirects
        assert "You are being redirected." in result.content["formatted_content"]

class TestDefinitionLists:
    """Tests for processing of definition lists."""

    def test_process_with_definition_lists(self, processor):
        """Test processing of HTML with definition lists."""
        html = """
        <html>
            <body>
                <dl>
                    <dt>Term 1</dt>
                    <dd>Definition 1</dd>
                    <dt>Term 2</dt>
                    <dd>Definition 2</dd>
                </dl>
            </body>
        </html>
        """
        result = processor.process(html)
        
        assert "**Term 1**: Definition 1" in result.content["formatted_content"]
        assert "**Term 2**: Definition 2" in result.content["formatted_content"]

class TestEmbeddedIframes:
    """Tests for handling of embedded iframes within content."""

    def test_process_with_embedded_iframes(self, processor):
        """Test processing of HTML with embedded iframes."""
        html = """
        <html>
            <body>
                <iframe src="https://example.com/embed" width="600" height="400"></iframe>
                <p>Content after iframe.</p>
            </body>
        </html>
        """
        result = processor.process(html)
        
        assert "[iframe](https://example.com/embed)" in result.content["formatted_content"]
        assert "Content after iframe." in result.content["formatted_content"]

    def test_multiple_iframes(self, processor):
        """Test that multiple iframes are correctly converted."""
        html = """
        <html>
            <body>
                <iframe src="https://example.com/embed1" width="600" height="400"></iframe>
                <iframe src="https://example.com/embed2" width="600" height="400"></iframe>
            </body>
        </html>
        """
        result = processor.process(html)
        
        formatted_content = result.content["formatted_content"]
        assert "[iframe](https://example.com/embed1)" in formatted_content
        assert "[iframe](https://example.com/embed2)" in formatted_content

class TestInlineCodeHandling:
    """Tests for handling of inline code within content."""

    def test_inline_code_handling(self, processor):
        """Test that inline code is correctly formatted."""
        html = """
        <html>
            <body>
                <p>This is an <code>inline code</code> example.</p>
            </body>
        </html>
        """
        result = processor.process(html)
        
        formatted_content = result.content["formatted_content"]
        assert "This is an `inline code` example." in formatted_content

    def test_code_blocks_within_paragraphs(self, processor):
        """Test that code blocks within paragraphs are correctly formatted."""
        html = """
        <html>
            <body>
                <p>Here is some code: <code>print("Hello")</code></p>
            </body>
        </html>
        """
        result = processor.process(html)
        
        formatted_content = result.content["formatted_content"]
        assert 'Here is some code: `print("Hello")`' in formatted_content

class TestTableConversion:
    """Tests for conversion of HTML tables to Markdown."""

    def test_convert_table_to_markdown(self, processor):
        """Test that HTML tables are converted to Markdown tables."""
        html = """
        <html>
            <body>
                <table>
                    <thead>
                        <tr><th>Name</th><th>Age</th></tr>
                    </thead>
                    <tbody>
                        <tr><td>Alice</td><td>30</td></tr>
                        <tr><td>Bob</td><td>25</td></tr>
                    </tbody>
                </table>
            </body>
        </html>
        """
        result = processor.process(html)
        
        formatted_content = result.content["formatted_content"]
        assert "| Name | Age |\n| --- | --- |\n| Alice | 30 |\n| Bob | 25 |" in formatted_content

    def test_convert_table_with_custom_attributes(self, processor):
        """Test table conversion with colspan, rowspan, and complex content."""
        html = """
        <table class="custom-table">
            <thead>
                <tr>
                    <th colspan="2">Merged Header</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td rowspan="2">Spanned Cell</td>
                    <td><strong>Bold Text</strong></td>
                </tr>
                <tr>
                    <td><em>Italic Text</em></td>
                </tr>
            </tbody>
        </table>
        """
        markdown = processor._convert_table_to_markdown(BeautifulSoup(html, 'html.parser').find('table'))
        assert "| Merged Header |" in markdown
        assert "| --- | --- |" in markdown
        assert "| Spanned Cell | Bold Text |" in markdown
        assert "| Italic Text |" in markdown

class TestInlineStyles:
    """Tests for removal of inline styles from content."""

    def test_processor_with_inline_styles(self, processor):
        """Test that inline styles are removed from content."""
        html = """
        <html>
            <body>
                <p style="color:red;">Red text.</p>
                <p style="font-size:20px;">Large text.</p>
            </body>
        </html>
        """
        result = processor.process(html)
        
        # Inline styles should be removed, text should remain
        assert "Red text." in result.content["formatted_content"]
        assert "Large text." in result.content["formatted_content"]
        assert 'style="color:red;"' not in result.content["formatted_content"]
        assert 'style="font-size:20px;"' not in result.content["formatted_content"]

    def test_inline_styles_within_allowed_tags(self, processor):
        """Test that inline styles within allowed tags are removed but content remains."""
        html = """
        <html>
            <body>
                <p style="color:blue;">Blue text.</p>
                <strong style="font-weight:normal;">Normal Weight</strong>
            </body>
        </html>
        """
        result = processor.process(html)
        
        formatted_content = result.content["formatted_content"]
        assert "Blue text." in formatted_content
        assert "**Normal Weight**" in formatted_content
        assert 'style="color:blue;"' not in formatted_content
        assert 'style="font-weight:normal;"' not in formatted_content

class TestEmptyElements:
    """Tests for handling of empty HTML elements."""

    def test_empty_paragraphs(self, processor):
        """Test that empty paragraphs are handled correctly."""
        html = """
        <html>
            <body>
                <p></p>
                <p>Non-empty paragraph.</p>
                <p></p>
            </body>
        </html>
        """
        result = processor.process(html)
        
        assert "Non-empty paragraph." in result.content["formatted_content"]
        # No content from empty paragraphs
        assert result.content["formatted_content"].count("<p></p>") == 0

    def test_tables_with_no_content(self, processor):
        """Test that tables without content are handled gracefully."""
        html = """
        <html>
            <body>
                <table></table>
            </body>
        </html>
        """
        result = processor.process(html)
        
        formatted_content = result.content["formatted_content"]
        # Empty table should not appear
        assert "|" not in formatted_content

    def test_media_without_source(self, processor):
        """Test that media tags without source attributes are handled."""
        html = """
        <html>
            <body>
                <video controls></video>
                <audio controls></audio>
            </body>
        </html>
        """
        result = processor.process(html)
        
        assets = result.assets
        # No sources should be collected
        assert not assets["media"]
        
        formatted_content = result.content["formatted_content"]
        # Video without src should not appear
        assert "![video](#)" not in formatted_content

class TestMultipleTitles:
    """Tests for handling multiple title tags in HTML."""

    def test_multiple_titles(self, processor):
        """Test that the processor handles multiple title tags correctly."""
        html = """
        <html>
            <head>
                <title>First Title</title>
            </head>
            <body>
                <title>Second Title</title>
                <p>Content.</p>
            </body>
        </html>
        """
        result = processor.process(html)
        
        # Should prioritize the first title in the head
        assert_metadata(result.metadata, "title", "First Title")
        formatted_content = result.content["formatted_content"]
        # The second title should be treated as text
        assert "Second Title" in formatted_content

class TestCodeBlockHandling:
    """Tests for handling of various code block scenarios."""

    def test_code_blocks_with_different_indentation(self, processor):
        """Test that code blocks with different indentation levels are correctly formatted."""
        html = """
        <html>
            <body>
                <pre><code class="language-python">
    def foo():
        print("Hello, World!")
                </code></pre>
            </body>
        </html>
        """
        result = processor.process(html)
        
        formatted_content = result.content["formatted_content"]
        assert "```python\ndef foo():\n    print(\"Hello, World!\")\n```" in formatted_content

    def test_code_blocks_without_language(self, processor):
        """Test that code blocks without language classes are handled."""
        html = """
        <html>
            <body>
                <pre><code>print("Hello, World!")</code></pre>
            </body>
        </html>
        """
        result = processor.process(html)
        
        formatted_content = result.content["formatted_content"]
        # Code block without language should not have language specifier
        assert "```\nprint(\"Hello, World!\")\n```" in formatted_content

    def test_multiple_code_blocks(self, processor):
        """Test that multiple code blocks are correctly formatted."""
        html = """
        <html>
            <body>
                <pre><code class="language-python">def foo(): pass</code></pre>
                <pre><code class="language-javascript">function foo() {}</code></pre>
            </body>
        </html>
        """
        result = processor.process(html)
        
        formatted_content = result.content["formatted_content"]
        assert "```python\ndef foo(): pass\n```" in formatted_content
        assert "```javascript\nfunction foo() {}\n```" in formatted_content

    def test_code_blocks_with_unsupported_languages(self, processor):
        """Test that code blocks with unsupported languages are handled appropriately."""
        html = """
        <html>
            <body>
                <pre><code class="language-go">package main</code></pre>
                <pre><code class="language-python">print("Hello, Python!")</code></pre>
            </body>
        </html>
        """
        config = {
            'code_languages': ['python']
        }
        processor.configure(config)
        result = processor.process(html)
        
        formatted_content = result.content["formatted_content"]
        # 'go' is not in allowed code languages, should not be processed
        assert "```go\npackage main\n```" not in formatted_content
        # 'python' is allowed
        assert "```python\nprint(\"Hello, Python!\")\n```" in formatted_content

class TestMetadataExtractionVariations:
    """Tests for various metadata extraction scenarios."""

    def test_metadata_extraction_with_all_types(self, processor):
        """Test metadata extraction with all supported types."""
        html = """
        <html>
            <head>
                <!-- Standard meta tags -->
                <title>Page Title</title>
                <meta name="description" content="Page description">
                <meta name="keywords" content="key1, key2, key3">
                <meta name="author" content="Author Name">

                <!-- OpenGraph meta tags -->
                <meta property="og:title" content="OG Title">
                <meta property="og:description" content="OG description">
                <meta property="og:image" content="https://example.com/image.jpg">
                <meta property="og:url" content="https://example.com/page">

                <!-- Twitter Card meta tags -->
                <meta name="twitter:card" content="summary">
                <meta name="twitter:title" content="Twitter Title">
                <meta name="twitter:description" content="Twitter description">
                <meta name="twitter:image" content="https://example.com/twitter.jpg">

                <!-- Dublin Core meta tags -->
                <meta name="dc.title" content="DC Title">
                <meta name="dc.creator" content="DC Creator">
                <meta name="dc.subject" content="DC Subject">

                <!-- Custom meta tags -->
                <meta name="custom-tag" content="Custom value">
                <meta property="custom:property" content="Property value">
            </head>
            <body>
                <h1>Page Content</h1>
                <p>Content here.</p>
            </body>
        </html>
        """
        result = processor.process(html)
    
        # Check standard meta
        assert_metadata(result.metadata, "title", "Page Title")
        assert_metadata(result.metadata, "description", "Page description")
        assert "key1" in result.metadata["keywords"].split(", ")
        assert_metadata(result.metadata, "author", "Author Name")
        
        # Check OpenGraph
        assert_metadata(result.metadata, "og:title", "OG Title")
        assert_metadata(result.metadata, "og:description", "OG description")
        assert_metadata(result.metadata, "og:image", "https://example.com/image.jpg")
        assert_metadata(result.metadata, "og:url", "https://example.com/page")
        
        # Check Twitter Card
        assert_metadata(result.metadata, "twitter:card", "summary")
        assert_metadata(result.metadata, "twitter:title", "Twitter Title")
        assert_metadata(result.metadata, "twitter:description", "Twitter description")
        assert_metadata(result.metadata, "twitter:image", "https://example.com/twitter.jpg")
        
        # Check Dublin Core
        assert_metadata(result.metadata, "dc.title", "DC Title")
        assert_metadata(result.metadata, "dc.creator", "DC Creator")
        assert_metadata(result.metadata, "dc.subject", "DC Subject")
        
        # Check Custom meta
        assert_metadata(result.metadata, "custom-tag", "Custom value")
        assert_metadata(result.metadata, "custom:property", "Property value")

    def test_metadata_extraction_with_case_sensitivity(self, processor):
        """Test that metadata keys are case-insensitive and stored in lowercase."""
        html = """
        <html>
            <head>
                <title>Case Sensitivity Test</title>
                <meta name="Description" content="Uppercase Description">
                <meta property="OG:Title" content="Uppercase OG Title">
            </head>
            <body>
                <p>Content here.</p>
            </body>
        </html>
        """
        result = processor.process(html)
        
        # Metadata keys should be in lowercase
        assert_metadata(result.metadata, "description", "Uppercase Description")
        assert_metadata(result.metadata, "og:title", "Uppercase OG Title")

    def test_metadata_extraction_with_microdata(self, processor):
        """Test processing of HTML with microdata."""
        html = """
        <html>
            <head>
                <title>Microdata Test</title>
                <meta name="description" content="Testing microdata extraction.">
            </head>
            <body>
                <div itemscope itemtype="https://schema.org/Person">
                    <meta itemprop="name" content="John Doe">
                    <meta itemprop="jobTitle" content="Software Engineer">
                    <p>About John Doe.</p>
                </div>
            </body>
        </html>
        """
        result = processor.process(html)
        
        assert_metadata(result.metadata, "name", "John Doe")
        assert_metadata(result.metadata, "jobtitle", "Software Engineer")
        assert "About John Doe." in result.content["formatted_content"]

    def test_metadata_extraction_with_meta_redirects(self, processor):
        """Test metadata extraction of meta refresh redirects."""
        html = """
        <html>
            <head>
                <meta http-equiv="refresh" content="5; URL='https://example.com/redirected-page'">
                <meta http-equiv="refresh" content="10; URL='https://example.com/another-page'">
            </head>
            <body>
                <p>Redirecting...</p>
            </body>
        </html>
        """
        result = processor.process(html)
        
        redirects = result.metadata.get("meta_redirects", [])
        assert "https://example.com/redirected-page" in redirects
        assert "https://example.com/another-page" in redirects

class TestAdditionalFeatures:
    """Additional tests covering other functionalities."""

    def test_processor_with_multiple_custom_configurations(self, processor):
        """Test processor with multiple custom configurations."""
        config = {
            'allowed_tags': ['p', 'a', 'strong', 'em', 'code'],
            'max_heading_level': 5,
            'preserve_whitespace_elements': ['pre', 'code'],
            'code_languages': ['python', 'javascript'],
            'sanitize_urls': True,
            'metadata_prefixes': ['custom:', 'app:'],
            'extract_comments': True
        }
        processor.configure(config)
    
        html = """
        <html>
            <head>
                <title>Custom Config Test</title>
                <meta name="custom:meta" content="Custom Meta Value">
            </head>
            <body>
                <h1>Heading 1</h1>
                <h5>Heading 5</h5>
                <p>Paragraph with <strong>bold</strong> and <em>italic</em> text.</p>
                <pre><code class="python">print("Hello, Python!")</code></pre>
                <pre><code class="ruby">puts "Hello, Ruby!"</code></pre>
                <a href="https://example.com">Valid Link</a>
                <a href="javascript:alert('XSS')">Bad Link</a>
                <!-- Extracted Comment -->
            </body>
        </html>
        """
        result = processor.process(html, base_url='https://example.com')
    
        # Check headings
        headings = result.content["headings"]
        assert any(h["text"] == "Heading 1" and h["level"] == 1 for h in headings)
        assert any(h["text"] == "Heading 5" and h["level"] == 5 for h in headings)
    
        # Check allowed tags
        assert "**bold**" in result.content["formatted_content"]
        assert "_italic_" in result.content["formatted_content"]
    
        # Check code blocks
        assert "```python\nprint(\"Hello, Python!\")\n```" in result.content["formatted_content"]
        assert "```ruby\nputs \"Hello, Ruby!\"\n```" not in result.content["formatted_content"]  # 'ruby' not allowed
    
        # Check URL sanitization
        assert "[Bad Link](#)" in result.content["formatted_content"]
        assert "[Valid Link](https://example.com)" in result.content["formatted_content"]
    
        # Check metadata prefixes
        assert_metadata(result.metadata, "custom:meta", "Custom Meta Value")
    
        # Check comments extraction
        assert "<!-- Extracted Comment -->" in result.content["formatted_content"]

    def test_processor_with_multiple_custom_configurations_duplicate(self, processor):
        """Duplicate test for processor with multiple custom configurations."""
        # This test appears to be a duplicate in the original test suite.
        # Ensure that it is handled appropriately.
        config = {
            'allowed_tags': ['p', 'a', 'strong', 'em', 'code'],
            'max_heading_level': 5,
            'preserve_whitespace_elements': ['pre', 'code'],
            'code_languages': ['python', 'javascript'],
            'sanitize_urls': True,
            'metadata_prefixes': ['custom:', 'app:'],
            'extract_comments': True
        }
        processor.configure(config)
    
        html = """
        <html>
            <head>
                <title>Custom Config Test</title>
                <meta name="custom:meta" content="Custom Meta Value">
            </head>
            <body>
                <h1>Heading 1</h1>
                <h5>Heading 5</h5>
                <p>Paragraph with <strong>bold</strong> and <em>italic</em> text.</p>
                <pre><code class="python">print("Hello, Python!")</code></pre>
                <pre><code class="ruby">puts "Hello, Ruby!"</code></pre>
                <a href="https://example.com">Valid Link</a>
                <a href="javascript:alert('XSS')">Bad Link</a>
                <!-- Extracted Comment -->
            </body>
        </html>
        """
        result = processor.process(html, base_url='https://example.com')
    
        # The assertions are identical to the previous test
        headings = result.content["headings"]
        assert any(h["text"] == "Heading 1" and h["level"] == 1 for h in headings)
        assert any(h["text"] == "Heading 5" and h["level"] == 5 for h in headings)
    
        assert "**bold**" in result.content["formatted_content"]
        assert "_italic_" in result.content["formatted_content"]
    
        assert "```python\nprint(\"Hello, Python!\")\n```" in result.content["formatted_content"]
        assert "```ruby\nputs \"Hello, Ruby!\"\n```" not in result.content["formatted_content"]  # 'ruby' not allowed
    
        assert "[Bad Link](#)" in result.content["formatted_content"]
        assert "[Valid Link](https://example.com)" in result.content["formatted_content"]
    
        assert_metadata(result.metadata, "custom:meta", "Custom Meta Value")
    
        assert "<!-- Extracted Comment -->" in result.content["formatted_content"]

class TestComprehensiveIntegration:
    """Integration tests combining multiple features."""

    def test_process_with_mixed_content_types(self, processor):
        """Test that various content types (lists, tables, code blocks) are processed correctly."""
        html = """
        <html>
            <body>
                <h1>Heading</h1>
                <p>Paragraph with <strong>bold</strong> text.</p>
                <ul>
                    <li>List item 1</li>
                    <li>List item 2</li>
                </ul>
                <pre><code>print("Hello, World!")</code></pre>
                <table>
                    <tr><th>Header</th></tr>
                    <tr><td>Data</td></tr>
                </table>
                <blockquote>
                    <p>This is a quote.</p>
                </blockquote>
                <code>Inline code</code>
            </body>
        </html>
        """
        result = processor.process(html)
        
        formatted_content = result.content["formatted_content"]
        assert "# Heading" in formatted_content
        assert "**bold**" in formatted_content
        assert "- List item 1" in formatted_content
        assert "- List item 2" in formatted_content
        assert "```python\nprint(\"Hello, World!\")\n```" in formatted_content
        assert "| Header |\n| --- |\n| Data |" in formatted_content
        assert "> This is a quote." in formatted_content
        assert "`Inline code`" in formatted_content

    def test_complex_nested_structures(self, processor):
        """Test that complex nested HTML structures are processed correctly."""
        html = """
        <html>
            <body>
                <div>
                    <section>
                        <article>
                            <div>
                                <p>Deeply nested paragraph.</p>
                                <ul>
                                    <li>Nested list item</li>
                                </ul>
                            </div>
                        </article>
                    </section>
                </div>
            </body>
        </html>
        """
        result = processor.process(html)
        
        formatted_content = result.content["formatted_content"]
        assert "Deeply nested paragraph." in formatted_content
        assert "- Nested list item" in formatted_content

    def test_nested_code_blocks(self, processor):
        """Test that nested code blocks are correctly formatted."""
        html = """
        <html>
            <body>
                <pre><code class="language-python">
    def outer():
        <pre><code class="language-python">
        def inner():
            pass
        </code></pre>
                </code></pre>
            </body>
        </html>
        """
        result = processor.process(html)
        
        formatted_content = result.content["formatted_content"]
        # Depending on markdownify's handling, nested code blocks might not be supported
        # Adjust expectations accordingly
        assert "```python\ndef outer():\n    ```python\ndef inner():\n    pass\n    ```\n```" in formatted_content

    def test_nested_code_blocks_integration(self, processor):
        """Integration test for nested code blocks."""
        html = """
        <html>
            <body>
                <pre><code class="language-python">def foo():
    def bar():
        pass
    return bar
                </code></pre>
            </body>
        </html>
        """
        result = processor.process(html)
        
        formatted_content = result.content["formatted_content"]
        expected = "```python\ndef foo():\n    def bar():\n        pass\n    return bar\n```"
        assert expected in formatted_content

class TestAssetDuplicates:
    """Tests for handling duplicate asset URLs."""

    def test_multiple_images_same_src(self, processor):
        """Test that multiple images with the same src are handled correctly."""
        html = """
        <html>
            <body>
                <img src="image.jpg" alt="Image">
                <img src="image.jpg" alt="Duplicate Image">
            </body>
        </html>
        """
        result = processor.process(html, base_url='https://example.com')
        
        assets = result.assets
        # Images should be collected twice
        assert assets["images"].count("https://example.com/image.jpg") == 2
        formatted_content = result.content["formatted_content"]
        assert "![Image](https://example.com/image.jpg)" in formatted_content
        assert "![Duplicate Image](https://example.com/image.jpg)" in formatted_content

    def test_multiple_scripts_styles(self, processor):
        """Test that multiple scripts and stylesheets are correctly collected."""
        html = """
        <html>
            <head>
                <link rel="stylesheet" href="style1.css">
                <link rel="stylesheet" href="style2.css">
                <script src="script1.js"></script>
                <script src="script2.js"></script>
            </head>
            <body>
                <p>Content with multiple styles and scripts.</p>
            </body>
        </html>
        """
        result = processor.process(html, base_url='https://example.com')
        
        assets = result.assets
        assert "https://example.com/style1.css" in assets["stylesheets"]
        assert "https://example.com/style2.css" in assets["stylesheets"]
        assert "https://example.com/script1.js" in assets["scripts"]
        assert "https://example.com/script2.js" in assets["scripts"]

    def test_multiple_meta_same_name(self, processor):
        """Test that multiple meta tags with the same name are handled correctly."""
        html = """
        <html>
            <head>
                <title>Meta Test</title>
                <meta name="keywords" content="keyword1, keyword2">
                <meta name="keywords" content="keyword3, keyword4">
            </head>
        </html>
        """
        result = processor.process(html)
        
        # Assuming last occurrence overwrites
        assert_metadata(result.metadata, "keywords", "keyword3, keyword4")

# --------------------
# Additional Edge Case Tests
# --------------------

class TestAdditionalEdgeCases:
    """Additional edge case tests for the processor."""

    def test_images_with_empty_src(self, processor):
        """Test that images with empty src attributes are handled gracefully."""
        html = """
        <html>
            <body>
                <img src="" alt="Empty Src Image">
            </body>
        </html>
        """
        result = processor.process(html)
        
        assets = result.assets
        # Images with empty src should not be collected
        assert not assets["images"]
        
        formatted_content = result.content["formatted_content"]
        # Image with empty src should not appear
        assert "![Empty Src Image](#)" not in formatted_content

    def test_images_with_special_characters_in_src(self, processor):
        """Test that images with special characters in src are handled correctly."""
        html = """
        <html>
            <body>
                <img src="https://example.com/image name.jpg" alt="Image with Space">
                <img src="https://example.com/image%20encoded.jpg" alt="Image with Encoded Space">
            </body>
        </html>
        """
        result = processor.process(html)
        
        formatted_content = result.content["formatted_content"]
        assert "![Image with Space](https://example.com/image name.jpg)" in formatted_content
        assert "![Image with Encoded Space](https://example.com/image%20encoded.jpg)" in formatted_content

    def test_links_with_fragment_identifiers(self, processor):
        """Test that links with fragment identifiers are correctly formatted."""
        html = """
        <html>
            <body>
                <a href="https://example.com/page#section">Section Link</a>
                <a href="#top">Top Link</a>
            </body>
        </html>
        """
        result = processor.process(html, base_url='https://example.com/page')
        
        formatted_content = result.content["formatted_content"]
        assert "[Section Link](https://example.com/page#section)" in formatted_content
        assert "[Top Link](https://example.com/page#top)" in formatted_content

    def test_links_with_special_characters(self, processor):
        """Test that links with special characters are correctly formatted."""
        html = """
        <html>
            <body>
                <a href="https://example.com/page?name=John Doe&age=30">John's Page</a>
            </body>
        </html>
        """
        result = processor.process(html)
        
        formatted_content = result.content["formatted_content"]
        assert "[John's Page](https://example.com/page?name=John Doe&age=30)" in formatted_content

    def test_links_with_no_text(self, processor):
        """Test that links without text are handled correctly."""
        html = """
        <html>
            <body>
                <a href="https://example.com"></a>
            </body>
        </html>
        """
        result = processor.process(html)
        
        formatted_content = result.content["formatted_content"]
        # Link with no text might appear as empty or with placeholder
        assert "[](https://example.com)" in formatted_content

# --------------------
# Summary
# --------------------