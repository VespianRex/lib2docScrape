# src/processors/content_processor.py

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from bs4 import BeautifulSoup, Comment, NavigableString, Tag
import markdownify
from urllib.parse import urljoin, urlparse

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


@dataclass
class ProcessorConfig:
    allowed_tags: List[str] = field(default_factory=lambda: [
        'p', 'a', 'strong', 'em', 'code', 'pre', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'img', 'blockquote', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'iframe', 'object', 'abbr'
    ])
    max_heading_level: int = 6
    preserve_whitespace_elements: List[str] = field(default_factory=lambda: ['pre', 'code'])
    code_languages: List[str] = field(default_factory=lambda: ['python', 'javascript', 'ruby'])
    sanitize_urls: bool = True
    metadata_prefixes: List[str] = field(default_factory=lambda: ['og:', 'twitter:', 'dc:'])
    extract_comments: bool = False
    max_content_length: Optional[int] = None
    min_content_length: Optional[int] = None


@dataclass
class ProcessedContent:
    title: str = "Untitled Document"
    content: Dict[str, Any] = field(default_factory=lambda: {})
    metadata: Dict[str, Any] = field(default_factory=lambda: {})
    assets: Dict[str, List[str]] = field(default_factory=lambda: {
        'images': [],
        'stylesheets': [],
        'scripts': [],
        'media': []
    })
    errors: List[str] = field(default_factory=list)


