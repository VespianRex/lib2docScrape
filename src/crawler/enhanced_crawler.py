#!/usr/bin/env python3
"""
Enhanced Crawler with Relevance Detection

Integrates relevance detection into the crawling process to filter out irrelevant content.
"""

import logging
from typing import Any

from processors.relevance_detection import HybridRelevanceDetector

logger = logging.getLogger(__name__)


class EnhancedCrawler:
    """Enhanced crawler with integrated relevance detection."""

    def __init__(self, relevance_detection: bool = True, threshold: float = 0.6):
        """
        Initialize enhanced crawler.

        Args:
            relevance_detection: Whether to enable relevance detection
            threshold: Relevance threshold for filtering content
        """
        self.relevance_detection = relevance_detection
        self.threshold = threshold

        if relevance_detection:
            self.relevance_detector = HybridRelevanceDetector()
        else:
            self.relevance_detector = None

    def filter_relevant_pages(
        self, pages: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Filter pages based on relevance detection.

        Args:
            pages: List of page dictionaries with 'url' and 'content' keys

        Returns:
            List of relevant pages with relevance scores
        """
        if not self.relevance_detection or not self.relevance_detector:
            # Return all pages if relevance detection is disabled
            return [
                {**page, "relevance_score": 1.0, "is_relevant": True} for page in pages
            ]

        relevant_pages = []

        for page in pages:
            content = page.get("content", "")

            if len(content) < 10:  # Skip very short content
                continue

            # Analyze relevance
            relevance_result = self.relevance_detector.is_documentation_relevant(
                content
            )
            relevance_score = relevance_result.get("combined_score", 0.5)
            is_relevant = relevance_score >= self.threshold

            if is_relevant:
                page_with_relevance = {
                    **page,
                    "relevance_score": relevance_score,
                    "is_relevant": True,
                    "relevance_reasoning": relevance_result.get("reasoning", ""),
                }
                relevant_pages.append(page_with_relevance)

        return relevant_pages
