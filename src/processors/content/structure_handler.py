"""Handle document structure elements like headings, lists, tables, etc."""
import logging
from typing import Dict, List, Any
from bs4 import BeautifulSoup, Tag, NavigableString # Added NavigableString
from bs4 import BeautifulSoup, Tag

# Configure logging
logger = logging.getLogger(__name__)

class StructureHandler:
    """Handle document structure elements and convert them to markdown."""

    def __init__(self, code_handler: 'CodeHandler', max_heading_level: int = 3): # Add code_handler
        self.max_heading_level = max_heading_level
        self.code_handler = code_handler # Store code_handler

    def extract_headings(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract headings with proper level filtering."""
        headings = []
        for level in range(1, min(self.max_heading_level + 1, 7)):
            for heading in soup.find_all(f'h{level}'):
                text = heading.get_text().strip()
                if text:  # Only add non-empty headings
                    headings.append({
                        'type': 'heading',
                        'level': level,
                        'text': text
                    })
        return headings

    def extract_structure(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract document structure sequentially, preserving order and handling nesting."""
        structure: List[Dict[str, Any]] = []
        # Find the main content area, default to body if not found
        content_area = soup.find('main') or soup.body or soup

        if not content_area:
            logger.warning("Could not find main content area (main/body) for structure extraction.")
            return []

        # Define tags to recurse into vs tags to process directly
        container_tags = {'div', 'section', 'article', 'aside', 'nav', 'header', 'footer', 'figure'}
        # Add blockquote?

        def process_element(element: Tag, current_structure: List[Dict[str, Any]]):
            """Recursive helper to process elements."""
            if not isinstance(element, Tag):
                return # Skip NavigableString, Comment, etc.

            element_data = None
            tag_name = element.name

            # --- Process Direct Content Tags ---
            # Headings
            if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                level = int(tag_name[1])
                if level <= self.max_heading_level:
                    text = element.get_text().strip()
                    if text:
                        element_data = {
                            'type': 'heading', 'level': level, 'title': text,
                            'id': element.get('id', ''), 'classes': element.get('class', [])
                        }
            # Paragraphs - process inline elements within
            elif tag_name == 'p':
                paragraph_parts = []
                for child in element.children:
                    if isinstance(child, NavigableString):
                        text = child.strip()
                        if text:
                            paragraph_parts.append({'type': 'text_inline', 'content': text})
                    elif isinstance(child, Tag) and child.name == 'a':
                        href = child.get('href', '').strip() or "#"
                        text = child.get_text(strip=True)
                        if text: # Add link even if href is invalid initially
                             paragraph_parts.append({'type': 'link_inline', 'text': text, 'href': href})
                    elif isinstance(child, Tag) and child.name == 'code':
                         inline_code_content = child.get_text().strip()
                         if inline_code_content:
                              paragraph_parts.append({'type': 'inline_code', 'content': inline_code_content})
                    # Add other inline tags like strong, em if needed
                if paragraph_parts:
                     # Represent paragraph as a list of its inline parts
                     element_data = {'type': 'text', 'content': paragraph_parts} # Use 'text' type, content is list of inline parts
            # Lists
            elif tag_name in ['ul', 'ol']:
                list_items_data = [li.get_text(strip=True) for li in element.find_all('li', recursive=False) if li.get_text(strip=True)]
                if list_items_data:
                    element_data = {'type': 'list', 'tag': tag_name, 'content': list_items_data}
            # Code Blocks (pre)
            elif tag_name == 'pre':
                code_tag = element.find('code')
                if code_tag:
                    classes = code_tag.get('class') or []
                    if isinstance(classes, str): classes = classes.split()
                    raw_code = code_tag.get_text()
                    language = next((cls[len("language-"):] for cls in classes if cls.startswith("language-")), None) or (classes[0] if classes else None)
                else:
                    raw_code = element.get_text()
                    language = None
                if raw_code.strip():
                    if language is None or self.code_handler.is_language_supported(language):
                        element_data = {'type': 'code', 'language': language, 'content': raw_code}
            # Tables
            elif tag_name == 'table':
                table_content = self._extract_table_content(element)
                if table_content.get('headers') or table_content.get('rows'):
                    element_data = {'type': 'table', 'content': table_content}
            # Links (handle standalone links)
            elif tag_name == 'a':
                href = element.get('href', '').strip() or "#" # Default to # if empty
                text = element.get_text(strip=True) # Keep getting text for potential use
                # Add link regardless of text content, formatting handles empty text
                # if text: # Removed condition
                element_data = {'type': 'link', 'text': text, 'href': href} # Correct indentation
            # Inline code tags (Standalone)
            elif tag_name == 'code' and element.parent.name != 'pre':
                inline_code_content = element.get_text().strip()
                if inline_code_content:
                    element_data = {'type': 'inline_code', 'content': inline_code_content}

            # --- Append or Recurse ---
            if element_data:
                current_structure.append(element_data)
            elif tag_name in container_tags:
                # Recurse into container tags
                for child in element.find_all(recursive=False):
                    process_element(child, current_structure)
            # else: ignore other tags or handle them specifically

        # Start processing from the direct children of the content area
        for child in content_area.find_all(recursive=False):
             process_element(child, structure) # Process each child

        return structure


    def process_lists(self, soup: BeautifulSoup) -> None:
        """Process lists (ul, ol) to markdown format."""
        # Removed list processing from here, moved to structure extraction
        pass

    def process_definition_lists(self, soup: BeautifulSoup) -> None:
        """Process definition lists to markdown format."""
        for dl in soup.find_all('dl'):
            terms = []
            for dt in dl.find_all('dt'):
                term = dt.get_text().strip()
                dd = dt.find_next_sibling('dd')
                definition = dd.get_text().strip() if dd else ''
                terms.append(f'**{term}**: {definition}')
            if terms:
                dl.replace_with('\n'.join(terms))
            else:
                dl.decompose()  # Remove empty lists

    def process_tables(self, soup: BeautifulSoup) -> None:
        """Process tables to markdown format."""
        for table in soup.find_all('table'):
            markdown_table = self._convert_table_to_markdown(table)
            if markdown_table:
                new_tag = soup.new_tag('p')
                new_tag.string = markdown_table
                table.replace_with(new_tag)
            else:
                table.decompose()  # Remove empty tables

    def _convert_table_to_markdown(self, table: Tag) -> str:
        """Convert HTML table to markdown format with proper handling of empty tables."""
        if not table.find_all(['tr', 'th', 'td']):
            return ''  # Return empty string for empty tables

        rows = []
        header_row = table.find('tr')

        # Process header row
        if header_row:
            headers = []
            header_cells = header_row.find_all('th')
            if not header_cells:
                header_cells = header_row.find_all('td')
            for th in header_cells:
                colspan = int(th.get('colspan', 1))
                text = th.get_text().strip() or ' '  # Use space for empty cells
                headers.extend([text] * colspan)
            if headers:
                rows.append('| ' + ' | '.join(headers) + ' |')
                rows.append('| ' + ' | '.join(['---'] * len(headers)) + ' |')
        # Process data rows
        data_rows = table.find_all('tr')[1:] if header_row else table.find_all('tr')
        for row in data_rows:
            cells = []
            for cell in row.find_all(['td', 'th']):
                colspan = int(cell.get('colspan', 1))
                text = cell.get_text().strip() or ' '
                cells.extend([text] * colspan)
            if cells:
                rows.append('| ' + ' | '.join(cells) + ' |')
        return '\n'.join(rows) if rows else ''

    def _extract_table_content(self, table: Tag) -> Dict[str, Any]:
        """Extract table content (headers and rows) as structured data."""
        print("DEBUG: Extracting table content...")  # Debug output
        headers = []
        rows = []
        header_row = table.find('tr')
        print(f"DEBUG: Found header row: {header_row}")  # Debug output

        if header_row:
            header_cells = header_row.find_all('th')
            if not header_cells:
                header_cells = header_row.find_all('td')
            print(f"DEBUG: Found header cells: {header_cells}")  # Debug output
            for th in header_cells:
                headers.append(th.get_text().strip())
        data_rows = table.find_all('tr')[1:] if header_row else table.find_all('tr')
        print(f"DEBUG: Found data rows: {data_rows}")  # Debug output
        for row in data_rows:
            cell_texts = []
            for cell in row.find_all(['td', 'th']):
                cell_texts.append(cell.get_text().strip())
            rows.append(cell_texts)
        table_content = {'headers': headers, 'rows': rows}
        print(f"DEBUG: Extracted table content: {table_content}")  # Debug output
        return table_content

    def process_footnotes(self, soup: BeautifulSoup) -> None:
        """Process footnotes into markdown format."""
        footnotes = {}
        for ref in soup.find_all('sup', id=lambda x: x and x.startswith('fnref')):
            link = ref.find('a')
            if link and link.get('href', '').startswith('#fn'):
                fn_id = link['href'][1:]
                footnotes[fn_id] = len(footnotes) + 1
                ref.string = f"[{footnotes[fn_id]}]"
        footnote_div = soup.find('div', class_='footnotes')
        if footnote_div:
            footnote_content = []
            for fn in footnote_div.find_all('li', id=lambda x: x in footnotes):
                number = footnotes[fn['id']]
                content = fn.get_text().strip()
                footnote_content.append(f"{number}. {content}")
            if footnote_content:
                footnote_div.replace_with('\n\n' + '\n'.join(footnote_content))
            else:
                footnote_div.decompose()

    def process_abbreviations(self, soup: BeautifulSoup) -> None:
        """Process abbreviations into markdown format."""
        for abbr in soup.find_all('abbr'):
            title = abbr.get('title')
            if title:
                abbr.replace_with(f"{abbr.get_text()} ({title})")
            else:
                abbr.replace_with(abbr.get_text())

    def process_iframes(self, soup: BeautifulSoup) -> None:
        """Process iframes to markdown format."""
        from .url_handler import is_safe_url
        for iframe in soup.find_all('iframe'):
            src = iframe.get('src', '')
            if src and is_safe_url(src):
                markdown_iframe = f'[iframe]({src})'
                iframe.replace_with(BeautifulSoup(markdown_iframe, "html.parser"))
            else:
                iframe.decompose()
