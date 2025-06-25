#!/usr/bin/env python3
"""
Trending Libraries Tracker for Advanced Search & Discovery

Tracks library usage patterns, searches, views, and downloads to identify trending libraries.
"""

import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)


class TrendingLibrariesTracker:
    """Tracker for identifying trending libraries based on user interactions."""

    def __init__(self, data_file: Optional[str] = None):
        """
        Initialize the trending libraries tracker.

        Args:
            data_file: Optional file to persist tracking data
        """
        self.data_file = data_file

        # Storage for different types of interactions
        self.searches = defaultdict(list)  # library_name -> [timestamps]
        self.views = defaultdict(list)  # library_name -> [timestamps]
        self.downloads = defaultdict(list)  # library_name -> [timestamps]
        self.ratings = defaultdict(list)  # library_name -> [rating_values]

        # Load existing data if available
        if data_file:
            self._load_data()

    def record_search(self, library_name: str, timestamp: Optional[datetime] = None):
        """
        Record a search interaction for a library.

        Args:
            library_name: Name of the library that was searched
            timestamp: When the search occurred (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()

        self.searches[library_name].append(timestamp)
        self._save_data()
        logger.debug(f"Recorded search for {library_name}")

    def record_view(self, library_name: str, timestamp: Optional[datetime] = None):
        """
        Record a view interaction for a library.

        Args:
            library_name: Name of the library that was viewed
            timestamp: When the view occurred (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()

        self.views[library_name].append(timestamp)
        self._save_data()
        logger.debug(f"Recorded view for {library_name}")

    def record_download(self, library_name: str, timestamp: Optional[datetime] = None):
        """
        Record a download interaction for a library.

        Args:
            library_name: Name of the library that was downloaded
            timestamp: When the download occurred (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()

        self.downloads[library_name].append(timestamp)
        self._save_data()
        logger.debug(f"Recorded download for {library_name}")

    def record_rating(self, library_name: str, rating: float):
        """
        Record a rating for a library.

        Args:
            library_name: Name of the library that was rated
            rating: Rating value (typically 1-5)
        """
        self.ratings[library_name].append(rating)
        self._save_data()
        logger.debug(f"Recorded rating {rating} for {library_name}")

    def get_trending_libraries(
        self, period: str = "day", limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Get trending libraries for a specific time period.

        Args:
            period: Time period ('hour', 'day', 'week', 'month')
            limit: Maximum number of trending libraries to return

        Returns:
            List of trending libraries with scores and interaction counts
        """
        try:
            # Calculate time cutoff
            now = datetime.now()
            if period == "hour":
                cutoff = now - timedelta(hours=1)
            elif period == "day":
                cutoff = now - timedelta(days=1)
            elif period == "week":
                cutoff = now - timedelta(weeks=1)
            elif period == "month":
                cutoff = now - timedelta(days=30)
            else:
                cutoff = now - timedelta(days=1)  # Default to day

            # Calculate trending scores
            trending_scores = {}
            all_libraries = set()
            all_libraries.update(self.searches.keys())
            all_libraries.update(self.views.keys())
            all_libraries.update(self.downloads.keys())

            for library in all_libraries:
                score = self._calculate_trending_score(library, cutoff)
                if score > 0:
                    interactions = self._get_interaction_counts(library, cutoff)
                    trending_scores[library] = {
                        "score": score,
                        "interactions": interactions,
                        "total_interactions": sum(interactions.values()),
                    }

            # Sort by score and return top results
            sorted_trending = sorted(
                trending_scores.items(), key=lambda x: x[1]["score"], reverse=True
            )

            result = []
            for library, data in sorted_trending[:limit]:
                result.append(
                    {
                        "library": library,
                        "score": data["score"],
                        "interactions": data["interactions"],
                        "total_interactions": data["total_interactions"],
                        "period": period,
                    }
                )

            return result

        except Exception as e:
            logger.error(f"Error getting trending libraries: {e}")
            return []

    def get_library_analytics(self, library_name: str) -> dict[str, Any]:
        """
        Get detailed analytics for a specific library.

        Args:
            library_name: Name of the library to analyze

        Returns:
            Dictionary with detailed analytics
        """
        try:
            now = datetime.now()
            periods = {
                "hour": now - timedelta(hours=1),
                "day": now - timedelta(days=1),
                "week": now - timedelta(weeks=1),
                "month": now - timedelta(days=30),
            }

            analytics = {
                "library": library_name,
                "total_searches": len(self.searches[library_name]),
                "total_views": len(self.views[library_name]),
                "total_downloads": len(self.downloads[library_name]),
                "average_rating": self._calculate_average_rating(library_name),
                "periods": {},
            }

            # Calculate metrics for each period
            for period_name, cutoff in periods.items():
                interactions = self._get_interaction_counts(library_name, cutoff)
                score = self._calculate_trending_score(library_name, cutoff)

                analytics["periods"][period_name] = {
                    "interactions": interactions,
                    "trending_score": score,
                    "total_interactions": sum(interactions.values()),
                }

            return analytics

        except Exception as e:
            logger.error(f"Error getting library analytics: {e}")
            return {"error": str(e)}

    def get_trending_insights(self) -> dict[str, Any]:
        """
        Get insights about trending patterns.

        Returns:
            Dictionary with trending insights and statistics
        """
        try:
            now = datetime.now()
            day_cutoff = now - timedelta(days=1)
            week_cutoff = now - timedelta(weeks=1)

            # Get trending libraries for different periods
            daily_trending = self.get_trending_libraries("day", 5)
            weekly_trending = self.get_trending_libraries("week", 10)

            # Calculate growth rates
            growth_rates = {}
            for library in set(lib["library"] for lib in weekly_trending):
                daily_score = next(
                    (
                        lib["score"]
                        for lib in daily_trending
                        if lib["library"] == library
                    ),
                    0,
                )
                weekly_score = next(
                    (
                        lib["score"]
                        for lib in weekly_trending
                        if lib["library"] == library
                    ),
                    0,
                )

                if weekly_score > 0:
                    growth_rate = (
                        (daily_score - weekly_score / 7) / (weekly_score / 7) * 100
                    )
                    growth_rates[library] = growth_rate

            # Find fastest growing libraries
            fastest_growing = sorted(
                growth_rates.items(), key=lambda x: x[1], reverse=True
            )[:5]

            insights = {
                "daily_trending": daily_trending,
                "weekly_trending": weekly_trending,
                "fastest_growing": [
                    {"library": lib, "growth_rate": rate}
                    for lib, rate in fastest_growing
                ],
                "total_tracked_libraries": len(
                    set().union(
                        self.searches.keys(), self.views.keys(), self.downloads.keys()
                    )
                ),
                "most_searched": self._get_most_interacted("searches"),
                "most_viewed": self._get_most_interacted("views"),
                "most_downloaded": self._get_most_interacted("downloads"),
            }

            return insights

        except Exception as e:
            logger.error(f"Error getting trending insights: {e}")
            return {"error": str(e)}

    def _calculate_trending_score(self, library_name: str, cutoff: datetime) -> float:
        """Calculate trending score for a library within a time period."""
        # Get interactions within the time period
        recent_searches = [ts for ts in self.searches[library_name] if ts >= cutoff]
        recent_views = [ts for ts in self.views[library_name] if ts >= cutoff]
        recent_downloads = [ts for ts in self.downloads[library_name] if ts >= cutoff]

        # Weight different types of interactions
        search_weight = 1.0
        view_weight = 2.0
        download_weight = 5.0

        # Calculate base score
        score = (
            len(recent_searches) * search_weight
            + len(recent_views) * view_weight
            + len(recent_downloads) * download_weight
        )

        # Apply time decay (more recent interactions have higher weight)
        now = datetime.now()
        time_weighted_score = 0

        for interaction_list, weight in [
            (recent_searches, search_weight),
            (recent_views, view_weight),
            (recent_downloads, download_weight),
        ]:
            for timestamp in interaction_list:
                hours_ago = (now - timestamp).total_seconds() / 3600
                time_decay = max(0, 1 - (hours_ago / 24))  # Decay over 24 hours
                time_weighted_score += weight * time_decay

        # Apply rating boost
        avg_rating = self._calculate_average_rating(library_name)
        if avg_rating > 0:
            rating_multiplier = 1 + (avg_rating - 3) * 0.2  # Boost for ratings above 3
            time_weighted_score *= rating_multiplier

        return round(time_weighted_score, 2)

    def _get_interaction_counts(
        self, library_name: str, cutoff: datetime
    ) -> dict[str, int]:
        """Get interaction counts for a library within a time period."""
        return {
            "searches": len([ts for ts in self.searches[library_name] if ts >= cutoff]),
            "views": len([ts for ts in self.views[library_name] if ts >= cutoff]),
            "downloads": len(
                [ts for ts in self.downloads[library_name] if ts >= cutoff]
            ),
        }

    def _calculate_average_rating(self, library_name: str) -> float:
        """Calculate average rating for a library."""
        ratings = self.ratings[library_name]
        if not ratings:
            return 0.0
        return sum(ratings) / len(ratings)

    def _get_most_interacted(self, interaction_type: str) -> list[dict[str, Any]]:
        """Get most interacted libraries for a specific interaction type."""
        if interaction_type == "searches":
            data = self.searches
        elif interaction_type == "views":
            data = self.views
        elif interaction_type == "downloads":
            data = self.downloads
        else:
            return []

        # Count total interactions
        counts = {lib: len(interactions) for lib, interactions in data.items()}
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)

        return [{"library": lib, "count": count} for lib, count in sorted_counts[:5]]

    def _save_data(self):
        """Save tracking data to file."""
        if not self.data_file:
            return

        try:
            data = {
                "searches": {
                    lib: [ts.isoformat() for ts in timestamps]
                    for lib, timestamps in self.searches.items()
                },
                "views": {
                    lib: [ts.isoformat() for ts in timestamps]
                    for lib, timestamps in self.views.items()
                },
                "downloads": {
                    lib: [ts.isoformat() for ts in timestamps]
                    for lib, timestamps in self.downloads.items()
                },
                "ratings": dict(self.ratings),
            }

            with open(self.data_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.warning(f"Failed to save tracking data: {e}")

    def _load_data(self):
        """Load tracking data from file."""
        if not self.data_file:
            return

        try:
            with open(self.data_file) as f:
                data = json.load(f)

            # Load searches
            for lib, timestamps in data.get("searches", {}).items():
                self.searches[lib] = [datetime.fromisoformat(ts) for ts in timestamps]

            # Load views
            for lib, timestamps in data.get("views", {}).items():
                self.views[lib] = [datetime.fromisoformat(ts) for ts in timestamps]

            # Load downloads
            for lib, timestamps in data.get("downloads", {}).items():
                self.downloads[lib] = [datetime.fromisoformat(ts) for ts in timestamps]

            # Load ratings
            for lib, ratings in data.get("ratings", {}).items():
                self.ratings[lib] = ratings

            logger.info(f"Loaded tracking data from {self.data_file}")

        except FileNotFoundError:
            logger.info(f"No existing tracking data found at {self.data_file}")
        except Exception as e:
            logger.warning(f"Failed to load tracking data: {e}")
