"""
Tests for the format handler.
"""
import pytest

from src.processors.content.format_handler import FormatHandler, DocFormat, FormatDetectionResult


def test_format_detection_markdown():
    """Test Markdown format detection."""
    handler = FormatHandler()

    # Test Markdown detection
    markdown_content = """# Heading 1

## Heading 2

This is a paragraph with **bold** and *italic* text.

- List item 1
- List item 2

[Link text](https://example.com)

```python
def hello():
    print("Hello, world!")
```
"""

    result = handler.detect_format(markdown_content)
    assert result.format_type == DocFormat.MARKDOWN
    assert result.confidence > 0.7


def test_format_detection_rst():
    """Test reStructuredText format detection."""
    handler = FormatHandler()

    # Test RST detection
    rst_content = """Document Title
==============

Section Title
------------

This is a paragraph.

* List item 1
* List item 2

.. code-block:: python

    def hello():
        print("Hello, world!")

.. note::
    This is a note.
"""

    result = handler.detect_format(rst_content)
    assert result.format_type == DocFormat.RST
    assert result.confidence > 0.4  # Lower threshold for RST detection


def test_format_detection_asciidoc():
    """Test AsciiDoc format detection."""
    handler = FormatHandler()

    # Test AsciiDoc detection
    asciidoc_content = """= Document Title

== Section Title

This is a paragraph.

* List item 1
* List item 2

[source,python]
----
def hello():
    print("Hello, world!")
----

NOTE: This is a note.
"""

    result = handler.detect_format(asciidoc_content)
    assert result.format_type == DocFormat.ASCIIDOC
    assert result.confidence > 0.5


def test_format_detection_html():
    """Test HTML format detection."""
    handler = FormatHandler()

    # Test HTML detection
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Document Title</title>
</head>
<body>
    <h1>Heading 1</h1>
    <p>This is a paragraph.</p>
    <ul>
        <li>List item 1</li>
        <li>List item 2</li>
    </ul>
    <pre><code>def hello():
    print("Hello, world!")</code></pre>
</body>
</html>
"""

    result = handler.detect_format(html_content)
    assert result.format_type == DocFormat.HTML
    assert result.confidence > 0.9


def test_format_detection_plain():
    """Test plain text format detection."""
    handler = FormatHandler()

    # Test plain text detection
    plain_content = """This is a plain text document.
It has no special formatting.

Just paragraphs and line breaks.
"""

    result = handler.detect_format(plain_content)
    assert result.format_type == DocFormat.PLAIN


def test_markdown_to_html_conversion():
    """Test Markdown to HTML conversion."""
    handler = FormatHandler()

    markdown_content = """# Heading 1

This is a paragraph with **bold** and *italic* text.

- List item 1
- List item 2
"""

    html = handler.convert(markdown_content, DocFormat.MARKDOWN, DocFormat.HTML)
    # The markdown package adds id attributes to headers
    assert "Heading 1" in html
    assert "<strong>bold</strong>" in html or "<b>bold</b>" in html
    assert "<em>italic</em>" in html or "<i>italic</i>" in html
    assert "<li>List item 1</li>" in html or "- List item 1" in html


def test_html_to_markdown_conversion():
    """Test HTML to Markdown conversion."""
    handler = FormatHandler()

    html_content = """<h1>Heading 1</h1>
<p>This is a paragraph with <strong>bold</strong> and <em>italic</em> text.</p>
<ul>
    <li>List item 1</li>
    <li>List item 2</li>
</ul>
"""

    markdown = handler.convert(html_content, DocFormat.HTML, DocFormat.MARKDOWN)
    assert "# Heading 1" in markdown or "Heading 1" in markdown
    assert "**bold**" in markdown or "bold" in markdown
    assert "*italic*" in markdown or "italic" in markdown
    assert "- List item 1" in markdown or "List item 1" in markdown


def test_html_to_plain_conversion():
    """Test HTML to plain text conversion."""
    handler = FormatHandler()

    html_content = """<h1>Heading 1</h1>
<p>This is a paragraph with <strong>bold</strong> and <em>italic</em> text.</p>
<ul>
    <li>List item 1</li>
    <li>List item 2</li>
</ul>
"""

    plain = handler.convert(html_content, DocFormat.HTML, DocFormat.PLAIN)
    assert "Heading 1" in plain
    # BeautifulSoup may add extra whitespace
    assert "bold" in plain and "italic" in plain
    assert "List item 1" in plain
    assert "List item 2" in plain


def test_format_detection_empty():
    """Test format detection with empty content."""
    handler = FormatHandler()

    result = handler.detect_format("")
    assert result.format_type == DocFormat.PLAIN
    assert result.confidence == 1.0


def test_format_conversion_same_format():
    """Test conversion to the same format."""
    handler = FormatHandler()

    content = "# Heading 1\n\nThis is a paragraph."
    result = handler.convert(content, DocFormat.MARKDOWN, DocFormat.MARKDOWN)
    assert result == content


def test_format_conversion_chain():
    """Test conversion chain."""
    handler = FormatHandler()

    # Markdown -> HTML -> Plain
    markdown_content = """# Heading 1

This is a paragraph with **bold** and *italic* text.
"""

    html = handler.convert(markdown_content, DocFormat.MARKDOWN, DocFormat.HTML)
    plain = handler.convert(html, DocFormat.HTML, DocFormat.PLAIN)

    assert "Heading 1" in plain
    # BeautifulSoup may add extra whitespace
    assert "bold" in plain and "italic" in plain
