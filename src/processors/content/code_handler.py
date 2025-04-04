"""Handle code blocks and syntax highlighting."""
import logging
import textwrap
from typing import Optional
from bs4 import BeautifulSoup, Tag

# Configure logging
logger = logging.getLogger(__name__)

class CodeHandler:
    """Process and format code blocks with language detection."""

    def __init__(self, code_languages: list[str]):
        self.code_languages = code_languages

    def process_code_blocks(self, soup: BeautifulSoup) -> None:
        """Process code blocks with enhanced language detection."""
        # First handle code blocks (pre + code)
        for pre in soup.find_all('pre'):
            code = pre.find('code')
            if code:
                # First try to get language directly from the class
                language = self._detect_language(code)
                # Process code content only if language is supported
                if language and self.is_language_supported(language):
                    markdown_block = self._format_code_block(code, language)
                    pre.string = markdown_block  # Use string to prevent HTML parsing
                elif language: # Language detected but not supported, remove the pre block
                    pre.decompose()
                else: # No language detected, format as plain code block
                    markdown_block = self._format_code_block(code, None) # Pass None for language
                    pre.string = markdown_block

        # Then handle inline code (standalone code tags)
        for code in soup.find_all('code', recursive=True):
            # Skip if this code tag is inside a pre tag
            if not code.find_parent('pre'):
                inline_code = self._format_inline_code(code)
                code.string = inline_code

    def _detect_language(self, code: Tag) -> Optional[str]:
        """Detect programming language from code tag classes."""
        if 'class' in code.attrs:
            classes = code['class'] if isinstance(code['class'], list) else [code['class']]
            for cls in classes:
                if cls.lower() == 'python':
                    return 'python'
                if cls.lower() == 'javascript':  # Add explicit javascript recognition
                    return 'javascript'
                for prefix in ['language-', 'lang-', 'brush:', 'syntax-']:
                    if cls.lower().startswith(prefix):
                        lang = cls[len(prefix):].lower()
                        if lang in self.code_languages:
                            return lang
        return None

    def _format_code_block(self, code: Tag, language: Optional[str] = None) -> str:
        """Format code blocks with language and indentation handling."""
        # Get the raw content to preserve HTML entities and tags
        raw_code_text = ''.join(str(content) for content in code.contents)
        if raw_code_text:
            # Dedent first to handle common indentation
            dedented_code = textwrap.dedent(raw_code_text)
            # Then strip leading/trailing whitespace/newlines
            code_text = dedented_code.strip()

            # Prepend language to code text if available
            lang_marker = language if language else ''
            markdown_block = f"```{lang_marker}\n{code_text}\n```" # code_text is already stripped
            return markdown_block
        return ''

    def _format_inline_code(self, code: Tag) -> str:
        """Format inline code with single backticks."""
        code_text = ''.join(str(content) for content in code.contents)
        if code_text:
            return f"`{code_text.strip()}`"
        return ''

    def is_language_supported(self, language: str) -> bool:
        """Check if a language is supported for syntax highlighting."""
        return language.lower() in (lang.lower() for lang in self.code_languages)