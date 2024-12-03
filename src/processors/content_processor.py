# src/processors/content_processor.py

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, NamedTuple

class ContentProcessingError(Exception):
    """Custom exception for content processing errors."""
    pass

class URLInfo(NamedTuple):
    """Structured information about a URL."""
    original_url: str
    normalized_url: str
    scheme: str
    netloc: str
    path: str
    query: str
    fragment: str

from bs4 import BeautifulSoup, Comment, NavigableString, Tag
import markdownify
from urllib.parse import urljoin, urlparse

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


@dataclass
class ProcessorConfig:
    """Configuration for the content processor."""
    allowed_tags: List[str] = field(default_factory=lambda: ['p', 'a', 'img', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'code', 'pre', 'blockquote', 'em', 'strong', 'table', 'tr', 'td', 'th'])
    max_heading_level: int = 6
    preserve_whitespace_elements: List[str] = field(default_factory=lambda: ['pre', 'code'])
    code_languages: List[str] = field(default_factory=list)
    sanitize_urls: bool = True
    metadata_prefixes: List[str] = field(default_factory=lambda: ['og:', 'twitter:', 'dc.', 'article:', 'book:'])
    extract_comments: bool = False
    max_content_length: int = 1000000
    min_content_length: int = 0


@dataclass
class ProcessedContent:
    """Result of content processing."""
    content: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    assets: Dict[str, List[str]] = field(default_factory=lambda: {
        'images': [], 'stylesheets': [], 'scripts': [], 'media': []
    })
    headings: List[Dict[str, Any]] = field(default_factory=list)
    structure: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    title: str = field(default="Untitled Document")


