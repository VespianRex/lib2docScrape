import html

from bs4 import BeautifulSoup, Comment, NavigableString

from .models import ContentProcessingError, ProcessorConfig


class PreprocessingHandler:
    def __init__(self, config: ProcessorConfig):
        self.config = config

    def preprocess_content(self, html_content: str) -> BeautifulSoup:
        """Preprocess HTML content: unescaping entities, checking length."""
        soup = BeautifulSoup(html_content, "html.parser")

        # Check content length
        content_length = len(str(soup))
        if content_length > self.config.max_content_length:
            raise ContentProcessingError(
                f"Content too long: {content_length} characters"
            )
        if content_length < self.config.min_content_length:
            raise ContentProcessingError(
                f"Content too short: {content_length} characters"
            )

        # Unescape HTML entities
        for tag in soup.find_all(string=True):
            if isinstance(tag, NavigableString) and not isinstance(tag, Comment):
                unescaped = html.unescape(str(tag))
                if unescaped != str(tag):
                    tag.replace_with(unescaped)

        return soup
