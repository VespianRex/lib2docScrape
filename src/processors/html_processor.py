"""HTML processor module for parsing and cleaning HTML content."""

from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional, Set
import re

class HTMLProcessor:
    """Processes HTML content with configurable cleaning and extraction rules."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the HTML processor with optional configuration.
        
        Args:
            config: Optional configuration dictionary with processing rules
        """
        self.config = config or {}
        self.allowed_tags = set(self.config.get('allowed_tags', [
            'p', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li', 'a', 'img', 'code', 'pre', 'table',
            'tr', 'td', 'th', 'thead', 'tbody'
        ]))
        self.remove_tags = set(self.config.get('remove_tags', [
            'script', 'style', 'iframe', 'noscript', 'header', 'footer'
        ]))

    def process(self, html: str) -> Dict[str, Any]:
        """Process HTML content and return cleaned and structured data.
        
        Args:
            html: Raw HTML content to process
            
        Returns:
            Dict containing processed HTML and extracted data
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            self._clean_html(soup)
            return {
                'html': str(soup),
                'text': self._extract_text(soup),
                'links': self._extract_links(soup),
                'images': self._extract_images(soup),
                'tables': self._extract_tables(soup)
            }
        except Exception as e:
            raise ValueError(f"Failed to process HTML: {str(e)}")

    def _clean_html(self, soup: BeautifulSoup) -> None:
        """Clean the HTML by removing unwanted elements and attributes."""
        # Remove unwanted tags
        for tag in soup.find_all(self.remove_tags):
            tag.decompose()
        
        # Remove unwanted attributes
        for tag in soup.find_all(True):
            allowed_attrs = {'href', 'src', 'alt', 'title', 'class'}
            attrs = dict(tag.attrs)
            for attr in attrs:
                if attr not in allowed_attrs:
                    del tag[attr]

    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extract clean text content from the HTML."""
        # Remove script and style content
        for tag in soup(['script', 'style']):
            tag.decompose()
        
        text = soup.get_text()
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _extract_links(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract all links from the HTML."""
        links = []
        for a in soup.find_all('a', href=True):
            links.append({
                'text': a.get_text().strip(),
                'href': a['href'],
                'title': a.get('title', '')
            })
        return links

    def _extract_images(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract all images from the HTML."""
        images = []
        for img in soup.find_all('img', src=True):
            images.append({
                'src': img['src'],
                'alt': img.get('alt', ''),
                'title': img.get('title', '')
            })
        return images

    def _extract_tables(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract all tables from the HTML."""
        tables = []
        for table in soup.find_all('table'):
            headers = []
            rows = []
            
            # Extract headers
            for th in table.find_all('th'):
                headers.append(th.get_text().strip())
            
            # Extract rows
            for tr in table.find_all('tr'):
                row = []
                for td in tr.find_all('td'):
                    row.append(td.get_text().strip())
                if row:  # Only add non-empty rows
                    rows.append(row)
            
            tables.append({
                'headers': headers,
                'rows': rows
            })
        
        return tables
