#!/usr/bin/env python3
"""
Multi-Library Crawler for Comprehensive Documentation

Crawls documentation for multiple libraries and generates unified documentation.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from processors.dependency_parser import DependencyParser

logger = logging.getLogger(__name__)


class MultiLibraryCrawler:
    """Crawler for handling multiple library documentation simultaneously."""

    def __init__(self, max_concurrent: int = 5):
        """
        Initialize the multi-library crawler.

        Args:
            max_concurrent: Maximum number of concurrent crawling operations
        """
        self.max_concurrent = max_concurrent
        self.dependency_parser = DependencyParser()
        self.crawl_results = {}

    async def crawl_dependencies(
        self, dependencies: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Crawl documentation for multiple dependencies.

        Args:
            dependencies: List of dependency dictionaries from DependencyParser

        Returns:
            Dictionary mapping library names to crawl results
        """
        results = {}

        # Create semaphore to limit concurrent operations
        semaphore = asyncio.Semaphore(self.max_concurrent)

        # Create crawling tasks for each dependency
        tasks = []
        for dependency in dependencies:
            task = self._crawl_single_dependency(semaphore, dependency)
            tasks.append(task)

        # Execute all crawling tasks concurrently
        crawl_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for i, result in enumerate(crawl_results):
            dependency = dependencies[i]
            library_name = dependency["name"]

            if isinstance(result, Exception):
                logger.error(f"Failed to crawl {library_name}: {result}")
                results[library_name] = {
                    "status": "error",
                    "error": str(result),
                    "dependency_info": dependency,
                }
            else:
                results[library_name] = result

        self.crawl_results = results
        return results

    async def _crawl_single_dependency(
        self, semaphore: asyncio.Semaphore, dependency: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Crawl documentation for a single dependency.

        Args:
            semaphore: Semaphore for limiting concurrent operations
            dependency: Single dependency dictionary

        Returns:
            Crawl result dictionary
        """
        async with semaphore:
            library_name = dependency["name"]
            library_type = dependency["type"]

            logger.info(f"Starting crawl for {library_name} ({library_type})")

            try:
                # Import search functions dynamically to avoid circular imports
                if library_type == "python":
                    from run_gui import get_package_docs, search_duckduckgo

                    # Try PyPI first
                    package_info = await get_package_docs(library_name)
                    documentation_urls = []

                    if "docs" in package_info:
                        documentation_urls.extend(package_info["docs"])

                    # Fallback to DuckDuckGo search
                    if not documentation_urls:
                        ddg_results = await search_duckduckgo(
                            f"{library_name} documentation"
                        )
                        documentation_urls.extend(ddg_results[:3])  # Take top 3 results

                elif library_type == "javascript":
                    from run_gui import search_duckduckgo

                    # Search for npm package documentation
                    search_terms = [
                        f"{library_name} npm documentation",
                        f"{library_name} javascript docs",
                        f"{library_name} js library",
                    ]

                    documentation_urls = []
                    for term in search_terms:
                        results = await search_duckduckgo(term)
                        documentation_urls.extend(results[:2])  # Take top 2 per search
                        if len(documentation_urls) >= 5:  # Limit total results
                            break

                else:
                    # Generic search for other types
                    from run_gui import search_duckduckgo

                    documentation_urls = await search_duckduckgo(
                        f"{library_name} documentation"
                    )

                return {
                    "status": "success",
                    "library_name": library_name,
                    "dependency_info": dependency,
                    "documentation_urls": documentation_urls[:5],  # Limit to top 5
                    "crawl_timestamp": asyncio.get_event_loop().time(),
                }

            except Exception as e:
                logger.error(f"Error crawling {library_name}: {e}")
                return {
                    "status": "error",
                    "library_name": library_name,
                    "dependency_info": dependency,
                    "error": str(e),
                    "documentation_urls": [],
                }

    async def generate_unified_docs(
        self, crawl_results: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        Generate unified documentation from multiple library crawl results.

        Args:
            crawl_results: Optional crawl results, uses self.crawl_results if not provided

        Returns:
            Unified documentation dictionary
        """
        if crawl_results is None:
            crawl_results = self.crawl_results

        if not crawl_results:
            raise ValueError(
                "No crawl results available for unified documentation generation"
            )

        # Extract successful crawls
        successful_crawls = {
            name: result
            for name, result in crawl_results.items()
            if result.get("status") == "success"
        }

        if not successful_crawls:
            return {
                "status": "error",
                "message": "No successful crawls to generate unified documentation",
                "failed_libraries": list(crawl_results.keys()),
            }

        # Generate unified documentation structure
        unified_docs = {
            "overview": self._generate_project_overview(successful_crawls),
            "libraries": self._organize_library_docs(successful_crawls),
            "integration_examples": self._generate_integration_examples(
                successful_crawls
            ),
            "compatibility_matrix": self._generate_compatibility_matrix(
                successful_crawls
            ),
            "dependency_graph": self.create_dependency_graph(successful_crawls),
            "quick_start_guide": self._generate_quick_start_guide(successful_crawls),
            "troubleshooting": self._generate_troubleshooting_section(
                successful_crawls
            ),
        }

        return unified_docs

    def create_dependency_graph(self, crawl_results: dict[str, Any]) -> dict[str, Any]:
        """
        Create a dependency relationship graph.

        Args:
            crawl_results: Results from crawling multiple libraries

        Returns:
            Dependency graph structure
        """
        nodes = []
        edges = []

        # Create nodes for each library
        for library_name, result in crawl_results.items():
            if result.get("status") == "success":
                dependency_info = result.get("dependency_info", {})

                node = {
                    "id": library_name,
                    "name": library_name,
                    "type": dependency_info.get("type", "unknown"),
                    "version": dependency_info.get("version", ""),
                    "dev": dependency_info.get("dev", False),
                    "documentation_count": len(result.get("documentation_urls", [])),
                }
                nodes.append(node)

        # For now, create a simple graph structure
        # In a more advanced implementation, we would analyze actual dependencies
        graph = {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "total_libraries": len(nodes),
                "library_types": list(set(node["type"] for node in nodes)),
                "has_dev_dependencies": any(node["dev"] for node in nodes),
            },
        }

        return graph

    def _generate_project_overview(self, crawl_results: dict[str, Any]) -> str:
        """Generate a project overview from multiple libraries."""
        library_count = len(crawl_results)
        library_types = set()

        for result in crawl_results.values():
            dep_info = result.get("dependency_info", {})
            library_types.add(dep_info.get("type", "unknown"))

        overview = f"""
# Project Documentation Overview

This project uses {library_count} libraries across {len(library_types)} different ecosystems:
{', '.join(library_types)}.

## Libraries Included:
"""

        for library_name, result in crawl_results.items():
            dep_info = result.get("dependency_info", {})
            lib_type = dep_info.get("type", "unknown")
            version = dep_info.get("version", "latest")
            doc_count = len(result.get("documentation_urls", []))

            overview += f"- **{library_name}** ({lib_type}) - Version: {version} - {doc_count} documentation sources\n"

        return overview

    def _organize_library_docs(self, crawl_results: dict[str, Any]) -> dict[str, Any]:
        """Organize documentation by library."""
        organized = {}

        for library_name, result in crawl_results.items():
            organized[library_name] = {
                "name": library_name,
                "type": result.get("dependency_info", {}).get("type", "unknown"),
                "version": result.get("dependency_info", {}).get("version", ""),
                "documentation_urls": result.get("documentation_urls", []),
                "status": result.get("status", "unknown"),
            }

        return organized

    def _generate_integration_examples(
        self, crawl_results: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Generate examples showing how libraries work together."""
        examples = []

        # Get library names and types
        libraries = []
        for library_name, result in crawl_results.items():
            dep_info = result.get("dependency_info", {})
            libraries.append(
                {"name": library_name, "type": dep_info.get("type", "unknown")}
            )

        # Generate integration examples based on common patterns
        python_libs = [lib for lib in libraries if lib["type"] == "python"]
        js_libs = [lib for lib in libraries if lib["type"] == "javascript"]

        if len(python_libs) >= 2:
            # Create Python integration example
            lib1, lib2 = python_libs[0], python_libs[1]
            examples.append(
                {
                    "title": f'Integrating {lib1["name"]} with {lib2["name"]}',
                    "description": f'Example showing how to use {lib1["name"]} and {lib2["name"]} together',
                    "code": f"""
import {lib1["name"]}
import {lib2["name"]}

# Example integration code
# This is a generated example - refer to individual library docs for specifics
""",
                    "language": "python",
                    "libraries": [lib1["name"], lib2["name"]],
                }
            )

        if len(js_libs) >= 2:
            # Create JavaScript integration example
            lib1, lib2 = js_libs[0], js_libs[1]
            examples.append(
                {
                    "title": f'Using {lib1["name"]} with {lib2["name"]}',
                    "description": f'JavaScript example combining {lib1["name"]} and {lib2["name"]}',
                    "code": f"""
const {lib1["name"].replace('-', '_')} = require('{lib1["name"]}');
const {lib2["name"].replace('-', '_')} = require('{lib2["name"]}');

// Example integration code
// This is a generated example - refer to individual library docs for specifics
""",
                    "language": "javascript",
                    "libraries": [lib1["name"], lib2["name"]],
                }
            )

        return examples

    def _generate_compatibility_matrix(
        self, crawl_results: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate a compatibility matrix for the libraries."""
        libraries = list(crawl_results.keys())

        # Simple compatibility matrix (in real implementation, this would check actual compatibility)
        matrix = {}
        for lib1 in libraries:
            matrix[lib1] = {}
            for lib2 in libraries:
                if lib1 == lib2:
                    matrix[lib1][lib2] = "self"
                else:
                    # For now, assume compatibility based on type
                    type1 = crawl_results[lib1].get("dependency_info", {}).get("type")
                    type2 = crawl_results[lib2].get("dependency_info", {}).get("type")

                    if type1 == type2:
                        matrix[lib1][lib2] = "compatible"
                    else:
                        matrix[lib1][lib2] = "different_ecosystem"

        return {
            "matrix": matrix,
            "legend": {
                "self": "Same library",
                "compatible": "Likely compatible (same ecosystem)",
                "different_ecosystem": "Different ecosystem",
                "unknown": "Compatibility unknown",
            },
        }

    def _generate_quick_start_guide(self, crawl_results: dict[str, Any]) -> str:
        """Generate a quick start guide for the project."""
        guide = "# Quick Start Guide\n\n"

        # Group by type
        by_type = {}
        for library_name, result in crawl_results.items():
            lib_type = result.get("dependency_info", {}).get("type", "unknown")
            if lib_type not in by_type:
                by_type[lib_type] = []
            by_type[lib_type].append(library_name)

        # Generate installation instructions by type
        for lib_type, libraries in by_type.items():
            guide += f"## {lib_type.title()} Dependencies\n\n"

            if lib_type == "python":
                guide += "Install Python dependencies:\n```bash\n"
                for lib in libraries:
                    guide += f"pip install {lib}\n"
                guide += "```\n\n"

            elif lib_type == "javascript":
                guide += "Install JavaScript dependencies:\n```bash\n"
                for lib in libraries:
                    guide += f"npm install {lib}\n"
                guide += "```\n\n"

            elif lib_type == "rust":
                guide += "Add to Cargo.toml:\n```toml\n[dependencies]\n"
                for lib in libraries:
                    guide += f'{lib} = "latest"\n'
                guide += "```\n\n"

        return guide

    def _generate_troubleshooting_section(
        self, crawl_results: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Generate common troubleshooting tips."""
        issues = []

        # Generic troubleshooting based on library types
        library_types = set()
        for result in crawl_results.values():
            lib_type = result.get("dependency_info", {}).get("type", "unknown")
            library_types.add(lib_type)

        if "python" in library_types:
            issues.append(
                {
                    "problem": "Python package installation fails",
                    "solution": "Try upgrading pip: `pip install --upgrade pip`",
                    "category": "installation",
                }
            )

        if "javascript" in library_types:
            issues.append(
                {
                    "problem": "npm install fails with permission errors",
                    "solution": "Use `npm install --prefix ./local` or configure npm properly",
                    "category": "installation",
                }
            )

        return issues
