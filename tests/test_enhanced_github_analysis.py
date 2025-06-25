#!/usr/bin/env python3
"""
Enhanced GitHub Repository Analysis Tests
Following TDD methodology for comprehensive repository structure detection.
"""

import json

import pytest

from src.processors.enhanced_github_analyzer import (
    DocumentationMap,
    DocumentationType,
    EnhancedGitHubAnalyzer,
    RepositoryStructure,
    SourcePriority,
)


class TestEnhancedGitHubAnalyzer:
    """Test enhanced GitHub repository analysis."""

    def test_analyzer_initialization(self):
        """Test that analyzer initializes correctly."""
        # RED: This should fail because class doesn't exist yet
        analyzer = EnhancedGitHubAnalyzer()
        assert analyzer is not None
        assert hasattr(analyzer, "documentation_patterns")
        assert hasattr(analyzer, "source_priorities")

    def test_repository_structure_detection(self):
        """Test comprehensive repository structure detection."""
        # RED: Test complete repository structure analysis
        analyzer = EnhancedGitHubAnalyzer()

        # Mock repository file tree
        mock_file_tree = [
            "README.md",
            "docs/index.md",
            "docs/api/reference.md",
            "docs/tutorials/getting-started.md",
            "docs/examples/basic.py",
            "examples/advanced/complex.py",
            "src/main.py",
            "tests/test_main.py",
            "CONTRIBUTING.md",
            "LICENSE",
            "setup.py",
            "requirements.txt",
            "docs/conf.py",  # Sphinx config
            "mkdocs.yml",  # MkDocs config
            ".github/workflows/docs.yml",
        ]

        structure = analyzer.analyze_repository_structure(
            repo_url="https://github.com/example/repo", file_tree=mock_file_tree
        )

        # Should detect all documentation components
        assert isinstance(structure, RepositoryStructure)
        assert structure.has_readme == True
        assert structure.has_docs_folder == True
        assert structure.has_examples == True
        assert structure.documentation_system in ["sphinx", "mkdocs", "custom"]
        assert len(structure.documentation_files) >= 4
        assert len(structure.example_files) >= 2

    def test_documentation_mapping(self):
        """Test creation of comprehensive documentation map."""
        # RED: Test documentation mapping functionality
        analyzer = EnhancedGitHubAnalyzer()

        mock_files = {
            "README.md": {
                "content": "# Project\n\nMain documentation\n\n## Installation\n\n## Usage",
                "size": 1500,
                "last_modified": "2024-01-01T12:00:00Z",
            },
            "docs/api/reference.md": {
                "content": "# API Reference\n\nComplete API documentation",
                "size": 5000,
                "last_modified": "2024-01-02T10:00:00Z",
            },
            "docs/tutorials/getting-started.md": {
                "content": "# Getting Started\n\nStep-by-step tutorial",
                "size": 3000,
                "last_modified": "2024-01-03T14:00:00Z",
            },
        }

        doc_map = analyzer.create_documentation_map(mock_files)

        assert isinstance(doc_map, DocumentationMap)
        assert len(doc_map.primary_docs) >= 1  # README
        assert len(doc_map.api_docs) >= 1  # API reference
        assert len(doc_map.tutorials) >= 1  # Getting started
        assert doc_map.total_documentation_size > 0
        assert doc_map.estimated_read_time > 0

    def test_source_priority_assignment(self):
        """Test intelligent source priority assignment."""
        # RED: Test priority assignment for different documentation sources
        analyzer = EnhancedGitHubAnalyzer()

        mock_sources = [
            {"path": "README.md", "type": "readme", "size": 1500},
            {"path": "docs/api/reference.md", "type": "api_docs", "size": 5000},
            {"path": "CONTRIBUTING.md", "type": "contributing", "size": 800},
            {"path": "docs/tutorials/basic.md", "type": "tutorial", "size": 2000},
            {"path": "examples/demo.py", "type": "example", "size": 500},
        ]

        priorities = analyzer.assign_source_priorities(mock_sources)

        assert isinstance(priorities, dict)
        # API docs should have highest priority for technical documentation
        assert priorities["docs/api/reference.md"].priority == SourcePriority.HIGH
        # README should have critical priority as primary documentation
        assert priorities["README.md"].priority == SourcePriority.CRITICAL
        # Tutorials should have medium-high priority
        assert (
            priorities["docs/tutorials/basic.md"].priority.value
            >= SourcePriority.MEDIUM.value
        )
        # Contributing should have lower priority for general documentation
        assert (
            priorities["CONTRIBUTING.md"].priority.value <= SourcePriority.MEDIUM.value
        )

    def test_crawl_target_generation(self):
        """Test generation of optimized crawl targets."""
        # RED: Test crawl target generation based on repository analysis
        analyzer = EnhancedGitHubAnalyzer()

        mock_structure = RepositoryStructure(
            repo_url="https://github.com/example/repo",
            has_readme=True,
            has_docs_folder=True,
            has_wiki=True,
            has_examples=True,
            documentation_system="sphinx",
            primary_language="python",
        )

        crawl_targets = analyzer.generate_crawl_targets(mock_structure)

        assert isinstance(crawl_targets, list)
        assert len(crawl_targets) >= 3  # At least README, docs/, examples/

        # Should include main repository URL
        main_target = next(
            (t for t in crawl_targets if t["type"] == "repository_main"), None
        )
        assert main_target is not None
        assert main_target["url"] == "https://github.com/example/repo"

        # Should include docs folder if present
        docs_target = next(
            (t for t in crawl_targets if t["type"] == "docs_folder"), None
        )
        assert docs_target is not None
        assert "docs" in docs_target["url"]

        # Should include wiki if present
        wiki_target = next((t for t in crawl_targets if t["type"] == "wiki"), None)
        assert wiki_target is not None
        assert "wiki" in wiki_target["url"]

    def test_documentation_system_detection(self):
        """Test detection of documentation systems (Sphinx, MkDocs, etc.)."""
        # RED: Test documentation system detection
        analyzer = EnhancedGitHubAnalyzer()

        # Test Sphinx detection
        sphinx_files = ["docs/conf.py", "docs/index.rst", "docs/Makefile"]
        sphinx_system = analyzer.detect_documentation_system(sphinx_files)
        assert sphinx_system == "sphinx"

        # Test MkDocs detection
        mkdocs_files = ["mkdocs.yml", "docs/index.md"]
        mkdocs_system = analyzer.detect_documentation_system(mkdocs_files)
        assert mkdocs_system == "mkdocs"

        # Test GitBook detection
        gitbook_files = ["book.json", "SUMMARY.md"]
        gitbook_system = analyzer.detect_documentation_system(gitbook_files)
        assert gitbook_system == "gitbook"

        # Test custom/unknown
        custom_files = ["docs/index.md", "README.md"]
        custom_system = analyzer.detect_documentation_system(custom_files)
        assert custom_system == "custom"

    def test_file_type_classification(self):
        """Test classification of different file types."""
        # RED: Test file type classification
        analyzer = EnhancedGitHubAnalyzer()

        test_files = [
            "README.md",
            "docs/api.rst",
            "examples/demo.py",
            "tutorials/guide.ipynb",
            "CHANGELOG.md",
            "LICENSE",
            "setup.py",
            "requirements.txt",
            "docs/images/diagram.png",
            "docs/videos/demo.mp4",
        ]

        classifications = analyzer.classify_file_types(test_files)

        assert classifications["README.md"] == DocumentationType.PRIMARY
        assert classifications["docs/api.rst"] == DocumentationType.API
        assert classifications["examples/demo.py"] == DocumentationType.EXAMPLE
        assert classifications["tutorials/guide.ipynb"] == DocumentationType.TUTORIAL
        assert classifications["CHANGELOG.md"] == DocumentationType.META
        assert classifications["LICENSE"] == DocumentationType.LEGAL
        assert classifications["setup.py"] == DocumentationType.CONFIG
        assert classifications["docs/images/diagram.png"] == DocumentationType.MEDIA

    def test_documentation_quality_assessment(self):
        """Test assessment of documentation quality and completeness."""
        # RED: Test documentation quality assessment
        analyzer = EnhancedGitHubAnalyzer()

        mock_doc_map = DocumentationMap(
            primary_docs=["README.md"],
            api_docs=["docs/api.md"],
            tutorials=["docs/tutorial.md"],
            examples=["examples/demo.py"],
            total_files=10,
            total_documentation_size=15000,
            estimated_read_time=45,
        )

        quality_assessment = analyzer.assess_documentation_quality(mock_doc_map)

        assert "completeness_score" in quality_assessment
        assert "quality_score" in quality_assessment
        assert "coverage_areas" in quality_assessment
        assert "missing_components" in quality_assessment
        assert "recommendations" in quality_assessment

        # Scores should be between 0 and 1
        assert 0 <= quality_assessment["completeness_score"] <= 1
        assert 0 <= quality_assessment["quality_score"] <= 1

    def test_nested_documentation_discovery(self):
        """Test discovery of nested documentation structures."""
        # RED: Test nested documentation discovery
        analyzer = EnhancedGitHubAnalyzer()

        nested_structure = [
            "docs/index.md",
            "docs/user-guide/installation.md",
            "docs/user-guide/configuration.md",
            "docs/user-guide/advanced/plugins.md",
            "docs/user-guide/advanced/customization.md",
            "docs/api/core.md",
            "docs/api/extensions.md",
            "docs/api/reference/classes.md",
            "docs/api/reference/functions.md",
            "docs/tutorials/beginner/hello-world.md",
            "docs/tutorials/intermediate/advanced-usage.md",
            "docs/examples/basic/simple.py",
            "docs/examples/advanced/complex.py",
        ]

        nested_map = analyzer.discover_nested_structure(nested_structure)

        assert "user-guide" in nested_map
        assert "api" in nested_map
        assert "tutorials" in nested_map
        assert "examples" in nested_map

        # Should detect depth levels
        assert nested_map["user-guide"]["max_depth"] >= 2  # advanced/ subfolder
        assert nested_map["api"]["max_depth"] >= 2  # reference/ subfolder
        assert len(nested_map["tutorials"]["files"]) >= 2
        assert len(nested_map["examples"]["files"]) >= 2

    def test_wiki_detection_and_analysis(self):
        """Test detection and analysis of GitHub wiki pages."""
        # RED: Test wiki detection and analysis
        analyzer = EnhancedGitHubAnalyzer()

        mock_wiki_structure = {
            "has_wiki": True,
            "wiki_pages": [
                {"title": "Home", "path": "Home.md", "size": 1000},
                {"title": "Installation", "path": "Installation.md", "size": 1500},
                {"title": "FAQ", "path": "FAQ.md", "size": 2000},
                {
                    "title": "Troubleshooting",
                    "path": "Troubleshooting.md",
                    "size": 1200,
                },
            ],
        }

        wiki_analysis = analyzer.analyze_wiki_structure(mock_wiki_structure)

        assert wiki_analysis["has_wiki"] == True
        assert wiki_analysis["total_pages"] == 4
        assert wiki_analysis["total_size"] > 0
        assert "page_categories" in wiki_analysis
        assert "crawl_priority" in wiki_analysis

    def test_integration_with_existing_relevance_detection(self):
        """Test integration with existing relevance detection system."""
        # RED: Test integration with current relevance detection
        analyzer = EnhancedGitHubAnalyzer()

        # Mock integration with existing GitHubContentFilter

        mock_content = "# API Documentation\n\nComplete API reference..."

        # Enhanced analyzer should work with existing relevance detection
        enhanced_analysis = analyzer.analyze_with_relevance_context(
            content=mock_content,
            file_path="docs/api.md",
            repository_context={"type": "api_documentation", "priority": "high"},
        )

        assert "relevance_score" in enhanced_analysis
        assert "context_boost" in enhanced_analysis
        assert "file_type_confidence" in enhanced_analysis
        assert enhanced_analysis["relevance_score"] > 0.5  # Should be relevant


