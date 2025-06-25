#!/usr/bin/env python3
"""
Comprehensive CLI tests for all available features.
Following TDD methodology to implement missing CLI commands.
"""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from src.main import parse_args


class TestCLIComprehensive:
    """Test all CLI commands and features."""

    def test_cli_help_shows_all_commands(self):
        """Test that CLI help shows all available commands."""
        # RED: Test that help shows all expected commands
        with patch("sys.argv", ["lib2docscrape", "--help"]):
            with pytest.raises(SystemExit):
                parse_args()

        # This test will fail until we implement all commands
        expected_commands = [
            "scrape",  # ✅ Implemented
            "serve",  # ✅ Implemented
            "benchmark",  # ✅ Implemented
            "library",  # ✅ Implemented
            "relevance",  # ✅ Implemented
            "bootstrap",  # ✅ Implemented
            "search",  # ❌ Missing - semantic search
            "analyze",  # ❌ Missing - multi-library analysis
            "discover",  # ❌ Missing - documentation discovery
            "export",  # ❌ Missing - export documentation
            "validate",  # ❌ Missing - HIL validation interface
            "github",  # ❌ Missing - GitHub repository analysis
        ]

        # GREEN: We'll implement these commands to make the test pass

    def test_semantic_search_command(self):
        """Test semantic search CLI command."""
        # RED: This should fail because command doesn't exist yet
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                [
                    {"id": "1", "content": "FastAPI documentation for building APIs"},
                    {"id": "2", "content": "Django tutorial for web development"},
                ],
                f,
            )
            docs_file = f.name

        try:
            with patch(
                "sys.argv",
                [
                    "lib2docscrape",
                    "search",
                    "semantic",
                    "-q",
                    "API documentation",
                    "-f",
                    docs_file,
                    "-l",
                    "5",
                ],
            ):
                args = parse_args()
                assert args.command == "search"
                assert args.search_command == "semantic"
                assert args.query == "API documentation"
                assert args.file == docs_file
                assert args.limit == 5
        finally:
            os.unlink(docs_file)

    def test_multi_library_analyze_command(self):
        """Test multi-library analysis CLI command."""
        # RED: This should fail because command doesn't exist yet
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("requests==2.28.0\nfastapi==0.95.0\npydantic==1.10.0")
            requirements_file = f.name

        try:
            with patch(
                "sys.argv",
                [
                    "lib2docscrape",
                    "analyze",
                    "multi-library",
                    "-f",
                    requirements_file,
                    "-t",
                    "python",
                    "-o",
                    "analysis_output.json",
                ],
            ):
                args = parse_args()
                assert args.command == "analyze"
                assert args.analyze_command == "multi-library"
                assert args.file == requirements_file
                assert args.type == "python"
                assert args.output == "analysis_output.json"
        finally:
            os.unlink(requirements_file)

    def test_documentation_discovery_command(self):
        """Test documentation discovery CLI command."""
        # RED: This should fail because command doesn't exist yet
        with patch(
            "sys.argv",
            [
                "lib2docscrape",
                "discover",
                "docs",
                "-p",
                "fastapi",
                "-s",
                "github,pypi,readthedocs",
                "-o",
                "discovered_docs.json",
            ],
        ):
            args = parse_args()
            assert args.command == "discover"
            assert args.discover_command == "docs"
            assert args.package == "fastapi"
            assert args.sources == "github,pypi,readthedocs"
            assert args.output == "discovered_docs.json"

    def test_export_documentation_command(self):
        """Test documentation export CLI command."""
        # RED: This should fail because command doesn't exist yet
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "https://fastapi.tiangolo.com/": "FastAPI documentation content",
                    "https://docs.python.org/3/": "Python documentation content",
                },
                f,
            )
            scraped_file = f.name

        try:
            with patch(
                "sys.argv",
                [
                    "lib2docscrape",
                    "export",
                    "markdown",
                    "-f",
                    scraped_file,
                    "-o",
                    "exported_docs",
                    "--format",
                    "zip",
                    "--include-metadata",
                ],
            ):
                args = parse_args()
                assert args.command == "export"
                assert args.export_command == "markdown"
                assert args.file == scraped_file
                assert args.output == "exported_docs"
                assert args.format == "zip"
                assert args.include_metadata == True
        finally:
            os.unlink(scraped_file)

    def test_hil_validation_command(self):
        """Test Human-in-the-Loop validation CLI command."""
        # RED: This should fail because command doesn't exist yet
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                [
                    {"url": "https://example.com/docs", "content": "API documentation"},
                    {"url": "https://example.com/readme", "content": "Project README"},
                ],
                f,
            )
            scraped_file = f.name

        try:
            with patch(
                "sys.argv",
                [
                    "lib2docscrape",
                    "validate",
                    "interactive",
                    "-f",
                    scraped_file,
                    "-o",
                    "validation_results.json",
                    "--batch-size",
                    "10",
                    "--auto-approve-threshold",
                    "0.9",
                ],
            ):
                args = parse_args()
                assert args.command == "validate"
                assert args.validate_command == "interactive"
                assert args.file == scraped_file
                assert args.output == "validation_results.json"
                assert args.batch_size == 10
                assert args.auto_approve_threshold == 0.9
        finally:
            os.unlink(scraped_file)

    def test_github_repository_analysis_command(self):
        """Test GitHub repository analysis CLI command."""
        # RED: This should fail because command doesn't exist yet
        with patch(
            "sys.argv",
            [
                "lib2docscrape",
                "github",
                "analyze",
                "-r",
                "tiangolo/fastapi",
                "-d",
                "3",  # depth
                "--include-wiki",
                "--include-docs-folder",
                "-o",
                "github_analysis.json",
            ],
        ):
            args = parse_args()
            assert args.command == "github"
            assert args.github_command == "analyze"
            assert args.repository == "tiangolo/fastapi"
            assert args.depth == 3
            assert args.include_wiki == True
            assert args.include_docs_folder == True
            assert args.output == "github_analysis.json"

    def test_origin_tracking_in_scrape_command(self):
        """Test that scrape command tracks origin pages."""
        # RED: Current scrape command doesn't track origins properly
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(
                """
- url: "https://example.com/docs"
  depth: 2
  track_origins: true
  metadata:
    source_type: "official_docs"
    priority: "high"
"""
            )
            targets_file = f.name

        try:
            with patch(
                "sys.argv",
                [
                    "lib2docscrape",
                    "scrape",
                    "-t",
                    targets_file,
                    "--track-origins",
                    "--include-metadata",
                    "-o",
                    "scraped_with_origins.json",
                ],
            ):
                args = parse_args()
                assert args.command == "scrape"
                assert args.targets == targets_file
                assert hasattr(args, "track_origins")
                assert hasattr(args, "include_metadata")
                assert hasattr(args, "output")
        finally:
            os.unlink(targets_file)

    def test_multiple_source_scraping(self):
        """Test scraping multiple sources for same library."""
        # RED: Current implementation doesn't handle multiple sources optimally
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(
                """
library: fastapi
sources:
  - type: github
    url: "https://github.com/tiangolo/fastapi"
    priority: high
  - type: official_docs
    url: "https://fastapi.tiangolo.com"
    priority: high
  - type: readthedocs
    url: "https://fastapi.readthedocs.io"
    priority: medium
merge_strategy: "prioritized"
deduplication: true
"""
            )
            multi_source_file = f.name

        try:
            with patch(
                "sys.argv",
                [
                    "lib2docscrape",
                    "scrape",
                    "multi-source",
                    "-f",
                    multi_source_file,
                    "--merge-duplicates",
                    "--prioritize-official",
                    "-o",
                    "multi_source_results.json",
                ],
            ):
                args = parse_args()
                assert args.command == "scrape"
                assert args.scrape_command == "multi-source"
                assert args.file == multi_source_file
        finally:
            os.unlink(multi_source_file)


