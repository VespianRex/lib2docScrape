#!/usr/bin/env python3
"""
Difficulty Classifier for Documentation Content

Automatically classifies documentation content by difficulty level (beginner, intermediate, advanced).
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class DifficultyClassifier:
    """Classifier for determining documentation difficulty levels."""

    def __init__(self):
        """Initialize the difficulty classifier."""
        self.beginner_indicators = {
            "keywords": [
                "introduction",
                "getting started",
                "quick start",
                "tutorial",
                "basics",
                "simple",
                "easy",
                "first",
                "hello world",
                "install",
                "setup",
                "beginner",
                "start",
                "guide",
                "overview",
                "what is",
                "how to",
            ],
            "phrases": [
                "step by step",
                "for beginners",
                "getting started",
                "first time",
                "new to",
                "introduction to",
                "basic usage",
                "simple example",
            ],
            "patterns": [
                r"\bstep \d+\b",  # Step 1, Step 2, etc.
                r"\bfirst\b.*\btime\b",
                r"\bbasic\b.*\bexample\b",
            ],
        }

        self.intermediate_indicators = {
            "keywords": [
                "configuration",
                "customize",
                "options",
                "parameters",
                "features",
                "integration",
                "middleware",
                "plugin",
                "extension",
                "api",
                "methods",
                "functions",
                "classes",
                "modules",
                "framework",
            ],
            "phrases": [
                "advanced features",
                "configuration options",
                "api reference",
                "method parameters",
                "custom implementation",
                "integration guide",
            ],
            "patterns": [
                r"\bapi\b.*\breference\b",
                r"\bconfigur\w+\b",
                r"\bparameter\w*\b",
            ],
        }

        self.advanced_indicators = {
            "keywords": [
                "architecture",
                "internals",
                "performance",
                "optimization",
                "scaling",
                "advanced",
                "expert",
                "complex",
                "sophisticated",
                "enterprise",
                "production",
                "deployment",
                "security",
                "threading",
                "async",
                "concurrency",
                "distributed",
                "microservices",
                "algorithms",
            ],
            "phrases": [
                "advanced topics",
                "expert level",
                "production deployment",
                "performance optimization",
                "architectural patterns",
                "best practices",
                "enterprise features",
                "complex scenarios",
            ],
            "patterns": [
                r"\badvanced\b.*\btopic\w*\b",
                r"\bperformance\b.*\boptimiz\w+\b",
                r"\bproduction\b.*\bready\b",
            ],
        }

        # Technical complexity indicators
        self.complexity_indicators = {
            "high_complexity": [
                "algorithm",
                "complexity",
                "big o",
                "optimization",
                "performance",
                "memory",
                "cpu",
                "threading",
                "multiprocessing",
                "async",
                "await",
                "decorator",
                "metaclass",
                "inheritance",
                "polymorphism",
                "abstraction",
            ],
            "medium_complexity": [
                "class",
                "function",
                "method",
                "object",
                "instance",
                "attribute",
                "parameter",
                "argument",
                "return",
                "exception",
                "error",
                "debug",
            ],
            "low_complexity": [
                "print",
                "input",
                "variable",
                "string",
                "number",
                "list",
                "dictionary",
                "if",
                "else",
                "for",
                "while",
                "import",
                "from",
            ],
        }

    def classify_difficulty(self, content: str) -> str:
        """
        Classify the difficulty level of documentation content.

        Args:
            content: Documentation content to classify

        Returns:
            Difficulty level: 'beginner', 'intermediate', or 'advanced'
        """
        try:
            content_lower = content.lower()

            # Calculate scores for each difficulty level
            beginner_score = self._calculate_difficulty_score(
                content_lower, self.beginner_indicators
            )
            intermediate_score = self._calculate_difficulty_score(
                content_lower, self.intermediate_indicators
            )
            advanced_score = self._calculate_difficulty_score(
                content_lower, self.advanced_indicators
            )

            # Add complexity-based scoring
            complexity_score = self._calculate_complexity_score(content_lower)

            # Adjust scores based on complexity
            if complexity_score > 0.7:
                advanced_score += 2.0
            elif complexity_score > 0.4:
                intermediate_score += 1.0
            else:
                beginner_score += 1.0

            # Add length-based adjustment (longer content tends to be more advanced)
            length_factor = min(len(content) / 5000, 1.0)  # Normalize to 5000 chars
            advanced_score += length_factor * 0.5

            # Add code complexity scoring
            code_complexity = self._analyze_code_complexity(content)
            if code_complexity > 0.7:
                advanced_score += 1.5
            elif code_complexity > 0.4:
                intermediate_score += 1.0

            # Determine the highest scoring difficulty level
            scores = {
                "beginner": beginner_score,
                "intermediate": intermediate_score,
                "advanced": advanced_score,
            }

            # Return the difficulty level with the highest score
            difficulty = max(scores, key=scores.get)

            logger.debug(f"Difficulty scores: {scores}, classified as: {difficulty}")
            return difficulty

        except Exception as e:
            logger.error(f"Error classifying difficulty: {e}")
            return "intermediate"  # Default fallback

    def get_difficulty_analysis(self, content: str) -> dict[str, Any]:
        """
        Get detailed difficulty analysis of content.

        Args:
            content: Documentation content to analyze

        Returns:
            Dictionary with detailed difficulty analysis
        """
        try:
            content_lower = content.lower()

            # Calculate scores
            beginner_score = self._calculate_difficulty_score(
                content_lower, self.beginner_indicators
            )
            intermediate_score = self._calculate_difficulty_score(
                content_lower, self.intermediate_indicators
            )
            advanced_score = self._calculate_difficulty_score(
                content_lower, self.advanced_indicators
            )

            complexity_score = self._calculate_complexity_score(content_lower)
            code_complexity = self._analyze_code_complexity(content)

            # Find matched indicators
            matched_indicators = {
                "beginner": self._find_matched_indicators(
                    content_lower, self.beginner_indicators
                ),
                "intermediate": self._find_matched_indicators(
                    content_lower, self.intermediate_indicators
                ),
                "advanced": self._find_matched_indicators(
                    content_lower, self.advanced_indicators
                ),
            }

            # Calculate confidence
            scores = [beginner_score, intermediate_score, advanced_score]
            max_score = max(scores)
            second_max = sorted(scores, reverse=True)[1]
            confidence = (max_score - second_max) / max_score if max_score > 0 else 0

            difficulty = self.classify_difficulty(content)

            return {
                "difficulty": difficulty,
                "confidence": round(confidence, 2),
                "scores": {
                    "beginner": round(beginner_score, 2),
                    "intermediate": round(intermediate_score, 2),
                    "advanced": round(advanced_score, 2),
                },
                "complexity_score": round(complexity_score, 2),
                "code_complexity": round(code_complexity, 2),
                "matched_indicators": matched_indicators,
                "content_length": len(content),
                "reasoning": self._generate_reasoning(
                    difficulty, matched_indicators, complexity_score
                ),
            }

        except Exception as e:
            logger.error(f"Error analyzing difficulty: {e}")
            return {"difficulty": "intermediate", "confidence": 0.0, "error": str(e)}

    def classify_batch(self, contents: list[str]) -> list[dict[str, Any]]:
        """
        Classify difficulty for multiple content pieces.

        Args:
            contents: List of documentation content strings

        Returns:
            List of classification results
        """
        results = []
        for i, content in enumerate(contents):
            try:
                difficulty = self.classify_difficulty(content)
                analysis = self.get_difficulty_analysis(content)
                results.append(
                    {"index": i, "difficulty": difficulty, "analysis": analysis}
                )
            except Exception as e:
                logger.error(f"Error classifying content {i}: {e}")
                results.append(
                    {"index": i, "difficulty": "intermediate", "error": str(e)}
                )

        return results

    def _calculate_difficulty_score(
        self, content: str, indicators: dict[str, list[str]]
    ) -> float:
        """Calculate difficulty score based on indicators."""
        score = 0.0

        # Score based on keywords
        for keyword in indicators["keywords"]:
            count = content.count(keyword)
            score += count * 1.0

        # Score based on phrases
        for phrase in indicators["phrases"]:
            count = content.count(phrase)
            score += count * 2.0  # Phrases have higher weight

        # Score based on patterns
        for pattern in indicators["patterns"]:
            matches = len(re.findall(pattern, content))
            score += matches * 1.5

        # Normalize by content length
        if len(content) > 0:
            score = score / (len(content) / 1000)  # Per 1000 characters

        return score

    def _calculate_complexity_score(self, content: str) -> float:
        """Calculate technical complexity score."""
        high_count = sum(
            1
            for term in self.complexity_indicators["high_complexity"]
            if term in content
        )
        medium_count = sum(
            1
            for term in self.complexity_indicators["medium_complexity"]
            if term in content
        )
        low_count = sum(
            1
            for term in self.complexity_indicators["low_complexity"]
            if term in content
        )

        total_terms = high_count + medium_count + low_count
        if total_terms == 0:
            return 0.0

        # Weight the complexity
        weighted_score = (
            high_count * 3 + medium_count * 2 + low_count * 1
        ) / total_terms
        return min(weighted_score / 3, 1.0)  # Normalize to 0-1

    def _analyze_code_complexity(self, content: str) -> float:
        """Analyze code complexity in the content."""
        # Find code blocks
        code_blocks = re.findall(r"```[\s\S]*?```|`[^`]+`", content)

        if not code_blocks:
            return 0.0

        complexity_score = 0.0
        total_blocks = len(code_blocks)

        for block in code_blocks:
            block_score = 0.0

            # Check for complex constructs
            complex_patterns = [
                r"\bclass\s+\w+",  # Class definitions
                r"\bdef\s+\w+",  # Function definitions
                r"\btry\s*:",  # Exception handling
                r"\bwith\s+\w+",  # Context managers
                r"\bfor\s+\w+\s+in\s+",  # Loops
                r"\bif\s+.*:",  # Conditionals
                r"\blambda\s+",  # Lambda functions
                r"@\w+",  # Decorators
                r"\basync\s+def",  # Async functions
                r"\bawait\s+",  # Await expressions
            ]

            for pattern in complex_patterns:
                matches = len(re.findall(pattern, block))
                block_score += matches * 0.1

            complexity_score += min(block_score, 1.0)

        return complexity_score / total_blocks

    def _find_matched_indicators(
        self, content: str, indicators: dict[str, list[str]]
    ) -> list[str]:
        """Find which indicators were matched in the content."""
        matched = []

        # Check keywords
        for keyword in indicators["keywords"]:
            if keyword in content:
                matched.append(keyword)

        # Check phrases
        for phrase in indicators["phrases"]:
            if phrase in content:
                matched.append(phrase)

        # Check patterns
        for pattern in indicators["patterns"]:
            if re.search(pattern, content):
                matched.append(f"pattern: {pattern}")

        return matched

    def _generate_reasoning(
        self,
        difficulty: str,
        matched_indicators: dict[str, list[str]],
        complexity_score: float,
    ) -> str:
        """Generate human-readable reasoning for the classification."""
        reasoning_parts = []

        # Main classification reason
        main_indicators = matched_indicators.get(difficulty, [])
        if main_indicators:
            reasoning_parts.append(
                f"Classified as {difficulty} due to indicators: {', '.join(main_indicators[:3])}"
            )

        # Complexity reason
        if complexity_score > 0.7:
            reasoning_parts.append("High technical complexity detected")
        elif complexity_score > 0.4:
            reasoning_parts.append("Moderate technical complexity")
        else:
            reasoning_parts.append("Low technical complexity")

        # Additional context
        if difficulty == "beginner":
            reasoning_parts.append("Contains introductory language and basic concepts")
        elif difficulty == "intermediate":
            reasoning_parts.append("Includes API references and configuration details")
        else:
            reasoning_parts.append("Covers advanced topics and complex implementations")

        return ". ".join(reasoning_parts)
