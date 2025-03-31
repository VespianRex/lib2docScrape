"""URL utilities for normalizing and processing URLs."""
import re
from typing import Optional
from urllib.parse import urlparse, urljoin, urlunparse, parse_qsl, urlencode

class URLNormalizer:
    """Handles URL normalization with proper handling of trailing slashes."""

    @staticmethod
    def normalize_url(url: str, base_url: Optional[str] = None) -> str:
        """Normalize URL to canonical form."""
        if not url:
            raise ValueError("URL cannot be empty")

        # Security checks first
        low_url = url.lower()

        # Check for malicious schemes/protocols
        if any(scheme in low_url for scheme in [
            'javascript:', 'data:', 'vbscript:', 'file:', 'about:', 'blob:',
            'shell:', 'chrome://'
        ]):
            raise ValueError("Invalid URL scheme")

        # Check for XSS attempts
        if any(pattern in low_url for pattern in [
            '<script', 'alert(', 'eval(', 'onmouseover=', 'onclick=', 'onerror='
        ]):
            raise ValueError("XSS attempt detected")

        # Now proceed with URL processing
        # Handle relative URLs
        if base_url and not urlparse(url).netloc:
            url = urljoin(base_url, url)

        # Parse and process URL
        parsed = urlparse(url)
        
        # Handle empty or root URLs first
        if not parsed.path:
            return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}/"
            
        # Convert to lowercase and handle ports
        netloc = parsed.netloc.lower()
        if ':' in netloc:
            domain, port = netloc.split(':')
            if ((parsed.scheme == 'http' and port == '80') or
                (parsed.scheme == 'https' and port == '443')):
                netloc = domain

        # First analyze the original URL structure
        original_path = parsed.path.split('?')[0]  # Remove query part for analysis
        path_segments = [s for s in original_path.split('/') if s and s != '.']
        is_root = not path_segments
        had_trailing_slash = original_path.endswith('/')
        print(f"DEBUG: path='{original_path}' segments={path_segments} root={is_root} slash={had_trailing_slash}")
        
        # Clean up path segments
        clean_segments = []
        
        # Process path segments without trailing slash handling
        for segment in path_segments:
            if segment == '.' or not segment:
                continue
            elif segment == '..' and clean_segments:
                clean_segments.pop()
            elif segment != '..':
                clean_segments.append(segment)
# Handle path based on type and original slash
if not clean_segments:
    path = '/'  # Root paths always have slash
    print(f"DEBUG: root path='{path}'")
else:
    path = '/' + '/'.join(clean_segments)
    print(f"DEBUG: path before slash='{path}' root={is_root} had_slash={had_trailing_slash}")
    # Only add trailing slash for non-root paths that had one
    if had_trailing_slash and not is_root:
        path += '/'
        print(f"DEBUG: added slash, final='{path}'")
                path += '/'

        # Handle query parameters once
        if parsed.query:
            # Parse and sort query parameters
            params = parse_qsl(parsed.query, keep_blank_values=True)
            param_dict = {k: v for k, v in params}
            sorted_params = sorted(param_dict.items())
            query_string = urlencode(sorted_params)
            # Add query to path
            path = f"{path}?{query_string}"

        # Build final URL
        normalized = urlunparse((
            parsed.scheme.lower(),
            netloc,
            path,  # Path already has trailing slash and query if needed
            '',  # params
            '',  # query already in path
            ''  # fragment
        ))
            
        return normalized.rstrip('?')  # Remove any trailing ? if no query
