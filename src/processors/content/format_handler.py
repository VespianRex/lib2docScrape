"""
Documentation format handler for lib2docScrape.

This module provides support for various documentation formats:
- Markdown
- reStructuredText
- AsciiDoc
- HTML
- Plain text
"""
import logging
import re
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Union, Any

from bs4 import BeautifulSoup

from src.utils.error_handler import ErrorContext, handle_error, ErrorCategory, ErrorLevel
from src.utils.performance import memoize, CacheConfig, CacheStrategy

logger = logging.getLogger(__name__)

class DocFormat(str, Enum):
    """Supported documentation formats."""
    MARKDOWN = "markdown"
    RST = "rst"
    ASCIIDOC = "asciidoc"
    HTML = "html"
    PLAIN = "plain"
    UNKNOWN = "unknown"


class FormatDetectionResult:
    """Result of format detection."""

    def __init__(self, format_type: DocFormat, confidence: float, metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize format detection result.

        Args:
            format_type: Detected format
            confidence: Confidence level (0.0-1.0)
            metadata: Optional metadata about the format
        """
        self.format_type = format_type
        self.confidence = confidence
        self.metadata = metadata or {}


class FormatHandler:
    """Handler for different documentation formats."""

    def __init__(self):
        """Initialize the format handler."""
        self.format_detectors = {
            DocFormat.MARKDOWN: self._detect_markdown,
            DocFormat.RST: self._detect_rst,
            DocFormat.ASCIIDOC: self._detect_asciidoc,
            DocFormat.HTML: self._detect_html,
        }

        self.format_converters = {
            DocFormat.MARKDOWN: {
                DocFormat.HTML: self._markdown_to_html,
                DocFormat.PLAIN: self._markdown_to_plain,
            },
            DocFormat.RST: {
                DocFormat.HTML: self._rst_to_html,
                DocFormat.PLAIN: self._rst_to_plain,
                DocFormat.MARKDOWN: self._rst_to_markdown,
            },
            DocFormat.ASCIIDOC: {
                DocFormat.HTML: self._asciidoc_to_html,
                DocFormat.PLAIN: self._asciidoc_to_plain,
                DocFormat.MARKDOWN: self._asciidoc_to_markdown,
            },
            DocFormat.HTML: {
                DocFormat.PLAIN: self._html_to_plain,
                DocFormat.MARKDOWN: self._html_to_markdown,
            },
        }

    @memoize(config=CacheConfig(strategy=CacheStrategy.LRU, max_size=100))
    def detect_format(self, content: str) -> FormatDetectionResult:
        """
        Detect the format of the content.

        Args:
            content: Content to detect format for

        Returns:
            Format detection result
        """
        if not content or not content.strip():
            return FormatDetectionResult(DocFormat.PLAIN, 1.0)

        # Check if content is HTML
        if content.strip().startswith(("<html", "<!DOCTYPE", "<body", "<div")):
            return FormatDetectionResult(DocFormat.HTML, 1.0)

        # Try each detector
        results = []
        for format_type, detector in self.format_detectors.items():
            try:
                result = detector(content)
                if result.confidence > 0.0:
                    results.append(result)
            except Exception as e:
                handle_error(
                    e,
                    "FormatHandler",
                    "detect_format",
                    details={"format": format_type.value},
                    level=ErrorLevel.WARNING
                )

        # Return the result with highest confidence
        if results:
            return max(results, key=lambda r: r.confidence)

        # Default to plain text
        return FormatDetectionResult(DocFormat.PLAIN, 0.5)

    def convert(self, content: str, from_format: DocFormat, to_format: DocFormat) -> str:
        """
        Convert content from one format to another.

        Args:
            content: Content to convert
            from_format: Source format
            to_format: Target format

        Returns:
            Converted content
        """
        # No conversion needed
        if from_format == to_format:
            return content

        # Check if direct converter exists
        if from_format in self.format_converters and to_format in self.format_converters[from_format]:
            converter = self.format_converters[from_format][to_format]
            try:
                return converter(content)
            except Exception as e:
                handle_error(
                    e,
                    "FormatHandler",
                    "convert",
                    details={"from": from_format.value, "to": to_format.value},
                    level=ErrorLevel.ERROR
                )
                return content

        # Try to convert via HTML as intermediate format
        if from_format in self.format_converters and DocFormat.HTML in self.format_converters[from_format]:
            try:
                html_content = self.format_converters[from_format][DocFormat.HTML](content)
                if DocFormat.HTML in self.format_converters and to_format in self.format_converters[DocFormat.HTML]:
                    return self.format_converters[DocFormat.HTML][to_format](html_content)
            except Exception as e:
                handle_error(
                    e,
                    "FormatHandler",
                    "convert",
                    details={"from": from_format.value, "to": to_format.value, "via": "html"},
                    level=ErrorLevel.ERROR
                )

        # Fallback: return original content
        logger.warning(f"No converter found from {from_format} to {to_format}")
        return content

    def _detect_markdown(self, content: str) -> FormatDetectionResult:
        """
        Detect if content is Markdown.

        Args:
            content: Content to check

        Returns:
            Format detection result
        """
        # Check for common Markdown patterns
        patterns = [
            r'^#\s+.+$',  # Headers
            r'^-\s+.+$',  # List items
            r'^\*\s+.+$',  # List items
            r'^\d+\.\s+.+$',  # Numbered list
            r'^\[.+\]\(.+\)$',  # Links
            r'^!\[.+\]\(.+\)$',  # Images
            r'^```',  # Code blocks
            r'^\*\*.+\*\*',  # Bold
            r'^\*.+\*',  # Italic
        ]

        matches = 0
        lines = content.split('\n')
        for line in lines:
            for pattern in patterns:
                if re.match(pattern, line.strip()):
                    matches += 1
                    break

        confidence = min(0.9, matches / max(1, len(lines)) * 2)

        # Check for front matter
        if content.startswith('---') and '---' in content[3:]:
            confidence += 0.1

        return FormatDetectionResult(
            DocFormat.MARKDOWN,
            min(1.0, confidence),
            {"matches": matches}
        )

    def _detect_rst(self, content: str) -> FormatDetectionResult:
        """
        Detect if content is reStructuredText.

        Args:
            content: Content to check

        Returns:
            Format detection result
        """
        # Check for common RST patterns
        patterns = [
            r'^={3,}$',  # Section underlines
            r'^-{3,}$',  # Section underlines
            r'^~{3,}$',  # Section underlines
            r'^\.{3,}$',  # Section underlines
            r'^\.\.\s+\w+::',  # Directives
            r'^\.\.\s+_\w+:',  # References
            r'^\s*:[\w-]+:',  # Field lists
            r'`[^`]+`_',  # Hyperlink references
            r'^\s*\.\.\s+\[[\d#]+\]',  # Footnotes
            r'^\s*\.\.\s+code-block::\s+\w+$',  # Code blocks
        ]

        matches = 0
        lines = content.split('\n')
        for line in lines:
            for pattern in patterns:
                if re.match(pattern, line.strip()):
                    matches += 1
                    break

        confidence = min(0.9, matches / max(1, len(lines)) * 2)

        return FormatDetectionResult(
            DocFormat.RST,
            min(1.0, confidence),
            {"matches": matches}
        )

    def _detect_asciidoc(self, content: str) -> FormatDetectionResult:
        """
        Detect if content is AsciiDoc.

        Args:
            content: Content to check

        Returns:
            Format detection result
        """
        # Check for common AsciiDoc patterns
        patterns = [
            r'^=\s+.+$',  # Document title
            r'^==\s+.+$',  # Section title
            r'^===\s+.+$',  # Section title
            r'^:[\w-]+:',  # Attribute entries
            r'^\[[\w,]+\]$',  # Block attributes
            r'^\[source,\s*\w+\]$',  # Source blocks
            r'^----$',  # Delimited blocks
            r'^====+$',  # Delimited blocks
            r'^\.[\w\s]+$',  # Block titles
            r'link:[\w:/.]+\[.+\]',  # Links
        ]

        matches = 0
        lines = content.split('\n')
        for line in lines:
            for pattern in patterns:
                if re.match(pattern, line.strip()):
                    matches += 1
                    break

        confidence = min(0.9, matches / max(1, len(lines)) * 2)

        return FormatDetectionResult(
            DocFormat.ASCIIDOC,
            min(1.0, confidence),
            {"matches": matches}
        )

    def _detect_html(self, content: str) -> FormatDetectionResult:
        """
        Detect if content is HTML.

        Args:
            content: Content to check

        Returns:
            Format detection result
        """
        # Check for HTML tags
        if re.search(r'<[a-z]+[^>]*>', content, re.IGNORECASE):
            confidence = 0.7

            # Check for doctype or html tag
            if re.search(r'<!DOCTYPE\s+html|<html', content, re.IGNORECASE):
                confidence = 1.0

            return FormatDetectionResult(
                DocFormat.HTML,
                confidence
            )

        return FormatDetectionResult(DocFormat.HTML, 0.0)

    def _markdown_to_html(self, content: str) -> str:
        """
        Convert Markdown to HTML.

        Args:
            content: Markdown content

        Returns:
            HTML content
        """
        try:
            import markdown
            return markdown.markdown(content, extensions=['extra', 'codehilite', 'tables', 'toc'])
        except ImportError:
            logger.warning("markdown package not installed, using basic conversion")
            # Basic conversion
            html = content
            # Headers
            html = re.sub(r'^#\s+(.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
            html = re.sub(r'^##\s+(.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
            html = re.sub(r'^###\s+(.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
            # Bold and italic
            html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
            html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
            # Links
            html = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', html)
            # Lists
            html = re.sub(r'^-\s+(.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
            html = re.sub(r'(<li>.+</li>\n)+', r'<ul>\n\g<0></ul>', html)
            return f"<html><body>{html}</body></html>"

    def _markdown_to_plain(self, content: str) -> str:
        """
        Convert Markdown to plain text.

        Args:
            content: Markdown content

        Returns:
            Plain text content
        """
        # Convert to HTML first, then to plain text
        html = self._markdown_to_html(content)
        return self._html_to_plain(html)

    def _rst_to_html(self, content: str) -> str:
        """
        Convert reStructuredText to HTML.

        Args:
            content: RST content

        Returns:
            HTML content
        """
        try:
            from docutils.core import publish_string
            html = publish_string(content, writer_name='html').decode('utf-8')
            return html
        except ImportError:
            logger.warning("docutils package not installed, using HTML conversion")
            # Convert to HTML via Markdown as intermediate format
            markdown = self._rst_to_markdown(content)
            return self._markdown_to_html(markdown)

    def _rst_to_plain(self, content: str) -> str:
        """
        Convert reStructuredText to plain text.

        Args:
            content: RST content

        Returns:
            Plain text content
        """
        try:
            from docutils.core import publish_string
            text = publish_string(content, writer_name='text').decode('utf-8')
            return text
        except ImportError:
            logger.warning("docutils package not installed, using HTML conversion")
            # Convert to HTML first, then to plain text
            html = self._rst_to_html(content)
            return self._html_to_plain(html)

    def _rst_to_markdown(self, content: str) -> str:
        """
        Convert reStructuredText to Markdown.

        Args:
            content: RST content

        Returns:
            Markdown content
        """
        try:
            from m2r import convert
            return convert(content)
        except ImportError:
            logger.warning("m2r package not installed, using basic conversion")
            # Basic conversion
            markdown = content
            # Headers
            markdown = re.sub(r'^(.+)\n={3,}$', r'# \1', markdown, flags=re.MULTILINE)
            markdown = re.sub(r'^(.+)\n-{3,}$', r'## \1', markdown, flags=re.MULTILINE)
            markdown = re.sub(r'^(.+)\n~{3,}$', r'### \1', markdown, flags=re.MULTILINE)
            # Code blocks
            markdown = re.sub(r'^\.\.\s+code-block::\s+(\w+)\s*\n\s*\n([\s\S]+?)(?=\n\S|\Z)',
                             r'```\1\n\2\n```', markdown, flags=re.MULTILINE)
            return markdown

    def _asciidoc_to_html(self, content: str) -> str:
        """
        Convert AsciiDoc to HTML.

        Args:
            content: AsciiDoc content

        Returns:
            HTML content
        """
        try:
            import asciidoc
            return asciidoc.AsciiDocAPI().convert(content, backend='html5')
        except ImportError:
            try:
                import asciidocapi
                asciidoc_api = asciidocapi.AsciiDocAPI()
                import io
                output = io.StringIO()
                asciidoc_api.execute(content, output)
                return output.getvalue()
            except ImportError:
                logger.warning("asciidoc package not installed, using basic conversion")
                # Convert to Markdown as intermediate format
                markdown = self._asciidoc_to_markdown(content)
                return self._markdown_to_html(markdown)

    def _asciidoc_to_plain(self, content: str) -> str:
        """
        Convert AsciiDoc to plain text.

        Args:
            content: AsciiDoc content

        Returns:
            Plain text content
        """
        # Convert to HTML first, then to plain text
        html = self._asciidoc_to_html(content)
        return self._html_to_plain(html)

    def _asciidoc_to_markdown(self, content: str) -> str:
        """
        Convert AsciiDoc to Markdown.

        Args:
            content: AsciiDoc content

        Returns:
            Markdown content
        """
        # Basic conversion
        markdown = content
        # Headers
        markdown = re.sub(r'^=\s+(.+)$', r'# \1', markdown, flags=re.MULTILINE)
        markdown = re.sub(r'^==\s+(.+)$', r'## \1', markdown, flags=re.MULTILINE)
        markdown = re.sub(r'^===\s+(.+)$', r'### \1', markdown, flags=re.MULTILINE)
        # Code blocks
        markdown = re.sub(r'^\[source,\s*(\w+)\]\s*\n----\s*\n([\s\S]+?)----',
                         r'```\1\n\2\n```', markdown, flags=re.MULTILINE)
        # Links
        markdown = re.sub(r'link:([^\[]+)\[([^\]]+)\]', r'[\2](\1)', markdown)
        return markdown

    def _html_to_plain(self, content: str) -> str:
        """
        Convert HTML to plain text.

        Args:
            content: HTML content

        Returns:
            Plain text content
        """
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            return soup.get_text(separator='\n')
        except ImportError:
            logger.warning("BeautifulSoup not installed, using basic conversion")
            # Basic conversion
            text = content
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', '', text)
            # Decode HTML entities
            text = re.sub(r'&lt;', '<', text)
            text = re.sub(r'&gt;', '>', text)
            text = re.sub(r'&amp;', '&', text)
            text = re.sub(r'&quot;', '"', text)
            text = re.sub(r'&apos;', "'", text)
            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text)
            return text.strip()

    def _html_to_markdown(self, content: str) -> str:
        """
        Convert HTML to Markdown.

        Args:
            content: HTML content

        Returns:
            Markdown content
        """
        try:
            import html2text
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = False
            h.ignore_tables = False
            return h.handle(content)
        except ImportError:
            logger.warning("html2text not installed, using basic conversion")
            # Basic conversion using BeautifulSoup
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(content, 'html.parser')

                # Process headings
                for i in range(1, 7):
                    for heading in soup.find_all(f'h{i}'):
                        heading.replace_with(f"{'#' * i} {heading.get_text()}\n\n")

                # Process paragraphs
                for p in soup.find_all('p'):
                    p.replace_with(f"{p.get_text()}\n\n")

                # Process links
                for a in soup.find_all('a'):
                    href = a.get('href', '')
                    text = a.get_text()
                    a.replace_with(f"[{text}]({href})")

                # Process lists
                for ul in soup.find_all('ul'):
                    for li in ul.find_all('li'):
                        li.replace_with(f"- {li.get_text()}\n")

                for ol in soup.find_all('ol'):
                    for i, li in enumerate(ol.find_all('li')):
                        li.replace_with(f"{i+1}. {li.get_text()}\n")

                return soup.get_text()
            except ImportError:
                # Fallback to plain text
                return self._html_to_plain(content)
