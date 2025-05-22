"""Process HTML content into structured data and markdown."""
import html
import logging
from typing import Dict, Any, List
from bs4 import BeautifulSoup, Comment, NavigableString
from urllib.parse import urljoin, urlparse # Import urlparse
import bleach # Import bleach
import markdownify as md # Added markdownify for HTML to Markdown conversion

from .content.models import ProcessedContent, ProcessorConfig

# Default configuration class for when a mock is used
class DefaultProcessorConfig:
    def __init__(self):
        self.max_content_length = 100000
        self.min_content_length = 10
        self.extract_metadata = True
        self.extract_assets = True
        self.extract_code_blocks = True
        self.extract_comments = False
        self.code_languages = ["python", "javascript", "html", "css", "java", "c", "cpp"]
        self.max_heading_level = 6
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
        if config is None:
            # Use ProcessorConfig if available, otherwise use DefaultProcessorConfig
            try:
                self.config = ProcessorConfig()
            except Exception:
                logger.warning("ProcessorConfig not available, using DefaultProcessorConfig")
                self.config = DefaultProcessorConfig()
        else:
            self.config = config
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

    # _format_structure_to_markdown method removed as markdown conversion is now handled by markdownify library.
    async def process(self, content: str, base_url: str = None, content_type: str = None) -> ProcessedContent:
        """
        Process content and return structured result.

        Args:
            content: The content to process (HTML, Markdown, etc.)
            base_url: Optional base URL for resolving relative links
            content_type: Optional content type hint

        Returns:
            ProcessedContent object with the processed content
        """
        self.result = ProcessedContent()
        if not content or not content.strip():
            raise ContentProcessingError("Cannot process empty or whitespace-only content")

        # Detect content type if not provided
        if not content_type:
            from .content.format_detector import ContentTypeDetector
            content_type = ContentTypeDetector.detect_from_content(content)

        # Use format detector to get the appropriate handler
        from .content.format_detector import FormatDetector
        from .content.format_handlers import HTMLHandler, MarkdownHandler, ReStructuredTextHandler, AsciiDocHandler

        # Initialize format detector
        detector = FormatDetector()

        # Register handlers
        detector.register_handler(HTMLHandler(self))
        detector.register_handler(MarkdownHandler())
        detector.register_handler(ReStructuredTextHandler())
        detector.register_handler(AsciiDocHandler())

        # Detect format and get handler
        handler = detector.detect_format(content, content_type)

        # If a handler was found, use it to process the content
        if handler:
            logger.info(f"Using {handler.get_format_name()} handler to process content")

            # If it's the HTML handler, we'll process it directly
            if handler.get_format_name() == "HTML":
                # Process as HTML (original implementation)
                html_content = content
            else:
                # For non-HTML formats, use the handler to process the content
                try:
                    processed_data = await handler.process(content, base_url)

                    # Update the result with the processed data
                    self.result.content = processed_data

                    # If the handler returned structure, use it
                    if "structure" in processed_data:
                        self.result.structure = processed_data["structure"]

                    # If the handler returned headings, use them
                    if "headings" in processed_data:
                        self.result.headings = processed_data["headings"]

                    # If the handler returned metadata, use it
                    if "metadata" in processed_data:
                        self.result.metadata = processed_data["metadata"]

                    # If the handler returned assets, use them
                    if "assets" in processed_data:
                        self.result.assets = processed_data["assets"]

                    # If the handler returned a title, use it
                    if "title" in processed_data:
                        self.result.title = processed_data["title"]

                    # Return the result
                    return self.result

                except Exception as e:
                    logger.error(f"Error processing with {handler.get_format_name()} handler: {str(e)}")
                    # Fall back to HTML processing
                    logger.info("Falling back to HTML processing")
                    html_content = content

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
            else:
                logger.debug(f"ContentProcessor.process: effective_base_url='{effective_base_url}'")


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

            # Fallback for headings if structure handler fails to extract them
            if not headings and self.config.max_heading_level > 0:
                headings = []
                for level in range(1, min(7, self.config.max_heading_level + 1)):
                    for tag in soup.find_all(f'h{level}'):
                        heading_text = tag.get_text(strip=True)
                        headings.append({
                            "level": level,
                            "text": heading_text,
                            "id": tag.get('id', ''),
                            "type": "heading"
                        })
                logger.debug(f"Extracted {len(headings)} headings as fallback")

            # 11. Process code blocks in the cleaned soup (modifies soup)
            # This step is likely redundant now as structure is extracted first
            # if self.config.extract_code_blocks:
            #     self.code_handler.process_code_blocks(soup) # Re-enabled

            # 12. Generate markdown using the markdownify library.
            # Convert the BeautifulSoup object to string before passing to markdownify.
            # Use effective_base_url for markdownify's basefmt option to handle relative links.
            # Use ATX style headings (e.g., # Heading)
            formatted_content = md.markdownify(str(soup), basefmt=effective_base_url, heading_style=md.ATX)

            # 13. Add calculated metadata flags
            self.result.metadata['has_code_blocks'] = any(item.get('type') == 'code' for item in full_structure)
            self.result.metadata['has_tables'] = any(item.get('type') == 'table' for item in full_structure)

            # 14. Store results
            # Assign the full structure to the dedicated attribute
            self.result.structure = full_structure
            # Assign headings separately
            self.result.headings = headings
            # 14. Store results
            # Assign the full structure to the dedicated attribute
            self.result.structure = full_structure
            # Assign headings separately
            self.result.headings = headings
            # Store the markdownify output.
            self.result.content = {
                'formatted_content': formatted_content or '', # Markdownify output
            }

            # Ensure structure contains at least basic headings if it's empty
            if not self.result.structure and headings:
                self.result.structure = [
                    {"type": "heading", "level": h["level"], "title": h["text"]}
                    for h in headings
                ]

            return self.result

        except Exception as e:
            logger.error(f"Error processing content: {str(e)}", exc_info=True) # Log traceback
            self.result.errors.append(f"Error processing content: {str(e)}")
            # Ensure content is empty on error, especially for size limit errors
            self.result.content = {} # Set content to empty dict on error

            # Ensure structure is also default on error
            if not self.result.structure:
                self.result.structure = []
                # Try to extract basic headings even on error
                try:
                    temp_soup = BeautifulSoup(html_content, 'html.parser')
                    basic_headings = []
                    for level in range(1, 7):
                        for tag in temp_soup.find_all(f'h{level}'):
                            heading_text = tag.get_text(strip=True)
                            basic_headings.append({
                                "type": "heading",
                                "level": level,
                                "title": heading_text
                            })
                    if basic_headings:
                        self.result.structure = basic_headings
                        self.result.headings = [
                            {"level": h["level"], "text": h["title"], "id": "", "type": "heading"}
                            for h in basic_headings
                        ]
                except Exception as e:
                    logger.error(f"Failed to extract basic headings on error: {str(e)}")
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