class ContentProcessor:
    def __init__(self, config=None):
        self.config = config if config else ProcessorConfig()
        self.content_filters = []
        self.url_filters = []
        self.content_extractors = {}
        self.metadata_extractors = []
        self.markdownify_options = {
            'heading_style': "ATX",
            'bullets': "-",
            'strip': ['style'],
            'autolinks': True,
            'code_language': True,
            'strong_style': '**',
            'emphasis_style': '_',
            'escape_asterisks': False,
            'escape_underscores': False,
            'escape_code': False,
            'code_block_style': '```',
            'wrap_width': None,
            'convert_links': True,
            'hr_style': '---',
            'br_style': '  ',
            'default_title': 'Title',
            'newline_style': '\n',
            'convert_all': True,
            'preserve_whitespace': True
        }

    def process(self, html, base_url=None):
        """Process HTML content and return structured result."""
        try:
            if not html or not html.strip():
                return ProcessedContent(
                    title="Untitled Document",
                    content={'formatted_content': ''},
                    metadata={'title': 'Untitled Document'},
                    assets={'images': [], 'stylesheets': [], 'scripts': [], 'media': []},
                    errors=[]
                )

            # Parse HTML
            soup = BeautifulSoup(html, 'html.parser')
            result = ProcessedContent()

            # Extract title from head or first h1
            head = soup.find('head')
            if head and head.find('title') and head.find('title').string:
                result.title = head.find('title').string.strip()
                if not result.title:
                    result.title = "Untitled Document"
            else:
                h1 = soup.find('h1')
                if h1 and h1.string:
                    result.title = h1.string.strip()
                else:
                    result.title = "Untitled Document"

            # Extract metadata first
            self._extract_metadata(soup, result)

            # Process special elements before markdownify
            self._process_code_blocks(soup)
            self._process_definition_lists(soup)
            self._process_abbreviations(soup)
            self._process_comments(soup)
            self._process_iframes(soup)
            self._process_links(soup, base_url)
            self._process_images(soup, base_url)

            # Filter out headings beyond max level
            for i in range(self.config.max_heading_level + 1, 7):
                for h in soup.find_all(f'h{i}'):
                    h.decompose()

            # Apply content filters
            if self.content_filters:
                for filter_func in self.content_filters:
                    for element in soup.find_all(string=True):
                        if not isinstance(element, Comment):
                            try:
                                if not filter_func(str(element)):
                                    if element.parent:
                                        element.parent.decompose()
                            except Exception as e:
                                result.errors.append(f"Content filter error: {str(e)}")

            # Process content
            content = ''
            if soup.body:
                content = markdownify.markdownify(str(soup.body), **self.markdownify_options)
            elif soup.find(True):  # Find any tag if no body
                content = markdownify.markdownify(str(soup.find(True)), **self.markdownify_options)

            # Store content
            result.content = {
                'formatted_content': content.strip(),
                'headings': self._extract_headings(soup),
                'structure': self._extract_structure(soup)
            }

            # Extract assets
            self._extract_assets(soup, result, base_url)

            # Apply custom extractors
            for name, extractor in self.content_extractors.items():
                try:
                    result.content[name] = extractor(soup)
                except Exception as e:
                    result.errors.append(f"Error in {name}: {str(e)}")

            # Apply custom metadata extractors
            for extractor in self.metadata_extractors:
                try:
                    custom_metadata = extractor(soup)
                    if custom_metadata:
                        result.metadata.update(custom_metadata)
                except Exception as e:
                    result.errors.append(f"Error in metadata extractor: {str(e)}")

            return result

        except Exception as e:
            logger.error(f"Error processing content: {str(e)}")
            return ProcessedContent(
                title="Untitled Document",
                content={'formatted_content': ''},
                metadata={'title': 'Untitled Document'},
                assets={'images': [], 'stylesheets': [], 'scripts': [], 'media': []},
                errors=[str(e)]
            )

    def _extract_metadata(self, soup, result):
        """Extract metadata from HTML with proper handling of duplicates."""
        # Initialize metadata dict
        result.metadata = {'title': result.title}

        # Extract meta tags (keep last occurrence)
        meta_tags = {}
        for meta in soup.find_all('meta'):
            name = meta.get('name', meta.get('property', ''))
            content = meta.get('content', '')
            http_equiv = meta.get('http-equiv', '').lower()

            if http_equiv == 'refresh' and content:
                url_match = re.search(r'url=[\'"]*([^\'"]*)', content, re.I)
                if url_match:
                    if 'meta_redirects' not in result.metadata:
                        result.metadata['meta_redirects'] = []
                    result.metadata['meta_redirects'].append(url_match.group(1))
            elif name:
                name = name.lower()
                meta_tags[name] = content or ''
            elif meta.get('property', ''):
                prop = meta.get('property', '').lower()
                if prop:
                    meta_tags[prop] = content or ''

        # Extract microdata (takes precedence over meta tags)
        for element in soup.find_all(attrs={'itemprop': True}):
            prop = element.get('itemprop')
            content = element.get('content', element.string)
            if prop:
                prop = prop.lower()
                meta_tags[prop] = content.strip() if content else ''

        # Extract JSON-LD (lowest precedence)
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    if data.get('@type') == 'Organization':
                        meta_tags['organization'] = data
                    else:
                        for key, value in data.items():
                            if not key.startswith('@'):
                                key = key.lower()
                                meta_tags[key] = value
            except (json.JSONDecodeError, AttributeError):
                continue

        # Handle empty properties
        for key, value in meta_tags.items():
            if value is None:
                meta_tags[key] = ''

        # Update metadata with collected tags
        result.metadata.update(meta_tags)

    def _process_code_blocks(self, soup):
        """Process code blocks with proper language detection and indentation preservation."""
        for pre in soup.find_all('pre'):
            code = pre.find('code')
            if code:
                # Get language class if present
                lang_class = None
                for cls in code.get('class', []):
                    if cls.startswith('language-'):
                        lang = cls.replace('language-', '')
                        if not self.config.code_languages or lang in self.config.code_languages:
                            lang_class = lang
                            break
                    elif cls in self.config.code_languages:
                        lang_class = cls
                        break

                # Preserve indentation by splitting into lines
                code_text = code.get_text()
                if code_text:
                    lines = code_text.split('\n')
                    # Remove leading/trailing empty lines
                    while lines and not lines[0].strip():
                        lines.pop(0)
                    while lines and not lines[-1].strip():
                        lines.pop()
                    
                    if lines:
                        # Find common indentation
                        indents = []
                        for line in lines:
                            if line.strip():
                                indent = len(line) - len(line.lstrip())
                                indents.append(indent)
                        min_indent = min(indents) if indents else 0

                        # Remove common indentation and preserve internal indentation
                        processed_lines = []
                        for line in lines:
                            if line.strip():
                                # Preserve relative indentation
                                current_indent = len(line) - len(line.lstrip())
                                relative_indent = current_indent - min_indent
                                if relative_indent > 0:
                                    processed_lines.append('    ' * (relative_indent // 4) + line.lstrip())
                                else:
                                    processed_lines.append(line.lstrip())
                            else:
                                processed_lines.append('')

                        # Reconstruct code block with proper formatting
                        code_text = '\n'.join(processed_lines)
                        
                        # Create markdown code block
                        if lang_class:
                            pre.string = f"```{lang_class}\n{code_text}\n```"
                        else:
                            pre.string = f"```\n{code_text}\n```"
            else:
                # Handle inline code
                code_text = pre.get_text().strip()
                if code_text:
                    new_tag = soup.new_tag('code')
                    new_tag.string = f"`{code_text}`"
                    pre.replace_with(new_tag)

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

            # Handle javascript: URLs and other unsafe protocols
            if href.lower().startswith(('javascript:', 'data:', 'vbscript:')):
                new_tag = soup.new_tag('span')
                new_tag.string = f"[{text}](#)"
                a.replace_with(new_tag)
                continue

            # Handle relative URLs
            if base_url and not href.startswith(('http://', 'https://', 'mailto:', 'tel:', 'ftp://')):
                try:
                    href = urljoin(base_url, href)
                except Exception:
                    pass  # Keep original URL on error

            # Sanitize URL if enabled
            if self.config.sanitize_urls:
                href = self._sanitize_url(href)

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

    def _extract_assets(self, soup, result, base_url=None):
        """Extract assets with proper handling of duplicates and data URLs."""
        # Initialize assets dict if needed
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
            if base_url and not url.startswith(('http://', 'https://', 'data:')):
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

        # Extract other assets
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                if src.startswith('data:'):
                    if src not in result.assets['images']:
                        result.assets['images'].append(src)
                elif not src.lower().startswith(('javascript:', 'vbscript:')):
                    url = process_url(src)
                    if url and url not in result.assets['images']:
                        result.assets['images'].append(url)

        for script in soup.find_all('script', src=True):
            src = script.get('src')
            if src and not src.lower().startswith(('javascript:', 'data:', 'vbscript:')):
                url = process_url(src)
                if url and url not in result.assets['scripts']:
                    result.assets['scripts'].append(url)

        for media in soup.find_all(['audio', 'video', 'source']):
            src = media.get('src')
            if src and not src.lower().startswith(('javascript:', 'data:', 'vbscript:')):
                url = process_url(src)
                if url and url not in result.assets['media']:
                    result.assets['media'].append(url)

    def _sanitize_url(self, url):
        """Sanitize URL by removing unsafe characters and protocols."""
        if not url or url == '#':
            return '#'
        
        try:
            parsed = urlparse(url)
            if not parsed.scheme:
                return url
            if parsed.scheme.lower() not in ('http', 'https', 'mailto', 'tel', 'ftp'):
                return '#'
            return url
        except Exception:
            return '#'

    def _process_definition_lists(self, soup):
        """Process definition lists with proper formatting."""
        for dl in soup.find_all('dl'):
            items = []
            for dt in dl.find_all('dt'):
                term = dt.get_text().strip()
                definitions = []
                next_tag = dt.find_next_sibling()
                while next_tag and next_tag.name == 'dd':
                    definitions.append(next_tag.get_text().strip())
                    next_tag = next_tag.find_next_sibling()
                if term:
                    items.append(f"**{term}**")
                    for definition in definitions:
                        items.append(f": {definition}")
            if items:
                new_tag = soup.new_tag('div')
                new_tag.string = '\n'.join(items)
                dl.replace_with(new_tag)

    def _process_abbreviations(self, soup):
        """Process abbreviations with proper formatting."""
        for abbr in soup.find_all('abbr'):
            title = abbr.get('title', '')
            text = abbr.get_text().strip()
            if title and text:
                new_tag = soup.new_tag('span')
                new_tag.string = f"{text} ({title})"
                abbr.replace_with(new_tag)

    def _process_comments(self, soup):
        """Process HTML comments if enabled."""
        if self.config.extract_comments:
            for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                if comment.strip():
                    new_p = soup.new_tag('p')
                    new_p.string = f"<!-- {comment.strip()} -->"
                    comment.replace_with(new_p)
        else:
            for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                comment.extract()

    def _process_iframes(self, soup):
        """Process iframes with proper formatting."""
        for iframe in soup.find_all('iframe'):
            src = iframe.get('src', '')
            if src:
                new_tag = soup.new_tag('p')
                new_tag.string = f"[Embedded content]({src})"
                iframe.replace_with(new_tag)

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
                'heading_style': 'atx',
                'strong_style': '**',
                'emphasis_style': '*',
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

    def _convert_table_to_markdown(self, table):
        """Convert HTML table to markdown format."""
        rows = []
        
        # Process header
        header_row = table.find('tr')
        if header_row:
            headers = []
            for th in header_row.find_all(['th', 'td']):
                colspan = int(th.get('colspan', 1))
                headers.extend([th.get_text().strip()] * colspan)
            
            if headers:
                rows.append('| ' + ' | '.join(headers) + ' |')
                rows.append('| ' + ' | '.join(['---'] * len(headers)) + ' |')

        # Process data rows
        for row in table.find_all('tr')[1:]:
            cells = []
            for td in row.find_all('td'):
                rowspan = int(td.get('rowspan', 1))
                colspan = int(td.get('colspan', 1))
                cell_text = td.get_text().strip()
                cells.extend([cell_text] * colspan)
            
            if cells:
                rows.append('| ' + ' | '.join(cells) + ' |')

        return '\n'.join(rows)

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
        """Extract document structure."""
        structure = []
        for tag in soup.find_all(True):
            if tag.name in self.config.allowed_tags:
                structure.append({
                    'tag': tag.name,
                    'level': len(list(tag.parents)),
                    'text': tag.get_text().strip()
                })
        return structure

    def _process_metadata(self, soup):
        """Extract metadata from HTML."""
        metadata = {}
        
        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text().strip()
        
        # Extract meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name', '').lower()
            content = meta.get('content', '')
            if name and content:
                metadata[name] = content
        
        # Extract JSON-LD
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    if data.get('@type') == 'Organization':
                        metadata['organization'] = data
                    else:
                        metadata.update({k.lower(): v for k, v in data.items() 
                                      if k not in ['@context', '@type']})
            except (json.JSONDecodeError, AttributeError):
                continue
        
        return metadata

    def _collect_assets(self, soup, base_url=None):
        """Collect assets from HTML."""
        assets = {
            'images': [],
            'stylesheets': [],
            'scripts': [],
            'media': []
        }
        
        # Collect scripts
        for script in soup.find_all('script', src=True):
            src = script.get('src')
            if src and base_url:
                src = urljoin(base_url, src)
                assets["scripts"].append(src)
                
        # Collect stylesheets
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href')
            if href and base_url:
                href = urljoin(base_url, href)
                assets["stylesheets"].append(href)
                
        # Collect images
        for img in soup.find_all('img'):
            src = img.get('src')
            if src and base_url:
                src = urljoin(base_url, src)
                assets["images"].append(src)
                
        return assets

    def _apply_content_filters(self, content):
        """Apply content filters to HTML content."""
        if not content:
            return content
        
        soup = BeautifulSoup(content, 'html.parser')
        
        for filter_func in self.content_filters:
            # Apply filter to text nodes
            for text in soup.find_all(text=True):
                if not isinstance(text, Comment):
                    if not filter_func(text.string):
                        text.replace_with('')
        
        return str(soup)

    def _apply_url_filters(self, url):
        """Apply URL filters."""
        if not url:
            return '#'
        
        for filter_func in self.url_filters:
            if not filter_func(url):
                return '#'
        
        return url