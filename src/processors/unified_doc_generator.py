#!/usr/bin/env python3
"""
Unified Documentation Generator for Multi-Library Projects

Generates comprehensive documentation that combines multiple libraries.
"""

import re
from typing import Any, Optional


class UnifiedDocumentationGenerator:
    """Generator for creating unified documentation from multiple library docs."""

    def __init__(self):
        """Initialize the unified documentation generator."""
        self.integration_patterns = {
            "python": {
                "web_frameworks": ["fastapi", "flask", "django", "starlette"],
                "http_clients": ["requests", "httpx", "aiohttp"],
                "data_processing": ["pandas", "numpy", "scipy"],
                "testing": ["pytest", "unittest", "mock"],
            },
            "javascript": {
                "frameworks": ["react", "vue", "angular", "svelte"],
                "http_clients": ["axios", "fetch", "superagent"],
                "testing": ["jest", "mocha", "jasmine"],
                "build_tools": ["webpack", "vite", "rollup"],
            },
        }

    def generate_unified_docs(
        self, library_docs: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Generate unified documentation from multiple library documentation.

        Args:
            library_docs: Dictionary mapping library names to their documentation

        Returns:
            Unified documentation structure
        """
        unified = {
            "overview": self._generate_overview(library_docs),
            "libraries": self._organize_libraries(library_docs),
            "integration_examples": self._generate_integration_examples(library_docs),
            "compatibility_matrix": self._generate_compatibility_matrix(library_docs),
            "quick_start": self._generate_quick_start(library_docs),
            "common_patterns": self._identify_common_patterns(library_docs),
            "troubleshooting": self._generate_troubleshooting(library_docs),
        }

        return unified

    def _generate_overview(self, library_docs: dict[str, dict[str, Any]]) -> str:
        """Generate a comprehensive overview of all libraries."""
        overview = "# Project Documentation Overview\n\n"
        overview += f"This project integrates {len(library_docs)} libraries to provide comprehensive functionality.\n\n"

        # Categorize libraries
        categories = self._categorize_libraries(library_docs)

        for category, libraries in categories.items():
            if libraries:
                overview += f"## {category.title()} Libraries\n\n"
                for lib_name in libraries:
                    lib_doc = library_docs[lib_name]
                    content = lib_doc.get("content", "No description available")
                    # Extract first sentence as summary
                    summary = (
                        content.split(".")[0] + "."
                        if content
                        else "No description available."
                    )
                    overview += f"- **{lib_name}**: {summary}\n"
                overview += "\n"

        return overview

    def _organize_libraries(
        self, library_docs: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        """Organize library documentation by category and importance."""
        organized = {
            "core_libraries": {},
            "utility_libraries": {},
            "development_libraries": {},
            "all_libraries": library_docs,
        }

        # Categorize based on common patterns
        for lib_name, lib_doc in library_docs.items():
            content = lib_doc.get("content", "").lower()
            api_ref = lib_doc.get("api_reference", [])

            # Determine category based on content analysis
            if any(
                keyword in content
                for keyword in ["framework", "core", "main", "primary"]
            ):
                organized["core_libraries"][lib_name] = lib_doc
            elif any(
                keyword in content
                for keyword in ["test", "debug", "development", "dev"]
            ):
                organized["development_libraries"][lib_name] = lib_doc
            else:
                organized["utility_libraries"][lib_name] = lib_doc

        return organized

    def _generate_integration_examples(
        self, library_docs: dict[str, dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Generate examples showing how libraries work together."""
        examples = []
        library_names = list(library_docs.keys())

        # Generate pairwise integration examples
        for i, lib1 in enumerate(library_names):
            for lib2 in library_names[i + 1 :]:
                example = self._create_integration_example(lib1, lib2, library_docs)
                if example:
                    examples.append(example)

        # Limit to most relevant examples
        return examples[:5]

    def _create_integration_example(
        self, lib1: str, lib2: str, library_docs: dict[str, dict[str, Any]]
    ) -> Optional[dict[str, Any]]:
        """Create an integration example for two libraries."""
        lib1_doc = library_docs.get(lib1, {})
        lib2_doc = library_docs.get(lib2, {})

        # Check if libraries are likely to work together
        lib1_content = lib1_doc.get("content", "").lower()
        lib2_content = lib2_doc.get("content", "").lower()

        # Common integration patterns
        if "http" in lib1_content and "web" in lib2_content:
            return {
                "title": f"HTTP Client with Web Framework: {lib1} + {lib2}",
                "description": f"Example showing how to use {lib1} for HTTP requests with {lib2} web framework",
                "code": f"""
# Integration example: {lib1} with {lib2}
import {lib1}
import {lib2}

# Example usage combining both libraries
# This is a generated example - refer to individual docs for specifics
""",
                "libraries": [lib1, lib2],
                "category": "web_development",
            }

        elif "data" in lib1_content and "process" in lib2_content:
            return {
                "title": f"Data Processing: {lib1} + {lib2}",
                "description": f"Example showing data processing with {lib1} and {lib2}",
                "code": f"""
# Data processing example: {lib1} with {lib2}
import {lib1}
import {lib2}

# Example data processing workflow
# This is a generated example - refer to individual docs for specifics
""",
                "libraries": [lib1, lib2],
                "category": "data_processing",
            }

        return None

    def _generate_compatibility_matrix(
        self, library_docs: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        """Generate compatibility matrix between libraries."""
        libraries = list(library_docs.keys())
        matrix = {}

        for lib1 in libraries:
            matrix[lib1] = {}
            for lib2 in libraries:
                if lib1 == lib2:
                    matrix[lib1][lib2] = "self"
                else:
                    compatibility = self._assess_compatibility(lib1, lib2, library_docs)
                    matrix[lib1][lib2] = compatibility

        return {
            "matrix": matrix,
            "legend": {
                "compatible": "Known to work well together",
                "likely_compatible": "Likely compatible based on patterns",
                "unknown": "Compatibility unknown",
                "potential_conflict": "May have conflicts",
                "self": "Same library",
            },
        }

    def _assess_compatibility(
        self, lib1: str, lib2: str, library_docs: dict[str, dict[str, Any]]
    ) -> str:
        """Assess compatibility between two libraries."""
        lib1_doc = library_docs.get(lib1, {})
        lib2_doc = library_docs.get(lib2, {})

        lib1_content = lib1_doc.get("content", "").lower()
        lib2_content = lib2_doc.get("content", "").lower()

        # Check for known compatibility patterns
        web_frameworks = ["fastapi", "flask", "django"]
        http_clients = ["requests", "httpx"]

        if lib1 in web_frameworks and lib2 in http_clients:
            return "compatible"
        elif lib2 in web_frameworks and lib1 in http_clients:
            return "compatible"

        # Check for potential conflicts
        if "async" in lib1_content and "sync" in lib2_content:
            return "potential_conflict"

        # Default assessment
        return "likely_compatible"

    def _generate_quick_start(self, library_docs: dict[str, dict[str, Any]]) -> str:
        """Generate a quick start guide for the entire project."""
        guide = "# Quick Start Guide\n\n"
        guide += "Follow these steps to get started with this project:\n\n"

        # Installation section
        guide += "## Installation\n\n"
        guide += "Install all required libraries:\n\n```bash\n"
        for lib_name in library_docs.keys():
            guide += f"pip install {lib_name}\n"
        guide += "```\n\n"

        # Basic usage section
        guide += "## Basic Usage\n\n"
        guide += "Here's a simple example to get you started:\n\n```python\n"
        for lib_name in list(library_docs.keys())[:3]:  # Show first 3 libraries
            guide += f"import {lib_name}\n"
        guide += "\n# Your code here\n```\n\n"

        # Next steps
        guide += "## Next Steps\n\n"
        guide += "- Check individual library documentation for detailed usage\n"
        guide += "- Review integration examples for common patterns\n"
        guide += "- See troubleshooting section for common issues\n"

        return guide

    def _identify_common_patterns(
        self, library_docs: dict[str, dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Identify common usage patterns across libraries."""
        patterns = []

        # Analyze API references for common patterns
        all_apis = []
        for lib_doc in library_docs.values():
            api_ref = lib_doc.get("api_reference", [])
            if isinstance(api_ref, list):
                all_apis.extend(api_ref)

        # Look for common method names
        method_counts = {}
        for api in all_apis:
            if isinstance(api, str):
                methods = re.findall(r"\b\w+\(\)", api)
                for method in methods:
                    method_counts[method] = method_counts.get(method, 0) + 1

        # Identify patterns
        common_methods = {
            method: count for method, count in method_counts.items() if count > 1
        }

        if common_methods:
            patterns.append(
                {
                    "type": "common_methods",
                    "description": "Methods that appear across multiple libraries",
                    "items": list(common_methods.keys()),
                }
            )

        return patterns

    def _generate_troubleshooting(
        self, library_docs: dict[str, dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Generate troubleshooting guide for the project."""
        issues = []

        # Generic issues based on library count
        if len(library_docs) > 5:
            issues.append(
                {
                    "problem": "Import errors with multiple libraries",
                    "solution": "Check for naming conflicts and ensure all libraries are properly installed",
                    "category": "imports",
                }
            )

        # Library-specific issues
        library_names = list(library_docs.keys())

        if any(
            "async" in lib_doc.get("content", "").lower()
            for lib_doc in library_docs.values()
        ):
            issues.append(
                {
                    "problem": "Mixing async and sync code",
                    "solution": "Use asyncio.run() for async functions or ensure consistent async/await usage",
                    "category": "async",
                }
            )

        if "requests" in library_names and any(
            "async" in name for name in library_names
        ):
            issues.append(
                {
                    "problem": "Using requests in async context",
                    "solution": "Consider using httpx or aiohttp for async HTTP requests instead of requests",
                    "category": "http",
                }
            )

        return issues

    def _categorize_libraries(
        self, library_docs: dict[str, dict[str, Any]]
    ) -> dict[str, list[str]]:
        """Categorize libraries by their primary function."""
        categories = {
            "web_development": [],
            "data_processing": [],
            "testing": [],
            "utilities": [],
            "other": [],
        }

        for lib_name, lib_doc in library_docs.items():
            content = lib_doc.get("content", "").lower()

            if any(
                keyword in content
                for keyword in ["web", "http", "api", "server", "framework"]
            ):
                categories["web_development"].append(lib_name)
            elif any(
                keyword in content
                for keyword in ["data", "analysis", "numpy", "pandas"]
            ):
                categories["data_processing"].append(lib_name)
            elif any(keyword in content for keyword in ["test", "mock", "pytest"]):
                categories["testing"].append(lib_name)
            elif any(keyword in content for keyword in ["util", "tool", "helper"]):
                categories["utilities"].append(lib_name)
            else:
                categories["other"].append(lib_name)

        return categories
