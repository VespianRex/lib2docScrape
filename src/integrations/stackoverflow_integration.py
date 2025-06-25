#!/usr/bin/env python3
"""
Stack Overflow Integration for Documentation Discovery

Integrates with Stack Overflow API to find common issues and solutions.
"""

import logging
from typing import Any, Optional

import aiohttp

logger = logging.getLogger(__name__)


class StackOverflowIntegration:
    """Integration with Stack Overflow API for finding common issues."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Stack Overflow integration.

        Args:
            api_key: Optional Stack Overflow API key for higher rate limits
        """
        self.api_key = api_key
        self.base_url = "https://api.stackexchange.com/2.3"
        self.site = "stackoverflow"

    async def get_common_issues(
        self, library_name: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Get common issues and questions for a library from Stack Overflow.

        Args:
            library_name: Name of the library to search for
            limit: Maximum number of issues to return

        Returns:
            List of common issues with titles, links, and scores
        """
        try:
            # Search for questions tagged with the library name
            questions = await self._search_questions(library_name, limit)

            # Format results
            issues = []
            for question in questions:
                issues.append(
                    {
                        "title": question.get("title", ""),
                        "link": question.get("link", ""),
                        "score": question.get("score", 0),
                        "view_count": question.get("view_count", 0),
                        "answer_count": question.get("answer_count", 0),
                        "tags": question.get("tags", []),
                        "creation_date": question.get("creation_date", 0),
                        "is_answered": question.get("is_answered", False),
                    }
                )

            return issues

        except Exception as e:
            logger.error(f"Error getting Stack Overflow issues for {library_name}: {e}")
            return []

    async def get_trending_questions(
        self, library_name: str, days: int = 30
    ) -> list[dict[str, Any]]:
        """
        Get trending questions for a library in the last N days.

        Args:
            library_name: Name of the library
            days: Number of days to look back

        Returns:
            List of trending questions
        """
        try:
            # Calculate timestamp for N days ago
            import time

            from_date = int(time.time()) - (days * 24 * 60 * 60)

            questions = await self._search_questions(
                library_name, limit=20, from_date=from_date, sort="activity"
            )

            # Filter and format trending questions
            trending = []
            for question in questions:
                if question.get("view_count", 0) > 100:  # Minimum view threshold
                    trending.append(
                        {
                            "title": question.get("title", ""),
                            "link": question.get("link", ""),
                            "score": question.get("score", 0),
                            "view_count": question.get("view_count", 0),
                            "tags": question.get("tags", []),
                            "activity_date": question.get("last_activity_date", 0),
                        }
                    )

            # Sort by activity and views
            trending.sort(key=lambda x: (x["score"], x["view_count"]), reverse=True)
            return trending[:10]

        except Exception as e:
            logger.error(f"Error getting trending questions for {library_name}: {e}")
            return []

    async def get_top_answers(
        self, library_name: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        """
        Get top-rated answers for a library.

        Args:
            library_name: Name of the library
            limit: Maximum number of answers to return

        Returns:
            List of top answers
        """
        try:
            # First get questions
            questions = await self._search_questions(library_name, limit=20)

            # Get answers for top questions
            top_answers = []
            for question in questions[:5]:  # Top 5 questions
                question_id = question.get("question_id")
                if question_id:
                    answers = await self._get_question_answers(question_id)
                    if answers:
                        # Get the top answer
                        top_answer = max(answers, key=lambda x: x.get("score", 0))
                        top_answers.append(
                            {
                                "question_title": question.get("title", ""),
                                "question_link": question.get("link", ""),
                                "answer_score": top_answer.get("score", 0),
                                "answer_body": top_answer.get("body", "")[:500] + "...",
                                "is_accepted": top_answer.get("is_accepted", False),
                                "tags": question.get("tags", []),
                            }
                        )

            return top_answers

        except Exception as e:
            logger.error(f"Error getting top answers for {library_name}: {e}")
            return []

    async def _search_questions(
        self,
        library_name: str,
        limit: int = 10,
        from_date: Optional[int] = None,
        sort: str = "votes",
    ) -> list[dict[str, Any]]:
        """Search for questions on Stack Overflow."""
        try:
            params = {
                "order": "desc",
                "sort": sort,
                "tagged": library_name,
                "site": self.site,
                "pagesize": limit,
                "filter": "default",
            }

            if from_date:
                params["fromdate"] = from_date

            if self.api_key:
                params["key"] = self.api_key

            url = f"{self.base_url}/questions"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("items", [])
                    else:
                        logger.warning(
                            f"Stack Overflow API returned status {response.status}"
                        )
                        return []

        except Exception as e:
            logger.error(f"Error searching Stack Overflow questions: {e}")
            return []

    async def _get_question_answers(self, question_id: int) -> list[dict[str, Any]]:
        """Get answers for a specific question."""
        try:
            params = {
                "order": "desc",
                "sort": "votes",
                "site": self.site,
                "filter": "default",
            }

            if self.api_key:
                params["key"] = self.api_key

            url = f"{self.base_url}/questions/{question_id}/answers"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("items", [])
                    else:
                        return []

        except Exception as e:
            logger.error(f"Error getting question answers: {e}")
            return []

    def get_library_statistics(self, library_name: str) -> dict[str, Any]:
        """
        Get statistics about a library's presence on Stack Overflow.
        Note: This is a synchronous method that returns cached/estimated data.
        """
        # This would typically query cached data or make a simple API call
        # For now, return mock statistics
        return {
            "library": library_name,
            "total_questions": 1250,  # Mock data
            "answered_questions": 1100,
            "average_score": 3.2,
            "top_tags": [library_name, "python", "api"],
            "activity_trend": "increasing",
            "last_updated": "2024-12-23",
        }
