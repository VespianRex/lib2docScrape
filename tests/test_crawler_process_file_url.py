from unittest.mock import AsyncMock, Mock, mock_open, patch

import pytest

from src.crawler import (  # Removed CrawlResult as it's not directly used here
    CrawlStats,
    CrawlTarget,
    DocumentationCrawler,
)
from src.processors.content_processor import ProcessedContent
from src.utils.url.factory import create_url_info


@pytest.mark.asyncio
class TestProcessFileUrl:
    @pytest.fixture
    def setup(self):
        crawler = DocumentationCrawler(content_processor=Mock(), quality_checker=Mock())
        target_cfg = CrawlTarget()
        stats_obj = CrawlStats()
        # Ensure a unique file path for each test run if files are actually created
        # For purely mocked tests, this fixed path is fine.
        url_info = create_url_info("file:///path/to/file.html")
        return crawler, url_info, target_cfg, stats_obj

    @patch("os.path.exists", return_value=False)
    async def test_file_not_found(self, mock_exists, setup):
        crawler, url_info, target_cfg, stats_obj = setup
        result, new_links, metrics = await crawler._process_file_url(
            url_info, 0, target_cfg, stats_obj
        )
        assert result.issues[0].message.startswith("File not found")
        assert stats_obj.failed_crawls == 1

    @patch("os.path.exists", return_value=True)
    @patch("os.path.isdir", return_value=True)
    async def test_path_is_directory(self, mock_isdir, mock_exists, setup):
        crawler, url_info, target_cfg, stats_obj = setup
        # Directory without index.html
        with patch("os.path.join", return_value="/path/to/file.html/index.html"):
            with patch("os.path.exists", side_effect=[True, False]):
                result, new_links, metrics = await crawler._process_file_url(
                    url_info, 0, target_cfg, stats_obj
                )
                assert result.issues[0].message.startswith(
                    "Directory has no index.html"
                )
                assert stats_obj.failed_crawls == 1

    @patch("os.path.exists", return_value=True)
    @patch("os.path.isdir", return_value=False)
    @patch("os.path.isfile", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data="Mocked file content")
    async def test_successful_file_read_and_process(
        self,
        mock_file_open,
        mock_isfile,
        mock_isdir,
        mock_exists,
        setup,  # Renamed mock_file to mock_file_open
    ):
        crawler, url_info, target_cfg, stats_obj = setup

        # Debug: Print the file path that will be used
        print(f"DEBUG: url_info.path = {url_info.path}")
        print(f"DEBUG: url_info.normalized_url = {url_info.normalized_url}")

        # Correctly typed mock for ProcessedContent
        mock_processed_content = Mock(spec=ProcessedContent)
        mock_processed_content.url = url_info.normalized_url
        mock_processed_content.title = "Mocked Title"
        # ProcessedContent.content is a dict
        mock_processed_content.content = {
            "text": "Mocked file content",
            "html": "<p>Mocked file content</p>",
            "formatted_content": "Mocked file content",
        }
        mock_processed_content.metadata = {"source": "file"}
        # ProcessedContent.assets is a dict
        mock_processed_content.assets = {
            "images": [],
            "scripts": [],
            "stylesheets": [],
            "media": [],
        }
        # ProcessedContent.structure is a list of dicts
        mock_processed_content.structure = [
            {"type": "paragraph", "content": "Mocked file content"}
        ]
        mock_processed_content.headings = [
            {"level": 1, "text": "Mocked Title", "id": "mocked-title"}
        ]
        mock_processed_content.errors = []

        crawler.content_processor.process = AsyncMock(
            return_value=mock_processed_content
        )
        crawler.quality_checker.check_quality = AsyncMock(return_value=([], {}))
        # _find_links_recursive is synchronous
        crawler._find_links_recursive = Mock(return_value=[])

        result, new_links, metrics = await crawler._process_file_url(
            url_info, 0, target_cfg, stats_obj
        )

        assert result is not None, "CrawlResult should not be None"
        assert result.documents, "CrawlResult.documents should not be empty"
        assert (
            len(result.documents) == 1
        ), "CrawlResult.documents should contain one document"
        # The crawler extracts the "formatted_content" from the ProcessedContent.content dict
        expected_content = mock_processed_content.content.get(
            "formatted_content", "Mocked file content"
        )
        assert result.documents[0]["content"] == expected_content
        assert result.documents[0]["title"] == "Mocked Title"
        assert (
            result.issues == []
        ), f"Issues should be empty on success, got: {result.issues}"
        assert stats_obj.successful_crawls == 1
        assert stats_obj.failed_crawls == 0

    @patch("os.path.exists", return_value=True)
    @patch("os.path.isdir", return_value=False)
    @patch("os.path.isfile", return_value=True)
    @patch("builtins.open", side_effect=OSError("Read error"))
    async def test_file_read_error(
        self, mock_file_open, mock_isfile, mock_isdir, mock_exists, setup
    ):  # Renamed
        crawler, url_info, target_cfg, stats_obj = setup
        result, new_links, metrics = await crawler._process_file_url(
            url_info, 0, target_cfg, stats_obj
        )
        assert result is not None, "CrawlResult should not be None"
        assert not result.documents, "Documents should be empty on file read error"
        assert len(result.issues) == 1, "Should be one issue for file read error"
        assert "File read error" in result.issues[0].message
        assert (
            "Read error" in result.issues[0].message
        )  # Check for specific OSError message
        assert result.issues[0].type == "IssueType.GENERAL"
        assert stats_obj.failed_crawls == 1
        assert stats_obj.successful_crawls == 0

    @patch("os.path.exists", return_value=True)
    @patch("os.path.isdir", return_value=False)
    @patch("os.path.isfile", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data="Mocked file content")
    async def test_content_processor_error(
        self,
        mock_file_open,
        mock_isfile,
        mock_isdir,
        mock_exists,
        setup,  # Renamed
    ):
        crawler, url_info, target_cfg, stats_obj = setup
        processing_exception = Exception("Processing error")
        crawler.content_processor.process = AsyncMock(side_effect=processing_exception)
        # Mock quality checker in case it's reached, though it shouldn't be if processor fails
        crawler.quality_checker.check_quality = AsyncMock(return_value=([], {}))

        result, new_links, metrics = await crawler._process_file_url(
            url_info, 0, target_cfg, stats_obj
        )
        assert result is not None, "CrawlResult should not be None"
        assert (
            not result.documents
        ), "Documents should be empty on content processor error"
        assert (
            len(result.issues) == 1
        ), "Should be one issue for content processor error"
        assert (
            "File processing error" in result.issues[0].message
        )  # Updated message check
        assert "Processing error" in result.issues[0].message
        assert result.issues[0].type == "IssueType.GENERAL"
        assert stats_obj.failed_crawls == 1
        assert stats_obj.successful_crawls == 0
