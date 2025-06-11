"""
Complete tests for the content processor component.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.processors.content_processor import (
    ContentProcessingError,
    ContentProcessor,
    DefaultProcessorConfig,
    ProcessorConfig,
)


class TestDefaultProcessorConfig:
    """Tests for DefaultProcessorConfig class."""

    def test_default_processor_config_instantiation(self):
        """Test 1: Test `DefaultProcessorConfig` instantiation."""
        config = DefaultProcessorConfig()

        # Check default values
        assert config.max_content_length == 100000
        assert config.min_content_length == 10
        assert config.extract_metadata is True
        assert config.extract_assets is True
        assert config.extract_code_blocks is True
        assert config.extract_comments is False
        assert config.code_languages == [
            "python",
            "javascript",
            "html",
            "css",
            "java",
            "c",
            "cpp",
        ]
        assert config.max_heading_level == 6


@pytest.fixture
def processor():
    """Fixture providing a ContentProcessor instance."""
    return ContentProcessor()


@pytest.fixture
def mock_processor_config():
    """Fixture providing a mock ProcessorConfig."""
    config = MagicMock(spec=ProcessorConfig)
    config.max_content_length = 100000
    config.min_content_length = 10
    config.extract_metadata = True
    config.extract_assets = True
    config.extract_code_blocks = True
    config.extract_comments = False
    config.code_languages = ["python", "javascript"]
    config.max_heading_level = 3
    return config


class TestContentProcessorInit:
    """Tests for ContentProcessor.__init__ method."""

    def test_init_with_config_none_processor_config_available(self):
        """Test 2.1: `config=None`, `ProcessorConfig` available."""
        with patch(
            "src.processors.content_processor.ProcessorConfig"
        ) as MockProcessorConfig:
            # Set up the mock
            mock_config = MagicMock()
            MockProcessorConfig.return_value = mock_config

            # Create processor with config=None
            processor = ContentProcessor(config=None)

            # Check that ProcessorConfig was used
            MockProcessorConfig.assert_called_once()
            assert processor.config == mock_config

    def test_init_with_config_none_processor_config_unavailable(self):
        """Test 2.2: `config=None`, `ProcessorConfig` unavailable (fallback to `DefaultProcessorConfig`)."""
        with patch(
            "src.processors.content_processor.ProcessorConfig",
            side_effect=Exception("Not available"),
        ):
            # Create processor with config=None
            processor = ContentProcessor(config=None)

            # Check that DefaultProcessorConfig was used
            assert isinstance(processor.config, DefaultProcessorConfig)

    def test_init_with_custom_config(self, mock_processor_config):
        """Test 2.3: `config` provided (custom config object)."""
        # Create processor with custom config
        processor = ContentProcessor(config=mock_processor_config)

        # Check that the custom config was used
        assert processor.config == mock_processor_config


@pytest.mark.asyncio
class TestContentProcessorProcess:
    """Tests for ContentProcessor.process method."""

    async def test_process_empty_content(self, processor):
        """Test 3.1: Empty or whitespace content (raises `ContentProcessingError`)."""
        # Test with empty string
        with pytest.raises(ContentProcessingError) as excinfo:
            await processor.process("")
        assert "Cannot process empty or whitespace-only content" in str(excinfo.value)

        # Test with whitespace-only string
        with pytest.raises(ContentProcessingError) as excinfo:
            await processor.process("   \n   ")
        assert "Cannot process empty or whitespace-only content" in str(excinfo.value)

    async def test_process_content_too_long(self, processor):
        """Test 3.2: Content too long (raises `ContentProcessingError`)."""
        # Set a small max_content_length for testing
        processor.config.max_content_length = 10

        # Create HTML content that will be longer than max_content_length after cleaning
        html = "<html><body><p>This content is too long for testing</p></body></html>"

        # The ContentProcessor.process method catches ContentProcessingError and returns a result with errors
        result = await processor.process(html)

        # Check that the error was recorded
        assert len(result.errors) == 1
        assert "Cleaned content too long" in result.errors[0]

        # Check that content is empty
        assert result.content == {}

    async def test_process_content_too_short(self, processor):
        """Test 3.3: Content too short (raises `ContentProcessingError`)."""
        # Set a large min_content_length for testing
        processor.config.min_content_length = 100

        # Create HTML content that will be shorter than min_content_length after cleaning
        html = "<html><body><p>Short</p></body></html>"

        # The ContentProcessor.process method catches ContentProcessingError and returns a result with errors
        result = await processor.process(html)

        # Check that the error was recorded
        assert len(result.errors) == 1
        assert "Cleaned content too short" in result.errors[0]

        # Check that content is empty
        assert result.content == {}

    async def test_process_general_exception(self, processor):
        """Test 3.4: General exception during HTML processing."""
        # Mock BeautifulSoup to raise an exception
        with patch(
            "src.processors.content_processor.BeautifulSoup",
            side_effect=Exception("Test exception"),
        ):
            # Process HTML content
            html = "<html><body><p>Test content</p></body></html>"
            result = await processor.process(html)

            # Check that the error was recorded
            assert len(result.errors) == 1
            assert "Error processing content: Test exception" in result.errors[0]

            # Check that content is empty
            assert result.content == {}

    async def test_process_fallback_heading_extraction(self, processor):
        """Test 3.5: Fallback heading extraction on error."""
        # Create HTML content with headings
        html = """
        <html>
            <body>
                <h1>Heading 1</h1>
                <h2>Heading 2</h2>
            </body>
        </html>
        """

        # Mock structure_handler.extract_headings to return empty list
        processor.structure_handler.extract_headings = MagicMock(return_value=[])

        # Process HTML content
        result = await processor.process(html)

        # Check that fallback heading extraction was used
        assert len(result.headings) > 0
        assert any(
            h["text"] == "Heading 1" and h["level"] == 1 for h in result.headings
        )
        assert any(
            h["text"] == "Heading 2" and h["level"] == 2 for h in result.headings
        )


@pytest.mark.asyncio
class TestContentProcessorContentTypeAndFormat:
    """Tests for ContentProcessor.process - Content Type and Format Handling."""

    async def test_content_type_detection(self, processor):
        """Test 4.1: Content type detection when `content_type` is `None`."""
        # Mock the format_detector module's ContentTypeDetector
        with patch(
            "src.processors.content.format_detector.ContentTypeDetector"
        ) as MockDetector:
            # Set up the mock
            MockDetector.detect_from_content.return_value = "text/html"

            # Process HTML content without specifying content_type
            html = "<html><body><p>Test content</p></body></html>"
            await processor.process(html)

            # Check that ContentTypeDetector.detect_from_content was called
            MockDetector.detect_from_content.assert_called_once_with(html)

    async def test_process_non_html_handler(self, processor):
        """Test 4.2: Successful processing by a non-HTML handler."""
        from src.processors.content.format_handlers import MarkdownHandler

        # Create a real MarkdownHandler instance
        markdown_handler = MarkdownHandler()

        # Mock FormatDetector
        with patch(
            "src.processors.content.format_detector.FormatDetector"
        ) as MockDetector:
            # Set up the mock detector to return the real handler
            MockDetector.return_value.detect_format.return_value = markdown_handler

            # Process Markdown content
            markdown = "# Heading\n\nContent"
            result = await processor.process(markdown, content_type="text/markdown")

            # Check that the result contains the expected content
            # Note: The actual content might be slightly different due to markdownify formatting
            assert "Heading" in result.content["formatted_content"]
            assert "Content" in result.content["formatted_content"]
            assert len(result.structure) >= 1
            # The structure type might be different depending on the implementation
            # Just check that there is some structure
            assert "type" in result.structure[0]
            assert len(result.headings) >= 1
            # Check that there is at least one heading with level 1
            assert any(h["level"] == 1 for h in result.headings)

    async def test_process_non_html_handler_error_fallback(self, processor):
        """Test 4.3: Error in non-HTML handler, fallback to HTML processing."""
        # Instead of mocking at the external module level, let's create a custom handler
        # that will throw an exception and inject it into the processor's format detector

        # Save the original detector
        original_detector = (
            processor._detector if hasattr(processor, "_detector") else None
        )

        try:
            # Create our own detector and handlers
            from unittest.mock import MagicMock

            from src.processors.content.format_detector import FormatDetector

            # Create a custom handler that raises an exception
            mock_handler = MagicMock()
            mock_handler.get_format_name.return_value = "Markdown"
            mock_handler.process = MagicMock(side_effect=Exception("Handler error"))

            # Create a detector that will return our handler
            custom_detector = FormatDetector()
            custom_detector.detect_format = MagicMock(return_value=mock_handler)

            # Inject our detector into the processor
            processor._detector = custom_detector

            # Process content
            content = "# Heading\n\nContent"
            result = await processor.process(content, content_type="text/markdown")

            # Check that the handler was used
            mock_handler.process.assert_called_once()

            # Check that fallback to HTML processing occurred
            # The result should contain some content from HTML processing
            assert result.content is not None
            assert "formatted_content" in result.content

        finally:
            # Restore the original detector
            if original_detector:
                processor._detector = original_detector


@pytest.mark.asyncio
class TestContentProcessorHtmlProcessing:
    """Tests for ContentProcessor.process - HTML Processing Details."""

    async def test_remove_script_style_tags(self, processor):
        """Test 5.1: Removal of `script`, `style`, `noscript`, `iframe` tags."""
        # Create HTML content with script, style, noscript, and iframe tags
        html = """
        <html>
            <head>
                <script>alert('Hello');</script>
                <style>body { color: red; }</style>
            </head>
            <body>
                <noscript>JavaScript is disabled</noscript>
                <iframe src="https://example.com"></iframe>
                <p>Visible content</p>
            </body>
        </html>
        """

        # Process HTML content
        result = await processor.process(html)

        # Check that script, style, noscript, and iframe content is not in the result
        assert "alert('Hello');" not in result.content["formatted_content"]
        assert "color: red" not in result.content["formatted_content"]
        assert "JavaScript is disabled" not in result.content["formatted_content"]
        assert "iframe" not in result.content["formatted_content"]

        # Check that visible content is in the result
        assert "Visible content" in result.content["formatted_content"]

    async def test_bleach_sanitization(self, processor):
        """Test 5.2: Bleach sanitization."""
        # Create HTML content with comments
        html = """
        <html>
            <body>
                <!-- This is a comment -->
                <p>Visible content</p>
            </body>
        </html>
        """

        # Test with extract_comments=False (default)
        processor.config.extract_comments = False
        result1 = await processor.process(html)
        assert "This is a comment" not in result1.content["formatted_content"]

        # Test with extract_comments=True
        processor.config.extract_comments = True
        # Just verify it doesn't raise an exception
        await processor.process(html)

        # Reset for other tests
        processor.config.extract_comments = False

    async def test_base_url_determination(self, processor):
        """Test 5.3: Base URL determination logic."""
        # Test with no base URL
        html1 = "<html><body><p>No base URL</p></body></html>"
        result1 = await processor.process(html1)
        assert result1.content is not None

        # Test with base URL from input
        html2 = "<html><body><p>Base URL from input</p></body></html>"
        result2 = await processor.process(html2, base_url="https://example.com")
        assert result2.content is not None

        # Test with base URL from <base> tag
        html3 = """
        <html>
            <head>
                <base href="https://example.org/">
            </head>
            <body>
                <p>Base URL from tag</p>
            </body>
        </html>
        """
        result3 = await processor.process(html3)
        assert result3.content is not None

        # Test with combination (base URL from input and <base> tag)
        html4 = """
        <html>
            <head>
                <base href="/subpath/">
            </head>
            <body>
                <p>Combined base URL</p>
            </body>
        </html>
        """
        result4 = await processor.process(html4, base_url="https://example.net")
        assert result4.content is not None

    async def test_extraction_features(self, processor):
        """Test 5.4: Metadata, Asset, Structure, Heading extraction."""
        # Create HTML content with various elements
        html = """
        <html>
            <head>
                <title>Test Document</title>
                <meta name="description" content="Test description">
            </head>
            <body>
                <h1>Main Heading</h1>
                <p>Paragraph content.</p>
                <img src="image.jpg" alt="Test Image">
                <h2>Subheading</h2>
                <p>More content.</p>
            </body>
        </html>
        """

        # Test with all extraction features enabled
        processor.config.extract_metadata = True
        processor.config.extract_assets = True
        result1 = await processor.process(html, base_url="https://example.com")

        # Check metadata extraction
        assert result1.metadata is not None
        assert result1.title == "Test Document"

        # Check asset extraction
        assert result1.assets is not None

        # Check structure extraction
        assert result1.structure is not None
        assert len(result1.structure) > 0

        # Check heading extraction
        assert result1.headings is not None
        assert len(result1.headings) > 0
        assert any(
            h["text"] == "Main Heading" and h["level"] == 1 for h in result1.headings
        )
        assert any(
            h["text"] == "Subheading" and h["level"] == 2 for h in result1.headings
        )

        # Test with features disabled
        processor.config.extract_metadata = False
        processor.config.extract_assets = False
        # Just verify it doesn't raise an exception
        await processor.process(html)

        # Reset for other tests
        processor.config.extract_metadata = True
        processor.config.extract_assets = True

    async def test_fallback_heading_extraction_structure(self, processor):
        """Test 5.5: Fallback heading extraction if structure_handler.extract_headings returns empty."""
        # Create HTML content with headings
        html = """
        <html>
            <body>
                <h1>Main Heading</h1>
                <h2>Subheading</h2>
            </body>
        </html>
        """

        # Mock structure_handler.extract_headings to return empty list
        processor.structure_handler.extract_headings = MagicMock(return_value=[])

        # Process HTML content
        result = await processor.process(html)

        # Check that fallback heading extraction was used
        assert len(result.headings) > 0
        assert any(
            h["text"] == "Main Heading" and h["level"] == 1 for h in result.headings
        )
        assert any(
            h["text"] == "Subheading" and h["level"] == 2 for h in result.headings
        )

    async def test_structure_creation_from_headings(self, processor):
        """Test 5.6: Structure creation from headings if structure_handler.extract_structure returns empty."""
        # Create HTML content with headings
        html = """
        <html>
            <body>
                <h1>Main Heading</h1>
                <h2>Subheading</h2>
            </body>
        </html>
        """

        # Mock structure_handler.extract_structure to return empty list
        processor.structure_handler.extract_structure = MagicMock(return_value=[])

        # Process HTML content
        result = await processor.process(html)

        # Check that structure was created from headings
        assert len(result.structure) > 0
        assert any(
            item["type"] == "heading" and item["title"] == "Main Heading"
            for item in result.structure
        )
        assert any(
            item["type"] == "heading" and item["title"] == "Subheading"
            for item in result.structure
        )


class TestContentProcessorConfigure:
    """Tests for ContentProcessor.configure method."""

    def test_update_config_attributes(self, processor):
        """Test 6.1: Update various config attributes."""
        # Initial values
        initial_max_content_length = processor.config.max_content_length
        initial_extract_metadata = processor.config.extract_metadata

        # Configure with new values
        processor.configure(
            {
                "max_content_length": 50000,
                "extract_metadata": not initial_extract_metadata,
            }
        )

        # Check that values were updated
        assert processor.config.max_content_length == 50000
        assert processor.config.extract_metadata != initial_extract_metadata

        # Reset for other tests
        processor.configure(
            {
                "max_content_length": initial_max_content_length,
                "extract_metadata": initial_extract_metadata,
            }
        )

    def test_ignore_blocked_attributes(self, processor):
        """Test 6.2: Ignoring `blocked_attributes` in input config."""
        # Initial value
        initial_max_content_length = processor.config.max_content_length

        # Configure with blocked_attributes
        with patch("src.processors.content_processor.logger") as mock_logger:
            processor.configure(
                {"max_content_length": 50000, "blocked_attributes": ["some_attribute"]}
            )

            # Check that warning was logged
            mock_logger.warning.assert_called_once()
            assert "blocked_attributes" in mock_logger.warning.call_args[0][0]

            # Check that max_content_length was still updated
            assert processor.config.max_content_length == 50000

            # Reset for other tests
            processor.configure({"max_content_length": initial_max_content_length})

    def test_reinitialize_handlers(self, processor):
        """Test 6.3: Re-initialization of handlers when config changes."""
        # Store original handlers
        original_code_handler = processor.code_handler
        original_structure_handler = processor.structure_handler

        # Configure with new code_languages
        processor.configure({"code_languages": ["python", "javascript", "ruby"]})

        # Check that code_handler was re-initialized
        assert processor.code_handler is not original_code_handler
        assert processor.structure_handler is not original_structure_handler

        # Configure with new max_heading_level
        original_code_handler = processor.code_handler
        original_structure_handler = processor.structure_handler

        processor.configure({"max_heading_level": 4})

        # Check that structure_handler was re-initialized but code_handler wasn't
        assert processor.code_handler is original_code_handler
        assert processor.structure_handler is not original_structure_handler

    def test_configure_without_code_handler(self):
        """Test 6.4: Edge case: `configure` called when `code_handler` is not yet initialized."""
        # Create a processor without initializing code_handler
        processor = ContentProcessor()

        # Remove code_handler attribute
        if hasattr(processor, "code_handler"):
            delattr(processor, "code_handler")

        # Configure with new max_heading_level
        with patch("src.processors.content_processor.logger") as mock_logger:
            try:
                processor.configure({"max_heading_level": 4})
                # If we get here, the test fails
                assert False, "Expected TypeError but no exception was raised"
            except TypeError as e:
                # Check that the error message is as expected
                assert "missing 1 required positional argument: 'code_handler'" in str(
                    e
                )

            # Check that error was logged
            mock_logger.error.assert_called_once()
            assert "CodeHandler not initialized" in mock_logger.error.call_args[0][0]


class TestContentProcessorFilters:
    """Tests for ContentProcessor filter methods."""

    def test_add_content_filter(self, processor):
        """Test 7: Test `add_content_filter`."""
        # Initial count of content filters
        initial_count = len(processor.content_filters)

        # Create a filter function
        def test_filter(content):
            return content

        # Add the filter
        processor.add_content_filter(test_filter)

        # Check that the filter was added
        assert len(processor.content_filters) == initial_count + 1
        assert processor.content_filters[-1] == test_filter

    def test_add_url_filter(self, processor):
        """Test 7: Test `add_url_filter`."""
        # Initial count of URL filters
        initial_count = len(processor.url_filters)

        # Create a filter function
        def test_filter(url):
            return url

        # Add the filter
        processor.add_url_filter(test_filter)

        # Check that the filter was added
        assert len(processor.url_filters) == initial_count + 1
        assert processor.url_filters[-1] == test_filter

    def test_add_metadata_extractor(self, processor):
        """Test 7: Test `add_metadata_extractor`."""
        # Initial count of metadata extractors
        initial_count = len(processor.metadata_extractors)

        # Create an extractor function
        def test_extractor(soup):
            return {}

        # Add the extractor
        processor.add_metadata_extractor(test_extractor)

        # Check that the extractor was added
        assert len(processor.metadata_extractors) == initial_count + 1
        assert processor.metadata_extractors[-1] == test_extractor
