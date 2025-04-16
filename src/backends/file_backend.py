"""Backend for reading local files."""

import logging
from typing import Dict, Optional, Any
import aiofiles # Use aiofiles for async file operations
from urllib.parse import urlparse, unquote
from pathlib import Path

from .base import CrawlerBackend, CrawlResult
from ..utils.url_info import URLInfo # Import URLInfo

logger = logging.getLogger(__name__)

class FileBackend(CrawlerBackend):
    """Backend for fetching content from local files."""

    def __init__(self):
        """Initialize the File backend."""
        super().__init__(name="file_backend")
        # No session needed for file operations

    # Updated signature to match how it's called by DocumentationCrawler
    async def crawl(self, url: str, config: Optional[Any] = None) -> CrawlResult:
        """Read content from a local file URL (file://...)."""
        # Create URLInfo object from the passed URL string
        try:
            url_info = URLInfo(url) # Create URLInfo internally
            if not url_info.is_valid:
                 raise ValueError(f"Invalid file URL provided: {url}")
        except Exception as e:
             logger.error(f"Error parsing file URL {url}: {e}")
             return CrawlResult(url=url, content={}, metadata={}, status=500, error=f"Invalid file URL: {url}")

        raw_url = url # Keep original url for error reporting if needed
        normalized_url = url_info.normalized_url

        try:
            # Use the parsed URL from the created url_info
            parsed_url = url_info._parsed # Access internal parsed result
            if not parsed_url or parsed_url.scheme != 'file':
                raise ValueError(f"FileBackend only supports 'file://' scheme, got: {parsed_url.scheme if parsed_url else 'None'}")

            # Convert file URI path to a system path
            file_path_str = unquote(parsed_url.path)
            # Basic check for absolute path (might need refinement for Windows file URIs if used)
            if not Path(file_path_str).is_absolute():
                 # Handle cases like file:relative/path which urlparse might allow
                 # Or file:///C:/path on windows where path is absolute but doesn't start with / in POSIX sense
                 # For simplicity, rely on Path object resolution below.
                 pass

            file_path = Path(file_path_str)

            if not file_path.is_file():
                error_msg = f"File not found: {file_path}"
                logger.error(error_msg)
                # Use raw_url for reporting the original requested URL
                return CrawlResult(url=raw_url, content={}, metadata={}, status=404, error=error_msg)

            async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
                content = await f.read()

            # Determine content type based on extension (basic)
            content_type = "text/html" # Default for test files
            if file_path.suffix.lower() == '.css':
                content_type = "text/css"
            elif file_path.suffix.lower() == '.js':
                content_type = "application/javascript"
            # Add more types as needed

            logger.debug(f"Successfully read file: {file_path}")
            # Use normalized_url in the successful result
            return CrawlResult(
                url=normalized_url,
                content={"html": content}, # Assume HTML for now, adjust if needed
                metadata={
                    "status": 200,
                    "headers": {"content-type": content_type}, # Basic header
                    "content_type": content_type
                },
                status=200
            )

        except Exception as e:
            logger.error(f"Error reading file {raw_url}: {str(e)}", exc_info=True)
            # Use raw_url for reporting the original requested URL in case of error
            return CrawlResult(
                url=raw_url,
                content={},
                metadata={},
                status=500, # Internal Server Error equivalent
                error=f"Error reading file: {str(e)}"
            )

    async def validate(self, content: CrawlResult) -> bool:
        """Validate the file content (basic check)."""
        return content is not None and content.status == 200 and content.content is not None

    async def process(self, content: CrawlResult) -> Dict[str, Any]:
        """Process the file content (basic passthrough)."""
        if not await self.validate(content):
            return {}
        return {
            "url": content.url,
            "html": content.content.get("html", ""), # Pass through assumed HTML
            "metadata": content.metadata
        }

    async def close(self):
        """Close any resources (none needed for file backend)."""
        pass # No session to close