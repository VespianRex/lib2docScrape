#!/usr/bin/env python3
"""
Tag-Based Search Engine for Documentation Discovery

Provides search functionality based on tags and categories.
"""

import logging
from collections import defaultdict
from typing import Any

logger = logging.getLogger(__name__)


class TagSearchEngine:
    """Search engine for finding libraries based on tags and categories."""

    def __init__(self):
        """Initialize the tag search engine."""
        self.documents = {}
        self.tag_index = defaultdict(list)  # tag -> [library_names]
        self.library_tags = defaultdict(set)  # library_name -> {tags}

    def index_documents(
        self, documentation_content: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Index documentation content for tag-based search.

        Args:
            documentation_content: Dictionary mapping library names to their documentation

        Returns:
            Indexing result with status and statistics
        """
        try:
            self.documents = documentation_content
            self.tag_index.clear()
            self.library_tags.clear()

            for library_name, doc_data in documentation_content.items():
                # Get tags from document
                tags = doc_data.get("tags", [])

                # Extract additional tags from content
                extracted_tags = self._extract_tags_from_content(doc_data)
                all_tags = set(tags + extracted_tags)

                # Index tags
                for tag in all_tags:
                    tag_lower = tag.lower()
                    self.tag_index[tag_lower].append(library_name)
                    self.library_tags[library_name].add(tag_lower)

            return {
                "status": "success",
                "indexed_count": len(documentation_content),
                "total_tags": len(self.tag_index),
                "indexed_libraries": list(documentation_content.keys()),
            }

        except Exception as e:
            logger.error(f"Error indexing documents for tag search: {e}")
            return {"status": "error", "error": str(e), "indexed_count": 0}

    def search_by_tag(self, tag: str) -> list[dict[str, Any]]:
        """
        Search for libraries that have a specific tag.

        Args:
            tag: Tag to search for

        Returns:
            List of libraries with the specified tag
        """
        tag_lower = tag.lower()

        if tag_lower not in self.tag_index:
            return []

        results = []
        for library_name in self.tag_index[tag_lower]:
            if library_name in self.documents:
                doc_data = self.documents[library_name]
                results.append(
                    {
                        "library": library_name,
                        "tags": list(self.library_tags[library_name]),
                        "description": doc_data.get("content", "")[:200] + "...",
                        "difficulty": doc_data.get("difficulty", "unknown"),
                        "relevance_score": self._calculate_tag_relevance(
                            library_name, tag_lower
                        ),
                    }
                )

        # Sort by relevance score
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results

    def search_by_multiple_tags(
        self, tags: list[str], match_type: str = "any"
    ) -> list[dict[str, Any]]:
        """
        Search for libraries that match multiple tags.

        Args:
            tags: List of tags to search for
            match_type: 'any' (OR) or 'all' (AND) matching

        Returns:
            List of libraries matching the tag criteria
        """
        if not tags:
            return []

        tags_lower = [tag.lower() for tag in tags]

        if match_type == "all":
            # Find libraries that have ALL tags
            matching_libraries = None
            for tag in tags_lower:
                tag_libraries = set(self.tag_index.get(tag, []))
                if matching_libraries is None:
                    matching_libraries = tag_libraries
                else:
                    matching_libraries &= tag_libraries

            matching_libraries = matching_libraries or set()
        else:
            # Find libraries that have ANY of the tags
            matching_libraries = set()
            for tag in tags_lower:
                matching_libraries.update(self.tag_index.get(tag, []))

        results = []
        for library_name in matching_libraries:
            if library_name in self.documents:
                doc_data = self.documents[library_name]

                # Calculate how many tags match
                library_tag_set = self.library_tags[library_name]
                matched_tags = [tag for tag in tags_lower if tag in library_tag_set]
                match_ratio = len(matched_tags) / len(tags_lower)

                results.append(
                    {
                        "library": library_name,
                        "tags": list(library_tag_set),
                        "matched_tags": matched_tags,
                        "match_ratio": match_ratio,
                        "description": doc_data.get("content", "")[:200] + "...",
                        "difficulty": doc_data.get("difficulty", "unknown"),
                        "relevance_score": match_ratio,
                    }
                )

        # Sort by match ratio and relevance
        results.sort(
            key=lambda x: (x["match_ratio"], x["relevance_score"]), reverse=True
        )
        return results

    def get_popular_tags(self, limit: int = 20) -> list[dict[str, Any]]:
        """
        Get the most popular tags across all libraries.

        Args:
            limit: Maximum number of tags to return

        Returns:
            List of popular tags with usage counts
        """
        tag_counts = {}
        for tag, libraries in self.tag_index.items():
            tag_counts[tag] = len(libraries)

        # Sort by count
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)

        return [
            {
                "tag": tag,
                "count": count,
                "libraries": self.tag_index[tag][:5],  # Show first 5 libraries
            }
            for tag, count in sorted_tags[:limit]
        ]

    def get_related_tags(self, tag: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get tags that are commonly used together with the given tag.

        Args:
            tag: Reference tag
            limit: Maximum number of related tags to return

        Returns:
            List of related tags with co-occurrence scores
        """
        tag_lower = tag.lower()

        if tag_lower not in self.tag_index:
            return []

        # Get libraries that have this tag
        libraries_with_tag = set(self.tag_index[tag_lower])

        # Count co-occurring tags
        cooccurrence_counts = defaultdict(int)
        for library_name in libraries_with_tag:
            for other_tag in self.library_tags[library_name]:
                if other_tag != tag_lower:
                    cooccurrence_counts[other_tag] += 1

        # Calculate co-occurrence scores
        total_libraries_with_tag = len(libraries_with_tag)
        related_tags = []

        for other_tag, count in cooccurrence_counts.items():
            cooccurrence_score = count / total_libraries_with_tag
            related_tags.append(
                {
                    "tag": other_tag,
                    "cooccurrence_score": round(cooccurrence_score, 2),
                    "cooccurrence_count": count,
                    "total_usage": len(self.tag_index[other_tag]),
                }
            )

        # Sort by co-occurrence score
        related_tags.sort(key=lambda x: x["cooccurrence_score"], reverse=True)
        return related_tags[:limit]

    def get_tag_suggestions(self, partial_tag: str) -> list[str]:
        """
        Get tag suggestions based on partial input.

        Args:
            partial_tag: Partial tag string

        Returns:
            List of suggested tags
        """
        partial_lower = partial_tag.lower()
        suggestions = []

        for tag in self.tag_index.keys():
            if partial_lower in tag:
                suggestions.append(tag)

        # Sort by relevance (exact matches first, then by length)
        suggestions.sort(key=lambda x: (not x.startswith(partial_lower), len(x)))
        return suggestions[:10]

    def analyze_library_tags(self, library_name: str) -> dict[str, Any]:
        """
        Analyze tags for a specific library.

        Args:
            library_name: Name of the library to analyze

        Returns:
            Analysis of the library's tags
        """
        if library_name not in self.library_tags:
            return {"error": f"Library {library_name} not found"}

        library_tag_set = self.library_tags[library_name]

        # Get tag popularity scores
        tag_analysis = []
        for tag in library_tag_set:
            tag_popularity = len(self.tag_index[tag])
            tag_analysis.append(
                {
                    "tag": tag,
                    "popularity": tag_popularity,
                    "rarity_score": 1.0 / tag_popularity if tag_popularity > 0 else 0,
                }
            )

        # Sort by rarity (unique tags first)
        tag_analysis.sort(key=lambda x: x["rarity_score"], reverse=True)

        # Get related libraries based on tag similarity
        related_libraries = self._find_related_libraries_by_tags(library_name)

        return {
            "library": library_name,
            "tags": list(library_tag_set),
            "tag_count": len(library_tag_set),
            "tag_analysis": tag_analysis,
            "unique_tags": [t["tag"] for t in tag_analysis if t["popularity"] == 1],
            "common_tags": [t["tag"] for t in tag_analysis if t["popularity"] > 5],
            "related_libraries": related_libraries[:5],
        }

    def _extract_tags_from_content(self, doc_data: dict[str, Any]) -> list[str]:
        """Extract additional tags from documentation content."""
        content = doc_data.get("content", "").lower()

        # Common technology tags
        tech_tags = [
            "web",
            "api",
            "http",
            "rest",
            "json",
            "xml",
            "database",
            "sql",
            "machine learning",
            "ml",
            "ai",
            "data science",
            "visualization",
            "testing",
            "security",
            "authentication",
            "async",
            "sync",
            "framework",
            "library",
            "tool",
            "cli",
            "gui",
            "desktop",
            "mobile",
            "cloud",
            "aws",
            "docker",
            "kubernetes",
        ]

        extracted = []
        for tag in tech_tags:
            if tag in content:
                extracted.append(tag)

        return extracted

    def _calculate_tag_relevance(self, library_name: str, tag: str) -> float:
        """Calculate how relevant a tag is for a library."""
        # Base relevance
        relevance = 1.0

        # Boost if tag appears in library name
        if tag in library_name.lower():
            relevance += 0.5

        # Boost based on tag rarity (rarer tags are more specific)
        tag_popularity = len(self.tag_index[tag])
        if tag_popularity == 1:
            relevance += 0.3  # Unique tag
        elif tag_popularity <= 3:
            relevance += 0.2  # Rare tag

        # Check if tag appears in content
        if library_name in self.documents:
            content = self.documents[library_name].get("content", "").lower()
            if tag in content:
                relevance += 0.2

        return relevance

    def _find_related_libraries_by_tags(
        self, library_name: str
    ) -> list[dict[str, Any]]:
        """Find libraries with similar tag profiles."""
        if library_name not in self.library_tags:
            return []

        reference_tags = self.library_tags[library_name]
        similarities = []

        for other_library, other_tags in self.library_tags.items():
            if other_library == library_name:
                continue

            # Calculate Jaccard similarity
            intersection = len(reference_tags & other_tags)
            union = len(reference_tags | other_tags)

            if union > 0:
                similarity = intersection / union
                if similarity > 0:
                    similarities.append(
                        {
                            "library": other_library,
                            "similarity": round(similarity, 2),
                            "common_tags": list(reference_tags & other_tags),
                            "common_tag_count": intersection,
                        }
                    )

        # Sort by similarity
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        return similarities
