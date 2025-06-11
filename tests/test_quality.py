"""Tests for the quality checker component."""

import pytest

from src.processors.content_processor import ProcessedContent
from src.processors.quality_checker import (
    IssueLevel,
    IssueType,
    QualityChecker,
    QualityConfig,
)


def create_processed_content(
    title: str = "Test Document",
    content: dict = None,
    metadata: dict = None,
    assets: dict = None,
    url: str = "https://example.com",  # Add url as optional metadata source
) -> ProcessedContent:
    """Helper function to create ProcessedContent instances."""
    # Ensure metadata is initialized
    final_metadata = metadata or {}
    # Add url to metadata if provided
    if url:
        final_metadata["source_url"] = url

    return ProcessedContent(
        title=title,
        content=content or {},
        metadata=final_metadata,
        assets=assets or {},
        # Add default empty lists for other fields if needed by tests
        headings=[],
        structure=[],
        errors=[],
    )


@pytest.mark.asyncio
async def test_quality_checker_basic(quality_checker: QualityChecker):
    """Test basic quality checking functionality."""
    content = create_processed_content(
        url="https://example.com",
        title="Test Document",
        content={
            "text": "This is a test document",
            "headings": [{"level": 1, "text": "Test Document"}],
            "code_blocks": [],
            "links": [],
        },
    )

    issues, metrics = await quality_checker.check_quality(content)

    assert isinstance(issues, list)
    assert isinstance(metrics, dict)
    assert len(issues) > 0  # Should have some issues due to short content
    assert "content_length" in metrics


@pytest.mark.asyncio
async def test_quality_checker_content_length(quality_checker: QualityChecker):
    """Test content length validation."""
    # Test content that's too short
    short_content = create_processed_content(
        content={"formatted_content": "Too short"}  # Use formatted_content key
    )
    issues, metrics = await quality_checker.check_quality(short_content)
    assert any(i.type == IssueType.CONTENT_LENGTH for i in issues)

    # Test content that's acceptable
    good_content = create_processed_content(
        content={
            "formatted_content": "This is a sufficiently long piece of content that should pass the minimum length check. "
            * 5
        }  # Use formatted_content key
    )
    issues, metrics = await quality_checker.check_quality(good_content)
    assert not any(i.type == IssueType.CONTENT_LENGTH for i in issues)


@pytest.mark.asyncio
async def test_quality_checker_headings(quality_checker: QualityChecker):
    """Test heading structure validation."""
    # Test missing headings
    no_headings = create_processed_content(
        content={"text": "Content without headings", "headings": []}
    )
    issues, _ = await quality_checker.check_quality(no_headings)
    assert any(i.type == IssueType.HEADING_STRUCTURE for i in issues)

    # Test proper heading structure
    good_headings = create_processed_content(
        content={
            "text": "Content with good headings",
            "headings": [
                {"level": 1, "text": "Main Title"},
                {"level": 2, "text": "Subtitle"},
            ],
        }
    )
    issues, _ = await quality_checker.check_quality(good_headings)
    assert not any(i.type == IssueType.HEADING_STRUCTURE for i in issues)


@pytest.mark.asyncio
async def test_quality_checker_links(quality_checker: QualityChecker):
    """Test link validation."""
    # Test insufficient internal links
    few_links = create_processed_content(
        content={
            "text": "Content with few links",
            "links": [{"url": "https://external.com", "text": "External"}],
        }
    )
    issues, _ = await quality_checker.check_quality(few_links)
    assert any(i.type == IssueType.LINK_COUNT for i in issues)

    # Test sufficient internal links
    good_links = create_processed_content(
        content={
            "text": "Content with good links",
            "links": [
                {"url": "/internal1", "text": "Internal 1"},
                {"url": "/internal2", "text": "Internal 2"},
                {"url": "https://external.com", "text": "External"},
            ],
        }
    )
    issues, _ = await quality_checker.check_quality(good_links)
    assert not any(i.type == IssueType.LINK_COUNT for i in issues)


@pytest.mark.asyncio
async def test_quality_checker_code_blocks(quality_checker: QualityChecker):
    """Test code block validation."""
    # Test code block that's too short
    short_code = create_processed_content(
        content={
            "text": "Content with short code block",
            "code_blocks": [{"language": "python", "code": "x=1"}],
        }
    )
    issues, _ = await quality_checker.check_quality(short_code)
    assert any(i.type == IssueType.CODE_BLOCK_LENGTH for i in issues)

    # Test proper code block
    good_code = create_processed_content(
        content={
            "text": "Content with good code block",
            "code_blocks": [
                {
                    "language": "python",
                    "code": """
                    def example_function():
                        \"\"\"This is an example function.\"\"\"
                        result = 0
                        for i in range(10):
                            result += i
                        return result
                    """,
                }
            ],
        }
    )
    issues, _ = await quality_checker.check_quality(good_code)
    assert not any(i.type == IssueType.CODE_BLOCK_LENGTH for i in issues)


@pytest.mark.asyncio
async def test_quality_checker_metadata(quality_checker: QualityChecker):
    """Test metadata validation."""
    # Test missing required metadata
    missing_metadata = create_processed_content(content={"text": "Content"}, title="")
    issues, _ = await quality_checker.check_quality(missing_metadata)
    assert any(i.type == IssueType.METADATA for i in issues)

    # Test complete metadata
    good_metadata = create_processed_content(
        content={"text": "Content"}, title="Test Document"
    )
    good_metadata.metadata = {
        "title": "Test Document",
        "description": "Test description",
    }
    issues, _ = await quality_checker.check_quality(good_metadata)
    assert not any(i.type == IssueType.METADATA for i in issues)


@pytest.mark.asyncio
async def test_quality_checker_custom_config():
    """Test quality checker with custom configuration."""
    custom_config = QualityConfig(
        min_content_length=50,
        max_content_length=5000,
        min_headings=2,
        max_heading_level=3,
        min_internal_links=1,
        required_metadata=["title"],
        min_code_block_length=5,
        max_code_block_length=500,
    )
    checker = QualityChecker(config=custom_config)

    # Create test content that should pass with custom config
    content = ProcessedContent(
        url="https://example.com",
        title="Test Document",
        content={
            "formatted_content": "This is a test document with sufficient length to pass the custom minimum.",  # Use formatted_content key
            "headings": [
                {"level": 1, "text": "Main Title"},
                {"level": 2, "text": "Subtitle"},
            ],
            "links": [{"url": "/internal", "text": "Internal"}],
            "code_blocks": [{"language": "python", "code": "def test():\n    pass"}],
        },
        metadata={"title": "Test Document"},
        assets={},
        errors=[],
    )

    issues, metrics = await checker.check_quality(content)
    assert len([i for i in issues if i.level == IssueLevel.ERROR]) == 0
