"""Asset handling functionality for images, stylesheets, scripts and media."""
import logging
from typing import Dict, List
from bs4 import BeautifulSoup
from .url_handler import sanitize_and_join_url
from urllib.parse import urljoin # Keep top-level import

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
            if src:
                src = src.strip()
                if src:
                    if src.startswith('data:'):
                        self._add_asset('images', src) # Add data URLs directly
                    else:
                        # print(f"DEBUG AssetHandler: Calling sanitize_and_join_url for src='{src}', base_url='{base_url}'") # Debug Removed
                        url = sanitize_and_join_url(src, base_url)
                        # print(f"DEBUG AssetHandler: sanitize_and_join_url returned: '{url}'") # Debug Removed
                        if url:
                            self._add_asset('images', url)
                        # else:
                            # print(f"DEBUG AssetHandler: Not adding empty URL returned for src='{src}'") # Debug Removed


        # Extract scripts
        for script in soup.find_all('script', src=True):
            src = script.get('src')
            if src:
                 url = sanitize_and_join_url(src, base_url)
                 if url:
                     self._add_asset('scripts', url)


        # Extract media
        for media in soup.find_all(['audio', 'video', 'source']):
            src = media.get('src')
            if src and src.strip():
                 # print(f"DEBUG AssetHandler: Calling sanitize_and_join_url for media src='{src}', base_url='{base_url}'") # Debug Removed
                 url = sanitize_and_join_url(src, base_url)
                 # print(f"DEBUG AssetHandler: sanitize_and_join_url returned for media: '{url}'") # Debug Removed
                 if url:
                     self._add_asset('media', url)
                 # else:
                     # print(f"DEBUG AssetHandler: Not adding empty media URL returned for src='{src}'") # Debug Removed


        return self.assets

    def _add_asset(self, asset_type: str, url: str) -> None:
        """Add an asset URL if it's not already present."""
        if asset_type in self.assets and url not in self.assets[asset_type]:
            self.assets[asset_type].append(url)

    def process_images(self, soup: BeautifulSoup, base_url: str = None) -> None:
        """DEPRECATED/SIMPLIFIED: Only ensures image URLs are added to assets. Does not modify soup."""
        # This method originally modified the soup to insert markdown.
        # However, asset collection now happens in extract_assets based on the cleaned soup,
        # and markdown generation happens later based on the extracted structure.
        # We keep this method for now to ensure URLs are added, but it shouldn't modify the soup.
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if not src:
                continue # Skip images without src

            # Handle data URLs
            if src.startswith('data:'):
                # Ensure data URLs for images are added
                if src.startswith('data:image/'):
                     self._add_asset('images', src)
                # Do not modify the soup here
                continue # Skip to next img tag

            # Sanitize and process regular URLs
            processed_src = sanitize_and_join_url(src, base_url)

            if processed_src:
                # Add to assets (duplicates handled by _add_asset)
                self._add_asset('images', processed_src)
            # Do not modify the soup here (no replace_with or decompose)

    def clear(self) -> None:
        """Clear all stored assets."""
        for asset_type in self.assets:
            self.assets[asset_type].clear()