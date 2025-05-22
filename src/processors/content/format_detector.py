"""
Format detector for automatically detecting document formats.
"""
import logging
import re
from typing import List, Optional

from .format_handlers import FormatHandler

logger = logging.getLogger(__name__)

class FormatDetector:
    """
    Detects the format of a document and returns the appropriate handler.
    """

    def __init__(self):
        """Initialize the format detector."""
        self.handlers: List[FormatHandler] = []

    def register_handler(self, handler: FormatHandler) -> None:
        """
        Register a format handler.

        Args:
            handler: The handler to register
        """
        self.handlers.append(handler)
        logger.debug(f"Registered format handler: {handler.get_format_name()}")

    def detect_format(self, content: str, content_type: Optional[str] = None) -> Optional[FormatHandler]:
        """
        Detect the format of the content and return the appropriate handler.

        Args:
            content: The content to detect the format of
            content_type: Optional content type hint

        Returns:
            The appropriate handler or None if no handler can handle the content
        """
        # Try content type first if provided
        if content_type:
            for handler in self.handlers:
                if handler.can_handle("", content_type):
                    logger.debug(f"Detected format from content type: {handler.get_format_name()}")
                    return handler

        # Try content analysis
        for handler in self.handlers:
            if handler.can_handle(content, None):
                logger.debug(f"Detected format from content analysis: {handler.get_format_name()}")
                return handler

        logger.warning("Could not detect format, no handler found")
        return None

    def get_handler_for_format(self, format_name: str) -> Optional[FormatHandler]:
        """
        Get a handler for a specific format.

        Args:
            format_name: The name of the format

        Returns:
            The handler or None if no handler is found
        """
        for handler in self.handlers:
            if handler.get_format_name().lower() == format_name.lower():
                return handler

        return None

class ContentTypeDetector:
    """
    Detects the content type from file extensions or content analysis.
    """

    # Map of file extensions to content types
    EXTENSION_MAP = {
        "html": "text/html",
        "htm": "text/html",
        "xhtml": "application/xhtml+xml",
        "md": "text/markdown",
        "markdown": "text/markdown",
        "rst": "text/x-rst",
        "rest": "text/x-rst",
        "adoc": "text/asciidoc",
        "asciidoc": "text/asciidoc",
        "txt": "text/plain",
        "json": "application/json",
        "xml": "application/xml",
        "yaml": "application/yaml",
        "yml": "application/yaml",
        "css": "text/css",
        "js": "application/javascript",
        "py": "text/x-python",
        "java": "text/x-java",
        "c": "text/x-c",
        "cpp": "text/x-c++",
        "cs": "text/x-csharp",
        "go": "text/x-go",
        "rb": "text/x-ruby",
        "php": "text/x-php",
        "pl": "text/x-perl",
        "sh": "text/x-shellscript",
        "bat": "text/x-bat",
        "ps1": "text/x-powershell"
    }

    @classmethod
    def detect_from_filename(cls, filename: str) -> Optional[str]:
        """
        Detect content type from filename.

        Args:
            filename: The filename

        Returns:
            The content type or None if not detected
        """
        if not filename:
            return None

        # Extract extension
        parts = filename.split(".")
        if len(parts) > 1:
            ext = parts[-1].lower()
            return cls.EXTENSION_MAP.get(ext)

        return None

    @classmethod
    def detect_from_content(cls, content: str) -> Optional[str]:
        """
        Detect content type from content analysis.

        Args:
            content: The content

        Returns:
            The content type or None if not detected
        """
        # Check for HTML
        if re.search(r"<!DOCTYPE html>|<html|<body", content, re.IGNORECASE):
            return "text/html"

        # Check for reStructuredText first (more specific patterns)
        if re.search(r"^\.\. \w+::", content, re.MULTILINE) or \
           re.search(r"::\s*\n\s+\w+", content, re.MULTILINE) or \
           re.search(r"^\.\. \[.+\]", content, re.MULTILINE) or \
           re.search(r"^\.\. _\w+:", content, re.MULTILINE) or \
           (re.search(r"^=+\s*$", content, re.MULTILINE) and
            re.search(r"^[^\n]+\n=+\s*$", content, re.MULTILINE) and
            re.search(r"^=+\s*\n[^\n]+\n=+\s*$", content, re.MULTILINE)):
            return "text/x-rst"

        # Check for Markdown
        if re.search(r"^#+ |```|\[.+\]\(.+\)", content, re.MULTILINE) or \
           re.search(r"^[^\n]+\n=+\s*$", content, re.MULTILINE) or \
           re.search(r"^[^\n]+\n-+\s*$", content, re.MULTILINE):
            return "text/markdown"

        # No need for a second RST check as we already checked above

        # Check for AsciiDoc
        if re.search(r"^= \w+|^== \w+|^\[source,\w+\]", content, re.MULTILINE):
            return "text/asciidoc"

        # Check for XML
        if re.search(r"<\?xml|<[a-zA-Z0-9]+>", content):
            return "application/xml"

        # Check for JSON
        if re.search(r"^\s*[\{\[]", content) and re.search(r"[\}\]]\s*$", content):
            return "application/json"

        # Check for YAML
        if re.search(r"^---\n", content) and re.search(r":\s+", content, re.MULTILINE):
            return "application/yaml"

        # Default to plain text
        return "text/plain"
