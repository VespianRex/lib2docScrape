#!/usr/bin/env python3
"""
Search Analytics for Advanced Search & Discovery

Tracks and analyzes search patterns, queries, and user behavior.
"""

import json
import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)


class SearchAnalytics:
    """Analytics engine for tracking and analyzing search behavior."""

    def __init__(self, data_file: Optional[str] = None):
        """
        Initialize search analytics.

        Args:
            data_file: Optional file to persist analytics data
        """
        self.data_file = data_file

        # Storage for analytics data
        self.queries = []  # List of query records
        self.query_results = defaultdict(list)  # query -> [result_counts]
        self.click_through_data = defaultdict(list)  # query -> [clicked_results]
        self.zero_result_queries = []  # Queries that returned no results

        # Load existing data if available
        if data_file:
            self._load_data()

    def record_query(
        self,
        query: str,
        results_count: int,
        timestamp: Optional[datetime] = None,
        user_id: Optional[str] = None,
        filters: Optional[dict[str, Any]] = None,
    ):
        """
        Record a search query.

        Args:
            query: The search query string
            results_count: Number of results returned
            timestamp: When the query was made (defaults to now)
            user_id: Optional user identifier
            filters: Optional filters applied to the search
        """
        if timestamp is None:
            timestamp = datetime.now()

        query_record = {
            "query": query,
            "results_count": results_count,
            "timestamp": timestamp,
            "user_id": user_id,
            "filters": filters or {},
        }

        self.queries.append(query_record)
        self.query_results[query].append(results_count)

        # Track zero-result queries
        if results_count == 0:
            self.zero_result_queries.append(
                {
                    "query": query,
                    "timestamp": timestamp,
                    "user_id": user_id,
                    "filters": filters or {},
                }
            )

        self._save_data()
        logger.debug(f"Recorded query: {query} ({results_count} results)")

    def record_click_through(
        self,
        query: str,
        clicked_result: dict[str, Any],
        position: int,
        timestamp: Optional[datetime] = None,
    ):
        """
        Record a click-through event.

        Args:
            query: The original search query
            clicked_result: The result that was clicked
            position: Position of the result in the search results (0-based)
            timestamp: When the click occurred
        """
        if timestamp is None:
            timestamp = datetime.now()

        click_record = {
            "clicked_result": clicked_result,
            "position": position,
            "timestamp": timestamp,
        }

        self.click_through_data[query].append(click_record)
        self._save_data()
        logger.debug(
            f"Recorded click-through for query: {query} at position {position}"
        )

    def get_insights(self, period_days: int = 30) -> dict[str, Any]:
        """
        Get search analytics insights for a specific period.

        Args:
            period_days: Number of days to analyze (default: 30)

        Returns:
            Dictionary with analytics insights
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=period_days)

            # Filter queries by period
            recent_queries = [q for q in self.queries if q["timestamp"] >= cutoff_date]

            if not recent_queries:
                return {
                    "period_days": period_days,
                    "total_queries": 0,
                    "message": "No queries in the specified period",
                }

            # Calculate insights
            insights = {
                "period_days": period_days,
                "total_queries": len(recent_queries),
                "unique_queries": len(set(q["query"] for q in recent_queries)),
                "popular_queries": self._get_popular_queries(recent_queries),
                "search_trends": self._analyze_search_trends(recent_queries),
                "zero_result_queries": self._get_zero_result_insights(period_days),
                "average_results_per_query": self._calculate_average_results(
                    recent_queries
                ),
                "query_length_stats": self._analyze_query_lengths(recent_queries),
                "filter_usage": self._analyze_filter_usage(recent_queries),
                "temporal_patterns": self._analyze_temporal_patterns(recent_queries),
            }

            return insights

        except Exception as e:
            logger.error(f"Error generating search insights: {e}")
            return {"error": str(e)}

    def get_query_performance(self, query: str) -> dict[str, Any]:
        """
        Get performance metrics for a specific query.

        Args:
            query: The query to analyze

        Returns:
            Performance metrics for the query
        """
        try:
            # Get all instances of this query
            query_instances = [q for q in self.queries if q["query"] == query]

            if not query_instances:
                return {"error": f"No data found for query: {query}"}

            # Calculate metrics
            result_counts = [q["results_count"] for q in query_instances]
            click_throughs = self.click_through_data.get(query, [])

            performance = {
                "query": query,
                "total_searches": len(query_instances),
                "average_results": sum(result_counts) / len(result_counts),
                "min_results": min(result_counts),
                "max_results": max(result_counts),
                "zero_result_rate": len([r for r in result_counts if r == 0])
                / len(result_counts),
                "click_through_rate": len(click_throughs) / len(query_instances)
                if query_instances
                else 0,
                "average_click_position": self._calculate_average_click_position(
                    click_throughs
                ),
                "first_search": min(q["timestamp"] for q in query_instances),
                "last_search": max(q["timestamp"] for q in query_instances),
                "search_frequency": len(query_instances)
                / max(
                    (
                        datetime.now() - min(q["timestamp"] for q in query_instances)
                    ).days,
                    1,
                ),
            }

            return performance

        except Exception as e:
            logger.error(f"Error analyzing query performance: {e}")
            return {"error": str(e)}

    def get_search_suggestions(self, partial_query: str, limit: int = 10) -> list[str]:
        """
        Get search suggestions based on historical queries.

        Args:
            partial_query: Partial query string
            limit: Maximum number of suggestions

        Returns:
            List of suggested queries
        """
        partial_lower = partial_query.lower()

        # Find matching queries
        matching_queries = []
        query_counts = Counter(q["query"] for q in self.queries)

        for query, count in query_counts.items():
            if partial_lower in query.lower():
                matching_queries.append((query, count))

        # Sort by frequency and relevance
        matching_queries.sort(
            key=lambda x: (x[0].lower().startswith(partial_lower), x[1]), reverse=True
        )

        return [query for query, count in matching_queries[:limit]]

    def _get_popular_queries(
        self, queries: list[dict[str, Any]], limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get most popular queries in the given period."""
        query_counts = Counter(q["query"] for q in queries)
        popular = []

        for query, count in query_counts.most_common(limit):
            # Calculate additional metrics
            query_instances = [q for q in queries if q["query"] == query]
            avg_results = sum(q["results_count"] for q in query_instances) / len(
                query_instances
            )

            popular.append(
                {
                    "query": query,
                    "count": count,
                    "average_results": round(avg_results, 1),
                    "percentage": round((count / len(queries)) * 100, 1),
                }
            )

        return popular

    def _analyze_search_trends(self, queries: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze search trends over time."""
        if not queries:
            return {}

        # Group queries by day
        daily_counts = defaultdict(int)
        for query in queries:
            day = query["timestamp"].date()
            daily_counts[day] += 1

        # Calculate trend
        days = sorted(daily_counts.keys())
        if len(days) > 1:
            first_half = days[: len(days) // 2]
            second_half = days[len(days) // 2 :]

            first_half_avg = sum(daily_counts[day] for day in first_half) / len(
                first_half
            )
            second_half_avg = sum(daily_counts[day] for day in second_half) / len(
                second_half
            )

            trend = "increasing" if second_half_avg > first_half_avg else "decreasing"
            trend_percentage = (
                abs((second_half_avg - first_half_avg) / first_half_avg * 100)
                if first_half_avg > 0
                else 0
            )
        else:
            trend = "stable"
            trend_percentage = 0

        return {
            "trend": trend,
            "trend_percentage": round(trend_percentage, 1),
            "daily_average": round(sum(daily_counts.values()) / len(daily_counts), 1),
            "peak_day": max(daily_counts, key=daily_counts.get),
            "peak_count": max(daily_counts.values()),
        }

    def _get_zero_result_insights(self, period_days: int) -> dict[str, Any]:
        """Analyze zero-result queries."""
        cutoff_date = datetime.now() - timedelta(days=period_days)
        recent_zero_results = [
            q for q in self.zero_result_queries if q["timestamp"] >= cutoff_date
        ]

        if not recent_zero_results:
            return {"count": 0, "rate": 0}

        # Find common patterns in zero-result queries
        zero_queries = [q["query"] for q in recent_zero_results]
        common_terms = []

        # Simple term frequency analysis
        all_terms = []
        for query in zero_queries:
            all_terms.extend(query.lower().split())

        term_counts = Counter(all_terms)
        common_terms = [
            {"term": term, "count": count} for term, count in term_counts.most_common(5)
        ]

        total_queries_in_period = len(
            [q for q in self.queries if q["timestamp"] >= cutoff_date]
        )
        zero_result_rate = (
            len(recent_zero_results) / total_queries_in_period
            if total_queries_in_period > 0
            else 0
        )

        return {
            "count": len(recent_zero_results),
            "rate": round(zero_result_rate * 100, 1),
            "common_terms": common_terms,
            "sample_queries": zero_queries[:5],
        }

    def _calculate_average_results(self, queries: list[dict[str, Any]]) -> float:
        """Calculate average number of results per query."""
        if not queries:
            return 0.0

        total_results = sum(q["results_count"] for q in queries)
        return round(total_results / len(queries), 1)

    def _analyze_query_lengths(self, queries: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze query length statistics."""
        if not queries:
            return {}

        lengths = [len(q["query"].split()) for q in queries]

        return {
            "average_length": round(sum(lengths) / len(lengths), 1),
            "min_length": min(lengths),
            "max_length": max(lengths),
            "single_word_queries": len([l for l in lengths if l == 1]),
            "multi_word_queries": len([l for l in lengths if l > 1]),
        }

    def _analyze_filter_usage(self, queries: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze how filters are used in searches."""
        filter_usage = defaultdict(int)
        queries_with_filters = 0

        for query in queries:
            filters = query.get("filters", {})
            if filters:
                queries_with_filters += 1
                for filter_name in filters.keys():
                    filter_usage[filter_name] += 1

        filter_rate = queries_with_filters / len(queries) if queries else 0

        return {
            "filter_usage_rate": round(filter_rate * 100, 1),
            "popular_filters": dict(Counter(filter_usage).most_common(5)),
            "queries_with_filters": queries_with_filters,
        }

    def _analyze_temporal_patterns(
        self, queries: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Analyze temporal patterns in search behavior."""
        if not queries:
            return {}

        # Analyze by hour of day
        hour_counts = defaultdict(int)
        day_counts = defaultdict(int)

        for query in queries:
            hour_counts[query["timestamp"].hour] += 1
            day_counts[query["timestamp"].weekday()] += 1

        # Find peak hours and days
        peak_hour = max(hour_counts, key=hour_counts.get) if hour_counts else 0
        peak_day = max(day_counts, key=day_counts.get) if day_counts else 0

        day_names = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]

        return {
            "peak_hour": peak_hour,
            "peak_day": day_names[peak_day],
            "hourly_distribution": dict(hour_counts),
            "daily_distribution": {
                day_names[day]: count for day, count in day_counts.items()
            },
        }

    def _calculate_average_click_position(
        self, click_throughs: list[dict[str, Any]]
    ) -> float:
        """Calculate average position of clicked results."""
        if not click_throughs:
            return 0.0

        positions = [ct["position"] for ct in click_throughs]
        return round(sum(positions) / len(positions), 1)

    def _save_data(self):
        """Save analytics data to file."""
        if not self.data_file:
            return

        try:
            data = {
                "queries": [
                    {
                        "query": q["query"],
                        "results_count": q["results_count"],
                        "timestamp": q["timestamp"].isoformat(),
                        "user_id": q["user_id"],
                        "filters": q["filters"],
                    }
                    for q in self.queries
                ],
                "zero_result_queries": [
                    {
                        "query": q["query"],
                        "timestamp": q["timestamp"].isoformat(),
                        "user_id": q["user_id"],
                        "filters": q["filters"],
                    }
                    for q in self.zero_result_queries
                ],
            }

            with open(self.data_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.warning(f"Failed to save analytics data: {e}")

    def _load_data(self):
        """Load analytics data from file."""
        if not self.data_file:
            return

        try:
            with open(self.data_file) as f:
                data = json.load(f)

            # Load queries
            for q_data in data.get("queries", []):
                query_record = {
                    "query": q_data["query"],
                    "results_count": q_data["results_count"],
                    "timestamp": datetime.fromisoformat(q_data["timestamp"]),
                    "user_id": q_data["user_id"],
                    "filters": q_data["filters"],
                }
                self.queries.append(query_record)
                self.query_results[q_data["query"]].append(q_data["results_count"])

            # Load zero result queries
            for q_data in data.get("zero_result_queries", []):
                zero_query = {
                    "query": q_data["query"],
                    "timestamp": datetime.fromisoformat(q_data["timestamp"]),
                    "user_id": q_data["user_id"],
                    "filters": q_data["filters"],
                }
                self.zero_result_queries.append(zero_query)

            logger.info(f"Loaded analytics data from {self.data_file}")

        except FileNotFoundError:
            logger.info(f"No existing analytics data found at {self.data_file}")
        except Exception as e:
            logger.warning(f"Failed to load analytics data: {e}")
