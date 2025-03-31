"""Metadata extraction functionality."""
import json
import logging
import re
from typing import Dict, Any, List
from bs4 import BeautifulSoup

# Configure logging
logger = logging.getLogger(__name__)

def process_json_ld(data: Dict[str, Any], metadata: Dict[str, Any], prefix: str = '') -> None:
    """Process JSON-LD data recursively."""
    if isinstance(data, dict):
        # Process individual fields
        for key, value in data.items():
            if key.startswith('@'):
                continue  # Skip @context, @type, etc.

            current_key = (prefix + key).lower() if prefix else key.lower()
            
            if isinstance(value, (str, int, float, bool)):
                if current_key not in metadata:
                    metadata[current_key] = str(value)
            elif isinstance(value, dict):
                # Store complete object if it's a nested entity
                if '@type' in value:
                    if current_key not in metadata:
                        metadata[current_key] = value
                    new_prefix = f"{current_key}_"
                    process_json_ld(value, metadata, new_prefix)
                else:
                    process_json_ld(value, metadata, current_key + '_')
            elif isinstance(value, list):
                # Handle arrays of objects
                if value and isinstance(value[0], dict):
                    if current_key not in metadata:
                        metadata[current_key] = value
                for item in value:
                    process_json_ld(item, metadata, current_key + '_')

def process_microdata(element: BeautifulSoup, metadata: Dict[str, Any]) -> None:
    """Process microdata attributes."""
    for prop in element.find_all(True, itemprop=True):
        name = prop.get('itemprop', '').lower()
        # Get all possible content values
        content = prop.get('content', '')
        if content is None:  # If no content attribute
            content = prop.get('value', '')  # Try value attribute
        if content is None:  # If no value attribute
            content = prop.string or ''  # Try text content
        
        if name:
            metadata[name] = content.strip() if content else ''

def extract_metadata(soup: BeautifulSoup) -> Dict[str, Any]:
    """Extract metadata from HTML."""
    metadata = {}
    
    # Process JSON-LD first
    json_ld_scripts = soup.find_all('script', type='application/ld+json')
    for script in json_ld_scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, dict):
                process_json_ld(data, metadata)
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        process_json_ld(item, metadata)
        except (json.JSONDecodeError, AttributeError):
            continue

    # Extract standard meta tags
    meta_tags = soup.find_all('meta')
    for meta in meta_tags:
        # Get name/property and content values
        name = meta.get('name', '').lower()
        prop = meta.get('property', '').lower()
        content = meta.get('content')
        if content is None:
            content = meta.get('value', '')

        # Normalize content
        content = '' if content is None else str(content).strip()
        
        # Handle meta redirects
        if meta.get('http-equiv', '').lower() == 'refresh' and content:
            redirect_match = re.search(r'url=[\'"]*([^\'"]+)', content, re.IGNORECASE)
            if redirect_match:
                metadata.setdefault('meta_redirects', []).append(redirect_match.group(1))

        # Process metadata based on name/property
        if name:  # Regular meta tag with name
            if name not in metadata:
                metadata[name] = content
        elif prop:  # OpenGraph and similar with property
            if prop not in metadata:
                metadata[prop] = content
        elif meta.has_attr('property'):  # Empty property case
            key = meta.get('content', '').strip()
            if key:  # Use content as key if non-empty
                metadata[key.lower()] = ''

    # Extract title, prioritizing <head> section
    head_title = soup.head
    if head_title:
        title_tag = head_title.find('title')
    else:
        title_tag = soup.find('title')

    if not title_tag:
        title_tag = soup.find('h1')

    if title_tag and title_tag.string:
        title = title_tag.string.strip()
        metadata['title'] = title
    else:
        metadata['title'] = "Untitled Document"

    # Process microdata
    for element in soup.find_all(True, itemtype=True):
        process_microdata(element, metadata)

    return metadata