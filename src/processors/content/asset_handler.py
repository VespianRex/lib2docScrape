"""Asset handling functionality for images, stylesheets, scripts and media."""
import logging
from typing import Dict, List
from bs4 import BeautifulSoup
from .url_handler import sanitize_and_join_url

# Configure logging
logger = logging.getLogger(__name__)

class AssetHandler:
    """Handle extraction and processing of various asset types."""
    
    def __init__(self):
        self.assets: Dict[str, List[str]] = {
            'images': [],
            'stylesheets': [],
            'scripts': [],
            'media': []
        }

    def extract_assets(self, soup: BeautifulSoup, base_url: str = None) -> Dict[str, List[str]]:
        """Extract assets with proper handling of duplicates and data URLs."""
        # Extract stylesheets
        stylesheet_links = soup.find_all('link', rel='stylesheet')
        for link in stylesheet_links:
            href = link.get('href')
            if href:
                url = sanitize_and_join_url(href, base_url)
                if url:
                    self._add_asset('stylesheets', url)

        # Extract images
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:  # Process any non-None src
                src = src.strip()
                if src:  # Process non-empty src after stripping
                    if src.startswith('data:'):
                        self._add_asset('images', src)
                    elif not src.lower().startswith(('javascript:', 'vbscript:', 'data:', 'about:', 'blob:')):
                        # Accept relative URLs and non-dangerous absolute URLs
                        url = sanitize_and_join_url(src, base_url)
                        if url:
                            self._add_asset('images', url)

        # Extract scripts
        for script in soup.find_all('script', src=True):
            src = script.get('src')
            if src and not src.lower().startswith(('javascript:', 'data:', 'vbscript:')):
                url = sanitize_and_join_url(src, base_url)
                if url:
                    self._add_asset('scripts', url)

        # Extract media
        for media in soup.find_all(['audio', 'video', 'source']):
            src = media.get('src')
            if src and src.strip():  # Ensure src is not empty
                if not src.lower().startswith(('javascript:', 'data:', 'vbscript:')):
                    url = sanitize_and_join_url(src, base_url)
                    if url:
                        self._add_asset('media', url)

        return self.assets

    def _add_asset(self, asset_type: str, url: str) -> None:
        """Add an asset URL if it's not already present."""
        if asset_type in self.assets and url not in self.assets[asset_type]:
            self.assets[asset_type].append(url)

    def process_images(self, soup: BeautifulSoup, base_url: str = None) -> None:
        """Process images to markdown format while tracking them as assets."""
        for img in soup.find_all('img'):
            src = img.get('src', '')
            alt = img.get('alt', '')
            title = img.get('title', '')

            if not src:
                if alt:
                    new_tag = soup.new_tag('span')
                    new_tag.string = alt
                    img.replace_with(new_tag)
                return

            # Handle data URLs
            if src.startswith('data:'):
                if src not in self.assets['images']:
                    self.assets['images'].append(src)
                new_tag = soup.new_tag('span')
                new_tag.string = f"![{alt}]({src})"
                if title:
                    new_tag.string += f" \"{title}\""
                img.replace_with(new_tag)
                return

            # Sanitize and process URL
            src = sanitize_and_join_url(src, base_url)
            if src:
                # Add to assets if not already present
                self._add_asset('images', src)
                
                # Create markdown image
                new_tag = soup.new_tag('span')
                new_tag.string = f"![{alt}]({src})"
                if title:
                    new_tag.string += f" \"{title}\""
                img.replace_with(new_tag)
            else:
                # Remove img if URL is invalid
                img.decompose()

    def clear(self) -> None:
        """Clear all stored assets."""
        for asset_type in self.assets:
            self.assets[asset_type].clear()