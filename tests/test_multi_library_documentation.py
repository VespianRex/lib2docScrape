#!/usr/bin/env python3
"""
TDD Tests for Multi-Library Project Documentation Feature

These tests will FAIL initially and guide the implementation.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestMultiLibraryDocumentation:
    """Test suite for multi-library project documentation functionality."""

    @pytest.fixture
    def sample_requirements(self):
        """Sample requirements.txt content for testing."""
        return """
        requests>=2.28.0
        fastapi>=0.95.0
        numpy>=1.21.0
        pandas>=1.5.0
        pytest>=7.0.0
        """

    @pytest.fixture
    def sample_package_json(self):
        """Sample package.json content for testing."""
        return {
            "dependencies": {
                "react": "^18.2.0",
                "axios": "^1.3.0",
                "lodash": "^4.17.21",
            },
            "devDependencies": {"jest": "^29.0.0", "webpack": "^5.75.0"},
        }

    def test_dependency_parser_creation(self):
        """Test that DependencyParser can be created."""
        # This will fail - DependencyParser doesn't exist yet
        from processors.dependency_parser import DependencyParser

        parser = DependencyParser()
        assert parser is not None
        assert hasattr(parser, "parse_requirements")
        assert hasattr(parser, "parse_package_json")
        assert hasattr(parser, "parse_cargo_toml")

    def test_parse_requirements_txt(self, sample_requirements):
        """Test parsing Python requirements.txt file."""
        from processors.dependency_parser import DependencyParser

        parser = DependencyParser()
        dependencies = parser.parse_requirements(sample_requirements)

        assert isinstance(dependencies, list)
        assert len(dependencies) == 5

        # Check specific dependencies
        requests_dep = next((d for d in dependencies if d["name"] == "requests"), None)
        assert requests_dep is not None
        assert requests_dep["version"] == ">=2.28.0"
        assert requests_dep["type"] == "python"

        fastapi_dep = next((d for d in dependencies if d["name"] == "fastapi"), None)
        assert fastapi_dep is not None
        assert fastapi_dep["version"] == ">=0.95.0"

    def test_parse_package_json(self, sample_package_json):
        """Test parsing Node.js package.json file."""
        from processors.dependency_parser import DependencyParser

        parser = DependencyParser()
        dependencies = parser.parse_package_json(json.dumps(sample_package_json))

        assert isinstance(dependencies, list)
        assert len(dependencies) == 5  # 3 deps + 2 devDeps

        # Check production dependencies
        react_dep = next((d for d in dependencies if d["name"] == "react"), None)
        assert react_dep is not None
        assert react_dep["version"] == "^18.2.0"
        assert react_dep["type"] == "javascript"
        assert react_dep["dev"] == False

        # Check dev dependencies
        jest_dep = next((d for d in dependencies if d["name"] == "jest"), None)
        assert jest_dep is not None
        assert jest_dep["dev"] == True

    @pytest.mark.asyncio
    async def test_multi_library_crawler_creation(self):
        """Test that MultiLibraryCrawler can be created."""
        from crawler.multi_library_crawler import MultiLibraryCrawler

        crawler = MultiLibraryCrawler()
        assert crawler is not None
        assert hasattr(crawler, "crawl_dependencies")
        assert hasattr(crawler, "generate_unified_docs")
        assert hasattr(crawler, "create_dependency_graph")

    @pytest.mark.asyncio
    async def test_crawl_multiple_dependencies(self, sample_requirements):
        """Test crawling documentation for multiple dependencies."""
        from crawler.multi_library_crawler import MultiLibraryCrawler
        from processors.dependency_parser import DependencyParser

        parser = DependencyParser()
        dependencies = parser.parse_requirements(sample_requirements)

        crawler = MultiLibraryCrawler()

        # Mock the individual library crawling
        with patch("crawler.multi_library_crawler.search_duckduckgo") as mock_search:
            mock_search.return_value = [
                {"url": "https://docs.example.com", "title": "Example Docs"}
            ]

            results = await crawler.crawl_dependencies(
                dependencies[:2]
            )  # Test with first 2

            assert isinstance(results, dict)
            assert "requests" in results
            assert "fastapi" in results
            assert results["requests"]["status"] == "success"
            assert "documentation_urls" in results["requests"]

    def test_dependency_graph_creation(self, sample_requirements):
        """Test creating dependency relationship graph."""
        from processors.dependency_parser import DependencyParser
        from visualizers.dependency_graph import DependencyGraphGenerator

        parser = DependencyParser()
        dependencies = parser.parse_requirements(sample_requirements)

        graph_generator = DependencyGraphGenerator()
        graph = graph_generator.create_graph(dependencies)

        assert graph is not None
        assert hasattr(graph, "nodes")
        assert hasattr(graph, "edges")
        assert len(graph.nodes) == 5

    def test_unified_documentation_generation(self):
        """Test generating unified documentation from multiple libraries."""
        from processors.unified_doc_generator import UnifiedDocumentationGenerator

        sample_docs = {
            "requests": {
                "content": "HTTP library for Python",
                "api_reference": ["get()", "post()", "put()"],
                "examples": ["Basic GET request", "POST with data"],
            },
            "fastapi": {
                "content": "Modern web framework for Python",
                "api_reference": ["FastAPI()", "app.get()", "app.post()"],
                "examples": ["Hello World API", "CRUD operations"],
            },
        }

        generator = UnifiedDocumentationGenerator()
        unified_docs = generator.generate_unified_docs(sample_docs)

        assert isinstance(unified_docs, dict)
        assert "overview" in unified_docs
        assert "libraries" in unified_docs
        assert "integration_examples" in unified_docs
        assert "compatibility_matrix" in unified_docs

        # Check that integration examples are generated
        assert len(unified_docs["integration_examples"]) > 0

        # Check for integration examples containing both libraries
        example_found = False
        for example in unified_docs["integration_examples"]:
            if isinstance(example, dict):
                # Check in code, title, description, or libraries list
                example_text = (
                    example.get("code", "")
                    + example.get("title", "")
                    + example.get("description", "")
                ).lower()
                libraries = example.get("libraries", [])

                if ("requests" in example_text and "fastapi" in example_text) or (
                    "requests" in libraries and "fastapi" in libraries
                ):
                    example_found = True
                    break
            elif isinstance(example, str):
                if "requests" in example.lower() and "fastapi" in example.lower():
                    example_found = True
                    break

        assert example_found, f"No integration example found containing both 'requests' and 'fastapi'. Examples: {unified_docs['integration_examples']}"

    def test_version_compatibility_checking(self):
        """Test checking version compatibility between dependencies."""
        from processors.compatibility_checker import CompatibilityChecker

        dependencies = [
            {"name": "requests", "version": ">=2.28.0", "type": "python"},
            {
                "name": "urllib3",
                "version": ">=1.26.0",
                "type": "python",
            },  # requests dependency
            {"name": "fastapi", "version": ">=0.95.0", "type": "python"},
        ]

        checker = CompatibilityChecker()
        compatibility_report = checker.check_compatibility(dependencies)

        assert isinstance(compatibility_report, dict)
        assert "compatible" in compatibility_report
        assert "conflicts" in compatibility_report
        assert "warnings" in compatibility_report

        # Should detect potential conflicts
        assert isinstance(compatibility_report["conflicts"], list)
        assert isinstance(compatibility_report["warnings"], list)

    @pytest.mark.asyncio
    async def test_multi_library_api_endpoint(self):
        """Test the API endpoint for multi-library documentation."""
        # This will fail - endpoint doesn't exist yet
        import sys

        from fastapi.testclient import TestClient

        sys.path.insert(0, "src")
        from main import app

        client = TestClient(app)

        # Test with requirements.txt content
        response = client.post(
            "/api/multi-library/analyze",
            json={
                "project_type": "python",
                "dependencies_file": "requests>=2.28.0\nfastapi>=0.95.0\nnumpy>=1.21.0",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "dependencies" in data
        assert "documentation_urls" in data
        assert "unified_docs" in data
        assert "dependency_graph" in data

        # Check that all dependencies were processed
        assert len(data["dependencies"]) == 3
        assert any(dep["name"] == "requests" for dep in data["dependencies"])

    def test_project_type_detection(self):
        """Test automatic detection of project type from files."""
        from processors.project_detector import ProjectTypeDetector

        detector = ProjectTypeDetector()

        # Test Python project detection
        python_files = ["requirements.txt", "setup.py", "pyproject.toml"]
        project_type = detector.detect_project_type(python_files)
        assert project_type == "python"

        # Test Node.js project detection
        node_files = ["package.json", "package-lock.json"]
        project_type = detector.detect_project_type(node_files)
        assert project_type == "javascript"

        # Test Rust project detection
        rust_files = ["Cargo.toml", "Cargo.lock"]
        project_type = detector.detect_project_type(rust_files)
        assert project_type == "rust"

    def test_dependency_tree_visualization(self):
        """Test generating visual dependency tree."""
        from visualizers.dependency_tree import DependencyTreeVisualizer

        dependencies = [
            {"name": "fastapi", "version": ">=0.95.0", "type": "python"},
            {
                "name": "starlette",
                "version": ">=0.27.0",
                "type": "python",
                "parent": "fastapi",
            },
            {
                "name": "pydantic",
                "version": ">=1.10.0",
                "type": "python",
                "parent": "fastapi",
            },
        ]

        visualizer = DependencyTreeVisualizer()
        tree_html = visualizer.generate_tree_html(dependencies)

        assert isinstance(tree_html, str)
        assert "fastapi" in tree_html
        assert "starlette" in tree_html
        assert "pydantic" in tree_html
        assert '<div class="dependency-tree">' in tree_html


if __name__ == "__main__":
    # Run the tests to see them fail
    pytest.main([__file__, "-v", "--tb=short"])
