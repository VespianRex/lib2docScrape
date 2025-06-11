"""
Test Content Processing Improvements

This module contains failing tests that define the expected behavior for improved
content processing, specifically addressing issues found in scraped documentation:

1. Complete content extraction (no truncation)
2. Proper markdown formatting (clean output)
3. Link resolution (relative to absolute)
4. Content structure preservation (headings, code blocks)

These tests follow TDD principles - they are written to fail first, then we implement
the fixes to make them pass.
"""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.processors.content_processor import ContentProcessor  # noqa: E402


class TestContentProcessingImprovements:
    """Test suite for content processing improvements."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = ContentProcessor()

    @pytest.mark.asyncio
    async def test_complete_content_extraction_no_truncation(self):
        """
        Test that content processing extracts complete content without truncation.

        ISSUE: Current implementation truncates content at 5000 characters in demo script.
        EXPECTED: Full content should be extracted and processed.
        """
        # Create a large HTML document (larger than 5000 chars)
        large_content = """
        <html>
        <head><title>Large Documentation</title></head>
        <body>
        <h1>Introduction</h1>
        <p>This is a large documentation page that should be processed completely.</p>
        """

        # Add many paragraphs to make it large
        for i in range(100):
            large_content += f"<p>Content paragraph number {i}</p>\n"

        large_content += """
        <h2>Advanced Topics</h2>
        <p>This section contains important information that should not be truncated.</p>
        <h3>Code Examples</h3>
        <pre><code>
        def important_function():
            return "This code should be preserved"
        </code></pre>
        </body>
        </html>
        """

        # Process the content
        result = await self.processor.process(
            content=large_content, base_url="https://example.com/docs/"
        )

        # ASSERTIONS: Content should be complete, not truncated
        assert result.content is not None
        assert "formatted_content" in result.content

        formatted_content = result.content["formatted_content"]

        # Should contain all sections
        assert "Introduction" in formatted_content
        assert "Advanced Topics" in formatted_content
        assert "Code Examples" in formatted_content
        assert "important_function" in formatted_content

        # Should not be truncated (no "..." at the end)
        assert not formatted_content.endswith("...")

        # Should contain all 100 content paragraphs
        paragraph_count = formatted_content.count("Content paragraph number")
        assert paragraph_count == 100, f"Expected 100 paragraphs, got {paragraph_count}"

    @pytest.mark.asyncio
    async def test_clean_markdown_formatting_no_html_artifacts(self):
        """
        Test that markdown output is clean without HTML artifacts.

        ISSUE: Current output contains artifacts like [¶](#...) anchor links.
        EXPECTED: Clean markdown without navigation artifacts.
        """
        html_with_artifacts = """
        <html>
        <head><title>Documentation with Artifacts</title></head>
        <body>
        <h1>Main Title<a class="headerlink" href="#main-title" title="Link to this heading">¶</a></h1>
        <p>Some content with <a href="#section1">internal link</a>.</p>
        <h2>Section 1<a class="headerlink" href="#section1" title="Link to this heading">¶</a></h2>
        <p>More content here.</p>
        <div class="navigation">
            <a href="prev.html">Previous</a> | <a href="next.html">Next</a>
        </div>
        </body>
        </html>
        """

        result = await self.processor.process(
            content=html_with_artifacts, base_url="https://docs.example.com/"
        )

        formatted_content = result.content["formatted_content"]

        # Should NOT contain anchor link artifacts
        assert "¶" not in formatted_content
        assert "headerlink" not in formatted_content
        assert "Link to this heading" not in formatted_content

        # Should contain clean headings
        assert "# Main Title" in formatted_content
        assert "## Section 1" in formatted_content

        # Should contain actual content
        assert "Some content with" in formatted_content
        assert "More content here" in formatted_content

    @pytest.mark.asyncio
    async def test_relative_to_absolute_link_resolution(self):
        """
        Test that relative links are converted to absolute URLs.

        ISSUE: Current output contains broken relative links.
        EXPECTED: All relative links should be converted to absolute URLs.
        """
        html_with_relative_links = """
        <html>
        <head><title>Documentation with Links</title></head>
        <body>
        <h1>API Reference</h1>
        <p>See the <a href="user/quickstart/">quickstart guide</a> for getting started.</p>
        <p>Check out the <a href="../advanced/topics.html">advanced topics</a>.</p>
        <p>External link: <a href="https://external.com/docs">external docs</a>.</p>
        <p>Absolute link: <a href="/api/reference">API reference</a>.</p>
        </body>
        </html>
        """

        result = await self.processor.process(
            content=html_with_relative_links,
            base_url="https://docs.example.com/en/latest/",
        )

        # Check that links are properly resolved
        links = result.content.get("links", [])

        # Should have 4 links
        assert len(links) == 4

        # Find specific links
        quickstart_link = next(
            (link for link in links if "quickstart" in link["text"]), None
        )
        advanced_link = next(
            (link for link in links if "advanced" in link["text"]), None
        )
        external_link = next(
            (link for link in links if "external" in link["text"]), None
        )
        api_link = next(
            (link for link in links if "API reference" in link["text"]), None
        )

        # Relative links should be converted to absolute
        assert quickstart_link is not None
        assert (
            quickstart_link["url"]
            == "https://docs.example.com/en/latest/user/quickstart/"
        )

        assert advanced_link is not None
        assert (
            advanced_link["url"] == "https://docs.example.com/en/advanced/topics.html"
        )

        # External links should remain unchanged
        assert external_link is not None
        assert external_link["url"] == "https://external.com/docs"

        # Absolute paths should be resolved relative to domain
        assert api_link is not None
        assert api_link["url"] == "https://docs.example.com/api/reference"

    @pytest.mark.asyncio
    async def test_proper_content_structure_extraction(self):
        """
        Test that content structure is properly extracted and organized.

        ISSUE: Current implementation doesn't use ContentProcessor's structure features.
        EXPECTED: Proper headings, code blocks, and structure should be extracted.
        """
        structured_html = """
        <html>
        <head><title>Structured Documentation</title></head>
        <body>
        <h1>Getting Started</h1>
        <p>Introduction paragraph.</p>

        <h2>Installation</h2>
        <p>Install using pip:</p>
        <pre><code class="language-bash">pip install example-library</code></pre>

        <h2>Basic Usage</h2>
        <p>Here's a simple example:</p>
        <pre><code class="language-python">
import example
result = example.process("data")
print(result)
        </code></pre>

        <h3>Advanced Features</h3>
        <p>For advanced usage, see the following:</p>
        <ul>
        <li>Feature A</li>
        <li>Feature B</li>
        </ul>

        <h2>API Reference</h2>
        <p>Complete API documentation.</p>
        </body>
        </html>
        """

        result = await self.processor.process(
            content=structured_html, base_url="https://docs.example.com/"
        )

        # Check headings extraction
        assert result.headings is not None
        assert len(result.headings) >= 4  # h1, h2, h2, h3, h2

        # Check heading hierarchy
        heading_texts = [h["text"] for h in result.headings]
        assert "Getting Started" in heading_texts
        assert "Installation" in heading_texts
        assert "Basic Usage" in heading_texts
        assert "Advanced Features" in heading_texts
        assert "API Reference" in heading_texts

        # Check heading levels
        h1_headings = [h for h in result.headings if h["level"] == 1]
        h2_headings = [h for h in result.headings if h["level"] == 2]
        h3_headings = [h for h in result.headings if h["level"] == 3]

        assert len(h1_headings) == 1
        assert len(h2_headings) == 3
        assert len(h3_headings) == 1

        # Check structure extraction
        assert result.structure is not None
        assert len(result.structure) > 0

        # Should contain code blocks
        code_blocks = [item for item in result.structure if item.get("type") == "code"]
        assert len(code_blocks) >= 2  # bash and python code blocks

        # Check metadata flags
        assert result.metadata.get("has_code_blocks") is True
        assert result.metadata.get("has_tables") is False  # No tables in this example

    @pytest.mark.asyncio
    async def test_markdown_output_quality_and_readability(self):
        """
        Test that markdown output is high quality and readable.

        ISSUE: Current output has excessive whitespace and poor formatting.
        EXPECTED: Clean, well-formatted markdown with proper spacing.
        """
        messy_html = """
        <html>
        <head><title>Messy HTML</title></head>
        <body>


        <h1>   Title with Spaces   </h1>


        <p>Paragraph with    multiple   spaces.</p>


        <h2>Another Section</h2>
        <p>Normal paragraph.</p>


        </body>
        </html>
        """

        result = await self.processor.process(
            content=messy_html, base_url="https://example.com/"
        )

        formatted_content = result.content["formatted_content"]

        # Should not have excessive blank lines (more than 2 consecutive)
        lines = formatted_content.split("\n")
        consecutive_empty = 0
        max_consecutive_empty = 0

        for line in lines:
            if line.strip() == "":
                consecutive_empty += 1
                max_consecutive_empty = max(max_consecutive_empty, consecutive_empty)
            else:
                consecutive_empty = 0

        assert (
            max_consecutive_empty <= 2
        ), f"Too many consecutive empty lines: {max_consecutive_empty}"

        # Should have clean headings (no extra spaces)
        assert "# Title with Spaces" in formatted_content
        assert "#   Title with Spaces   #" not in formatted_content

        # Should normalize whitespace in paragraphs
        assert "multiple spaces" in formatted_content
        assert "multiple   spaces" not in formatted_content

    @pytest.mark.asyncio
    async def test_image_and_asset_handling(self):
        """
        Test that images and assets are properly handled.

        ISSUE: Current output has broken image references.
        EXPECTED: Image paths should be converted to absolute URLs or handled gracefully.
        """
        html_with_images = """
        <html>
        <head><title>Documentation with Images</title></head>
        <body>
        <h1>Visual Guide</h1>
        <p>Here's a diagram:</p>
        <img src="_images/diagram.png" alt="System Diagram" />
        <p>And a relative image:</p>
        <img src="../assets/screenshot.jpg" alt="Screenshot" />
        <p>External image:</p>
        <img src="https://external.com/image.png" alt="External Image" />
        </body>
        </html>
        """

        result = await self.processor.process(
            content=html_with_images, base_url="https://docs.example.com/en/latest/"
        )

        # Check that assets are extracted
        assert result.assets is not None
        assert "images" in result.assets

        images = result.assets["images"]
        assert len(images) >= 3

        # Check that relative image URLs are converted to absolute
        diagram_image = next(
            (img for img in images if "diagram.png" in img["src"]), None
        )
        screenshot_image = next(
            (img for img in images if "screenshot.jpg" in img["src"]), None
        )
        external_image = next(
            (img for img in images if "external.com" in img["src"]), None
        )

        assert diagram_image is not None
        assert (
            diagram_image["src"]
            == "https://docs.example.com/en/latest/_images/diagram.png"
        )

        assert screenshot_image is not None
        assert (
            screenshot_image["src"]
            == "https://docs.example.com/en/assets/screenshot.jpg"
        )

        assert external_image is not None
        assert (
            external_image["src"] == "https://external.com/image.png"
        )  # Should remain unchanged
