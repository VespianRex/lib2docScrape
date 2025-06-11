"""Document processor module for processing documentation files."""

from typing import Any, Optional

from bs4 import BeautifulSoup


class DocumentProcessor:
    """Processes documentation files and extracts structured content."""

    def __init__(self, config: Optional[dict[str, Any]] = None):
        """Initialize the document processor with optional configuration."""
        self.config = config or {}

    def process(self, content: str) -> dict[str, Any]:
        """Process a document and extract structured content.

        Args:
            content: The document content to process

        Returns:
            Dict containing processed content and metadata
        """
        try:
            soup = BeautifulSoup(content, "html.parser")
            return {
                "title": self._extract_title(soup),
                "content": self._extract_content(soup),
                "metadata": self._extract_metadata(soup),
            }
        except Exception as e:
            raise ValueError(f"Failed to process document: {str(e)}") from e

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract the document title."""
        title = soup.find("title")
        if title:
            return title.get_text().strip()
        h1 = soup.find("h1")
        if h1:
            return h1.get_text().strip()
        return ""

    def _extract_content(self, soup: BeautifulSoup) -> dict[str, Any]:
        """Extract the main content from the document."""
        main = soup.find(["main", "article"]) or soup.find(
            "div", {"class": ["content", "main"]}
        )
        if not main:
            main = soup.body or soup

        return {"text": main.get_text().strip(), "html": str(main)}

    def _extract_metadata(self, soup: BeautifulSoup) -> dict[str, str]:
        """Extract metadata from the document."""
        metadata = {}

        # Extract meta tags
        for meta in soup.find_all("meta"):
            name = meta.get("name", meta.get("property", ""))
            content = meta.get("content", "")
            if name and content:
                metadata[name] = content

        return metadata
