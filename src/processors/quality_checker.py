"""Quality checker for processed content."""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from .content_processor import ProcessedContent


class IssueType(str, Enum):
    """Types of quality issues."""

    CONTENT_LENGTH = "content_length"
    HEADING_STRUCTURE = "heading_structure"
    LINK_COUNT = "link_count"
    CODE_BLOCK_LENGTH = "code_block_length"
    METADATA = "metadata"
    GENERAL = "general"


class IssueLevel(str, Enum):
    """Severity levels for quality issues."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class QualityIssue(BaseModel):
    """Represents a quality issue found in the content."""

    type: IssueType
    level: IssueLevel
    message: str
    location: Optional[str] = None
    details: dict[str, Any] = Field(default_factory=dict)


class QualityConfig(BaseModel):
    """Configuration for quality checking."""

    min_content_length: int = 100  # Set to 0 to disable minimum length check
    max_content_length: int = 100000  # Set to 0 to disable maximum length check
    min_headings: int = 1
    max_heading_level: int = 6
    min_internal_links: int = 2
    required_metadata: list[str] = Field(
        default_factory=lambda: ["title", "description"]
    )
    min_code_block_length: int = 10
    max_code_block_length: int = 1000


class QualityChecker:
    """Checks the quality of processed content."""

    def __init__(self, config: Optional[QualityConfig] = None):
        """Initialize quality checker with configuration."""
        self.config = config or QualityConfig()

    async def check_quality(
        self, content: ProcessedContent
    ) -> tuple[list[QualityIssue], dict[str, Any]]:
        """Check quality of processed content."""
        issues = []
        metrics = {}

        # Check content length
        text = content.content.get("formatted_content", "")
        if text is None:
            text = ""

        content_length = len(text)
        metrics["content_length"] = content_length

        # Only check minimum length if configured
        if (
            self.config.min_content_length > 0
            and content_length < self.config.min_content_length
        ):
            issues.append(
                QualityIssue(
                    type=IssueType.CONTENT_LENGTH,
                    level=IssueLevel.ERROR,
                    message=f"Content length ({content_length}) is below minimum ({self.config.min_content_length})",
                )
            )

        # Only check maximum length if configured
        if (
            self.config.max_content_length > 0
            and content_length > self.config.max_content_length
        ):
            issues.append(
                QualityIssue(
                    type=IssueType.CONTENT_LENGTH,
                    level=IssueLevel.WARNING,
                    message=f"Content length ({content_length}) exceeds maximum ({self.config.max_content_length})",
                )
            )

        # Check headings
        headings = content.content.get("headings", [])
        metrics["heading_count"] = len(headings)

        if len(headings) < self.config.min_headings:
            issues.append(
                QualityIssue(
                    type=IssueType.HEADING_STRUCTURE,
                    level=IssueLevel.ERROR,
                    message=f"Too few headings ({len(headings)}), minimum is {self.config.min_headings}",
                )
            )

        for heading in headings:
            if heading.get("level", 1) > self.config.max_heading_level:
                issues.append(
                    QualityIssue(
                        type=IssueType.HEADING_STRUCTURE,
                        level=IssueLevel.WARNING,
                        message=f"Heading level {heading.get('level')} exceeds maximum {self.config.max_heading_level}",
                    )
                )

        # Check internal links
        links = content.content.get("links", [])
        internal_links = [link for link in links if link.get("url", "").startswith("/")]
        metrics["internal_link_count"] = len(internal_links)

        if len(internal_links) < self.config.min_internal_links:
            issues.append(
                QualityIssue(
                    type=IssueType.LINK_COUNT,
                    level=IssueLevel.WARNING,
                    message=f"Too few internal links ({len(internal_links)}), minimum is {self.config.min_internal_links}",
                )
            )

        # Check code blocks
        code_blocks = content.content.get("code_blocks", [])
        metrics["code_block_count"] = len(code_blocks)

        for block in code_blocks:
            code = block.get("code", "")
            if len(code) < self.config.min_code_block_length:
                issues.append(
                    QualityIssue(
                        type=IssueType.CODE_BLOCK_LENGTH,
                        level=IssueLevel.WARNING,
                        message=f"Code block too short ({len(code)} chars), minimum is {self.config.min_code_block_length}",
                    )
                )
            elif len(code) > self.config.max_code_block_length:
                issues.append(
                    QualityIssue(
                        type=IssueType.CODE_BLOCK_LENGTH,
                        level=IssueLevel.WARNING,
                        message=f"Code block too long ({len(code)} chars), maximum is {self.config.max_code_block_length}",
                    )
                )

        # Check metadata
        for field in self.config.required_metadata:
            if field not in content.metadata:
                issues.append(
                    QualityIssue(
                        type=IssueType.METADATA,
                        level=IssueLevel.ERROR,
                        message=f"Missing required metadata field: {field}",
                    )
                )

        # Calculate overall quality score
        # Base score starts at 1.0 and is reduced for each issue
        quality_score = 1.0

        # Reduce score based on issues
        for issue in issues:
            if issue.level == IssueLevel.ERROR:
                quality_score -= 0.2
            elif issue.level == IssueLevel.WARNING:
                quality_score -= 0.1
            elif issue.level == IssueLevel.INFO:
                quality_score -= 0.05

        # Ensure score doesn't go below 0
        quality_score = max(0.0, quality_score)

        # Add quality score to metrics
        metrics["quality_score"] = quality_score

        return issues, metrics
