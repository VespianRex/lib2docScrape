import unittest
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

class TestBasicFunctionality(unittest.TestCase):
    """Tests for basic content extraction and processing."""

    def test_extract_text_basic(self):
        """Test basic text extraction from HTML."""
        html = "<html><body><h1>Title</h1><p>This is a paragraph.</p></body></html>"
        processor = ContentProcessor()
        result = processor.process(html)

        print(f"DEBUG: formatted_content: {result.content['formatted_content']}") # Debug print statement
        assert result.title == "Title"
        assert "This is a paragraph." in result.content["formatted_content"]

    def test_process_basic(self):
        """Test processing of basic HTML content."""
        html = "<html><head><title>Test Document</title></head><body><p>Content here.</p></body></html>"
        processor = ContentProcessor()
        result = processor.process(html)

        assert result.title == "Test Document"
        assert "Content here." in result.content["formatted_content"]
        assert not result.errors

    def test_format_as_markdown(self):
        """Test markdown formatting functionality."""
        html = "<html><body><h1>Title</h1><p>Paragraph.</p></body></html>"
        processor = ContentProcessor()
        result = processor.process(html)

        expected_markdown = "# Title\n\nParagraph."
        assert result.content["formatted_content"] == expected_markdown

    def test_extract_text_with_nested_content(self):
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
        processor = ContentProcessor()
        result = processor.process(html)

        assert "Deeply nested paragraph." in result.content["formatted_content"]

    def test_extract_text_with_special_characters(self):
        """Test text extraction handling special HTML entities."""
        html = """
        <html>
            <body>
                <p>Special characters: &amp;, <, >, ", &#39;</p>
            </body>
        </html>
        """
        processor = ContentProcessor()
        result = processor.process(html)

        assert "Special characters: &, <, >, \", '" in result.content["formatted_content"]

    def test_extract_text_with_complex_content(self):
        """Test text extraction from HTML with complex nested structures."""
        processor = ContentProcessor()
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

    def test_extract_text_with_mixed_content_types(self):
        """Test text extraction from HTML with mixed content types."""
        processor = ContentProcessor()
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
        assert "* Unordered list item" in result.content["formatted_content"]
        assert "1. Ordered list item" in result.content["formatted_content"]
        self.assertIn("```python\nprint(\"Hello\")\n```", result.content["formatted_content"])
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
        # Java is included in allowed languages, so it should be processed
        assert "```java\nSystem.out.println(\"Hello, World!\");\n```" in result.content["formatted_content"]

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
        # Note: 'description' is overwritten by microdata 'description'

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
                <link rel="stylesheet" href="https://example.com/styles.css"/>
                <script src="app.js"></script>
            </head>
            <body>
                <img src="image.png" alt="Image"/>
                <video src="video.mp4"></video>
                <audio src="audio.mp3"></audio>
                <source src="media.webm" type="video/webm">
            </body>
        </html>
        """
        result = processor.process(html, base_url="https://example.com")

        assert_asset(result.assets, "stylesheets", "https://example.com/styles.css")
        assert_asset(result.assets, "scripts", "https://example.com/app.js")
        assert_asset(result.assets, "images", "https://example.com/image.png")
        assert_asset(result.assets, "media", "https://example.com/video.mp4")
        assert_asset(result.assets, "media", "https://example.com/audio.mp3")
        assert_asset(result.assets, "media", "https://example.com/media.webm")

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
                <link rel="stylesheet" href="https://example.com/styles.css">
            </body>
        </html>
        """
        result = processor.process(html, base_url='https://example.com')

        assert "https://example.com/styles.css" in result.assets["stylesheets"]
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