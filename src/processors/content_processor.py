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

    # --- Updated _format_structure_to_markdown ---
    def _format_structure_to_markdown(self, structure: List[Dict[str, Any]], base_url: str = None, list_level: int = 0) -> str:
        """Format document structure to markdown. Added list_level for indentation."""
        if not structure:
            return ""

        result = []
        indent = "  " * list_level # Indentation for nested lists

        for section in structure:
            section_markdown = None # Initialize to None to detect if handled
            section_type = section.get('type')

            if section_type == 'heading':
                header = '#' * section.get('level', 1)
                section_markdown = f"{header} {section.get('title', '')}"
            elif section_type == 'text':
                parts = []
                for part in section.get('content', []): # Iterate through inline parts
                    part_type = part.get('type')
                    if part_type == 'text_inline':
                        parts.append(part.get('content', ''))
                    elif part_type == 'link_inline':
                        link_text = part.get('text', '')
                        link_href = part.get('href', '#')
                        safe_href = sanitize_and_join_url(link_href, base_url)
                        parts.append(f"[{link_text}]({safe_href})")
                    elif part_type == 'inline_code':
                        inline_code_content = part.get('content', '')
                        parts.append(f"`{inline_code_content}`")
                    # Handle other inline types recursively if needed
                    elif part.get('content') and isinstance(part.get('content'), list):
                         inner_md = self._format_structure_to_markdown(part['content'], base_url, list_level) # Pass current level
                         if part_type == 'strong' or part_type == 'b':
                              parts.append(f"**{inner_md}**")
                         elif part_type == 'em' or part_type == 'i':
                              parts.append(f"*{inner_md}*")
                         else: parts.append(inner_md)
                    elif part_type == 'linebreak':
                         parts.append("  \n")
                section_markdown = ''.join(parts)
            # Corrected list handling: Check for type 'list'
            elif section_type == 'list':
                list_items_structure = section.get('content', []) # Content is now a list of lists (sub-structures)
                if list_items_structure:
                    tag_type = section.get('tag') # Get 'ul' or 'ol' from the tag field
                    markdown_items = []
                    for index, item_structure in enumerate(list_items_structure): # item_structure is the content of one li
                        item_content_md = self._format_structure_to_markdown(item_structure, base_url, list_level + 1)
                        item_content_md = item_content_md.strip() # Strip result of recursive call
                        if item_content_md:
                            if tag_type == 'ul': list_prefix = "* "
                            elif tag_type == 'ol': list_prefix = f"{index + 1}. "
                            else: list_prefix = "- " # Fallback
                            lines = item_content_md.split('\n')
                            formatted_item = f"{indent}{list_prefix}{lines[0]}"
                            if len(lines) > 1:
                                formatted_item += '\n' + '\n'.join(f"{indent}  {line}" for line in lines[1:])
                            markdown_items.append(formatted_item)
                    section_markdown = '\n'.join(markdown_items)

            elif section_type == 'code':  # Handle code blocks
                language = section.get('language')
                # Check if language is supported before formatting
                if language is None or self.code_handler.is_language_supported(language):
                    raw_code = section.get('content', '').strip()
                    section_markdown = f"```{language or ''}\n{raw_code}\n```"
                # else: implicitly section_markdown remains None, skipping the block
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
            # --- Added direct handling for inline types at this level ---
            elif section_type == 'text_inline':
                section_markdown = section.get('content', '')
            elif section_type == 'link_inline':
                link_text = section.get('text', '')
                link_href = section.get('href', '#')
                # Sanitize the URL, default to '#' if invalid/unsafe
                safe_href = sanitize_and_join_url(link_href, base_url) or "#"
                # Always generate the markdown link, using '#' for invalid URLs
                section_markdown = f"[{link_text}]({safe_href})"
            elif section_type == 'inline_code':
                inline_code_content = section.get('content', '')
                section_markdown = f"`{inline_code_content}`"
            elif section_type in ['strong', 'em', 'b', 'i'] and isinstance(section.get('content'), list):
                 inner_md = self._format_structure_to_markdown(section['content'], base_url, list_level)
                 if section_type == 'strong' or section_type == 'b': section_markdown = f"**{inner_md}**"
                 elif section_type == 'em' or section_type == 'i': section_markdown = f"*{inner_md}*"
                 else: section_markdown = inner_md # Fallback
            elif section_type == 'linebreak':
                 section_markdown = "  \n" # Represent <br> as markdown line break

            # Only append if markdown was generated (avoids extra newlines for ignored elements)
            if section_markdown is not None: # Check for None, not just truthiness
                 # Append without adding extra indentation here; indentation is handled within list logic
                 # Strip only if it's not just whitespace intended for line breaks
                 append_content = section_markdown if section_markdown == "  \n" else section_markdown.strip()
                 # Append even if empty if it was text_inline (to preserve structure)
                 if append_content or section_type == 'text_inline':
                      result.append(append_content)


        # Join with double newlines only for top-level elements
        # Join with single newline for elements within a list item
        joiner = '\n\n' if list_level == 0 else '' # Use empty joiner for inline/list items
        # Simpler join, rely on content being correctly formatted including potential empty strings
        return joiner.join(result)

    # --- End Updated _format_structure_to_markdown ---

    # _sanitize_soup method removed, replaced by bleach.clean() in process method
    async def process(self, html_content: str, base_url: str = None) -> ProcessedContent: # Make method async
        """Process HTML content and return structured result."""
        self.result = ProcessedContent()
        if not html_content or not html_content.strip():
            raise ContentProcessingError("Cannot process empty or whitespace-only content")
        # headings_structure = [] # Removed redundant initialization

        try:
            # --- Pre-process to remove unwanted tags ---
            # 1. Parse raw HTML
            temp_soup = BeautifulSoup(html_content, 'html.parser')

            # 2. Remove script, style, noscript tags entirely
            # 2. Remove script, style, noscript, and iframe tags entirely
            for tag_name in ['script', 'style', 'noscript', 'iframe']:
                for tag in temp_soup.find_all(tag_name):
                    tag.decompose()

            # 3. Get the HTML string after removal
            pre_cleaned_html = str(temp_soup)

            # --- Sanitize Remaining HTML ---
            # 4. Sanitize the pre-cleaned HTML string
            cleaned_html = bleach.clean(
                pre_cleaned_html,
                tags=self.ALLOWED_TAGS,
                attributes=self.ALLOWED_ATTRIBUTES,
                protocols=bleach.sanitizer.ALLOWED_PROTOCOLS | {'data', 'ftp'},
                strip=True, # Strip tags not in ALLOWED_TAGS
                strip_comments=not self.config.extract_comments
            )
            # logger.debug(f"Cleaned HTML after bleach:\n{cleaned_html}") # Optional debug

            # 5. Check content length (of the final cleaned content) *before* full parsing
            content_length = len(cleaned_html)
            if content_length > self.config.max_content_length:
                raise ContentProcessingError(f"Cleaned content too long: {content_length} characters (limit: {self.config.max_content_length})")
            if content_length < self.config.min_content_length:
                raise ContentProcessingError(f"Cleaned content too short: {content_length} characters (limit: {self.config.min_content_length})")

            # --- Parse Cleaned HTML ---
            # 6. Parse the cleaned HTML *once*
            soup = BeautifulSoup(cleaned_html, 'html.parser')

            # --- Process Cleaned Soup ---
            # 7. Determine the effective base URL
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


            # 8. Extract metadata from the cleaned soup
            metadata = extract_metadata(soup) if self.config.extract_metadata else {}
            self.result.metadata = metadata
            self.result.title = metadata.get('title', 'Untitled Document')

            # 9. Extract assets from the cleaned soup, using the determined effective_base_url
            if self.config.extract_assets:
                self.result.assets = self.asset_handler.extract_assets(soup, effective_base_url)
                # process_images simplified to just add assets, no longer modifies soup significantly
                self.asset_handler.process_images(soup, effective_base_url)

            # 10. Extract structure and headings *before* modifying soup further
            full_structure = self.structure_handler.extract_structure(soup) # This contains links, text, etc.
            headings = self.structure_handler.extract_headings(soup)
            # headings_structure is no longer needed for the main structure field

            # 11. Process code blocks in the cleaned soup (modifies soup)
            # This step is likely redundant now as structure is extracted first
            # if self.config.extract_code_blocks:
            #     self.code_handler.process_code_blocks(soup) # Re-enabled

            # 12. Generate markdown from the *original* extracted structure
            # Pass full_structure to markdown formatter
            formatted_content = self._format_structure_to_markdown(full_structure, effective_base_url)

            # 13. Add calculated metadata flags
            self.result.metadata['has_code_blocks'] = any(item.get('type') == 'code' for item in full_structure)
            self.result.metadata['has_tables'] = any(item.get('type') == 'table' for item in full_structure)

            # 14. Store results
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
