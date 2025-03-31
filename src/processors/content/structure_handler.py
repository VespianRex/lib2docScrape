"""Handle document structure elements like headings, lists, tables, etc."""
import logging
from typing import Dict, List, Any
from bs4 import BeautifulSoup, Tag

# Configure logging
logger = logging.getLogger(__name__)

class StructureHandler:
    """Handle document structure elements and convert them to markdown."""

    def __init__(self, max_heading_level: int = 3):
        self.max_heading_level = max_heading_level

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
        """Extract document structure including headings, sections, paragraphs, code blocks, lists, tables, and links."""
        structure: List[Dict[str, Any]] = []

        # Process headings
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            level = int(tag.name[1])
            if level <= self.max_heading_level:
                heading = {
                    'type': 'heading',
                    'level': level,
                    'title': tag.get_text().strip(),
                    'id': tag.get('id', ''),
                    'classes': tag.get('class', [])
                }
                structure.append(heading)

        # Process paragraphs
        for paragraph in soup.find_all('p'):
            text_content = paragraph.get_text().strip()
            if text_content:
                paragraph_data = {
                    'type': 'text',
                    'content': text_content
                }
                structure.append(paragraph_data)

        # Process lists (ul, ol)
        for tag_list in soup.find_all(['ul', 'ol']):
            list_items_data = []
            for li in tag_list.find_all('li', recursive=False):
                item_text = li.get_text(strip=True)
                if item_text:
                    list_items_data.append(item_text)
            if list_items_data:
                list_data = {
                    'type': 'list',
                    'tag': tag_list.name,  # 'ul' or 'ol'
                    'content': list_items_data
                }
                structure.append(list_data)

        # Process code blocks
        for pre in soup.find_all('pre'):
            code_tag = pre.find('code')
            if code_tag:
                # Ensure classes is a list even if it's a string.
                classes = code_tag.get('class') or []
                if isinstance(classes, str):
                    classes = classes.split()
                raw_code = code_tag.get_text().strip()
                language = next((cls[len("language-"):] for cls in classes if cls.startswith("language-")), None)
                if language is None and classes:
                    language = classes[0]
            else:
                raw_code = pre.get_text().strip()
                language = ''
            formatted_code = f"```{language or ''}\n{raw_code}\n```"
            code_data = {
                'type': 'code',
                'language': language,
                'content': formatted_code
            }
            structure.append(code_data)

        # Process tables
        print("DEBUG: Looking for tables...")  # Debug output
        for table in soup.find_all('table'):
            print(f"DEBUG: Found table: {table}")  # Debug output
            table_content = self._extract_table_content(table)
            print(f"DEBUG: Extracted table content: {table_content}")  # Debug output
            table_data = {
                'type': 'table',
                'content': table_content
            }
            structure.append(table_data)
            print(f"DEBUG: Added table to structure: {table_data}")  # Debug output

        # Process links
        for link in soup.find_all('a'):
            href = link.get('href')
            if href is None or not href.strip():
                href = "#"
            else:
                href = href.strip()
            link_data = {
                'type': 'link',
                'text': link.get_text(strip=True),
                'href': href
            }
            structure.append(link_data)

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
