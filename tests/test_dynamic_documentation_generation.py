#!/usr/bin/env python3
"""
TDD Tests for Dynamic Documentation Generation Feature

These tests will FAIL initially and guide the implementation.
Tests AI-enhanced documentation creation and gap filling.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestDynamicDocumentationGeneration:
    """Test suite for dynamic documentation generation functionality."""

    @pytest.fixture
    def sparse_github_docs(self):
        """Sample sparse GitHub documentation that needs enhancement."""
        return {
            "library_name": "awesome-lib",
            "repository_url": "https://github.com/user/awesome-lib",
            "readme_content": """
            # Awesome Lib

            A simple library for doing awesome things.

            ## Installation

            ```bash
            pip install awesome-lib
            ```

            ## Usage

            ```python
            from awesome_lib import AwesomeClass
            obj = AwesomeClass()
            result = obj.do_something()
            ```
            """,
            "code_files": [
                {
                    "path": "awesome_lib/__init__.py",
                    "content": "from .core import AwesomeClass\n__version__ = '1.0.0'",
                },
                {
                    "path": "awesome_lib/core.py",
                    "content": """
class AwesomeClass:
    '''Main class for awesome operations.'''

    def __init__(self, config=None):
        '''Initialize with optional config.'''
        self.config = config or {}

    def do_something(self, data=None):
        '''Process data and return result.'''
        if not data:
            return "No data provided"
        return f"Processed: {data}"

    def advanced_feature(self, x, y, mode='default'):
        '''Advanced feature with multiple parameters.'''
        if mode == 'fast':
            return x + y
        elif mode == 'detailed':
            return {'sum': x + y, 'product': x * y}
        return x + y
                    """,
                },
            ],
            "dependencies": ["requests>=2.25.0", "numpy>=1.20.0"],
        }

    @pytest.fixture
    def comprehensive_docs_example(self):
        """Example of what comprehensive documentation should look like."""
        return {
            "overview": "Detailed library overview with use cases",
            "installation": "Step-by-step installation guide",
            "quick_start": "Quick start tutorial with examples",
            "api_reference": "Complete API documentation",
            "examples": "Comprehensive examples and tutorials",
            "integration_guide": "How to integrate with other libraries",
            "troubleshooting": "Common issues and solutions",
            "changelog": "Version history and changes",
        }

    def test_documentation_analyzer_creation(self):
        """Test that DocumentationAnalyzer can be created."""
        # This will fail - DocumentationAnalyzer doesn't exist yet
        from processors.doc_generation import DocumentationAnalyzer

        analyzer = DocumentationAnalyzer()
        assert analyzer is not None
        assert hasattr(analyzer, "analyze_completeness")
        assert hasattr(analyzer, "identify_gaps")
        assert hasattr(analyzer, "extract_code_structure")

    def test_documentation_completeness_analysis(self, sparse_github_docs):
        """Test analyzing documentation completeness and identifying gaps."""
        from processors.doc_generation import DocumentationAnalyzer

        analyzer = DocumentationAnalyzer()

        analysis = analyzer.analyze_completeness(sparse_github_docs)

        assert isinstance(analysis, dict)
        assert "completeness_score" in analysis
        assert "missing_sections" in analysis
        assert "existing_sections" in analysis
        assert "recommendations" in analysis

        # Should identify low completeness due to sparse docs
        assert 0 <= analysis["completeness_score"] <= 1
        assert analysis["completeness_score"] < 0.6  # Sparse docs should score low

        # Should identify missing sections
        missing = analysis["missing_sections"]
        assert "api_reference" in missing
        assert "examples" in missing
        assert "troubleshooting" in missing

    def test_code_structure_extraction(self, sparse_github_docs):
        """Test extracting code structure from repository files."""
        from processors.doc_generation import CodeStructureExtractor

        extractor = CodeStructureExtractor()

        structure = extractor.extract_structure(sparse_github_docs["code_files"])

        assert isinstance(structure, dict)
        assert "classes" in structure
        assert "functions" in structure
        assert "modules" in structure

        # Should find AwesomeClass
        classes = structure["classes"]
        assert len(classes) > 0
        awesome_class = next((c for c in classes if c["name"] == "AwesomeClass"), None)
        assert awesome_class is not None
        assert "methods" in awesome_class
        assert (
            len(awesome_class["methods"]) == 3
        )  # __init__, do_something, advanced_feature

    def test_ai_documentation_generator_creation(self):
        """Test that AI documentation generator can be created."""
        from processors.doc_generation import AIDocumentationGenerator

        generator = AIDocumentationGenerator()
        assert generator is not None
        assert hasattr(generator, "generate_api_reference")
        assert hasattr(generator, "generate_examples")
        assert hasattr(generator, "generate_tutorial")
        assert hasattr(generator, "enhance_existing_docs")

    @pytest.mark.asyncio
    async def test_api_reference_generation(self, sparse_github_docs):
        """Test generating comprehensive API reference from code."""
        from processors.doc_generation import AIDocumentationGenerator

        generator = AIDocumentationGenerator()

        # Mock AI service response
        with patch.object(generator, "_call_ai_service") as mock_ai:
            mock_ai.return_value = {
                "api_reference": {
                    "AwesomeClass": {
                        "description": "Main class for performing awesome operations on data",
                        "methods": {
                            "__init__": {
                                "description": "Initialize AwesomeClass with optional configuration",
                                "parameters": {
                                    "config": "Optional dictionary for configuration settings"
                                },
                                "examples": [
                                    "obj = AwesomeClass()",
                                    "obj = AwesomeClass({'debug': True})",
                                ],
                            },
                            "do_something": {
                                "description": "Process input data and return formatted result",
                                "parameters": {
                                    "data": "Input data to process (any type)"
                                },
                                "returns": "Processed data as string",
                                "examples": [
                                    "result = obj.do_something('hello')",
                                    "result = obj.do_something([1, 2, 3])",
                                ],
                            },
                        },
                    }
                }
            }

            api_ref = await generator.generate_api_reference(sparse_github_docs)

            assert isinstance(api_ref, dict)
            assert "AwesomeClass" in api_ref
            assert "description" in api_ref["AwesomeClass"]
            assert "methods" in api_ref["AwesomeClass"]

            methods = api_ref["AwesomeClass"]["methods"]
            assert "do_something" in methods
            assert "examples" in methods["do_something"]

    @pytest.mark.asyncio
    async def test_tutorial_generation(self, sparse_github_docs):
        """Test generating step-by-step tutorials."""
        from processors.doc_generation import AIDocumentationGenerator

        generator = AIDocumentationGenerator()

        with patch.object(generator, "_call_ai_service") as mock_ai:
            mock_ai.return_value = {
                "tutorial": {
                    "title": "Getting Started with Awesome Lib",
                    "sections": [
                        {
                            "title": "Basic Usage",
                            "content": "Learn how to use AwesomeClass for basic operations",
                            "code_example": "from awesome_lib import AwesomeClass\nobj = AwesomeClass()\nresult = obj.do_something('test')",
                        },
                        {
                            "title": "Advanced Features",
                            "content": "Explore advanced functionality",
                            "code_example": "result = obj.advanced_feature(5, 3, mode='detailed')",
                        },
                    ],
                }
            }

            tutorial = await generator.generate_tutorial(sparse_github_docs)

            assert isinstance(tutorial, dict)
            assert "title" in tutorial
            assert "sections" in tutorial
            assert len(tutorial["sections"]) > 0

            first_section = tutorial["sections"][0]
            assert "title" in first_section
            assert "content" in first_section
            assert "code_example" in first_section

    def test_dependency_integration_guide_generation(self, sparse_github_docs):
        """Test generating integration guides for dependencies."""
        from processors.doc_generation import DependencyIntegrationGenerator

        generator = DependencyIntegrationGenerator()

        integration_guide = generator.generate_integration_guide(sparse_github_docs)

        assert isinstance(integration_guide, dict)
        assert "dependencies" in integration_guide
        assert "integration_examples" in integration_guide

        # Should have guides for requests and numpy
        deps = integration_guide["dependencies"]
        assert any(dep["name"] == "requests" for dep in deps)
        assert any(dep["name"] == "numpy" for dep in deps)

        # Should have integration examples
        examples = integration_guide["integration_examples"]
        assert len(examples) > 0
        assert any("requests" in ex["code"] for ex in examples)

    def test_troubleshooting_guide_generation(self, sparse_github_docs):
        """Test generating troubleshooting guides based on common patterns."""
        from processors.doc_generation import TroubleshootingGenerator

        generator = TroubleshootingGenerator()

        troubleshooting = generator.generate_troubleshooting_guide(sparse_github_docs)

        assert isinstance(troubleshooting, dict)
        assert "common_issues" in troubleshooting
        assert "installation_issues" in troubleshooting
        assert "usage_issues" in troubleshooting

        # Should have common installation issues
        install_issues = troubleshooting["installation_issues"]
        assert len(install_issues) > 0
        assert any("pip" in issue["problem"].lower() for issue in install_issues)

    def test_example_code_generation(self, sparse_github_docs):
        """Test generating comprehensive code examples."""
        from processors.doc_generation import ExampleCodeGenerator

        generator = ExampleCodeGenerator()

        examples = generator.generate_examples(sparse_github_docs)

        assert isinstance(examples, dict)
        assert "basic_examples" in examples
        assert "advanced_examples" in examples
        assert "use_case_examples" in examples

        basic_examples = examples["basic_examples"]
        assert len(basic_examples) > 0

        # Should have examples for each public method
        example_methods = [ex["method"] for ex in basic_examples]
        assert "do_something" in example_methods
        assert "advanced_feature" in example_methods

    def test_documentation_enhancement(self, sparse_github_docs):
        """Test enhancing existing sparse documentation."""
        from processors.doc_generation import DocumentationEnhancer

        enhancer = DocumentationEnhancer()

        enhanced_docs = enhancer.enhance_documentation(sparse_github_docs)

        assert isinstance(enhanced_docs, dict)
        assert "original_content" in enhanced_docs
        assert "enhanced_content" in enhanced_docs
        assert "improvements" in enhanced_docs

        # Enhanced content should be more comprehensive
        enhanced = enhanced_docs["enhanced_content"]
        assert "api_reference" in enhanced
        assert "examples" in enhanced
        assert "troubleshooting" in enhanced

        # Should list what was improved
        improvements = enhanced_docs["improvements"]
        assert len(improvements) > 0
        assert any("api_reference" in imp for imp in improvements)

    def test_documentation_quality_scoring(self):
        """Test scoring documentation quality before and after enhancement."""
        from processors.doc_generation import DocumentationQualityScorer

        scorer = DocumentationQualityScorer()

        # Test sparse documentation
        sparse_score = scorer.calculate_quality_score(
            {
                "sections": ["installation", "basic_usage"],
                "code_examples": 1,
                "api_coverage": 0.3,
            }
        )

        # Test comprehensive documentation
        comprehensive_score = scorer.calculate_quality_score(
            {
                "sections": [
                    "installation",
                    "api_reference",
                    "examples",
                    "troubleshooting",
                ],
                "code_examples": 10,
                "api_coverage": 0.9,
            }
        )

        assert 0 <= sparse_score <= 1
        assert 0 <= comprehensive_score <= 1
        assert comprehensive_score > sparse_score
        assert sparse_score < 0.5
        assert comprehensive_score > 0.8

    def test_multi_format_documentation_export(self, sparse_github_docs):
        """Test exporting enhanced documentation in multiple formats."""
        from processors.doc_generation import DocumentationExporter

        exporter = DocumentationExporter()

        # Generate enhanced docs first
        enhanced_docs = {
            "overview": "Comprehensive library overview",
            "api_reference": {"AwesomeClass": {"description": "Main class"}},
            "examples": [{"title": "Basic Usage", "code": "obj = AwesomeClass()"}],
        }

        # Test markdown export
        markdown = exporter.export_to_markdown(enhanced_docs)
        assert isinstance(markdown, str)
        assert "# Overview" in markdown
        assert "## API Reference" in markdown
        assert "```python" in markdown

        # Test HTML export
        html = exporter.export_to_html(enhanced_docs)
        assert isinstance(html, str)
        assert "<h1>" in html
        assert "<code>" in html

        # Test JSON export
        json_export = exporter.export_to_json(enhanced_docs)
        assert isinstance(json_export, str)
        import json

        parsed = json.loads(json_export)
        assert "overview" in parsed

    @pytest.mark.asyncio
    async def test_real_time_documentation_generation(self):
        """Test real-time documentation generation during scraping."""
        from processors.doc_generation import RealtimeDocGenerator

        generator = RealtimeDocGenerator()

        # Simulate scraping session
        session_id = "test_session_456"

        # Add scraped content progressively
        await generator.add_scraped_content(
            session_id, {"type": "readme", "content": "Basic library description"}
        )

        await generator.add_scraped_content(
            session_id,
            {
                "type": "code_file",
                "path": "lib/core.py",
                "content": "class MainClass: pass",
            },
        )

        # Generate documentation from accumulated content
        docs = await generator.generate_documentation(session_id)

        assert isinstance(docs, dict)
        assert "status" in docs
        assert "generated_sections" in docs
        assert docs["status"] == "success"
        assert len(docs["generated_sections"]) > 0

    def test_documentation_gap_analysis(
        self, sparse_github_docs, comprehensive_docs_example
    ):
        """Test identifying specific documentation gaps."""
        from processors.doc_generation import DocumentationGapAnalyzer

        analyzer = DocumentationGapAnalyzer()

        gaps = analyzer.analyze_gaps(sparse_github_docs, comprehensive_docs_example)

        assert isinstance(gaps, dict)
        assert "critical_gaps" in gaps
        assert "minor_gaps" in gaps
        assert "recommendations" in gaps

        critical_gaps = gaps["critical_gaps"]
        assert "api_reference" in critical_gaps
        assert "examples" in critical_gaps

        # Should provide specific recommendations
        recommendations = gaps["recommendations"]
        assert len(recommendations) > 0
        assert any("generate api reference" in rec.lower() for rec in recommendations)

    def test_dynamic_documentation_api_endpoint(self):
        """Test the API endpoint for dynamic documentation generation."""
        import sys

        from fastapi.testclient import TestClient

        sys.path.insert(0, "src")
        from main import app

        client = TestClient(app)

        # Test documentation generation endpoint
        response = client.post(
            "/api/docs/generate",
            json={
                "repository_url": "https://github.com/user/repo",
                "enhancement_level": "comprehensive",
                "include_sections": ["api_reference", "examples", "troubleshooting"],
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert "generated_docs" in data
        assert "quality_score" in data
        assert "generation_time" in data

        # Test documentation enhancement endpoint
        enhance_response = client.post(
            "/api/docs/enhance",
            json={
                "existing_docs": "Basic documentation content",
                "code_files": [{"path": "main.py", "content": "def hello(): pass"}],
                "target_quality": 0.8,
            },
        )

        assert enhance_response.status_code == 200
        enhance_data = enhance_response.json()

        assert "enhanced_docs" in enhance_data
        assert "improvements" in enhance_data
        assert "before_score" in enhance_data
        assert "after_score" in enhance_data


if __name__ == "__main__":
    # Run the tests to see them fail
    pytest.main([__file__, "-v", "--tb=short"])
