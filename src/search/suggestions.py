#!/usr/bin/env python3
"""
Search Suggestions and Autocomplete for Advanced Search

Provides intelligent search suggestions and autocomplete functionality.
"""

import logging
from collections import Counter
from typing import Any

logger = logging.getLogger(__name__)


class SearchSuggestions:
    """Engine for providing search suggestions and autocomplete."""

    def __init__(self):
        """Initialize the search suggestions engine."""
        self.search_history = []
        self.popular_terms = Counter()
        self.library_names = set()
        self.common_queries = [
            "web development",
            "data science",
            "machine learning",
            "api",
            "testing",
            "database",
            "authentication",
            "visualization",
            "http client",
            "web framework",
            "async programming",
        ]

    def add_search_term(self, term: str):
        """
        Add a search term to the history.

        Args:
            term: Search term to add
        """
        term = term.strip().lower()
        if term:
            self.search_history.append(term)
            # Update popular terms
            words = term.split()
            for word in words:
                if len(word) > 2:  # Ignore very short words
                    self.popular_terms[word] += 1

    def add_library_name(self, library_name: str):
        """
        Add a library name to the suggestions database.

        Args:
            library_name: Name of the library
        """
        self.library_names.add(library_name.lower())

    def get_suggestions(self, partial_query: str, limit: int = 10) -> list[str]:
        """
        Get search suggestions for a partial query.

        Args:
            partial_query: Partial search query
            limit: Maximum number of suggestions to return

        Returns:
            List of suggested search terms
        """
        partial_lower = partial_query.lower().strip()
        if not partial_lower:
            return self.common_queries[:limit]

        suggestions = []

        # 1. Exact matches from search history
        for term in self.search_history:
            if term.startswith(partial_lower) and term not in suggestions:
                suggestions.append(term)

        # 2. Library name matches
        for lib_name in self.library_names:
            if partial_lower in lib_name and lib_name not in suggestions:
                suggestions.append(lib_name)

        # 3. Common query matches
        for query in self.common_queries:
            if partial_lower in query.lower() and query not in suggestions:
                suggestions.append(query)

        # 4. Word-based suggestions
        words = partial_lower.split()
        if words:
            last_word = words[-1]
            for term, count in self.popular_terms.most_common(50):
                if term.startswith(last_word):
                    # Reconstruct the full suggestion
                    suggestion = " ".join(words[:-1] + [term])
                    if suggestion not in suggestions:
                        suggestions.append(suggestion)

        # 5. Fuzzy matches (simple edit distance)
        if len(suggestions) < limit:
            fuzzy_matches = self._get_fuzzy_matches(partial_lower)
            for match in fuzzy_matches:
                if match not in suggestions:
                    suggestions.append(match)

        # Sort by relevance and return top results
        suggestions = self._rank_suggestions(suggestions, partial_lower)
        return suggestions[:limit]

    def get_popular_searches(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get most popular search terms.

        Args:
            limit: Maximum number of terms to return

        Returns:
            List of popular search terms with counts
        """
        # Count full search terms
        term_counts = Counter(self.search_history)
        popular = []

        for term, count in term_counts.most_common(limit):
            popular.append(
                {
                    "term": term,
                    "count": count,
                    "percentage": round((count / len(self.search_history)) * 100, 1)
                    if self.search_history
                    else 0,
                }
            )

        return popular

    def get_trending_searches(self, days: int = 7, limit: int = 10) -> list[str]:
        """
        Get trending search terms (mock implementation).

        Args:
            days: Number of days to consider for trending
            limit: Maximum number of trending terms

        Returns:
            List of trending search terms
        """
        # For now, return a mix of popular terms and common queries
        trending = []

        # Add some popular terms
        for term, count in self.popular_terms.most_common(5):
            if len(trending) < limit:
                trending.append(term)

        # Add some common queries
        for query in self.common_queries:
            if len(trending) < limit and query not in trending:
                trending.append(query)

        return trending[:limit]

    def get_related_suggestions(self, query: str, limit: int = 5) -> list[str]:
        """
        Get suggestions related to a specific query.

        Args:
            query: Base query to find related suggestions for
            limit: Maximum number of related suggestions

        Returns:
            List of related search suggestions
        """
        query_lower = query.lower()
        related = []

        # Find searches that contain similar words
        query_words = set(query_lower.split())

        for term in self.search_history:
            term_words = set(term.split())
            # Check for word overlap
            overlap = len(query_words & term_words)
            if overlap > 0 and term != query_lower and term not in related:
                related.append(term)

        # Add library names that might be related
        for lib_name in self.library_names:
            if (
                any(word in lib_name for word in query_words)
                and lib_name not in related
            ):
                related.append(lib_name)

        return related[:limit]

    def _get_fuzzy_matches(
        self, partial_query: str, max_distance: int = 2
    ) -> list[str]:
        """Get fuzzy matches using simple edit distance."""
        fuzzy_matches = []

        # Check against library names
        for lib_name in self.library_names:
            if self._edit_distance(partial_query, lib_name) <= max_distance:
                fuzzy_matches.append(lib_name)

        # Check against popular terms
        for term in self.popular_terms:
            if self._edit_distance(partial_query, term) <= max_distance:
                fuzzy_matches.append(term)

        return fuzzy_matches

    def _edit_distance(self, s1: str, s2: str) -> int:
        """Calculate simple edit distance between two strings."""
        if len(s1) > len(s2):
            s1, s2 = s2, s1

        distances = range(len(s1) + 1)
        for i2, c2 in enumerate(s2):
            distances_ = [i2 + 1]
            for i1, c1 in enumerate(s1):
                if c1 == c2:
                    distances_.append(distances[i1])
                else:
                    distances_.append(
                        1 + min((distances[i1], distances[i1 + 1], distances_[-1]))
                    )
            distances = distances_

        return distances[-1]

    def _rank_suggestions(
        self, suggestions: list[str], partial_query: str
    ) -> list[str]:
        """Rank suggestions by relevance to the partial query."""

        def relevance_score(suggestion: str) -> tuple:
            # Exact prefix match gets highest score
            starts_with = suggestion.startswith(partial_query)

            # Contains the partial query
            contains = partial_query in suggestion

            # Length (shorter is often better for suggestions)
            length = len(suggestion)

            # Popularity (if we have data)
            popularity = self.popular_terms.get(suggestion, 0)

            # Return tuple for sorting (higher values first, except length)
            return (starts_with, contains, popularity, -length)

        return sorted(suggestions, key=relevance_score, reverse=True)