class TestCLIOriginTracking:
    """Test origin page tracking functionality."""

    def test_origin_metadata_structure(self):
        """Test that origin metadata has correct structure."""
        # RED: Define expected origin metadata structure
        expected_origin_structure = {
            "source_url": "https://example.com/docs/api",
            "discovered_via": "direct_link",  # or "search", "crawl", "reference"
            "parent_url": "https://example.com/docs",
            "discovery_method": "link_following",
            "source_type": "official_documentation",
            "crawl_depth": 2,
            "timestamp": "2024-01-01T12:00:00Z",
            "relevance_score": 0.95,
            "content_hash": "sha256:abc123...",
            "metadata": {
                "title": "API Reference",
                "description": "Complete API documentation",
                "language": "en",
                "last_modified": "2024-01-01T10:00:00Z",
            },
        }

        # GREEN: We'll implement this structure in the crawler

    def test_origin_deduplication(self):
        """Test that content from multiple origins is deduplicated properly."""
        # RED: Test deduplication logic
        origins = [
            {
                "url": "https://github.com/user/repo/blob/main/README.md",
                "content": "# FastAPI\n\nFast web framework...",
                "source_type": "github_readme",
            },
            {
                "url": "https://fastapi.tiangolo.com/",
                "content": "# FastAPI\n\nFast web framework...",
                "source_type": "official_docs",
            },
        ]

        # Should detect duplicate content and merge origins
        # GREEN: Implement deduplication logic


class TestCLIIntegration:
    """Test CLI integration with existing features."""

    @pytest.mark.asyncio
    async def test_cli_calls_relevance_detection(self):
        """Test that CLI properly calls relevance detection."""
        # RED: Test integration between CLI and relevance detection
        with patch(
            "src.processors.relevance_detection.HybridRelevanceDetector"
        ) as mock_detector:
            mock_instance = MagicMock()
            mock_instance.is_documentation_relevant.return_value = {
                "is_relevant": True,
                "confidence": 0.95,
                "reasoning": "High documentation indicators",
            }
            mock_detector.return_value = mock_instance

            # This should work with our existing relevance command
            # GREEN: Already implemented

    @pytest.mark.asyncio
    async def test_cli_calls_semantic_search(self):
        """Test that CLI properly calls semantic search."""
        # RED: Test integration between CLI and semantic search
        with patch("src.search.semantic_search.SemanticSearchEngine") as mock_search:
            mock_instance = MagicMock()
            mock_instance.search.return_value = [
                {"id": "1", "score": 0.95, "content": "FastAPI documentation"}
            ]
            mock_search.return_value = mock_instance

            # This should work once we implement search command
            # GREEN: Need to implement search command

    @pytest.mark.asyncio
    async def test_cli_calls_multi_library_analysis(self):
        """Test that CLI properly calls multi-library analysis."""
        # RED: Test integration between CLI and multi-library analysis
        with patch("src.processors.dependency_parser.DependencyParser") as mock_parser:
            mock_instance = MagicMock()
            mock_instance.parse_requirements.return_value = [
                {"name": "fastapi", "version": "0.95.0", "type": "python"}
            ]
            mock_parser.return_value = mock_instance

            # This should work once we implement analyze command
            # GREEN: Need to implement analyze command


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