class TestRepositoryStructure:
    """Test RepositoryStructure data model."""

    def test_repository_structure_creation(self):
        """Test creation of RepositoryStructure objects."""
        # RED: Test data model creation
        structure = RepositoryStructure(
            repo_url="https://github.com/example/repo",
            has_readme=True,
            has_docs_folder=True,
            has_wiki=False,
            has_examples=True,
            documentation_system="sphinx",
            primary_language="python",
        )

        assert structure.repo_url == "https://github.com/example/repo"
        assert structure.has_readme == True
        assert structure.has_docs_folder == True
        assert structure.documentation_system == "sphinx"

    def test_structure_serialization(self):
        """Test serialization of repository structure."""
        # RED: Test JSON serialization
        structure = RepositoryStructure(
            repo_url="https://github.com/example/repo",
            has_readme=True,
            has_docs_folder=True,
        )

        serialized = structure.to_dict()
        assert isinstance(serialized, dict)
        assert serialized["repo_url"] == "https://github.com/example/repo"

        # Should be JSON serializable
        json_str = json.dumps(serialized)
        assert isinstance(json_str, str)


class TestDocumentationMap:
    """Test DocumentationMap data model."""

    def test_documentation_map_creation(self):
        """Test creation of DocumentationMap objects."""
        # RED: Test documentation map creation
        doc_map = DocumentationMap(
            primary_docs=["README.md"],
            api_docs=["docs/api.md"],
            tutorials=["docs/tutorial.md"],
            examples=["examples/demo.py"],
        )

        assert len(doc_map.primary_docs) == 1
        assert len(doc_map.api_docs) == 1
        assert len(doc_map.tutorials) == 1
        assert len(doc_map.examples) == 1

    def test_documentation_statistics(self):
        """Test documentation statistics calculation."""
        # RED: Test statistics calculation
        doc_map = DocumentationMap(
            primary_docs=["README.md"],
            api_docs=["docs/api.md", "docs/reference.md"],
            tutorials=["docs/tutorial1.md", "docs/tutorial2.md"],
            examples=["examples/demo1.py", "examples/demo2.py", "examples/demo3.py"],
        )

        stats = doc_map.calculate_statistics()

        assert stats["total_files"] == 8
        assert stats["api_coverage"] == 2
        assert stats["tutorial_coverage"] == 2
        assert stats["example_coverage"] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
