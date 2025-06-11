"""Asset handling functionality for images, stylesheets, scripts and media."""

import logging
from typing import Any

from bs4 import BeautifulSoup, Tag

from .url_handler import sanitize_and_join_url

# Configure logging
logger = logging.getLogger(__name__)


class AssetHandler:
    """Handle extraction and processing of various asset types."""

    def __init__(self):
        self.assets: dict[str, list[Any]] = {
            "images": [],
            "stylesheets": [],
            "scripts": [],
            "media": [],
        }

    def extract_assets(
        self, soup: BeautifulSoup, base_url: str | None = None
    ) -> dict[str, list[Any]]:
        """Extract assets with proper handling of duplicates and data URLs."""
        # Extract stylesheets
        stylesheet_links = soup.find_all("link", rel="stylesheet")
        for link in stylesheet_links:
            if isinstance(link, Tag) and link.has_attr(
                "href"
            ):  # Check if link is a Tag and has href
                href = link.get("href")
                if isinstance(href, str):  # Ensure href is a string
                    url = sanitize_and_join_url(href, base_url)
                    if url:
                        self._add_asset("stylesheets", url)

        # Extract images - return as dictionaries with src and alt attributes
        for img_element in soup.find_all("img"):
            if not isinstance(img_element, Tag):  # Skip if not a Tag
                continue

            # Now we know img_element is a Tag
            img: Tag = img_element
            src = img.get("src")
            if src and isinstance(src, str):  # Ensure src is a string
                src = src.strip()
                if src:
                    alt_attr = img.get("alt", "")
                    alt = alt_attr if isinstance(alt_attr, str) else ""
                    alt = alt.strip()

                    if src.startswith("data:"):
                        # Add data URLs directly
                        image_data = {"src": src, "alt": alt}
                        self._add_image_asset(image_data)
                    else:
                        url = sanitize_and_join_url(src, base_url)
                        if url:
                            image_data = {"src": url, "alt": alt}
                            self._add_image_asset(image_data)

        # Extract scripts
        for script_element in soup.find_all("script", src=True):
            if not isinstance(script_element, Tag) or not script_element.has_attr(
                "src"
            ):
                continue

            # Now we know script_element is a Tag with src attribute
            script: Tag = script_element
            src = script.get("src")
            if isinstance(src, str):  # Ensure src is a string
                url = sanitize_and_join_url(src, base_url)
                if url:
                    self._add_asset("scripts", url)

        # Extract media
        for media_element in soup.find_all(["audio", "video", "source"]):
            if not isinstance(media_element, Tag):
                continue

            # Now we know media_element is a Tag
            media: Tag = media_element
            src = media.get("src")
            if src and isinstance(src, str) and src.strip():  # Ensure src is a string
                url = sanitize_and_join_url(src, base_url)
                if url:
                    self._add_asset("media", url)

        return self.assets

    def _add_asset(self, asset_type: str, url: str) -> None:
        """Add an asset URL if it's not already present."""
        if asset_type in self.assets and url not in self.assets[asset_type]:
            self.assets[asset_type].append(url)

    def _add_image_asset(self, image_data: dict[str, str]) -> None:
        """Add an image asset if it's not already present."""
        if "images" in self.assets:
            # Check if image with same src already exists
            existing_srcs = []
            for img_asset in self.assets["images"]:
                if isinstance(img_asset, dict) and img_asset.get("src"):
                    existing_srcs.append(img_asset.get("src"))

            if image_data.get("src") not in existing_srcs:
                self.assets["images"].append(image_data)

    def process_images(self, soup: BeautifulSoup, base_url: str | None = None) -> None:
        """DEPRECATED/SIMPLIFIED: Only ensures image URLs are added to assets. Does not modify soup."""
        # This method originally modified the soup to insert markdown.
        # However, asset collection now happens in extract_assets based on the cleaned soup,
        # and markdown generation happens later based on the extracted structure.
        # We keep this method for now to ensure URLs are added, but it shouldn't modify the soup.
        for img_element in soup.find_all("img"):
            if not isinstance(
                img_element, Tag
            ):  # Skip if not a Tag (e.g., NavigableString)
                continue

            # Now we know img_element is a Tag
            img: Tag = img_element
            src = img.get("src", "")  # get() on Tag is safe
            if not src or not isinstance(src, str):  # Ensure src is a string
                continue  # Skip images without src

            # Handle data URLs
            if src.startswith("data:"):
                # Ensure data URLs for images are added
                if src.startswith("data:image/"):
                    alt_attr = img.get("alt", "")  # get() on Tag is safe
                    alt = alt_attr if isinstance(alt_attr, str) else ""
                    image_data = {"src": src, "alt": alt.strip()}
                    self._add_image_asset(image_data)
                # Do not modify the soup here
                continue  # Skip to next img tag

            # Sanitize and process regular URLs
            processed_src = sanitize_and_join_url(src, base_url)
            if processed_src:
                # Add to assets (duplicates handled by _add_image_asset)
                alt_attr = img.get("alt", "")  # get() on Tag is safe
                alt = alt_attr if isinstance(alt_attr, str) else ""
                image_data = {"src": processed_src, "alt": alt.strip()}
                self._add_image_asset(image_data)
            # Do not modify the soup here (no replace_with or decompose)

    def clear(self) -> None:
        """Clear all stored assets."""
        for asset_type in self.assets:
            self.assets[asset_type].clear()
