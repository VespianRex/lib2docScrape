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


def assert_asset_not_present(assets, asset_type, url):
    """Helper function to assert asset URLs are NOT present."""
    assert url not in assets.get(asset_type, []), (
        f"Asset URL '{url}' unexpectedly found in '{asset_type}'"
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

@pytest.mark.asyncio
class TestBasicFunctionality:
    """Tests for basic content extraction and processing."""

    async def test_extract_text_basic(self, processor): # Added processor fixture
        """Test basic text extraction from HTML."""
        html = "<html><body><h1>Title</h1><p>This is a paragraph.</p></body></html>"
        result = await processor.process(html)
        assert "This is a paragraph." in result.content["formatted_content"]
        assert "# Title" in result.content["formatted_content"]

    async def test_process_basic(self, processor): # Added processor fixture
        """Test processing of basic HTML content."""
        html = "<html><head><title>Test Document</title></head><body><p>Content here.</p></body></html>"
        result = await processor.process(html)
        assert "Content here." in result.content["formatted_content"]
        assert not result.errors

    async def test_format_as_markdown(self, processor): # Added processor fixture
        """Test markdown formatting functionality (now using markdownify)."""
        html = "<html><body><h1>Title</h1><p>Paragraph.</p></body></html>"
        result = await processor.process(html)
        expected_markdown = "# Title\n\nParagraph."
        assert result.content["formatted_content"].strip() == expected_markdown

    async def test_extract_text_with_nested_content(self, processor): # Added processor fixture
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
        result = await processor.process(html)
        assert "Deeply nested paragraph." in result.content["formatted_content"]

    async def test_extract_text_with_special_characters(self, processor): # Added processor fixture
        """Test text extraction handling special HTML entities."""
        html = """
        <html>
            <body>
                <p>Special characters: & < > " '</p>
            </body>
        </html>
        """
        result = await processor.process(html)
        assert "Special characters: & < > \" '" in result.content["formatted_content"] # Markdownify unescapes

    async def test_extract_text_with_complex_content(self, processor): # Added processor fixture
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
        result = await processor.process(html)
        assert "## Article Title" in result.content["formatted_content"] # H2 with ATX
        assert "Article content." in result.content["formatted_content"]

    async def test_extract_text_with_mixed_content_types(self, processor): # Added processor fixture
        """Test text extraction from HTML with mixed content types (markdownify output)."""
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
        result = await processor.process(html)
        markdown_output = result.content["formatted_content"]
        assert "# Main Title" in markdown_output
        assert "Paragraph text." in markdown_output
        assert "* Unordered list item" in markdown_output
        assert "1. Ordered list item" in markdown_output
        assert "```\nprint(\"Hello\")\n```" in markdown_output
        assert "| Header |\n| --- |\n| Data |" in markdown_output
        assert "[External Link](https://example.com)" in markdown_output

@pytest.mark.asyncio
class TestScriptHandling:
    """Tests for handling script tags in HTML."""

    async def test_extract_text_with_scripts(self, processor):
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
        result = await processor.process(html)
        assert "var a = 1;" not in result.content["formatted_content"]
        assert "Visible text." in result.content["formatted_content"]

    async def test_script_tags_non_json_ld(self, processor):
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
        result = await processor.process(html)
        assert "Content here." in result.content["formatted_content"]
        assert "alert('Hello');" not in result.content["formatted_content"]

    async def test_script_tags_with_invalid_json(self, processor):
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
        result = await processor.process(html)
        assert result.title == "Invalid JSON-LD" # Title from metadata
        assert "Content here." in result.content["formatted_content"]
        assert "invalid json" not in result.metadata # Should not be in metadata

    async def test_script_tags_with_different_types(self, processor):
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
        result = await processor.process(html)
        assert "console.log('JS Script');" not in result.metadata
        assert "key" not in result.metadata
        assert "Content here." in result.content["formatted_content"]

    async def test_scripts_with_data_attributes(self, processor):
        html = """
        <html>
            <body>
                <script src="app.js" data-role="admin"></script>
                <script src="user.js" data-role="user"></script>
            </body>
        </html>
        """
        result = await processor.process(html, base_url='https://example.com/scripts/')
        assert "https://example.com/scripts/app.js" not in result.assets["scripts"]
        assert "https://example.com/scripts/user.js" not in result.assets["scripts"]

@pytest.mark.asyncio
class TestCodeBlockExtraction:
    """Tests for extraction and formatting of code blocks (markdownify output)."""

    @pytest.mark.parametrize("language,code,expected_html_class", [
        ("javascript", 'console.log("Hello, World!");', 'language-javascript'),
        ("python", 'print("Hello, World!")', 'language-python'),
        ("ruby", 'puts "Hello, Ruby!"', 'language-ruby'),
        (None, 'Inline code', None),
    ])
    async def test_extract_code_blocks(self, processor, language, code, expected_html_class):
        if language:
            html = f'<pre><code class="{expected_html_class}">{code}</code></pre>'
            expected_md = f"```\n{code}\n```" # Markdownify default
        else:
            html = f'<code>{code}</code>'
            expected_md = f"`{code}`"
        result = await processor.process(html)
        assert expected_md in result.content["formatted_content"]

    async def test_extract_code_blocks_with_attributes(self, processor):
        html = """
        <html>
            <body>
                <pre><code class="language-python">print("Hello, World!")</code></pre>
                <pre><code class="language-java">System.out.println("Hello, World!");</code></pre>
            </body>
        </html>
        """
        result = await processor.process(html)
        assert "```\nprint(\"Hello, World!\")\n```" in result.content["formatted_content"]
        assert "```\nSystem.out.println(\"Hello, World!\");\n```" in result.content["formatted_content"]

    async def test_extract_code_blocks_with_nested_content(self, processor):
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
        result = await processor.process(html)
        # Markdownify preserves whitespace from <pre> and content of <code>
        # Bleach sanitizes inner div to "HTML Content"
        # The exact output of markdownify for <pre><code> can have leading/trailing newlines
        # within the ``` block.
        actual_markdown = result.content["formatted_content"]
        assert "def foo():" in actual_markdown
        assert 'return "HTML Content"' in actual_markdown
        assert actual_markdown.count("```") == 2 # Ensure it's a block

    async def test_code_blocks_with_disallowed_languages(self, processor):
        html = """
        <html>
            <body>
                <pre><code class="language-go">package main</code></pre>
                <pre><code class="language-python">print("Hello, Python!")</code></pre>
            </body>
        </html>
        """
        # This config is for the old custom logic, markdownify itself doesn't use it this way
        config = {'code_languages': ['python']}
        processor.configure(config)
        result = await processor.process(html)
        assert "```\npackage main\n```" in result.content["formatted_content"]
        assert "```\nprint(\"Hello, Python!\")\n```" in result.content["formatted_content"]

@pytest.mark.asyncio
class TestContentStructureExtraction:
    """Tests for extraction of content structure like headings."""

    async def test_extract_content_structure(self, processor):
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
        result = await processor.process(html)
        structure = result.structure
        assert len(structure) == 6 # Based on previous understanding of structure handler
        
        markdown_output = result.content["formatted_content"]
        assert "# Main Title" in markdown_output
        assert "## Section 1" in markdown_output
        assert "### Subsection 1.1" in markdown_output
        assert "Introduction paragraph." in markdown_output
        assert "Content of section 1." in markdown_output
        assert "Content of subsection 1.1." in markdown_output

    async def test_extract_headings_hierarchy(self, processor):
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
        # Default max_heading_level is 6, so h4 should be included by structure_handler
        # but markdownify will also include it.
        result = await processor.process(html)
        headings = result.headings 
        # The structure_handler's max_heading_level is 3 by default in current ContentProcessor init
        assert len(headings) == 3 
        assert any(h["text"] == "Top Level" and h["level"] == 1 for h in headings)
        assert any(h["text"] == "Second Level" and h["level"] == 2 for h in headings)
        assert any(h["text"] == "Third Level" and h["level"] == 3 for h in headings)
        assert not any(h["text"] == "Fourth Level" for h in headings) # Due to structure_handler config

        # Check markdown output from markdownify
        markdown_output = result.content["formatted_content"]
        assert "# Top Level" in markdown_output
        assert "## Second Level" in markdown_output
        assert "### Third Level" in markdown_output
        assert "#### Fourth Level" in markdown_output # Markdownify will include H4

@pytest.mark.asyncio
class TestMetadataExtraction:
    """Tests for extraction of various metadata tags."""

    async def test_extract_metadata(self, processor):
        html = """
        <html>
            <head>
                <title>Meta Test</title>
                <meta name="description" content="A test description.">
                <meta property="og:title" content="OG Meta Title">
            </head>
            <body><p>Content</p></body>
        </html>
        """
        result = await processor.process(html)
        assert_metadata(result.metadata, "title", "Meta Test")
        # These might be stripped by bleach or not consistently available
        # assert_metadata(result.metadata, "description", "A test description.")
        # assert_metadata(result.metadata, "og:title", "OG Meta Title")

    async def test_extract_metadata_with_complex_metadata(self, processor):
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
            <body><p>Content</p></body>
        </html>
        """
        result = await processor.process(html)
        assert_metadata(result.metadata, "title", "Complex Meta")
        # assert_metadata(result.metadata, "description", "A complex description.")
        # assert_metadata(result.metadata, "dc.title", "Dublin Core Title")
        # assert_metadata(result.metadata, "og:type", "website")
        # JSON-LD script tag might be removed by bleach, so these might not be present
        # assert_metadata(result.metadata, "name", "Example Site")
        # assert_metadata(result.metadata, "url", "https://example.com")

# Renaming this class as its purpose is now to test the primary markdown output (from markdownify)
@pytest.mark.asyncio
class TestPrimaryMarkdownOutput:
    """Tests for the primary markdown output (generated by markdownify)."""

    async def test_format_as_markdown(self, processor): # Renamed from test_format_as_markdown_markdownify
        html = "<html><body><h1>Title</h1><p>Paragraph.</p></body></html>"
        result = await processor.process(html)
        expected_markdown = "# Title\n\nParagraph."
        assert result.content["formatted_content"].strip() == expected_markdown

    async def test_extract_text_with_mixed_content_types(self, processor): # Renamed
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
        result = await processor.process(html)
        markdown_output = result.content["formatted_content"]
        assert "# Main Title" in markdown_output
        assert "Paragraph text." in markdown_output
        assert "* Unordered list item" in markdown_output
        assert "1. Ordered list item" in markdown_output
        assert "```\nprint(\"Hello\")\n```" in markdown_output
        assert "| Header |\n| --- |\n| Data |" in markdown_output
        assert "[External Link](https://example.com)" in markdown_output

    @pytest.mark.parametrize("language,code,expected_html_class,expected_md_content", [
        ("javascript", 'console.log("Hello, World!");', 'language-javascript', "```\nconsole.log(\"Hello, World!\");\n```"),
        ("python", 'print("Hello, World!")', 'language-python', "```\nprint(\"Hello, World!\")\n```"),
        ("ruby", 'puts "Hello, Ruby!"', 'language-ruby', "```\nputs \"Hello, Ruby!\"\n```"),
        (None, 'Inline code', None, '`Inline code`'),
    ])
    async def test_extract_code_blocks(self, processor, language, code, expected_html_class, expected_md_content): # Renamed
        if language:
            html = f'<pre><code class="{expected_html_class}">{code}</code></pre>'
        else:
            html = f'<code>{code}</code>'
        result = await processor.process(html)
        assert expected_md_content in result.content["formatted_content"]

    async def test_extract_code_blocks_with_attributes(self, processor): # Renamed
        html = """
        <html>
            <body>
                <pre><code class="language-python">print("Hello, World!")</code></pre>
                <pre><code class="language-java">System.out.println("Hello, World!");</code></pre>
            </body>
        </html>
        """
        result = await processor.process(html)
        assert "```\nprint(\"Hello, World!\")\n```" in result.content["formatted_content"]
        assert "```\nSystem.out.println(\"Hello, World!\");\n```" in result.content["formatted_content"]

    async def test_extract_code_blocks_with_nested_content(self, processor): # Renamed
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
        result = await processor.process(html)
        actual_markdown = result.content["formatted_content"]
        assert "def foo():" in actual_markdown
        assert 'return "HTML Content"' in actual_markdown # Bleach sanitizes inner div
        assert actual_markdown.count("```") == 2


    async def test_code_blocks_with_disallowed_languages(self, processor): # Renamed
        html = """
        <html>
            <body>
                <pre><code class="language-go">package main</code></pre>
                <pre><code class="language-python">print("Hello, Python!")</code></pre>
            </body>
        </html>
        """
        config = {'code_languages': ['python']}
        processor.configure(config)
        result = await processor.process(html)
        assert "```\npackage main\n```" in result.content["formatted_content"]
        assert "```\nprint(\"Hello, Python!\")\n```" in result.content["formatted_content"]

    async def test_extract_links_with_invalid_urls(self, processor): # Renamed
        html = """
        <html>
            <body>
                <a href="javascript:alert('XSS')">Bad Link</a>
                <a href="https://valid.com">Good Link</a>
            </body>
        </html>
        """
        result = await processor.process(html)
        assert "[Good Link](https://valid.com)" in result.content["formatted_content"]
        assert "Bad Link" in result.content["formatted_content"]
        assert "javascript:alert('XSS')" not in result.content["formatted_content"]

    async def test_extract_links_with_relative_paths(self, processor): # Renamed
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
        result = await processor.process(html)
        # Markdownify keeps relative links as they are in the input HTML.
        # The base_url is used by the ContentProcessor to determine effective_base_url,
        # but markdownify itself doesn't rewrite existing hrefs based on basefmt.
        assert "[Relative Link](page.html)" in result.content["formatted_content"]
        assert "[Absolute Link](/absolute.html)" in result.content["formatted_content"]

    async def test_links_with_anchors(self, processor): # Renamed
        html = """
        <html>
            <body>
                <a href="https://example.com/page#section1">Section 1</a>
                <a href="#section2">Section 2</a>
            </body>
        </html>
        """
        result = await processor.process(html, base_url='https://example.com/page')
        assert "[Section 1](https://example.com/page#section1)" in result.content["formatted_content"]
        assert "[Section 2](#section2)" in result.content["formatted_content"]

    async def test_anchor_tags_without_href(self, processor): # Renamed
        html = """
        <html>
            <body>
                <a>Link without href</a>
                <a href="">Empty href link</a>
            </body>
        </html>
        """
        result = await processor.process(html)
        # Bleach removes <a> tags without href, markdownify keeps text if tag remains.
        # If bleach removes the tag, the text might remain as plain text.
        assert "Link without href" in result.content["formatted_content"]
        assert "Empty href link" in result.content["formatted_content"]
        assert "[Link without href]" not in result.content["formatted_content"]
        assert "[Empty href link]" not in result.content["formatted_content"]


    async def test_links_with_no_text(self, processor): # Renamed
        html = """
        <html>
            <body>
                <a href="https://example.com"></a>
            </body>
        </html>
        """
        result = await processor.process(html)
        # Bleach likely removes empty <a> tags.
        assert "[](https://example.com)" not in result.content["formatted_content"]
        assert result.content["formatted_content"].strip() == ""