"""
Format handlers for different document formats.
"""
import logging
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class FormatHandler(ABC):
    """Base class for document format handlers."""

    @abstractmethod
    def can_handle(self, content: str, content_type: Optional[str] = None) -> bool:
        """
        Check if this handler can process the given content.

        Args:
            content: The content to check
            content_type: Optional content type hint

        Returns:
            True if this handler can process the content
        """
        pass

    @abstractmethod
    async def process(self, content: str, base_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Process the content and return structured data.

        Args:
            content: The content to process
            base_url: Optional base URL for resolving relative links

        Returns:
            Dictionary with processed content
        """
        pass

    @abstractmethod
    def get_format_name(self) -> str:
        """
        Get the name of the format this handler processes.

        Returns:
            Format name
        """
        pass

class HTMLHandler(FormatHandler):
    """Handler for HTML content."""

    def __init__(self, html_processor):
        """
        Initialize the HTML handler.

        Args:
            html_processor: The HTML processor to use
        """
        self.html_processor = html_processor

    def can_handle(self, content: str, content_type: Optional[str] = None) -> bool:
        """Check if content is HTML."""
        if content_type and "html" in content_type.lower():
            return True

        # Check for HTML tags
        return bool(re.search(r"<\s*html|<\s*body|<\s*div|<\s*p|<\s*h[1-6]", content, re.IGNORECASE))

    async def process(self, content: str, base_url: Optional[str] = None) -> Dict[str, Any]:
        """Process HTML content."""
        return await self.html_processor.process(content, base_url)

    def get_format_name(self) -> str:
        """Get format name."""
        return "HTML"

class MarkdownHandler(FormatHandler):
    """Handler for Markdown content."""

    def can_handle(self, content: str, content_type: Optional[str] = None) -> bool:
        """Check if content is Markdown."""
        if content_type and ("markdown" in content_type.lower() or "md" in content_type.lower()):
            return True

        # Check for Markdown patterns
        # Look for headings, code blocks, lists, etc.
        if not content:
            return False

        # Simple check for common Markdown patterns
        if content.startswith("# "):
            return True

        if "```" in content:
            return True

        if re.search(r"^\* ", content, re.MULTILINE):
            return True

        if re.search(r"^- ", content, re.MULTILINE):
            return True

        if re.search(r"^\d+\. ", content, re.MULTILINE):
            return True

        if re.search(r"\[.+\]\(.+\)", content):
            return True

        # Check for Setext-style headers (underlined with = or -)
        if re.search(r"^[^\n]+\n=+\s*$", content, re.MULTILINE):
            return True

        if re.search(r"^[^\n]+\n-+\s*$", content, re.MULTILINE):
            return True

        return False

    async def process(self, content: str, base_url: Optional[str] = None) -> Dict[str, Any]:
        """Process Markdown content."""
        # Basic processing without conversion
        logger.info("Processing Markdown content with basic processing")
        return {
            "formatted_content": content,
            "structure": self._extract_basic_structure(content)
        }

    def _extract_basic_structure(self, content: str) -> List[Dict[str, Any]]:
        """Extract basic structure from Markdown content."""
        structure = []

        # Extract headings
        heading_pattern = r"^(#+) (.+)$"
        for line in content.split("\n"):
            match = re.match(heading_pattern, line)
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                structure.append({
                    "type": "heading",
                    "level": level,
                    "title": text
                })

        return structure

    def get_format_name(self) -> str:
        """Get format name."""
        return "Markdown"

class ReStructuredTextHandler(FormatHandler):
    """Handler for reStructuredText content."""

    def can_handle(self, content: str, content_type: Optional[str] = None) -> bool:
        """Check if content is reStructuredText."""
        if content_type and ("restructuredtext" in content_type.lower() or "x-rst" in content_type.lower()):
            return True

        # Check for reStructuredText patterns
        if not content:
            return False

        # Simple check for common RST patterns
        if re.search(r"^=+\s*$", content, re.MULTILINE) and re.search(r"^\w+\s*$", content, re.MULTILINE):
            return True

        if re.search(r"^\.\. \w+::", content, re.MULTILINE):
            return True

        if re.search(r"^\.\. \[.+\]", content, re.MULTILINE):
            return True

        if re.search(r"^\.\. _\w+:", content, re.MULTILINE):
            return True

        if re.search(r":`[^`]+`", content):
            return True

        # Check for literal blocks
        if re.search(r"::\s*\n\s+\w+", content, re.MULTILINE):
            return True

        return False

    async def process(self, content: str, base_url: Optional[str] = None) -> Dict[str, Any]:
        """Process reStructuredText content."""
        try:
            from docutils.core import publish_parts

            # Convert RST to HTML
            html_content = publish_parts(content, writer_name="html")["html_body"]

            # Use the HTML processor to process the converted content
            from ..content_processor import ContentProcessor
            html_processor = ContentProcessor()
            return await html_processor.process(html_content, base_url)

        except ImportError:
            logger.warning("docutils library not available, using basic processing")
            return {
                "formatted_content": content,
                "structure": self._extract_basic_structure(content)
            }

    def _extract_basic_structure(self, content: str) -> List[Dict[str, Any]]:
        """Extract basic structure from reStructuredText content."""
        structure = []

        # Extract section titles
        lines = content.split("\n")
        for i in range(len(lines) - 2):
            # Check for overline/underline style
            if (i > 0 and
                re.match(r"^[=\-`:'\"~^_*+#]", lines[i]) and
                re.match(r"^[=\-`:'\"~^_*+#]", lines[i+2]) and
                len(lines[i]) == len(lines[i+2])):

                title = lines[i+1].strip()
                level = 1  # Simplified level assignment
                structure.append({
                    "type": "heading",
                    "level": level,
                    "title": title
                })

            # Check for underline style
            elif (i < len(lines) - 1 and
                  re.match(r"^[=\-`:'\"~^_*+#]+$", lines[i+1]) and
                  len(lines[i]) == len(lines[i+1])):

                title = lines[i].strip()
                level = 1  # Simplified level assignment
                structure.append({
                    "type": "heading",
                    "level": level,
                    "title": title
                })

        return structure

    def get_format_name(self) -> str:
        """Get format name."""
        return "reStructuredText"

class AsciiDocHandler(FormatHandler):
    """Handler for AsciiDoc content."""

    def can_handle(self, content: str, content_type: Optional[str] = None) -> bool:
        """Check if content is AsciiDoc."""
        if content_type and "asciidoc" in content_type.lower():
            return True

        # Check for AsciiDoc patterns
        asciidoc_patterns = [
            r"^= \w+",         # Document title
            r"^== \w+",        # Section title
            r"^=== \w+",       # Section title
            r"^\[source,\w+\]", # Source block
            r"^\[NOTE\]",      # Admonition
            r"^\[TIP\]",       # Admonition
            r"^\[IMPORTANT\]", # Admonition
            r"^\[CAUTION\]",   # Admonition
            r"^\[WARNING\]"    # Admonition
        ]

        for pattern in asciidoc_patterns:
            if re.search(pattern, content, re.MULTILINE):
                return True

        return False

    async def process(self, content: str, base_url: Optional[str] = None) -> Dict[str, Any]:
        """Process AsciiDoc content."""
        try:
            import asciidocapi

            # Convert AsciiDoc to HTML
            import io
            output = io.StringIO()
            asciidoc = asciidocapi.AsciiDocAPI()
            asciidoc.options("--no-header-footer")
            asciidoc.execute(io.StringIO(content), output)
            html_content = output.getvalue()

            # Use the HTML processor to process the converted content
            from ..content_processor import ContentProcessor
            html_processor = ContentProcessor()
            return await html_processor.process(html_content, base_url)

        except ImportError:
            logger.warning("asciidocapi library not available, using basic processing")
            return {
                "formatted_content": content,
                "structure": self._extract_basic_structure(content)
            }

    def _extract_basic_structure(self, content: str) -> List[Dict[str, Any]]:
        """Extract basic structure from AsciiDoc content."""
        structure = []

        # Extract headings
        heading_pattern = r"^(=+) (.+)$"
        for line in content.split("\n"):
            match = re.match(heading_pattern, line)
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                structure.append({
                    "type": "heading",
                    "level": level,
                    "title": text
                })

        return structure

    def get_format_name(self) -> str:
        """Get format name."""
        return "AsciiDoc"
