"""Tests for the DocumentationCrawler._generate_search_queries method."""

import re
from unittest.mock import Mock, patch

import pytest

from src.crawler.crawler import Crawler as DocumentationCrawler
from src.crawler.models import CrawlConfig
from src.models.project import ProjectIdentity, ProjectType


class TestGenerateSearchQueries:
    """Tests for the _generate_search_queries method of DocumentationCrawler."""

    @pytest.fixture
    def setup_crawler(self):
        """Set up DocumentationCrawler instance."""
        crawler = DocumentationCrawler(content_processor=Mock(), quality_checker=Mock())
        return crawler

    def test_library_with_version(self, setup_crawler):
        """Test generating search queries for a library with version."""
        crawler = setup_crawler

        # Create a config with library project type and version
        config = CrawlConfig(
            project_identity=ProjectIdentity(
                name="TestLibrary", type=ProjectType.LIBRARY, version="1.2.3"
            )
        )

        queries = crawler._generate_search_queries(config)

        # Verify the expected queries were generated
        assert "TestLibrary documentation" in queries
        assert "TestLibrary 1.2.3 documentation" in queries
        assert "TestLibrary 1.2.3 api reference" in queries
        assert "TestLibrary 1.2 documentation" in queries  # Major.minor version
        assert "TestLibrary 1 documentation" in queries  # Major version only

    def test_library_without_version(self, setup_crawler):
        """Test generating search queries for a library without version."""
        crawler = setup_crawler

        # Create a config with library project type but no version
        config = CrawlConfig(
            project_identity=ProjectIdentity(
                name="TestLibrary", type=ProjectType.LIBRARY, version=None
            )
        )

        queries = crawler._generate_search_queries(config)

        # Verify the expected queries were generated
        assert "TestLibrary documentation" in queries
        assert "TestLibrary api reference" in queries
        assert "TestLibrary tutorial" in queries
        assert "TestLibrary guide" in queries

        # Verify no version-specific queries
        for query in queries:
            assert not re.search(
                r"\d+\.\d+", query
            ), f"Query '{query}' should not contain version numbers"

    def test_non_library_project_type(self, setup_crawler):
        """Test generating search queries for a non-library project type."""
        crawler = setup_crawler

        # Create a config with non-library project type
        config = CrawlConfig(
            project_identity=ProjectIdentity(
                name="TestApp", type=ProjectType.PROGRAM, version="2.0.0"
            )
        )

        queries = crawler._generate_search_queries(config)

        # Verify the expected queries were generated
        assert "TestApp documentation" in queries
        assert "TestApp guide" in queries
        assert "TestApp tutorial" in queries
        assert "TestApp how to" in queries

    @patch("src.crawler.crawler.Crawler._extract_major_minor_version")
    def test_attribute_error_during_version_parsing(
        self, mock_extract_version, setup_crawler
    ):
        """Test handling of AttributeError during version parsing."""
        crawler = setup_crawler

        # Mock to simulate an AttributeError during version parsing
        mock_extract_version.side_effect = AttributeError("Version parsing error")

        # Create a config with library project type and version
        config = CrawlConfig(
            project_identity=ProjectIdentity(
                name="TestLibrary", type=ProjectType.LIBRARY, version="1.2.3"
            )
        )

        # This should not raise an exception despite the AttributeError in version parsing
        queries = crawler._generate_search_queries(config)

        # Should still have the basic queries
        assert "TestLibrary documentation" in queries

        # Method should have been called
        mock_extract_version.assert_called()