class ContentProcessor:
    """Process HTML content into structured data and markdown."""
    
    def __init__(self, config=None):
        """Initialize the content processor."""
        self.config = config or ProcessorConfig()
        self.result = ProcessedContent()
        self.content_filters = []
        self.url_filters = []
        self.metadata_extractors = []
        self.content_extractors = {}  # Add this line
        self.markdownify_options = {
            'heading_style': 'ATX',
            'strong_style': '**',
            'emphasis_style': '_',
            'bullets': '-',
            'code_language': True,
            'escape_asterisks': False,
            'escape_underscores': False,
            'escape_code': False,
            'code_block_style': '```',
            'wrap_width': None,
            'convert_links': True,
            'hr_style': '---',
            'br_style': '  ',
            'default_title': 'Untitled Document',
            'newline_style': '\n',
            'convert_all': True,
            'preserve_whitespace': True,
            'strip': ['style', 'onclick', 'onload', 'onmouseover', 'onmouseout', 'onkeydown', 'onkeyup']
        }
    
    def configure(self, config):
        """Configure the processor with custom settings."""
        if isinstance(config, dict):
            # Update configuration from dictionary
            if 'allowed_tags' in config:
                self.config.allowed_tags = config['allowed_tags']
            
            if 'max_heading_level' in config:
                self.config.max_heading_level = config['max_heading_level']
            
            if 'preserve_whitespace_elements' in config:
                self.config.preserve_whitespace_elements = config['preserve_whitespace_elements']
            
            if 'code_languages' in config:
                self.config.code_languages = config['code_languages']
            
            if 'sanitize_urls' in config:
                self.config.sanitize_urls = config['sanitize_urls']
            
            if 'metadata_prefixes' in config:
                self.config.metadata_prefixes = config['metadata_prefixes']
            
            if 'extract_comments' in config:
                self.config.extract_comments = config['extract_comments']
            
            if 'max_content_length' in config:
                self.config.max_content_length = config['max_content_length']
            
            if 'min_content_length' in config:
                self.config.min_content_length = config['min_content_length']
    
    def process(self, html, base_url=None):
        """Process HTML content and return structured result."""
        self.result = ProcessedContent()
        if not html:
            return self.result

        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract metadata first
            self._extract_metadata(soup)
            
            # Process content
            self._process_content(soup, base_url)
            
            return self.result
        except Exception as e:
            self.result.errors.append(f"Error processing content: {str(e)}")
            return self.result

    def add_content_filter(self, filter_func):
        """Add a custom content filter function."""
        self.content_filters.append(filter_func)
    
    def add_url_filter(self, filter_func):
        """Add a custom URL filter function."""
        self.url_filters.append(filter_func)

    def add_content_extractor(self, name, extractor):
        """Add a custom content extractor."""
        self.content_extractors[name] = extractor

    def add_metadata_extractor(self, extractor):
        """Add a custom metadata extractor."""
        self.metadata_extractors.append(extractor)
        
    def _extract_metadata(self, soup):
        """Extract metadata from HTML."""
        # Initialize metadata
        self.result.metadata = {}
        self.result.title = "Untitled Document"
        
        # Process JSON-LD first
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    self._process_json_ld(data)
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            self._process_json_ld(item)
            except (json.JSONDecodeError, AttributeError):
                continue

        # Extract standard meta tags
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            name = meta.get('name', '').lower() or meta.get('property', '').lower()
            content = meta.get('content', '')
            if name and content:
                # Only add the first occurrence of a metadata tag
                if name not in self.result.metadata:
                    self.result.metadata[name] = content

        # Extract title, prioritizing <head> section
        head_title = soup.find('head', recursive=False)
        if head_title:
            title_tag = head_title.find('title')
        else:
            title_tag = soup.find('title')

        if title_tag and title_tag.string:
            self.result.title = title_tag.string.strip()
            self.result.metadata['title'] = self.result.title

        # Process microdata
        for element in soup.find_all(True, itemtype=True):
            self._process_microdata(element)

        # Apply custom extractors
        for extractor in self.metadata_extractors:
            try:
                extractor(soup, self.result.metadata)
            except Exception as e:
                self.result.errors.append(f"Metadata extractor error: {str(e)}")

    def _process_json_ld(self, data, prefix=''):
        """Process JSON-LD data recursively."""
        for key, value in data.items():
            if isinstance(value, str):
                self.result.metadata[prefix + key.lower()] = value
            elif isinstance(value, dict):
                if '@type' in value:
                    new_prefix = f"{value['@type'].lower()}_"
                    self._process_json_ld(value, new_prefix)
                else:
                    self._process_json_ld(value, prefix)

    def _process_microdata(self, element):
        """Process microdata attributes."""
        for prop in element.find_all(True, itemprop=True):
            name = prop.get('itemprop', '').lower()
            content = prop.get('content', '') or prop.string
            if name and content:
                self.result.metadata[name] = content.strip()

    def _extract_assets(self, soup, result, base_url=None):
        """Extract assets with proper handling of duplicates and data URLs."""
        # Initialize assets dict
        result.assets = {
            'images': [],
            'stylesheets': [],
            'scripts': [],
            'media': []
        }

        # Helper function to process URLs
        def process_url(url):
            if not url:
                return None
            # Keep data URLs as is
            if url.startswith('data:'):
                return url
            # Handle base URL
            if base_url and not url.startswith(('http://', 'https://', 'mailto:', 'tel:', 'ftp://')):
                try:
                    return urljoin(base_url, url)
                except Exception:
                    return url  # Keep original URL on error
            return url

        # Extract stylesheets
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href')
            if href:
                url = process_url(href)
                if url and url not in result.assets['stylesheets']:
                    result.assets['stylesheets'].append(url)

        # Extract images
        for img in soup.find_all('img'):
            src = img.get('src')
            if src and src.strip():  # Ensure src is not empty
                if src.startswith('data:'):
                    if src not in result.assets['images']:
                        result.assets['images'].append(src)
                elif not src.lower().startswith(('javascript:', 'vbscript:')):
                    url = process_url(src)
                    if url and url not in result.assets['images']:
                        result.assets['images'].append(url)

        # Extract scripts
        for script in soup.find_all('script', src=True):
            src = script.get('src')
            if src and not src.lower().startswith(('javascript:', 'data:', 'vbscript:')):
                url = process_url(src)
                if url and url not in result.assets['scripts']:
                    result.assets['scripts'].append(url)

        # Extract media
        for media in soup.find_all(['audio', 'video', 'source']):
            src = media.get('src')
            if src and src.strip():  # Ensure src is not empty
                if not src.lower().startswith(('javascript:', 'data:', 'vbscript:')):
                    url = process_url(src)
                    if url and url not in result.assets['media']:
                        result.assets['media'].append(url)

    def _sanitize_url(self, url, base_url=None):
        """Sanitize and normalize URLs."""
        if not url:
            return url
        
        # Handle data URLs
        if url.startswith('data:'):
            return url
        
        # Remove dangerous protocols
        if any(url.lower().startswith(proto) for proto in ['javascript:', 'data:', 'vbscript:']):
            return '#'
        
        # Handle relative URLs
        if base_url and not url.startswith(('http://', 'https://', 'mailto:', 'tel:', 'ftp://')):
            return urljoin(base_url, url)
        
        return url

    def _process_code_blocks(self, soup):
        """Process code blocks with enhanced language detection."""
        for pre in soup.find_all('pre'):
            code = pre.find('code')
            if code:
                # Detect language from class
                language = None
                for cls in code.get('class', []):
                    if cls.startswith(('language-', 'lang-')):
                        lang = cls.split('-')[1]
                        if not self.config.code_languages or lang in self.config.code_languages:
                            language = lang
                            break
                
                # Process code content
                code_text = code.get_text()
                if code_text:
                    lines = code_text.splitlines()
                    # Preserve indentation
                    if lines:
                        min_indent = min((len(line) - len(line.lstrip()) 
                                       for line in lines if line.strip()), default=0)
                        processed_lines = [line[min_indent:] if line.strip() else '' 
                                        for line in lines]
                        code_text = '\n'.join(processed_lines)
                        
                        # Create markdown code block
                        markdown_block = f"```{language or ''}\n{code_text.strip()}\n```"
                        pre.replace_with(BeautifulSoup(markdown_block, 'html.parser'))

    def _process_links(self, soup, base_url=None):
        """Process links with proper URL handling and sanitization."""
        for a in soup.find_all('a'):
            href = a.get('href', '')
            text = a.get_text() or ''

            if not href:
                if text:
                    new_tag = soup.new_tag('span')
                    new_tag.string = text
                    a.replace_with(new_tag)
                continue

            # Handle javascript: and other unsafe URLs
            if re.match(r'^(javascript|data|vbscript):', href.lower()):
                a['href'] = '#'
            elif self.config.sanitize_urls:
                a['href'] = self._sanitize_url(href, base_url)

            # Apply URL filters
            if self.url_filters and not all(f(href) for f in self.url_filters):
                new_tag = soup.new_tag('span')
                new_tag.string = f"[{text}](#)"
                a.replace_with(new_tag)
                continue

            # Create markdown link
            new_tag = soup.new_tag('span')
            new_tag.string = f"[{text}]({href})"
            a.replace_with(new_tag)

    def _extract_headings(self, soup):
        """Extract headings with proper level filtering."""
        headings = []
        for level in range(1, min(self.config.max_heading_level + 1, 7)):
            for heading in soup.find_all(f'h{level}'):
                text = heading.get_text().strip()
                if text:  # Only add non-empty headings
                    headings.append({
                        'level': level,
                        'text': text
                    })
        return headings

    def _extract_structure(self, soup):
        """Extract document structure including headings and sections."""
        structure = {
            'headings': [],
            'sections': [],
            'custom_elements': []
        }
        
        # Process headings
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            level = int(tag.name[1])
            if level <= self.config.max_heading_level:
                heading = {
                    'level': level,
                    'text': tag.get_text().strip(),
                    'id': tag.get('id', ''),
                    'classes': tag.get('class', [])
                }
                structure['headings'].append(heading)
        
        # Process sections
        for section in soup.find_all(['section', 'article', 'div'], class_=lambda x: x and 'section' in x):
            section_data = {
                'id': section.get('id', ''),
                'classes': section.get('class', []),
                'heading': None,
                'content_type': section.get('data-content-type', '')
            }
            
            # Find section heading
            heading = section.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if heading:
                section_data['heading'] = heading.get_text().strip()
            
            structure['sections'].append(section_data)

        return structure

    def _process_images(self, soup, base_url=None):
        """Process images with proper URL handling."""
        for img in soup.find_all('img'):
            src = img.get('src', '')
            alt = img.get('alt', '')
            title = img.get('title', '')

            if not src:
                if alt:
                    new_tag = soup.new_tag('span')
                    new_tag.string = alt
                    img.replace_with(new_tag)
                continue

            # Handle data URLs
            if src.startswith('data:'):
                if src not in self.assets['images']:
                    self.assets['images'].append(src)
                new_tag = soup.new_tag('span')
                new_tag.string = f"![{alt}]({src})"
                if title:
                    new_tag.string += f" \"{title}\""
                img.replace_with(new_tag)
                continue

            # Handle relative URLs
            if base_url and not src.startswith(('http://', 'https://')):
                try:
                    src = urljoin(base_url, src)
                except Exception:
                    pass  # Keep original URL on error

            # Create markdown image
            new_tag = soup.new_tag('span')
            new_tag.string = f"![{alt}]({src})"
            if title:
                new_tag.string += f" \"{title}\""
            img.replace_with(new_tag)

    def configure(self, config):
        """Configure the processor with custom settings."""
        if isinstance(config, dict):
            # Update allowed tags
            if 'allowed_tags' in config:
                self.config.allowed_tags = config['allowed_tags']

            # Update max heading level
            if 'max_heading_level' in config:
                self.config.max_heading_level = config['max_heading_level']

            # Update preserve whitespace elements
            if 'preserve_whitespace_elements' in config:
                self.config.preserve_whitespace_elements = config['preserve_whitespace_elements']

            # Update code languages
            if 'code_languages' in config:
                self.config.code_languages = config['code_languages']

            # Update URL sanitization
            if 'sanitize_urls' in config:
                self.config.sanitize_urls = config['sanitize_urls']

            # Update metadata prefixes
            if 'metadata_prefixes' in config:
                self.config.metadata_prefixes = config['metadata_prefixes']

            # Update comment extraction
            if 'extract_comments' in config:
                self.config.extract_comments = config['extract_comments']

            # Update content length limits
            if 'max_content_length' in config:
                self.config.max_content_length = config['max_content_length']
            if 'min_content_length' in config:
                self.config.min_content_length = config['min_content_length']

            # Update markdownify options
            self.markdownify_options.update({
                'heading_style': 'ATX',
                'strong_style': '**',
                'emphasis_style': '_',
                'bullets': '-',
                'code_language': False,
                'escape_asterisks': False,
                'escape_underscores': False,
                'escape_code': False,
                'code_block_style': '```',
                'wrap_width': None,
                'convert_links': True,
                'hr_style': '---',
                'br_style': '  ',
                'default_title': 'Untitled Document',
                'newline_style': '\n',
                'convert_all': True,
                'preserve_whitespace': True,
                'strip': ['style', 'onclick', 'onload', 'onmouseover', 'onmouseout', 'onkeydown', 'onkeyup']
            })

    def add_content_filter(self, filter_func):
        """Add a custom content filter."""
        self.content_filters.append(filter_func)

    def add_url_filter(self, filter_func):
        """Add a custom URL filter."""
        self.url_filters.append(filter_func)

    def add_content_extractor(self, name, extractor):
        """Add a custom content extractor."""
        self.content_extractors[name] = extractor

    def add_metadata_extractor(self, extractor):
        """Add a custom metadata extractor."""
        self.metadata_extractors.append(extractor)

    def _process_definition_lists(self, soup):
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

    def _process_footnotes(self, soup):
        """Process footnotes into markdown format."""
        footnotes = {}
        # Find all footnote references
        for ref in soup.find_all('sup', id=re.compile(r'^fnref\d+')):
            link = ref.find('a')
            if link and link.get('href', '').startswith('#fn'):
                fn_id = link['href'][1:]  # Remove #
                footnotes[fn_id] = len(footnotes) + 1
                ref.string = f"[{footnotes[fn_id]}]"
        
        # Process footnote content
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

    def _process_abbreviations(self, soup):
        """Process abbreviations into markdown format."""
        for abbr in soup.find_all('abbr'):
            title = abbr.get('title')
            if title:
                abbr.replace_with(f"{abbr.get_text()} ({title})")
            else:
                abbr.replace_with(abbr.get_text())
    def _process_iframes(self, soup):
        """Process iframes to markdown format."""
        for iframe in soup.find_all('iframe'):
            src = iframe.get('src', '')
            if src and self._is_safe_url(src):
                markdown_iframe = f'[iframe]({src})'
                iframe.replace_with(BeautifulSoup(markdown_iframe, 'html.parser'))
            else:
                iframe.decompose()

    def _convert_table_to_markdown(self, table):
        """Convert HTML table to markdown format with proper handling of empty tables."""
        if not table.find_all(['tr', 'th', 'td']):
            return ''  # Return empty string for empty tables
            
        rows = []
        header_row = table.find('tr')
        
        # Process header row
        if header_row:
            headers = []
            for th in header_row.find_all(['th', 'td']):
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
                text = cell.get_text().strip() or ' '  # Use space for empty cells
                cells.extend([text] * colspan)
            
            if cells:
                rows.append('| ' + ' | '.join(cells) + ' |')
        
        return '\n'.join(rows) if rows else ''

    def _is_safe_url(self, url):
        """Check if URL is safe to use."""
        if not url:
            return False
        
        # Allow data URLs only for images
        if url.startswith('data:'):
            return url.startswith('data:image/')
        
        # Check for dangerous protocols
        if any(url.lower().startswith(proto) for proto in [
            'javascript:', 'data:', 'vbscript:', 'file:', 'about:', 'blob:'
        ]):
            return False
        
        try:
            parsed = urlparse(url)
            return bool(parsed.netloc) and parsed.scheme in ['http', 'https', 'ftp', 'mailto']
        except Exception:
            return False

    def _process_content(self, soup, base_url=None):
        """Process HTML content with all features."""
        try:
            # Check content length
            content_length = len(str(soup))
            if content_length > self.config.max_content_length:
                self.result.title = "Content Too Large"
                return
            
            # Initialize content and structure
            self.result.content = {}
            self.result.structure = {'headings': [], 'sections': [], 'custom_elements': []}

            # Process body or full document
            body = soup.find('body') or soup

            # Extract structure first
            self.result.structure = self._extract_structure(body)
            
            # Process special elements
            self._process_definition_lists(body)
            self._process_footnotes(body)
            self._process_abbreviations(body)
            self._process_iframes(body)
            self._process_code_blocks(body)
            
            # Extract assets
            self._extract_assets(body, self.result, base_url)
            
            # Process links and images
            self._process_links(body, base_url)
            self._process_images(body, base_url)
            
            # Convert to markdown
            markdown = self._convert_to_markdown(body)
            self.result.content["formatted_content"] = markdown.strip()
            
            # Apply content filters
            if self.content_filters:
                filtered_content = self.result.content["formatted_content"]
                for filter_func in self.content_filters:
                    if not filter_func(filtered_content):
                        self.result.content["formatted_content"] = ""
                        break
            
        except Exception as e:
            self.result.errors.append(f"Error processing content: {str(e)}")

    def _convert_to_markdown(self, soup):
        """Convert HTML to markdown with enhanced features."""
        class CustomConverter(markdownify.MarkdownConverter):
            def __init__(self, processor, **options):
                super().__init__(**options)
                self.processor = processor

            def convert_table(self, el, text, convert_as_inline):
                return self.processor._convert_table_to_markdown(el)

            def convert_pre(self, el, text, convert_as_inline):
                code = el.find('code')
                if code:
                    # Get language class if present
                    lang_class = None
                    language = ''
                    for cls in code.get('class', []):
                        if cls.startswith('language-'):
                            lang = cls.replace('language-', '')
                            if not self.processor.config.code_languages or lang in self.processor.config.code_languages:
                                lang_class = lang
                                break
                        elif cls.startswith(('language-', 'lang-')):
                            language = cls.split('-')[1]
                            break
                    content = code.get_text().strip()
                    return f'```{language}\n{content}\n```'
                return f'```\n{text}\n```'
                
            def convert_img(self, el, text, convert_as_inline):
                alt = el.get('alt', '')
                src = el.get('src', '')
                title = el.get('title', '')
                if src:
                    if title:
                        return f'![{alt}]({src} "{title}")'
                    return f'![{alt}]({src})'
                return alt

        return CustomConverter(heading_style='atx').convert_soup(soup)

# Alias for backward compatibility
ProcessingResult = ProcessedContent
