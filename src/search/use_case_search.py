#!/usr/bin/env python3
"""
Use Case Search Engine for Documentation Discovery

Provides search functionality based on specific use cases and application domains.
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class UseCaseSearchEngine:
    """Search engine for finding libraries based on use cases and application domains."""

    def __init__(self):
        """Initialize the use case search engine."""
        self.documents = {}
        self.use_case_patterns = {
            "web development": [
                "web",
                "http",
                "server",
                "api",
                "rest",
                "framework",
                "flask",
                "django",
                "fastapi",
                "web application",
                "web service",
                "endpoint",
                "route",
                "middleware",
            ],
            "data science": [
                "data",
                "analysis",
                "machine learning",
                "ml",
                "statistics",
                "numpy",
                "pandas",
                "visualization",
                "plot",
                "chart",
                "dataset",
                "model",
                "algorithm",
            ],
            "database": [
                "database",
                "sql",
                "orm",
                "query",
                "table",
                "record",
                "sqlalchemy",
                "mongodb",
                "postgresql",
                "mysql",
                "sqlite",
                "nosql",
            ],
            "testing": [
                "test",
                "testing",
                "unittest",
                "pytest",
                "mock",
                "assertion",
                "coverage",
                "test case",
                "test suite",
                "automation",
                "quality assurance",
            ],
            "networking": [
                "network",
                "socket",
                "tcp",
                "udp",
                "protocol",
                "client",
                "server",
                "connection",
                "request",
                "response",
                "http",
                "https",
            ],
            "file processing": [
                "file",
                "io",
                "read",
                "write",
                "parse",
                "csv",
                "json",
                "xml",
                "document",
                "text processing",
                "format",
                "encoding",
            ],
            "gui development": [
                "gui",
                "interface",
                "window",
                "button",
                "widget",
                "tkinter",
                "qt",
                "user interface",
                "desktop",
                "application",
                "form",
            ],
            "security": [
                "security",
                "encryption",
                "authentication",
                "authorization",
                "crypto",
                "hash",
                "password",
                "token",
                "ssl",
                "tls",
                "certificate",
            ],
            "image processing": [
                "image",
                "picture",
                "photo",
                "pixel",
                "filter",
                "resize",
                "crop",
                "opencv",
                "pillow",
                "graphics",
                "vision",
                "processing",
            ],
            "automation": [
                "automation",
                "script",
                "task",
                "schedule",
                "cron",
                "workflow",
                "batch",
                "process",
                "selenium",
                "scraping",
                "bot",
            ],
        }

    def index_documents(
        self, documentation_content: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Index documentation content for use case search.

        Args:
            documentation_content: Dictionary mapping library names to their documentation

        Returns:
            Indexing result with status and statistics
        """
        try:
            self.documents = documentation_content

            # Analyze each document for use case patterns
            for library_name, doc_data in documentation_content.items():
                doc_data["use_cases"] = self._extract_use_cases(doc_data)

            return {
                "status": "success",
                "indexed_count": len(documentation_content),
                "indexed_libraries": list(documentation_content.keys()),
            }

        except Exception as e:
            logger.error(f"Error indexing documents for use case search: {e}")
            return {"status": "error", "error": str(e), "indexed_count": 0}

    def search_by_use_case(self, use_case: str) -> list[dict[str, Any]]:
        """
        Search for libraries that match a specific use case.

        Args:
            use_case: Use case description (e.g., "web development", "data analysis")

        Returns:
            List of matching libraries with relevance scores
        """
        if not self.documents:
            logger.warning("No documents indexed for use case search")
            return []

        try:
            use_case_lower = use_case.lower()
            results = []

            # Find matching use case patterns
            matching_patterns = []
            for pattern_name, keywords in self.use_case_patterns.items():
                if any(keyword in use_case_lower for keyword in keywords):
                    matching_patterns.extend(keywords)
                if pattern_name in use_case_lower:
                    matching_patterns.extend(keywords)

            # If no patterns found, use the use case directly
            if not matching_patterns:
                matching_patterns = [use_case_lower]

            # Score each library
            for library_name, doc_data in self.documents.items():
                score = self._calculate_use_case_score(doc_data, matching_patterns)

                if score > 0:
                    results.append(
                        {
                            "library": library_name,
                            "use_case_score": score,
                            "matched_use_cases": doc_data.get("use_cases", []),
                            "description": doc_data.get("content", "")[:200] + "...",
                            "tags": doc_data.get("tags", []),
                        }
                    )

            # Sort by relevance score
            results.sort(key=lambda x: x["use_case_score"], reverse=True)
            return results

        except Exception as e:
            logger.error(f"Error searching by use case: {e}")
            return []

    def get_use_case_suggestions(self, partial_query: str) -> list[str]:
        """
        Get use case suggestions based on partial query.

        Args:
            partial_query: Partial use case query

        Returns:
            List of suggested use cases
        """
        partial_lower = partial_query.lower()
        suggestions = []

        # Find matching use case categories
        for use_case_name, keywords in self.use_case_patterns.items():
            if partial_lower in use_case_name or any(
                partial_lower in keyword for keyword in keywords
            ):
                suggestions.append(use_case_name)

        # Add specific keyword matches
        for use_case_name, keywords in self.use_case_patterns.items():
            for keyword in keywords:
                if partial_lower in keyword and keyword not in suggestions:
                    suggestions.append(keyword)

        return suggestions[:10]  # Limit to top 10 suggestions

    def analyze_library_use_cases(self, library_name: str) -> dict[str, Any]:
        """
        Analyze what use cases a specific library is good for.

        Args:
            library_name: Name of the library to analyze

        Returns:
            Analysis of the library's use cases
        """
        if library_name not in self.documents:
            return {"error": f"Library {library_name} not found"}

        doc_data = self.documents[library_name]
        use_cases = doc_data.get("use_cases", [])

        # Score against all use case patterns
        use_case_scores = {}
        for use_case_name, keywords in self.use_case_patterns.items():
            score = self._calculate_use_case_score(doc_data, keywords)
            if score > 0:
                use_case_scores[use_case_name] = score

        # Sort by score
        sorted_use_cases = sorted(
            use_case_scores.items(), key=lambda x: x[1], reverse=True
        )

        return {
            "library": library_name,
            "primary_use_cases": [uc for uc, score in sorted_use_cases[:3]],
            "all_use_case_scores": dict(sorted_use_cases),
            "detected_use_cases": use_cases,
            "recommendations": self._generate_use_case_recommendations(
                sorted_use_cases
            ),
        }

    def _extract_use_cases(self, doc_data: dict[str, Any]) -> list[str]:
        """Extract use cases from documentation content."""
        content = doc_data.get("content", "").lower()
        sections = doc_data.get("sections", [])
        tags = doc_data.get("tags", [])

        # Combine all text content
        all_text = content
        for section in sections:
            if isinstance(section, dict):
                all_text += " " + section.get("content", "")
            elif isinstance(section, str):
                all_text += " " + section

        # Add tags
        all_text += " " + " ".join(tags)

        detected_use_cases = []

        # Check against use case patterns
        for use_case_name, keywords in self.use_case_patterns.items():
            matches = sum(1 for keyword in keywords if keyword in all_text)
            if matches >= 2:  # Require at least 2 keyword matches
                detected_use_cases.append(use_case_name)

        return detected_use_cases

    def _calculate_use_case_score(
        self, doc_data: dict[str, Any], keywords: list[str]
    ) -> float:
        """Calculate how well a document matches a set of use case keywords."""
        content = doc_data.get("content", "").lower()
        sections = doc_data.get("sections", [])
        tags = doc_data.get("tags", [])

        # Combine all text content
        all_text = content
        for section in sections:
            if isinstance(section, dict):
                all_text += " " + section.get("content", "")
            elif isinstance(section, str):
                all_text += " " + section

        # Add tags with higher weight
        tag_text = " ".join(tags).lower()

        score = 0.0

        # Score based on keyword matches
        for keyword in keywords:
            # Content matches
            content_matches = len(
                re.findall(r"\b" + re.escape(keyword) + r"\b", all_text)
            )
            score += content_matches * 1.0

            # Tag matches (higher weight)
            tag_matches = len(re.findall(r"\b" + re.escape(keyword) + r"\b", tag_text))
            score += tag_matches * 2.0

        # Normalize by content length
        if len(all_text) > 0:
            score = score / (len(all_text) / 1000)  # Normalize per 1000 characters

        return min(score, 10.0)  # Cap at 10.0

    def _generate_use_case_recommendations(
        self, sorted_use_cases: list[tuple]
    ) -> list[str]:
        """Generate recommendations based on detected use cases."""
        if not sorted_use_cases:
            return ["This library appears to be general-purpose"]

        recommendations = []
        top_use_case = sorted_use_cases[0][0]

        recommendations.append(f"Best suited for {top_use_case}")

        if len(sorted_use_cases) > 1:
            secondary_use_cases = [uc for uc, score in sorted_use_cases[1:3]]
            recommendations.append(f"Also useful for {', '.join(secondary_use_cases)}")

        return recommendations
