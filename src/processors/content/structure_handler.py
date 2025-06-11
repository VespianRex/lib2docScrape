"""Handle document structure elements like headings, lists, tables, etc."""

import logging
from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup, NavigableString, Tag  # Added NavigableString

if TYPE_CHECKING:
    from .code_handler import CodeHandler

# Removed duplicate import: from bs4 import BeautifulSoup, Tag

# Configure logging
logger = logging.getLogger(__name__)


class StructureHandler:
    """Handle document structure elements and convert them to markdown."""

    def __init__(
        self, code_handler: "CodeHandler", max_heading_level: int = 3
    ):  # Add code_handler
        self.max_heading_level = max_heading_level
        self.code_handler = code_handler  # Store code_handler

    def extract_headings(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        """Extract headings with proper level filtering."""
        headings = []
        for level in range(1, min(self.max_heading_level + 1, 7)):
            for heading in soup.find_all(f"h{level}"):
                text = heading.get_text().strip()
                if text:  # Only add non-empty headings
                    headings.append({"type": "heading", "level": level, "text": text})
        return headings

    def extract_structure(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        """Extract document structure sequentially, preserving order and handling nesting."""
        structure: list[dict[str, Any]] = []
        # Find the main content area, default to body if not found
        content_area = soup.find("main") or soup.body or soup

        if not content_area:
            logger.warning(
                "Could not find main content area (main/body) for structure extraction."
            )
            return []

        # Define tags to recurse into vs tags to process directly
        # Removed ul, ol, li - they are handled specifically now
        container_tags = {
            "div",
            "section",
            "article",
            "aside",
            "nav",
            "header",
            "footer",
            "figure",
        }
        # Add blockquote?

        def process_element(element: Any, current_structure: list[dict[str, Any]]):
            """Recursive helper to process elements (Tags and NavigableStrings)."""
            if isinstance(element, NavigableString):
                text = str(element)  # Keep whitespace initially
                if text.strip():  # Only add if not just whitespace
                    # Append as inline text, preserving original whitespace
                    current_structure.append({"type": "text_inline", "content": text})
                return

            if not isinstance(element, Tag):
                return  # Skip Comment, etc.

            element_data = None
            tag_name = element.name

            # --- Process Direct Content Tags ---
            # Headings
            if tag_name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                level = int(tag_name[1])
                if level <= self.max_heading_level:
                    text = element.get_text().strip()
                    if text:
                        element_data = {
                            "type": "heading",
                            "level": level,
                            "title": text,
                            "id": element.get("id", ""),
                            "classes": element.get("class", []),
                        }
            # Paragraphs - process inline elements within
            elif tag_name == "p":
                paragraph_parts = []
                for child in element.children:
                    process_element(
                        child, paragraph_parts
                    )  # Process children recursively
                if paragraph_parts:
                    element_data = {"type": "text", "content": paragraph_parts}
            # Lists - Special handling to capture nested structure within <li>
            elif tag_name in ["ul", "ol"]:
                list_items_structure = []
                for li in element.find_all("li", recursive=False):
                    item_structure = []
                    # Process the *children* of the li tag
                    for child in li.children:
                        process_element(child, item_structure)
                    if (
                        item_structure
                    ):  # Only add if the list item resulted in some structure
                        list_items_structure.append(
                            item_structure
                        )  # Append the list representing li's structure
                if list_items_structure:
                    # Create the structure expected by the markdown formatter
                    element_data = {
                        "type": "list",
                        "tag": tag_name,
                        "content": list_items_structure,
                    }
            # Code Blocks (pre)
            elif tag_name == "pre":
                code_tag = element.find("code")
                if code_tag:
                    classes = code_tag.get("class") or []
                    if isinstance(classes, str):
                        classes = classes.split()
                    raw_code = code_tag.get_text()  # Keep original formatting
                    language = next(
                        (
                            cls[len("language-") :]
                            for cls in classes
                            if cls.startswith("language-")
                        ),
                        None,
                    ) or (classes[0] if classes else None)
                else:
                    raw_code = element.get_text()
                    language = None
                if raw_code.strip():  # Check if not just whitespace
                    element_data = {
                        "type": "code",
                        "language": language,
                        "content": raw_code,
                    }
            # Tables
            elif tag_name == "table":
                table_content = self._extract_table_content(element)
                if table_content.get("headers") or table_content.get("rows"):
                    element_data = {"type": "table", "content": table_content}
            # Links (handle standalone links or links found during recursion)
            elif tag_name == "a":
                href = element.get("href", "").strip() or "#"  # Default to # if empty
                text = element.get_text(
                    strip=True
                )  # Keep getting text for potential use
                # Represent as inline link structure
                element_data = {"type": "link_inline", "text": text, "href": href}
            # Inline code tags (Standalone)
            elif tag_name == "code" and element.parent.name != "pre":
                inline_code_content = element.get_text()  # Keep internal spaces
                if inline_code_content.strip():  # Check if not just whitespace
                    element_data = {
                        "type": "inline_code",
                        "content": inline_code_content,
                    }
            # Handle inline formatting tags (strong, em, etc.)
            elif tag_name in ["strong", "em", "b", "i", "u", "s", "sub", "sup"]:
                inline_parts = []
                for child in element.children:
                    process_element(child, inline_parts)
                if inline_parts:
                    element_data = {"type": tag_name, "content": inline_parts}
            # Handle <br> tags
            elif tag_name == "br":
                element_data = {"type": "linebreak"}

            # --- Append or Recurse ---
            if element_data:
                current_structure.append(element_data)
            # Only recurse into defined containers if no specific data was extracted
            elif tag_name in container_tags:
                for child in element.children:
                    process_element(child, current_structure)
            # else: ignore other tags like 'li' as they are handled by their parent ('ul'/'ol')

        # Start processing from the direct children of the content area
        for child in content_area.children:  # Use children to include NavigableString
            process_element(child, structure)  # Process each child

        return structure

    def process_lists(self, soup: BeautifulSoup) -> None:
        """Process lists (ul, ol) to markdown format."""
        # Removed list processing from here, handled by structure extraction and markdown formatting
        pass

    def process_definition_lists(self, soup: BeautifulSoup) -> None:
        """Process definition lists to markdown format."""
        for dl in soup.find_all("dl"):
            terms = []
            for dt in dl.find_all("dt"):
                term = dt.get_text().strip()
                dd = dt.find_next_sibling("dd")
                definition = dd.get_text().strip() if dd else ""
                terms.append(f"**{term}**: {definition}")
            if terms:
                dl.replace_with("\n".join(terms))
            else:
                dl.decompose()  # Remove empty lists

    def process_tables(self, soup: BeautifulSoup) -> None:
        """Process tables to markdown format."""
        for table in soup.find_all("table"):
            markdown_table = self._convert_table_to_markdown(table)
            if markdown_table:
                new_tag = soup.new_tag("p")
                new_tag.string = markdown_table
                table.replace_with(new_tag)
            else:
                table.decompose()  # Remove empty tables

    def _convert_table_to_markdown(self, table: Tag) -> str:
        """Convert HTML table to markdown format with proper handling of empty tables."""
        if not table.find_all(["tr", "th", "td"]):
            return ""  # Return empty string for empty tables

        rows = []
        header_row = table.find("tr")

        # Process header row
        if header_row:
            headers = []
            header_cells = header_row.find_all("th")
            if not header_cells:
                header_cells = header_row.find_all("td")
            for th in header_cells:
                colspan = int(th.get("colspan", 1))
                text = th.get_text().strip() or " "  # Use space for empty cells
                headers.extend([text] * colspan)
            if headers:
                rows.append("| " + " | ".join(headers) + " |")
                rows.append("| " + " | ".join(["---"] * len(headers)) + " |")
        # Process data rows
        data_rows = table.find_all("tr")[1:] if header_row else table.find_all("tr")
        for row in data_rows:
            cells = []
            for cell in row.find_all(["td", "th"]):
                colspan = int(cell.get("colspan", 1))
                text = cell.get_text().strip() or " "
                cells.extend([text] * colspan)
            if cells:
                rows.append("| " + " | ".join(cells) + " |")
        return "\n".join(rows) if rows else ""

    def _extract_table_content(self, table: Tag) -> dict[str, Any]:
        """Extract table content (headers and rows) as structured data."""
        headers = []
        rows = []
        header_row = table.find("tr")

        if header_row:
            header_cells = header_row.find_all("th")
            if not header_cells:
                header_cells = header_row.find_all("td")
            for th in header_cells:
                headers.append(th.get_text().strip())
        data_rows = table.find_all("tr")[1:] if header_row else table.find_all("tr")
        for row in data_rows:
            cell_texts = []
            for cell in row.find_all(["td", "th"]):
                cell_texts.append(cell.get_text().strip())
            rows.append(cell_texts)
        table_content = {"headers": headers, "rows": rows}
        return table_content

    def process_footnotes(self, soup: BeautifulSoup) -> None:
        """Process footnotes into markdown format."""
        footnotes = {}
        for ref in soup.find_all("sup", id=lambda x: x and x.startswith("fnref")):
            link = ref.find("a")
            if link and link.get("href", "").startswith("#fn"):
                fn_id = link["href"][1:]
                footnotes[fn_id] = len(footnotes) + 1
                ref.string = f"[{footnotes[fn_id]}]"
        footnote_div = soup.find("div", class_="footnotes")
        if footnote_div:
            footnote_content = []
            for fn in footnote_div.find_all("li", id=lambda x: x in footnotes):
                number = footnotes[fn["id"]]
                content = fn.get_text().strip()
                footnote_content.append(f"{number}. {content}")
            if footnote_content:
                footnote_div.replace_with("\n\n" + "\n".join(footnote_content))
            else:
                footnote_div.decompose()

    def process_abbreviations(self, soup: BeautifulSoup) -> None:
        """Process abbreviations into markdown format."""
        for abbr in soup.find_all("abbr"):
            title = abbr.get("title")
            if title:
                abbr.replace_with(f"{abbr.get_text()} ({title})")
            else:
                abbr.replace_with(abbr.get_text())

    def process_iframes(self, soup: BeautifulSoup) -> None:
        """Process iframes to markdown format."""
        from .url_handler import is_safe_url

        for iframe in soup.find_all("iframe"):
            src = iframe.get("src", "")
            if src and is_safe_url(src):
                markdown_iframe = f"[iframe]({src})"
                iframe.replace_with(BeautifulSoup(markdown_iframe, "html.parser"))
            else:
                iframe.decompose()
