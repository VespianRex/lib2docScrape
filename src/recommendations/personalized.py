#!/usr/bin/env python3
"""
Personalized Recommendations for Documentation Discovery

Provides personalized library recommendations based on user history and preferences.
"""

import logging
from collections import defaultdict
from typing import Any

logger = logging.getLogger(__name__)


class PersonalizedRecommendations:
    """Engine for generating personalized library recommendations."""

    def __init__(self):
        """Initialize the personalized recommendations engine."""
        self.library_relationships = {
            # Web development ecosystem
            "requests": ["httpx", "aiohttp", "urllib3", "fastapi", "flask"],
            "fastapi": ["starlette", "pydantic", "uvicorn", "requests", "sqlalchemy"],
            "flask": ["jinja2", "werkzeug", "requests", "sqlalchemy", "wtforms"],
            "django": ["djangorestframework", "celery", "psycopg2", "pillow"],
            # Data science ecosystem
            "pandas": ["numpy", "matplotlib", "seaborn", "scikit-learn", "jupyter"],
            "numpy": ["scipy", "matplotlib", "pandas", "scikit-learn"],
            "matplotlib": ["seaborn", "plotly", "pandas", "numpy"],
            "scikit-learn": ["pandas", "numpy", "matplotlib", "scipy"],
            # Testing ecosystem
            "pytest": ["pytest-cov", "pytest-mock", "tox", "black", "flake8"],
            "unittest": ["mock", "coverage", "nose2"],
            # Async ecosystem
            "asyncio": ["aiohttp", "aiofiles", "asyncpg", "uvloop"],
            "aiohttp": ["aiofiles", "asyncpg", "requests"],
        }

        self.category_mappings = {
            "web": ["requests", "fastapi", "flask", "django", "aiohttp", "httpx"],
            "data": ["pandas", "numpy", "matplotlib", "seaborn", "scikit-learn"],
            "testing": ["pytest", "unittest", "mock", "coverage"],
            "async": ["asyncio", "aiohttp", "aiofiles", "uvloop"],
            "database": ["sqlalchemy", "psycopg2", "pymongo", "redis"],
            "api": ["fastapi", "flask", "django", "requests", "httpx"],
        }

    def get_recommendations(
        self, user_history: dict[str, list[str]], limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Get personalized recommendations based on user history.

        Args:
            user_history: Dictionary with user interaction history
                         {'searched': [...], 'viewed': [...], 'downloaded': [...]}
            limit: Maximum number of recommendations to return

        Returns:
            List of recommended libraries with scores and reasons
        """
        try:
            # Combine all user interactions
            all_interactions = []
            weights = {"searched": 1.0, "viewed": 2.0, "downloaded": 3.0}

            for interaction_type, libraries in user_history.items():
                weight = weights.get(interaction_type, 1.0)
                for library in libraries:
                    all_interactions.append((library.lower(), weight))

            if not all_interactions:
                return self._get_default_recommendations(limit)

            # Calculate recommendation scores
            recommendation_scores = defaultdict(float)
            recommendation_reasons = defaultdict(list)

            # Get recommendations based on library relationships
            for library, weight in all_interactions:
                related_libs = self.library_relationships.get(library, [])
                for related_lib in related_libs:
                    if related_lib.lower() not in [
                        lib.lower() for lib, _ in all_interactions
                    ]:
                        recommendation_scores[related_lib] += weight * 0.8
                        recommendation_reasons[related_lib].append(
                            f"Related to {library}"
                        )

            # Get recommendations based on categories
            user_categories = self._identify_user_categories(all_interactions)
            for category in user_categories:
                category_libs = self.category_mappings.get(category, [])
                for lib in category_libs:
                    if lib.lower() not in [
                        library.lower() for library, _ in all_interactions
                    ]:
                        recommendation_scores[lib] += 0.5
                        recommendation_reasons[lib].append(f"Popular in {category}")

            # Convert to recommendation list
            recommendations = []
            for library, score in recommendation_scores.items():
                recommendations.append(
                    {
                        "library": library,
                        "score": round(score, 2),
                        "reasons": recommendation_reasons[library],
                        "category": self._get_library_category(library),
                        "confidence": min(score / 3.0, 1.0),  # Normalize confidence
                    }
                )

            # Sort by score and return top recommendations
            recommendations.sort(key=lambda x: x["score"], reverse=True)
            return recommendations[:limit]

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return self._get_default_recommendations(limit)

    def get_similar_users_recommendations(
        self,
        user_history: dict[str, list[str]],
        all_users_data: list[dict[str, Any]],
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Get recommendations based on similar users' preferences.

        Args:
            user_history: Current user's history
            all_users_data: List of other users' data for comparison
            limit: Maximum number of recommendations

        Returns:
            List of recommendations based on similar users
        """
        try:
            current_user_libs = set()
            for libraries in user_history.values():
                current_user_libs.update(lib.lower() for lib in libraries)

            if not current_user_libs:
                return []

            # Find similar users
            similar_users = []
            for other_user in all_users_data:
                other_user_libs = set()
                for libraries in other_user.get("history", {}).values():
                    other_user_libs.update(lib.lower() for lib in libraries)

                # Calculate similarity (Jaccard index)
                intersection = len(current_user_libs & other_user_libs)
                union = len(current_user_libs | other_user_libs)

                if union > 0:
                    similarity = intersection / union
                    if similarity > 0.2:  # Minimum similarity threshold
                        similar_users.append((other_user, similarity))

            # Sort by similarity
            similar_users.sort(key=lambda x: x[1], reverse=True)

            # Get recommendations from similar users
            recommendations = defaultdict(float)
            for other_user, similarity in similar_users[:5]:  # Top 5 similar users
                for libraries in other_user.get("history", {}).values():
                    for lib in libraries:
                        if lib.lower() not in current_user_libs:
                            recommendations[lib] += similarity

            # Convert to recommendation list
            result = []
            for library, score in recommendations.items():
                result.append(
                    {
                        "library": library,
                        "score": round(score, 2),
                        "reason": "Used by similar users",
                        "category": self._get_library_category(library),
                    }
                )

            # Sort and return
            result.sort(key=lambda x: x["score"], reverse=True)
            return result[:limit]

        except Exception as e:
            logger.error(f"Error generating similar user recommendations: {e}")
            return []

    def get_trending_recommendations(
        self, user_categories: list[str], limit: int = 5
    ) -> list[dict[str, Any]]:
        """
        Get trending recommendations in user's areas of interest.

        Args:
            user_categories: List of categories user is interested in
            limit: Maximum number of recommendations

        Returns:
            List of trending recommendations
        """
        # Mock trending data - in real implementation, this would come from analytics
        trending_by_category = {
            "web": [
                {"library": "fastapi", "trend_score": 0.9},
                {"library": "httpx", "trend_score": 0.8},
                {"library": "starlette", "trend_score": 0.7},
            ],
            "data": [
                {"library": "polars", "trend_score": 0.9},
                {"library": "plotly", "trend_score": 0.8},
                {"library": "streamlit", "trend_score": 0.7},
            ],
            "testing": [
                {"library": "pytest-xdist", "trend_score": 0.8},
                {"library": "hypothesis", "trend_score": 0.7},
            ],
        }

        recommendations = []
        for category in user_categories:
            if category in trending_by_category:
                for item in trending_by_category[category]:
                    recommendations.append(
                        {
                            "library": item["library"],
                            "score": item["trend_score"],
                            "reason": f"Trending in {category}",
                            "category": category,
                            "trend_indicator": "📈",
                        }
                    )

        # Sort by trend score and return
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:limit]

    def _identify_user_categories(self, interactions: list[tuple]) -> list[str]:
        """Identify user's areas of interest based on interactions."""
        category_scores = defaultdict(float)

        for library, weight in interactions:
            for category, libs in self.category_mappings.items():
                if library in [lib.lower() for lib in libs]:
                    category_scores[category] += weight

        # Return categories with significant interest
        threshold = max(category_scores.values()) * 0.3 if category_scores else 0
        return [cat for cat, score in category_scores.items() if score >= threshold]

    def _get_library_category(self, library: str) -> str:
        """Get the primary category for a library."""
        library_lower = library.lower()

        for category, libs in self.category_mappings.items():
            if library_lower in [lib.lower() for lib in libs]:
                return category

        return "other"

    def _get_default_recommendations(self, limit: int) -> list[dict[str, Any]]:
        """Get default recommendations for new users."""
        default_recommendations = [
            {
                "library": "requests",
                "score": 1.0,
                "reasons": ["Popular HTTP library"],
                "category": "web",
            },
            {
                "library": "pandas",
                "score": 0.9,
                "reasons": ["Essential for data analysis"],
                "category": "data",
            },
            {
                "library": "pytest",
                "score": 0.8,
                "reasons": ["Standard testing framework"],
                "category": "testing",
            },
            {
                "library": "fastapi",
                "score": 0.8,
                "reasons": ["Modern web framework"],
                "category": "web",
            },
            {
                "library": "numpy",
                "score": 0.7,
                "reasons": ["Fundamental for scientific computing"],
                "category": "data",
            },
            {
                "library": "matplotlib",
                "score": 0.7,
                "reasons": ["Standard plotting library"],
                "category": "data",
            },
            {
                "library": "flask",
                "score": 0.6,
                "reasons": ["Lightweight web framework"],
                "category": "web",
            },
            {
                "library": "sqlalchemy",
                "score": 0.6,
                "reasons": ["Popular ORM"],
                "category": "database",
            },
        ]

        return default_recommendations[:limit]
