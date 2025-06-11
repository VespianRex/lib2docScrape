"""Data models for content processing."""

from dataclasses import dataclass, field
from datetime import datetime  # add import
from typing import Any


@dataclass
class ProcessorConfig:
    """Configuration for the content processor."""

    allowed_tags: list[str] = field(
        default_factory=lambda: [
            "p",
            "a",
            "img",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "ul",
            "ol",
            "li",
            "code",
            "pre",
            "blockquote",
            "em",
            "strong",
            "table",
            "tr",
            "td",
            "th",
        ]
    )
    max_heading_level: int = 3
    preserve_whitespace_elements: list[str] = field(
        default_factory=lambda: ["pre", "code"]
    )
    code_languages: list[str] = field(
        default_factory=lambda: [
            "python",
            "javascript",
            "typescript",
            "java",
            "cpp",
            "c",
            "csharp",
            "go",
            "rust",
            "swift",
            "kotlin",
            "php",
            "ruby",
            "scala",
            "perl",
            "r",
            "html",
            "css",
            "sql",
            "shell",
            "bash",
            "powershell",
        ]
    )
    sanitize_urls: bool = True
    metadata_prefixes: list[str] = field(
        default_factory=lambda: ["og:", "twitter:", "dc.", "article:", "book:"]
    )
    extract_comments: bool = False
    max_content_length: int = 1000000
    min_content_length: int = 0
    max_heading_length: int = 100  # Default to 100 characters
    # Additional fields
    max_code_block_size: int = 1000
    preserve_whitespace: bool = False
    sanitize_content: bool = True
    extract_metadata: bool = True
    extract_assets: bool = True
    extract_code_blocks: bool = True
    # blocked_attributes field removed as bleach handles allowed attributes directly

    def __post_init__(self):
        # Ensure max_heading_level is between 1 and 6
        self.max_heading_level = max(1, min(6, self.max_heading_level))
        # Ensure max_heading_length is at least max_heading_level * 10 characters
        min_length = self.max_heading_level * 10
        if self.max_heading_length < min_length:
            self.max_heading_length = min_length


@dataclass
class ProcessedContent:
    """Result of content processing."""

    url: str = ""
    content_type: str = ""
    raw: str = ""
    text: str = ""
    markdown: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    content: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    assets: dict[str, list[str]] = field(
        default_factory=lambda: {
            "images": [],
            "stylesheets": [],
            "scripts": [],
            "media": [],
        }
    )
    headings: list[dict[str, Any]] = field(default_factory=list)
    structure: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    title: str = field(default="Untitled Document")

    def __str__(self) -> str:
        """Convert to string representation."""
        if "formatted_content" in self.content:
            return str(self.content["formatted_content"])
        return ""

    def __contains__(self, item: str) -> bool:
        """Check if string is in content."""
        if isinstance(item, str):
            # Directly check the formatted content to avoid recursion
            formatted_content = self.content.get("formatted_content", "")
            return item in str(formatted_content)
        return False

    def __len__(self) -> int:
        """Get length of main content."""
        return len(str(self))

    def __bool__(self) -> bool:
        """Check if content exists."""
        return bool(self.content)

    def __iter__(self):
        """Iterate over content."""
        return iter(str(self))

    @property
    def processed_content(self) -> dict[str, str]:
        """Get processed content."""
        return self.content

    @property
    def main_content(self) -> str:
        """Get main content."""
        return str(self)

    @property
    def has_errors(self) -> bool:
        """Check if processing had errors."""
        return bool(self.errors)

    def get_content_section(self, section: str) -> str:
        """Get content for a specific section."""
        return str(self.content.get(section, ""))

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(str(error))

    def add_content(self, section: str, content: Any) -> None:
        """Add content to a section."""
        self.content[section] = content

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata."""
        self.metadata[key] = value

    def add_asset(self, asset_type: str, url: str) -> None:
        """Add an asset URL."""
        if asset_type in self.assets:
            if url not in self.assets[asset_type]:
                self.assets[asset_type].append(url)

    def add_heading(self, heading: dict[str, Any]) -> None:
        """Add a heading."""
        self.headings.append(heading)
        # Structure is a list, not a dict, so just append the heading
        self.structure.append(heading)

    def is_valid(self) -> bool:
        """Check if the processed content is valid."""
        return bool(self.title and self.content and self.metadata)


# Alias for backward compatibility with code expecting ProcessingConfig
ProcessingConfig = ProcessorConfig
