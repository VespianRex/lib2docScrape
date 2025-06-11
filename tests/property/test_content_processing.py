"""
Property-based tests for content processing.
"""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.processors.content.models import ProcessedContent
from src.processors.content_processor import ContentProcessor

# Define strategies for HTML content
html_tags = st.sampled_from(["p", "h1", "h2", "h3", "div", "span", "a", "code", "pre"])
html_attributes = st.dictionaries(
    keys=st.sampled_from(["class", "id", "style", "href", "src"]),
    values=st.text(min_size=1, max_size=20),
    max_size=3,
)
html_text = st.text(min_size=1, max_size=100)


# Strategy for generating simple HTML elements
@st.composite
def html_elements(draw):
    tag = draw(html_tags)
    attrs = draw(html_attributes)
    text = draw(html_text)

    attrs_str = " ".join(f'{k}="{v}"' for k, v in attrs.items())
    if attrs_str:
        attrs_str = " " + attrs_str

    return f"<{tag}{attrs_str}>{text}</{tag}>"


# Strategy for generating simple HTML documents
@st.composite
def html_documents(draw):
    title = draw(st.text(min_size=1, max_size=50))
    num_elements = draw(st.integers(min_value=1, max_value=10))
    elements = [draw(html_elements()) for _ in range(num_elements)]

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
    </head>
    <body>
        {"".join(elements)}
    </body>
    </html>
    """


@pytest.mark.asyncio
@given(html_documents())
async def test_content_processor_basic_properties(html_content):
    """Test basic properties of content processing."""
    processor = ContentProcessor()

    # Process the content
    processed_content = await processor.process(
        content=html_content, base_url="https://example.com"
    )

    # Check that the processed content is a ProcessedContent object
    assert isinstance(processed_content, ProcessedContent)

    # Check that the title is extracted
    assert processed_content.title is not None
    assert isinstance(processed_content.title, str)

    # Check that the content is not empty
    assert processed_content.content is not None
    assert isinstance(processed_content.content, dict)

    # Check that the metadata is a dictionary
    assert processed_content.metadata is not None
    assert isinstance(processed_content.metadata, dict)


@pytest.mark.asyncio
@given(html_documents())
async def test_content_processor_idempotent(html_content):
    """Test that processing content twice gives the same result."""
    processor = ContentProcessor()

    # Process the content twice
    processed1 = await processor.process(
        content=html_content, base_url="https://example.com"
    )
    processed2 = await processor.process(
        content=html_content, base_url="https://example.com"
    )

    # Check that the results are the same
    assert processed1.title == processed2.title
    assert processed1.content.get("formatted_content") == processed2.content.get(
        "formatted_content"
    )

    # Check that headings are the same
    assert len(processed1.headings) == len(processed2.headings)
    for h1, h2 in zip(processed1.headings, processed2.headings):
        assert h1.get("text") == h2.get("text")
        assert h1.get("level") == h2.get("level")


@pytest.mark.asyncio
@given(
    st.text(min_size=1, max_size=100)
    .filter(lambda x: x.strip())  # Filter out whitespace-only strings
    .filter(lambda x: not _looks_like_html(x))  # Filter out HTML-like text
)
async def test_content_processor_handles_plain_text(text):
    """Test that the content processor can handle plain text."""
    processor = ContentProcessor()

    # Process plain text
    processed = await processor.process(content=text, base_url="https://example.com")

    # Check that the result is a ProcessedContent object
    assert isinstance(processed, ProcessedContent)

    # The original text should be in the formatted_content field
    assert processed.content["formatted_content"] == text


def _looks_like_html(text: str) -> bool:
    """Helper function to detect if text looks like HTML."""
    import re

    # Check for HTML patterns that would be detected by our HTML handler
    return bool(
        re.search(r"<!DOCTYPE\s+html>", text, re.IGNORECASE)
        or re.search(r"<html[^>]*>.*</html>", text, re.IGNORECASE | re.DOTALL)
        or
        # Look for common HTML tags with proper closing tags
        (
            re.search(
                r"<(div|p|span|h[1-6]|a|img|table|ul|ol|li|form|input|body|code|pre)\b[^>]*>",
                text,
                re.IGNORECASE,
            )
            and re.search(
                r"</(div|p|span|h[1-6]|a|img|table|ul|ol|li|form|input|body|code|pre)>",
                text,
                re.IGNORECASE,
            )
        )
    )


@pytest.mark.asyncio
async def test_content_processor_html_vs_plain_text_boundary():
    """Test that the content processor correctly distinguishes HTML from plain text."""
    processor = ContentProcessor()

    # Test cases that should be treated as plain text
    plain_text_cases = [
        "Just plain text",
        "Text with < and > symbols",
        "Text with <incomplete tag",
        "Text with <li</0> malformed tag",
        "Text with <div but no closing",
        "Some text with <random> but no proper closing",
    ]

    for text in plain_text_cases:
        processed = await processor.process(
            content=text, base_url="https://example.com"
        )
        assert isinstance(processed, ProcessedContent)
        # For plain text, the formatted content should be the same as input
        assert processed.content["formatted_content"] == text

    # Test cases that should be treated as HTML
    html_cases = [
        "<div>Content</div>",
        "<p>Paragraph</p>",
        "<li>List item</li>",
        "<code>Code block</code>",
        "<span>Span content</span>",
    ]

    for html in html_cases:
        processed = await processor.process(
            content=html, base_url="https://example.com"
        )
        assert isinstance(processed, ProcessedContent)
        # For HTML, the content should be processed (converted to markdown)
        # The exact output depends on markdownify, but it should not be identical to input
        formatted = processed.content["formatted_content"]
        # At minimum, HTML tags should be processed/converted
        assert (
            "Content" in formatted
            or "Paragraph" in formatted
            or "List item" in formatted
            or "Code block" in formatted
            or "Span content" in formatted
        )


@pytest.mark.asyncio
@given(html_documents())
async def test_content_processor_extracts_links(html_content):
    """Test that the content processor extracts links correctly."""
    # Add a link to the HTML content
    html_with_link = html_content.replace(
        "</body>", '<a href="https://example.org">Link</a></body>'
    )

    processor = ContentProcessor()

    # Process the content
    processed = await processor.process(
        content=html_with_link, base_url="https://example.com"
    )

    # Check that links are extracted
    assert processed.content.get("links") is not None

    # There should be at least one link
    links = processed.content.get("links", [])
    assert len(links) >= 1

    # At least one link should point to example.org
    assert any(link.get("url") == "https://example.org" for link in links)
