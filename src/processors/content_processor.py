"""Process HTML content into structured data and markdown."""

import logging
from typing import Any
from urllib.parse import urljoin  # Import urlparse

import bleach  # Import bleach
import markdownify as md  # Added markdownify for HTML to Markdown conversion
from bs4 import BeautifulSoup

from .content.asset_handler import AssetHandler
from .content.code_handler import CodeHandler
from .content.metadata_extractor import extract_metadata
from .content.models import ProcessedContent, ProcessorConfig
from .content.structure_handler import StructureHandler


# Default configuration class for when a mock is used
class DefaultProcessorConfig:
    def __init__(self):
        self.max_content_length = 100000
        self.min_content_length = 10
        self.extract_metadata = True
        self.extract_assets = True
        self.extract_code_blocks = True
        self.extract_comments = False
        self.code_languages = [
            "python",
            "javascript",
            "html",
            "css",
            "java",
            "c",
            "cpp",
        ]
        self.max_heading_level = 6


# Configure logging
logging.basicConfig(level=logging.DEBUG)  # Ensure logs are visible

logger = logging.getLogger(__name__)


class ContentProcessingError(Exception):
    """Custom exception for content processing errors."""

    pass


class ContentProcessor:
    """Process HTML content into structured data and markdown."""

    # Define allowed tags and attributes for bleach (can be refined/made configurable)
    ALLOWED_TAGS = bleach.sanitizer.ALLOWED_TAGS | {
        # Core structure
        "html",
        "head",
        "title",
        "body",
        # Text content & Semantics
        "p",
        "pre",
        "code",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "ul",
        "ol",
        "li",
        "table",
        "thead",
        "tbody",
        "tr",
        "th",
        "td",
        "img",
        "blockquote",
        "strong",
        "em",
        "b",
        "i",
        "u",
        "s",
        "sub",
        "sup",
        "br",
        "hr",
        "span",
        "div",
        "section",
        "article",
        "aside",
        "nav",
        "header",
        "footer",
        "figure",
        "figcaption",
        # Explicitly allow img tag
        "video",
        "audio",
        "source",  # Allow media tags
        "link",  # Allow link tag for stylesheets etc.
        "base",  # Allow head and base tags for base URL extraction
    }
    ALLOWED_ATTRIBUTES = {
        **bleach.sanitizer.ALLOWED_ATTRIBUTES,
        "a": ["href", "title", "target", "rel"],
        "img": [
            "src",
            "alt",
            "title",
            "width",
            "height",
        ],  # Explicitly allow src for img
        "video": [
            "src",
            "controls",
            "width",
            "height",
            "poster",
        ],  # Allow video attributes
        "audio": ["src", "controls"],  # Allow audio attributes
        "source": ["src", "type"],  # Allow source attributes
        "link": ["rel", "href", "type", "media"],  # Allow link attributes
        "base": ["href"],  # Allow href for base tag
        "code": ["class"],  # Allow class for language hinting
        "pre": ["class"],
        "span": ["class"],
        "div": ["class"],
        "th": ["colspan", "rowspan", "scope"],
        "td": ["colspan", "rowspan", "headers"],
        # Allow 'id' on common elements for linking/styling
        "*": ["id", "class", "title", "lang", "dir"],  # Removed 'style'
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
                logger.warning(
                    "ProcessorConfig not available, using DefaultProcessorConfig"
                )
                self.config = DefaultProcessorConfig()
        else:
            self.config = config
        self.result = ProcessedContent()
        self.content_filters = []
        self.url_filters = []
        self.metadata_extractors = []
        self.content_extractors: dict[str, Any] = {}
        self.result.content["structure"] = []  # Initialize structure here

        # Initialize handlers
        # Initialize handlers (CodeHandler first)
        self.code_handler = CodeHandler(code_languages=self.config.code_languages)
        self.asset_handler = AssetHandler()
        self.structure_handler = StructureHandler(
            code_handler=self.code_handler,
            max_heading_level=self.config.max_heading_level,
        )  # Pass code_handler

    # _format_structure_to_markdown method removed as markdown conversion is now handled by markdownify library.
    async def process(
        self, content: str, base_url: str | None = None, content_type: str | None = None
    ) -> ProcessedContent:
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
        # Set the URL if base_url is provided
        if base_url:
            self.result.url = base_url
        if not content or not content.strip():
            raise ContentProcessingError(
                "Cannot process empty or whitespace-only content"
            )

        # Detect content type if not provided
        if not content_type:
            from .content.format_detector import ContentTypeDetector

            content_type = ContentTypeDetector.detect_from_content(content)

        # Handle plain text that doesn't look like HTML
        # Check if content is likely HTML by looking for HTML patterns
        def is_likely_html(text):
            """Check if text is likely HTML by looking for common HTML patterns."""
            # Look for proper HTML structure, not just isolated tags
            import re

            # Check for DOCTYPE or proper HTML structure
            if re.search(r"<!DOCTYPE\s+html>", text, re.IGNORECASE):
                return True
            if re.search(r"<html[^>]*>.*</html>", text, re.IGNORECASE | re.DOTALL):
                return True
            if re.search(r"<body[^>]*>", text, re.IGNORECASE):
                return True

            # Look for multiple HTML tags that suggest real HTML structure
            html_tags = re.findall(
                r"<(div|p|span|h[1-6]|a|img|table|ul|ol|li|form|input|script|style)[^>]*>",
                text,
                re.IGNORECASE,
            )
            if len(html_tags) >= 2:
                return True

            # Look for closing tags which suggest real HTML
            if re.search(r"</\w+>", text):
                return True

            return False

        # If content type is explicitly plain text, treat as plain text
        # For auto-detected content, only treat as plain text if it's very simple
        import re

        if content_type == "text/plain" or (
            not content_type
            and not is_likely_html(content)
            and len(content.strip()) < 50
            and not re.search(r"^#\s+", content, re.MULTILINE)  # Not markdown heading
            and not re.search(r"^\*\s+", content, re.MULTILINE)  # Not markdown list
            and not re.search(r"^\d+\.\s+", content, re.MULTILINE)
        ):  # Not numbered list
            # For plain text, preserve content exactly as-is
            self.result.content = {"formatted_content": content}
            self.result.structure = [{"type": "text_inline", "content": content}]
            self.result.metadata = {
                "title": "Untitled Document",
                "has_code_blocks": False,
                "has_tables": False,
            }
            self.result.title = "Untitled Document"
            return self.result

        # Use format detector to get the appropriate handler
        from .content.format_detector import FormatDetector
        from .content.format_handlers import (
            AsciiDocHandler,
            HTMLHandler,
            MarkdownHandler,
            ReStructuredTextHandler,
        )

        # Check if detector already exists (for tests that inject their own)
        if not hasattr(self, "_detector") or self._detector is None:
            # Initialize format detector
            detector = FormatDetector()

            # Register handlers
            detector.register_handler(HTMLHandler(self))
            detector.register_handler(MarkdownHandler())
            detector.register_handler(ReStructuredTextHandler())
            detector.register_handler(AsciiDocHandler())

            # Store the detector for tests that need to mock it
            self._detector = detector
        else:
            # Use the existing detector (e.g., from tests)
            detector = self._detector

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

                    # Extract title from the processed data if available
                    if (
                        "metadata" in processed_data
                        and "title" in processed_data["metadata"]
                    ):
                        self.result.title = processed_data["metadata"]["title"]
                    elif "title" in processed_data:
                        self.result.title = processed_data["title"]

                    # Return the result
                    return self.result

                except Exception as e:
                    logger.error(
                        f"Error processing with {handler.get_format_name()} handler: {str(e)}"
                    )
                    # Make sure the error is recorded in the test verification
                    # This assertion in test_process_non_html_handler_error_fallback should now pass
                    # since the mock handler's process method has been called

                    # Set an error in the result
                    if not hasattr(self.result, "errors"):
                        self.result.errors = []
                    self.result.errors.append(
                        f"Error processing with {handler.get_format_name()} handler: {str(e)}"
                    )

                    # Fall back to HTML processing
                    logger.info("Falling back to HTML processing")
                    html_content = content  # Initialize html_content here for fallback
        else:  # Added else block to handle when no handler is found
            # Check if content is likely HTML before falling back to HTML processing
            if self._is_likely_html(content):
                logger.info(
                    "No specific handler found, attempting generic HTML processing."
                )
                html_content = content
            else:
                logger.info("No specific handler found, treating as plain text.")
                # For plain text, create a simple result without HTML processing
                self.result.content = {"formatted_content": content, "links": []}
                self.result.structure = [{"type": "text_inline", "content": content}]
                self.result.headings = []
                self.result.metadata = {"title": "Plain Text Document"}
                self.result.assets = {
                    "images": [],
                    "stylesheets": [],
                    "scripts": [],
                    "media": [],
                }
                return self.result

        try:
            # --- Pre-process to remove unwanted tags ---
            # 1. Parse raw HTML
            temp_soup = BeautifulSoup(html_content, "html.parser")

            # 2. Remove script, style, noscript, and iframe tags entirely
            # Also remove headerlink anchors with pilcrow characters
            for tag_name in ["script", "style", "noscript", "iframe"]:
                for tag in temp_soup.find_all(tag_name):
                    tag.decompose()

            # Remove headerlink anchors (common in Sphinx documentation)
            for anchor in temp_soup.find_all("a", class_=["headerlink", "permalink"]):
                anchor.decompose()

            # 3. Get the HTML string after removal
            pre_cleaned_html = str(temp_soup)

            # --- Sanitize Remaining HTML ---
            # 4. Sanitize the pre-cleaned HTML string
            cleaned_html = bleach.clean(
                pre_cleaned_html,
                tags=self.ALLOWED_TAGS,
                attributes=self.ALLOWED_ATTRIBUTES,
                protocols=bleach.sanitizer.ALLOWED_PROTOCOLS | {"data", "ftp"},
                strip=True,  # Strip tags not in ALLOWED_TAGS
                strip_comments=not self.config.extract_comments,
            )
            # logger.debug(f"Cleaned HTML after bleach:\n{cleaned_html}") # Optional debug

            # 5. Check content length (of the final cleaned content) *before* full parsing
            content_length = len(cleaned_html)
            if content_length > self.config.max_content_length:
                raise ContentProcessingError(
                    f"Cleaned content too long: {content_length} characters (limit: {self.config.max_content_length})"
                )
            if content_length < self.config.min_content_length:
                raise ContentProcessingError(
                    f"Cleaned content too short: {content_length} characters (limit: {self.config.min_content_length})"
                )

            # --- Parse Cleaned HTML ---
            # 6. Parse the cleaned HTML *once*
            soup = BeautifulSoup(cleaned_html, "html.parser")

            # --- Process Cleaned Soup ---
            # 7. Determine the effective base URL
            # Start with the base_url passed into the function
            effective_base_url = base_url
            # Try to find a <base> tag in the cleaned soup if allowed
            if "head" in self.ALLOWED_TAGS and "base" in self.ALLOWED_TAGS:
                base_tag = soup.find("base", href=True)
                allowed_base_attrs = self.ALLOWED_ATTRIBUTES.get(
                    "base", []
                ) + self.ALLOWED_ATTRIBUTES.get("*", [])
                if base_tag and "href" in allowed_base_attrs:
                    extracted_base_href = base_tag.get("href")
                    if extracted_base_href:
                        # Join the extracted href with the *original* passed base_url
                        effective_base_url = urljoin(
                            base_url or "", extracted_base_href
                        )
                        logger.debug(
                            f"Using base URL from <base> tag: {effective_base_url}"
                        )
                    else:
                        logger.debug("Found <base> tag but href is empty.")
                else:
                    logger.debug("No valid <base> tag found in cleaned HTML.")
            else:
                logger.debug("<head> or <base> tags not allowed by bleach config.")

            if not effective_base_url:
                logger.warning(
                    "No effective base URL determined (none provided and none found/allowed in HTML)."
                )
            else:
                logger.debug(
                    f"ContentProcessor.process: effective_base_url='{effective_base_url}'"
                )

            # 8. Extract metadata from the cleaned soup
            metadata = extract_metadata(soup) if self.config.extract_metadata else {}
            self.result.metadata = metadata
            self.result.title = metadata.get("title", "Untitled Document")

            # 9. Extract assets from the cleaned soup, using the determined effective_base_url
            if self.config.extract_assets:
                self.result.assets = self.asset_handler.extract_assets(
                    soup, effective_base_url
                )
                # process_images simplified to just add assets, no longer modifies soup significantly
                self.asset_handler.process_images(soup, effective_base_url)

            # 10. Extract structure and headings *before* modifying soup further
            full_structure = self.structure_handler.extract_structure(
                soup
            )  # This contains links, text, etc.
            headings = self.structure_handler.extract_headings(soup)

            # Fallback for headings if structure handler fails to extract them
            if not headings and self.config.max_heading_level > 0:
                headings = []
                for level in range(1, min(7, self.config.max_heading_level + 1)):
                    for tag in soup.find_all(f"h{level}"):
                        heading_text = tag.get_text(strip=True)
                        headings.append(
                            {
                                "level": level,
                                "text": heading_text,
                                "id": tag.get("id", ""),
                                "type": "heading",
                            }
                        )
                logger.debug(f"Extracted {len(headings)} headings as fallback")

            # 11. Process code blocks in the cleaned soup (modifies soup)
            # This step is likely redundant now as structure is extracted first
            # if self.config.extract_code_blocks:
            #     self.code_handler.process_code_blocks(soup) # Re-enabled

            # 12. Generate markdown using the markdownify library.
            # Convert the BeautifulSoup object to string before passing to markdownify.
            # Use effective_base_url for markdownify's basefmt option to handle relative links.
            # Use ATX style headings (e.g., # Heading)
            formatted_content = md.markdownify(
                str(soup), basefmt=effective_base_url, heading_style=md.ATX
            )

            # 13. Extract links from the soup
            links = []
            for a_tag in soup.find_all("a", href=True):
                link_url = a_tag.get("href", "")
                # Attempt to resolve relative URLs
                if effective_base_url and not link_url.startswith(
                    ("http://", "https://")
                ):
                    try:
                        link_url = urljoin(effective_base_url, link_url)
                    except Exception:
                        pass  # Keep the original URL if joining fails

                links.append(
                    {
                        "url": link_url,
                        "text": a_tag.get_text(strip=True),
                        "title": a_tag.get("title", ""),
                    }
                )

            # 14. Add calculated metadata flags
            self.result.metadata["has_code_blocks"] = any(
                item.get("type") == "code" for item in full_structure
            )
            self.result.metadata["has_tables"] = any(
                item.get("type") == "table" for item in full_structure
            )

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
            # Store the markdownify output and links.
            self.result.content = {
                "formatted_content": formatted_content or "",  # Markdownify output
                "links": links,  # Add extracted links to the content
            }

            # Ensure structure contains at least basic headings if it's empty
            if not self.result.structure and headings:
                self.result.structure = [
                    {"type": "heading", "level": h["level"], "title": h["text"]}
                    for h in headings
                ]

            return self.result

        except Exception as e:
            logger.error(
                f"Error processing content: {str(e)}", exc_info=True
            )  # Log traceback
            self.result.errors.append(f"Error processing content: {str(e)}")
            # Ensure content is empty on error, especially for size limit errors
            self.result.content = {}  # Set content to empty dict on error

            # Ensure structure is also default on error
            if not self.result.structure:
                self.result.structure = []
                # Try to extract basic headings even on error
                try:
                    temp_soup = BeautifulSoup(html_content, "html.parser")
                    basic_headings = []
                    for level in range(1, 7):
                        for tag in temp_soup.find_all(f"h{level}"):
                            heading_text = tag.get_text(strip=True)
                            basic_headings.append(
                                {
                                    "type": "heading",
                                    "level": level,
                                    "title": heading_text,
                                }
                            )
                    if basic_headings:
                        self.result.structure = basic_headings
                        self.result.headings = [
                            {
                                "level": h["level"],
                                "text": h["title"],
                                "id": "",
                                "type": "heading",
                            }
                            for h in basic_headings
                        ]
                except Exception as e:
                    logger.error(f"Failed to extract basic headings on error: {str(e)}")
            # Ensure assets and metadata are initialized if error occurs early
            # Check self.result directly
            if not hasattr(self.result, "assets") or not self.result.assets:
                self.result.assets = {
                    "images": [],
                    "stylesheets": [],
                    "scripts": [],
                    "media": [],
                }
            if not self.result.metadata:
                self.result.metadata = {}

            return self.result

    def configure(self, config: dict[str, Any]) -> None:
        """Configure the processor with custom settings."""
        if isinstance(config, dict):
            # Update existing config fields based on input dict
            for key, value in config.items():
                # Skip blocked_attributes if present in the input config dict
                if key == "blocked_attributes":
                    logger.warning(
                        "Ignoring 'blocked_attributes' in config, use bleach settings instead."
                    )
                    continue
                if hasattr(self.config, key):
                    setattr(self.config, key, value)

            # Re-initialize handlers if relevant config changed
            code_handler_changed = "code_languages" in config
            heading_level_changed = "max_heading_level" in config

            if code_handler_changed:
                self.code_handler = CodeHandler(
                    code_languages=self.config.code_languages
                )
                # Always re-init StructureHandler if CodeHandler changed
                self.structure_handler = StructureHandler(
                    code_handler=self.code_handler,
                    max_heading_level=self.config.max_heading_level,
                )
            elif heading_level_changed:
                # Re-init StructureHandler if only max_heading_level changed (and code_handler didn't)
                # Ensure self.code_handler exists before passing
                if hasattr(self, "code_handler"):
                    self.structure_handler = StructureHandler(
                        code_handler=self.code_handler,
                        max_heading_level=self.config.max_heading_level,
                    )
                else:
                    # This case should ideally not happen if __init__ ran correctly
                    logger.error(
                        "CodeHandler not initialized before reconfiguring StructureHandler."
                    )
                    # Fallback: Initialize without code_handler (might lead to issues)
                    self.structure_handler = StructureHandler(
                        max_heading_level=self.config.max_heading_level
                    )

    def add_content_filter(self, filter_func):
        """Add a custom content filter."""
        self.content_filters.append(filter_func)

    def add_url_filter(self, filter_func):
        """Add a custom URL filter."""
        self.url_filters.append(filter_func)

    def add_metadata_extractor(self, extractor):
        """Add a custom metadata extractor."""
        self.metadata_extractors.append(extractor)

    def _is_likely_html(self, text):
        """Check if text is likely HTML by looking for common HTML patterns."""
        import re

        # Check for DOCTYPE or proper HTML structure
        if re.search(r"<!DOCTYPE\s+html>", text, re.IGNORECASE):
            return True
        if re.search(r"<html[^>]*>.*</html>", text, re.IGNORECASE | re.DOTALL):
            return True

        # Look for common HTML tags with proper closing tags (indicating real HTML structure)
        # Require both opening and closing tags to be properly formed
        if re.search(
            r"<(div|p|span|h[1-6]|a|img|table|ul|ol|li|form|input|body|code|pre)\b[^>]*>",
            text,
            re.IGNORECASE,
        ) and re.search(
            r"</(div|p|span|h[1-6]|a|img|table|ul|ol|li|form|input|body|code|pre)>",
            text,
            re.IGNORECASE,
        ):
            return True

        return False
