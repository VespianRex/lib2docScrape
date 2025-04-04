"""Process HTML content into structured data and markdown."""
import html
import logging
from typing import Dict, Any, List
from bs4 import BeautifulSoup, Comment, NavigableString
from urllib.parse import urljoin, urlparse # Import urlparse
import bleach # Import bleach
# import markdownify as md # Removed markdownify import

from .content.models import ProcessedContent, ProcessorConfig
from .content.metadata_extractor import extract_metadata
from .content.asset_handler import AssetHandler
from .content.structure_handler import StructureHandler
from .content.code_handler import CodeHandler
from .content.url_handler import sanitize_and_join_url # Added import

# Configure logging
logging.basicConfig(level=logging.DEBUG) # Ensure logs are visible

logger = logging.getLogger(__name__)

class ContentProcessingError(Exception):
    """Custom exception for content processing errors."""
    pass

class ContentProcessor:
    """Process HTML content into structured data and markdown."""

    # Define allowed tags and attributes for bleach (can be refined/made configurable)
    ALLOWED_TAGS = bleach.sanitizer.ALLOWED_TAGS | {
        # Core structure
        'html', 'head', 'title', 'body',
        # Text content & Semantics
        'p', 'pre', 'code', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
        'img', 'blockquote', 'strong', 'em', 'b', 'i', 'u', 's', 'sub', 'sup',
        'br', 'hr', 'span', 'div', 'section', 'article', 'aside', 'nav', 'header', 'footer',
        'figure', 'figcaption',
        'img', # Explicitly allow img tag
        'video', 'audio', 'source', # Allow media tags
        'link', # Allow link tag for stylesheets etc.
        'head', 'base' # Allow head and base tags for base URL extraction
    }
    ALLOWED_ATTRIBUTES = {
        **bleach.sanitizer.ALLOWED_ATTRIBUTES,
        'a': ['href', 'title', 'target', 'rel'],
        'img': ['src', 'alt', 'title', 'width', 'height'], # Explicitly allow src for img
        'video': ['src', 'controls', 'width', 'height', 'poster'], # Allow video attributes
        'audio': ['src', 'controls'], # Allow audio attributes
        'source': ['src', 'type'], # Allow source attributes
        'link': ['rel', 'href', 'type', 'media'], # Allow link attributes
        'base': ['href'], # Allow href for base tag
        'code': ['class'], # Allow class for language hinting
        'pre': ['class'],
        'span': ['class'],
        'div': ['class'],
        'th': ['colspan', 'rowspan', 'scope'],
        'td': ['colspan', 'rowspan', 'headers'],
        # Allow 'id' on common elements for linking/styling
        '*': ['id', 'class', 'title', 'lang', 'dir'] # Removed 'style'
    }
    # Define allowed CSS properties if inline styles are allowed
    # ALLOWED_STYLES = ['color', 'background-color', 'font-weight', 'font-style', 'text-decoration'] # Removed as bleach.clean doesn't support 'styles' kwarg directly


    def __init__(self, config=None):
        """Initialize the content processor."""
        self.config = config or ProcessorConfig()
        self.result = ProcessedContent()
        self.content_filters = []
        self.url_filters = []
        self.metadata_extractors = []
        self.content_extractors: Dict[str, Any] = {}
        self.result.content["structure"] = []  # Initialize structure here

        # Initialize handlers
        # Initialize handlers (CodeHandler first)
        self.code_handler = CodeHandler(code_languages=self.config.code_languages)
        self.asset_handler = AssetHandler()
        self.structure_handler = StructureHandler(code_handler=self.code_handler, max_heading_level=self.config.max_heading_level) # Pass code_handler

    # --- Re-added _format_structure_to_markdown ---
    def _format_structure_to_markdown(self, structure: List[Dict[str, Any]], base_url: str = None) -> str:
        """Format document structure to markdown."""
        if not structure:
            return ""

        result = []
        for section in structure:
            section_markdown = ""
            section_type = section.get('type')

            if section_type == 'heading':
                header = '#' * section.get('level', 1)
                section_markdown = f"{header} {section.get('title', '')}"
            # Handle 'text' type which now contains list of inline parts
            elif section_type == 'text':
                parts = []
                for part in section.get('content', []): # Iterate through inline parts
                    part_type = part.get('type')
                    if part_type == 'text_inline':
                        parts.append(part.get('content', ''))
                    elif part_type == 'link_inline':
                        link_text = part.get('text', '')
                        link_href = part.get('href', '#')
                        safe_href = sanitize_and_join_url(link_href, base_url) # Use imported function
                        parts.append(f"[{link_text}]({safe_href})")
                    elif part_type == 'inline_code':
                        inline_code_content = part.get('content', '')
                        parts.append(f"`{inline_code_content}`")
                    # Add formatting for other inline types (strong, em) if extracted
                # Join parts - use empty string join as spaces are part of text_inline
                section_markdown = ''.join(parts)
            elif section_type == 'list':  # Handle lists
                list_content = section.get('content', [])
                if list_content:
                    tag_type = section.get('tag')
                    if tag_type == 'ul':
                        list_prefix = "* "
                        section_markdown = '\n'.join([f"{list_prefix}{item}" for item in list_content])
                    elif tag_type == 'ol':
                        section_markdown_lines = []
                        for index, item in enumerate(list_content):
                            list_prefix = f"{index + 1}. "
                            section_markdown_lines.append(f"{list_prefix}{item}")
                        section_markdown = '\n'.join(section_markdown_lines)
            elif section_type == 'code':  # Handle code blocks
                language = section.get('language')
                if language is None or self.code_handler.is_language_supported(language):
                     raw_code = section.get('content', '').strip()
                     section_markdown = f"```{language or ''}\n{raw_code}\n```"
            elif section_type == 'table':  # Handle tables
                table_content = section.get('content', {})
                headers = table_content.get('headers', [])
                if headers:
                    rows = table_content.get('rows', [])
                    table_lines = [
                        '| ' + ' | '.join(headers) + ' |',
                        '| ' + ' | '.join(['---'] * len(headers)) + ' |'
                    ]
                    table_lines.extend('| ' + ' | '.join(row) + ' |' for row in rows)
                    section_markdown = '\n'.join(table_lines)
            # Handle standalone links extracted by extract_structure
            elif section_type == 'link':
                link_text = section.get('text', '')
                link_href = section.get('href', '#')
                # Sanitize and resolve URL here before formatting (using top-level import)
                safe_href = sanitize_and_join_url(link_href, base_url)
                section_markdown = f"[{link_text}]({safe_href})"
            # Handle standalone inline_code extracted by extract_structure
            elif section_type == 'inline_code':
                inline_code_content = section.get('content', '')
                section_markdown = f"`{inline_code_content}`"
            # They are handled within the 'paragraph' type now.


            if section_markdown.strip():
                result.append(section_markdown.strip())

        return '\n\n'.join(result)
    # --- End Re-added _format_structure_to_markdown ---

    # _sanitize_soup method removed, replaced by bleach.clean() in process method
    async def process(self, html_content: str, base_url: str = None) -> ProcessedContent: # Make method async
        """Process HTML content and return structured result."""
        self.result = ProcessedContent()
        if not html_content or not html_content.strip():
            raise ContentProcessingError("Cannot process empty or whitespace-only content")
        headings_structure = [] # Initialize before try block

        # headings_structure = [] # Redundant initialization removed
        try:
            # --- Sanitize First ---
            # 1. Sanitize the raw HTML string first
            #    Note: bleach handles unescaping internally.
            cleaned_html = bleach.clean(
                html_content,
                tags=self.ALLOWED_TAGS,
                attributes=self.ALLOWED_ATTRIBUTES,
                protocols=bleach.sanitizer.ALLOWED_PROTOCOLS | {'data', 'ftp'}, # Allow data URIs and ftp
                # styles=self.ALLOWED_STYLES, # Removed unsupported 'styles' argument
                strip=True,
                strip_comments=not self.config.extract_comments
            )

            # 2. Check content length (of the cleaned content) *before* parsing
            content_length = len(cleaned_html)
            if content_length > self.config.max_content_length:
                raise ContentProcessingError(f"Cleaned content too long: {content_length} characters (limit: {self.config.max_content_length})")
            if content_length < self.config.min_content_length:
                raise ContentProcessingError(f"Cleaned content too short: {content_length} characters (limit: {self.config.min_content_length})")

            # --- Parse Cleaned HTML ---
            # 3. Parse the cleaned HTML *once*
            soup = BeautifulSoup(cleaned_html, 'html.parser')

            # --- Process Cleaned Soup ---
            # 4. Determine the effective base URL
            # Start with the base_url passed into the function
            effective_base_url = base_url
            # Try to find a <base> tag in the cleaned soup if allowed
            if 'head' in self.ALLOWED_TAGS and 'base' in self.ALLOWED_TAGS:
                base_tag = soup.find('base', href=True)
                allowed_base_attrs = self.ALLOWED_ATTRIBUTES.get('base', []) + self.ALLOWED_ATTRIBUTES.get('*', [])
                if base_tag and 'href' in allowed_base_attrs:
                    extracted_base_href = base_tag.get('href')
                    if extracted_base_href:
                        # Join the extracted href with the *original* passed base_url
                        effective_base_url = urljoin(base_url or '', extracted_base_href)
                        logger.debug(f"Using base URL from <base> tag: {effective_base_url}")
                    else:
                         logger.debug("Found <base> tag but href is empty.")
                else:
                     logger.debug("No valid <base> tag found in cleaned HTML.")
            else:
                 logger.debug("<head> or <base> tags not allowed by bleach config.")

            if not effective_base_url:
                 logger.warning("No effective base URL determined (none provided and none found/allowed in HTML).")


            # 5. Extract metadata from the cleaned soup
            metadata = extract_metadata(soup) if self.config.extract_metadata else {}
            self.result.metadata = metadata
            self.result.title = metadata.get('title', 'Untitled Document')

            # 6. Extract assets from the cleaned soup, using the determined effective_base_url
            if self.config.extract_assets:
                self.result.assets = self.asset_handler.extract_assets(soup, effective_base_url)
                # process_images simplified to just add assets, no longer modifies soup significantly
                self.asset_handler.process_images(soup, effective_base_url)

            # 7. Extract structure and headings *before* modifying soup further
            full_structure = self.structure_handler.extract_structure(soup) # This contains links, text, etc.
            headings = self.structure_handler.extract_headings(soup)
            # headings_structure is no longer needed for the main structure field
            # headings_structure = [{'type': 'heading', 'level': h['level'], 'text': h['text']} for h in headings]

            # 8. Process code blocks in the cleaned soup (modifies soup)
            if self.config.extract_code_blocks:
                self.code_handler.process_code_blocks(soup) # Re-enabled

            # 9. Generate markdown from the *original* extracted structure (before code block modification)
            # Pass full_structure to markdown formatter
            formatted_content = self._format_structure_to_markdown(full_structure, effective_base_url)

            # 10. Store results
            # Reverted structure storage
            # Assign the full structure to the dedicated attribute
            self.result.structure = full_structure
            # Assign headings separately
            self.result.headings = headings
            # Content dict now only needs formatted_content (if kept)
            self.result.content = {
                'formatted_content': formatted_content or '', # Default to empty string
                # 'structure' key removed from here
                # 'headings' key removed from here (now a top-level attribute)
            }

            return self.result

        except Exception as e:
            logger.error(f"Error processing content: {str(e)}", exc_info=True) # Log traceback
            self.result.errors.append(f"Error processing content: {str(e)}")
            # Ensure default structure even on error
            self.result.content = {
                'formatted_content': '',
                # 'structure' key removed from here
                'headings': [], # Keep headings empty on error
            }
            # Ensure structure is also default on error
            if not self.result.structure:
                 self.result.structure = []
            # Ensure assets and metadata are initialized if error occurs early
            # Check self.result directly
            if not hasattr(self.result, 'assets') or not self.result.assets:
                 self.result.assets = {'images': [], 'stylesheets': [], 'scripts': [], 'media': []}
            if not self.result.metadata:
                 self.result.metadata = {}

            return self.result

    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the processor with custom settings."""
        if isinstance(config, dict):
            # Update existing config fields based on input dict
            for key, value in config.items():
                # Skip blocked_attributes if present in the input config dict
                if key == 'blocked_attributes':
                    logger.warning("Ignoring 'blocked_attributes' in config, use bleach settings instead.")
                    continue
                if hasattr(self.config, key):
                    setattr(self.config, key, value)

            # Re-initialize handlers if relevant config changed
            code_handler_changed = 'code_languages' in config
            heading_level_changed = 'max_heading_level' in config

            if code_handler_changed:
                 self.code_handler = CodeHandler(code_languages=self.config.code_languages)
                 # Always re-init StructureHandler if CodeHandler changed
                 self.structure_handler = StructureHandler(code_handler=self.code_handler, max_heading_level=self.config.max_heading_level)
            elif heading_level_changed:
                 # Re-init StructureHandler if only max_heading_level changed (and code_handler didn't)
                 # Ensure self.code_handler exists before passing
                 if hasattr(self, 'code_handler'):
                      self.structure_handler = StructureHandler(code_handler=self.code_handler, max_heading_level=self.config.max_heading_level)
                 else:
                      # This case should ideally not happen if __init__ ran correctly
                      logger.error("CodeHandler not initialized before reconfiguring StructureHandler.")
                      # Fallback: Initialize without code_handler (might lead to issues)
                      self.structure_handler = StructureHandler(max_heading_level=self.config.max_heading_level)


    def add_content_filter(self, filter_func):
        """Add a custom content filter."""
        self.content_filters.append(filter_func)

    def add_url_filter(self, filter_func):
        """Add a custom URL filter."""
        self.url_filters.append(filter_func)

    def add_metadata_extractor(self, extractor):
        """Add a custom metadata extractor."""
        self.metadata_extractors.append(extractor)
