#!/usr/bin/env python3
"""
TDD Tests for Smart Content Relevance Detection Feature

These tests will FAIL initially and guide the implementation.
Tests both NLP-based and traditional rule-based approaches.
"""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestContentRelevanceDetection:
    """Test suite for smart content relevance detection functionality."""

    @pytest.fixture
    def documentation_content(self):
        """Sample documentation content (relevant)."""
        return """
        # FastAPI Documentation

        FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.7+
        based on standard Python type hints.

        ## Installation

        ```bash
        pip install fastapi
        ```

        ## First Steps

        Create a file `main.py` with:

        ```python
        from fastapi import FastAPI

        app = FastAPI()

        @app.get("/")
        def read_root():
            return {"Hello": "World"}
        ```

        ## Path Parameters

        You can declare path parameters with the same syntax used by Python format strings.
        """

    @pytest.fixture
    def non_documentation_content(self):
        """Sample non-documentation content (irrelevant)."""
        return """
        # Contributing to FastAPI

        Thanks for your interest in contributing to FastAPI! There are many ways to contribute.

        ## Code of Conduct

        Please read our Code of Conduct before contributing.

        ## Issues

        If you find a bug, please create an issue with:
        - A clear description
        - Steps to reproduce
        - Expected behavior
        - Actual behavior

        ## Pull Requests

        Before submitting a pull request:
        1. Fork the repository
        2. Create a feature branch
        3. Make your changes
        4. Add tests
        5. Submit the PR

        ## Development Setup

        Clone the repository and install dependencies:

        ```bash
        git clone https://github.com/tiangolo/fastapi.git
        cd fastapi
        pip install -e .
        ```
        """

    @pytest.fixture
    def github_readme_content(self):
        """Sample GitHub README content (mixed relevance)."""
        return """
        # FastAPI

        <p align="center">
          <a href="https://fastapi.tiangolo.com"><img src="https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png" alt="FastAPI"></a>
        </p>

        FastAPI framework, high performance, easy to learn, fast to code, ready for production

        ## Features

        * **Fast**: Very high performance, on par with **NodeJS** and **Go** (thanks to Starlette and Pydantic).
        * **Fast to code**: Increase the speed to develop features by about 200% to 300%.
        * **Fewer bugs**: Reduce about 40% of human (developer) induced errors.

        ## Installation

        ```console
        $ pip install fastapi
        ```

        ## Example

        ### Create it

        * Create a file `main.py` with:

        ```Python
        from fastapi import FastAPI

        app = FastAPI()

        @app.get("/")
        def read_root():
            return {"Hello": "World"}
        ```

        ## License

        This project is licensed under the terms of the MIT license.

        ## Contributors

        Thanks to all the contributors who have helped make FastAPI better!
        """

    def test_nlp_relevance_detector_creation(self):
        """Test that NLP-based relevance detector can be created."""
        # This will fail - NLPRelevanceDetector doesn't exist yet
        from processors.relevance_detection import NLPRelevanceDetector

        detector = NLPRelevanceDetector()
        assert detector is not None
        assert hasattr(detector, "is_documentation_relevant")
        assert hasattr(detector, "get_relevance_score")
        assert hasattr(detector, "extract_documentation_sections")

    def test_rule_based_relevance_detector_creation(self):
        """Test that rule-based relevance detector can be created."""
        from processors.relevance_detection import RuleBasedRelevanceDetector

        detector = RuleBasedRelevanceDetector()
        assert detector is not None
        assert hasattr(detector, "is_documentation_relevant")
        assert hasattr(detector, "get_relevance_score")
        assert hasattr(detector, "get_irrelevant_indicators")

    def test_nlp_detector_identifies_documentation(self, documentation_content):
        """Test NLP detector correctly identifies documentation content."""
        from processors.relevance_detection import NLPRelevanceDetector

        detector = NLPRelevanceDetector()

        result = detector.is_documentation_relevant(documentation_content)

        assert isinstance(result, dict)
        assert "is_relevant" in result
        assert "confidence" in result
        assert "reasoning" in result

        assert result["is_relevant"] == True
        assert result["confidence"] > 0.7  # High confidence for clear documentation
        assert (
            "installation" in result["reasoning"].lower()
            or "api" in result["reasoning"].lower()
        )

    def test_nlp_detector_identifies_non_documentation(self, non_documentation_content):
        """Test NLP detector correctly identifies non-documentation content."""
        from processors.relevance_detection import NLPRelevanceDetector

        detector = NLPRelevanceDetector()

        result = detector.is_documentation_relevant(non_documentation_content)

        assert result["is_relevant"] == False
        assert result["confidence"] > 0.6
        assert any(
            word in result["reasoning"].lower()
            for word in ["contributing", "development", "pull request"]
        )

    def test_rule_based_detector_identifies_documentation(self, documentation_content):
        """Test rule-based detector correctly identifies documentation content."""
        from processors.relevance_detection import RuleBasedRelevanceDetector

        detector = RuleBasedRelevanceDetector()

        result = detector.is_documentation_relevant(documentation_content)

        assert isinstance(result, dict)
        assert "is_relevant" in result
        assert "score" in result
        assert "matched_patterns" in result

        assert result["is_relevant"] == True
        assert result["score"] > 0.7
        assert len(result["matched_patterns"]) > 0

        # Should match documentation patterns
        patterns = result["matched_patterns"]
        assert any(
            "installation" in p.lower() or "example" in p.lower() for p in patterns
        )

    def test_rule_based_detector_identifies_non_documentation(
        self, non_documentation_content
    ):
        """Test rule-based detector correctly identifies non-documentation content."""
        from processors.relevance_detection import RuleBasedRelevanceDetector

        detector = RuleBasedRelevanceDetector()

        result = detector.is_documentation_relevant(non_documentation_content)

        assert result["is_relevant"] == False
        assert result["score"] < 0.5

        # Should identify irrelevant patterns
        irrelevant_indicators = detector.get_irrelevant_indicators(
            non_documentation_content
        )
        assert len(irrelevant_indicators) > 0
        assert any(
            "contributing" in ind.lower() or "pull request" in ind.lower()
            for ind in irrelevant_indicators
        )

    def test_hybrid_relevance_detector(
        self, documentation_content, non_documentation_content
    ):
        """Test hybrid detector that combines NLP and rule-based approaches."""
        from processors.relevance_detection import HybridRelevanceDetector

        detector = HybridRelevanceDetector()

        # Test with documentation content
        doc_result = detector.is_documentation_relevant(documentation_content)
        assert doc_result["is_relevant"] == True
        assert doc_result["confidence"] > 0.7
        assert "nlp_score" in doc_result
        assert "rule_score" in doc_result
        assert "combined_score" in doc_result

        # Test with non-documentation content
        non_doc_result = detector.is_documentation_relevant(non_documentation_content)
        assert non_doc_result["is_relevant"] == False
        assert non_doc_result["confidence"] > 0.6

    def test_github_content_filtering(self, github_readme_content):
        """Test filtering GitHub content to extract only documentation parts."""
        from processors.relevance_detection import GitHubContentFilter

        filter = GitHubContentFilter()

        filtered_content = filter.extract_documentation_sections(github_readme_content)

        assert isinstance(filtered_content, dict)
        assert "relevant_sections" in filtered_content
        assert "irrelevant_sections" in filtered_content
        assert "documentation_score" in filtered_content

        # Should extract installation and example sections
        relevant_sections = filtered_content["relevant_sections"]
        assert len(relevant_sections) > 0
        assert any(
            "installation" in section["title"].lower() for section in relevant_sections
        )
        assert any(
            "example" in section["title"].lower() for section in relevant_sections
        )

        # Should filter out license and contributors sections
        irrelevant_sections = filtered_content["irrelevant_sections"]
        assert any(
            "license" in section["title"].lower() for section in irrelevant_sections
        )

    def test_content_relevance_scoring(self):
        """Test detailed relevance scoring system."""
        from processors.relevance_detection import ContentRelevanceScorer

        scorer = ContentRelevanceScorer()

        # Test various content types
        test_cases = [
            ("API documentation with examples", 0.9),
            ("Installation instructions", 0.8),
            ("Code examples and tutorials", 0.85),
            ("Contributing guidelines", 0.2),
            ("License information", 0.1),
            ("Issue templates", 0.15),
            ("Changelog and release notes", 0.3),
        ]

        for content, expected_min_score in test_cases:
            score = scorer.calculate_relevance_score(content)
            assert isinstance(score, float)
            assert 0 <= score <= 1
            # Allow some tolerance in scoring
            assert score >= expected_min_score - 0.2

    def test_real_time_relevance_monitoring(self):
        """Test real-time monitoring of content relevance during scraping."""
        from processors.relevance_detection import RealtimeRelevanceMonitor

        monitor = RealtimeRelevanceMonitor(threshold=0.6)

        # Simulate scraping session
        session_id = "test_session_123"

        # Add relevant content
        monitor.add_content(session_id, "Installation guide", "pip install fastapi")
        monitor.add_content(session_id, "API Reference", "FastAPI class documentation")

        # Add irrelevant content
        monitor.add_content(
            session_id, "Contributing", "How to contribute to the project"
        )

        # Get session statistics
        stats = monitor.get_session_stats(session_id)

        assert "total_pages" in stats
        assert "relevant_pages" in stats
        assert "irrelevant_pages" in stats
        assert "relevance_ratio" in stats

        assert stats["total_pages"] == 3
        assert stats["relevant_pages"] == 2
        assert stats["irrelevant_pages"] == 1
        assert stats["relevance_ratio"] > 0.6

    def test_adaptive_threshold_adjustment(self):
        """Test adaptive threshold adjustment based on content patterns."""
        from processors.relevance_detection import AdaptiveThresholdManager

        manager = AdaptiveThresholdManager()

        # Simulate different types of websites
        github_repo_patterns = [
            ("README.md", 0.7),
            ("CONTRIBUTING.md", 0.2),
            ("docs/api.md", 0.9),
            ("LICENSE", 0.1),
        ]

        docs_site_patterns = [
            ("Getting Started", 0.9),
            ("API Reference", 0.95),
            ("Examples", 0.9),
            ("About Us", 0.3),
        ]

        # Train on GitHub repo
        github_threshold = manager.calculate_optimal_threshold(github_repo_patterns)
        assert 0.4 <= github_threshold <= 0.7  # Should be lower for GitHub repos

        # Train on docs site
        docs_threshold = manager.calculate_optimal_threshold(docs_site_patterns)
        assert 0.7 <= docs_threshold <= 0.9  # Should be higher for dedicated docs sites

    def test_performance_comparison(
        self, documentation_content, non_documentation_content
    ):
        """Test performance comparison between NLP and rule-based approaches."""
        from processors.relevance_detection import PerformanceBenchmark

        benchmark = PerformanceBenchmark()

        test_contents = [
            documentation_content,
            non_documentation_content,
        ] * 10  # 20 samples

        results = benchmark.compare_methods(test_contents)

        assert "nlp_method" in results
        assert "rule_based_method" in results
        assert "hybrid_method" in results

        for method_name, method_results in results.items():
            assert "accuracy" in method_results
            assert "precision" in method_results
            assert "recall" in method_results
            assert "avg_processing_time" in method_results
            assert "total_processing_time" in method_results

            # All methods should have reasonable accuracy
            assert method_results["accuracy"] > 0.7

    def test_relevance_detection_integration_with_crawler(self):
        """Test integration of relevance detection with the main crawler."""
        from crawler.enhanced_crawler import EnhancedCrawler

        crawler = EnhancedCrawler(relevance_detection=True)

        # Mock crawling with relevance detection
        mock_pages = [
            {
                "url": "https://example.com/docs/api",
                "content": "API documentation for developers. This section covers all the available endpoints, parameters, and response formats. Learn how to authenticate and make requests to our REST API.",
            },
            {
                "url": "https://example.com/contributing",
                "content": "Contributing guidelines for developers who want to contribute to this project. Please read our code of conduct and follow the pull request process.",
            },
            {
                "url": "https://example.com/docs/tutorial",
                "content": "Tutorial and examples showing how to use this library. Step-by-step instructions with code examples and best practices for getting started.",
            },
        ]

        filtered_pages = crawler.filter_relevant_pages(mock_pages)

        assert len(filtered_pages) == 2  # Should filter out contributing page
        assert all(page["relevance_score"] > 0.6 for page in filtered_pages)
        assert any("api" in page["url"] for page in filtered_pages)
        assert any("tutorial" in page["url"] for page in filtered_pages)

    def test_relevance_detection_api_endpoint(self):
        """Test the API endpoint for content relevance detection."""
        import sys

        from fastapi.testclient import TestClient

        sys.path.insert(0, ".")
        from run_gui import app

        client = TestClient(app)

        # Test relevance detection endpoint
        response = client.post(
            "/api/relevance/detect",
            json={
                "content": "FastAPI is a web framework for building APIs",
                "method": "hybrid",
                "threshold": 0.6,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "is_relevant" in data
        assert "confidence" in data
        assert "method_used" in data
        assert "processing_time" in data

        # Test batch relevance detection
        batch_response = client.post(
            "/api/relevance/detect-batch",
            json={
                "contents": [
                    {
                        "id": "1",
                        "content": "API documentation for developers. This comprehensive guide covers all endpoints, authentication methods, request/response formats, and code examples for integrating with our REST API.",
                    },
                    {
                        "id": "2",
                        "content": "Contributing guidelines for developers who want to contribute to this project. Please read our code of conduct and follow the pull request process.",
                    },
                ],
                "method": "rule_based",
            },
        )

        assert batch_response.status_code == 200
        batch_data = batch_response.json()

        assert "results" in batch_data
        assert len(batch_data["results"]) == 2
        assert batch_data["results"][0]["is_relevant"] == True
        assert batch_data["results"][1]["is_relevant"] == False


if __name__ == "__main__":
    # Run the tests to see them fail
    pytest.main([__file__, "-v", "--tb=short"])
