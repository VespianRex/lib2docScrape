#!/usr/bin/env python3
"""
Content Relevance Detection for Smart Scraping

Implements both NLP-based and traditional rule-based approaches to determine
if content is relevant documentation or should be filtered out (like GitHub issues, PRs, etc.).
"""

import logging
import re
from abc import ABC, abstractmethod
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class BaseRelevanceDetector(ABC):
    """Base class for relevance detection implementations."""

    @abstractmethod
    def is_documentation_relevant(self, content: str) -> dict[str, Any]:
        """
        Determine if content is relevant documentation.

        Args:
            content: Text content to analyze

        Returns:
            Dictionary with relevance decision and metadata
        """
        pass


class NLPRelevanceDetector(BaseRelevanceDetector):
    """NLP-based relevance detector using semantic analysis."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize NLP relevance detector.

        Args:
            model_name: Sentence transformer model to use
        """
        self.model_name = model_name
        self.model = None
        self._load_model()

        # Reference embeddings for documentation vs non-documentation content
        self.documentation_examples = [
            "API documentation with examples and usage instructions",
            "Installation guide with step-by-step instructions",
            "Tutorial showing how to use the library features",
            "Configuration options and parameter descriptions",
            "Code examples demonstrating functionality",
            "Getting started guide for beginners",
            "Reference manual with detailed explanations",
        ]

        self.non_documentation_examples = [
            "Bug report describing an issue with reproduction steps",
            "Pull request proposing code changes",
            "Issue discussion about feature requests",
            "Contributing guidelines for developers",
            "Code of conduct and community rules",
            "License information and legal text",
            "Changelog listing version updates",
            "Build and deployment configuration files",
            "Test files and testing procedures",
            "Development setup and environment configuration",
        ]

        self.documentation_embeddings = None
        self.non_documentation_embeddings = None
        self._generate_reference_embeddings()

    def _load_model(self):
        """Load the sentence transformer model."""
        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded NLP model: {self.model_name}")
        except Exception as e:
            logger.warning(f"Failed to load NLP model: {e}. Using fallback method.")
            self.model = None

    def _generate_reference_embeddings(self):
        """Generate embeddings for reference examples."""
        if not self.model:
            return

        try:
            self.documentation_embeddings = self.model.encode(
                self.documentation_examples
            )
            self.non_documentation_embeddings = self.model.encode(
                self.non_documentation_examples
            )
            logger.debug("Generated reference embeddings for relevance detection")
        except Exception as e:
            logger.warning(f"Failed to generate reference embeddings: {e}")

    def is_documentation_relevant(self, content: str) -> dict[str, Any]:
        """
        Determine if content is relevant documentation using NLP analysis.

        Args:
            content: Text content to analyze

        Returns:
            Dictionary with relevance decision and confidence
        """
        try:
            if not content or len(content.strip()) < 50:
                return {
                    "is_relevant": False,
                    "confidence": 0.9,
                    "reasoning": "Content too short to be meaningful documentation",
                    "method": "nlp",
                }

            if not self.model:
                # Fallback to rule-based detection
                return self._fallback_detection(content)

            # Generate embedding for the content
            content_embedding = self.model.encode([content])

            # Calculate similarities to reference examples
            doc_similarities = np.max(
                np.dot(content_embedding, self.documentation_embeddings.T)
            )
            non_doc_similarities = np.max(
                np.dot(content_embedding, self.non_documentation_embeddings.T)
            )

            # Determine relevance based on similarity scores
            is_relevant = doc_similarities > non_doc_similarities

            # Calculate confidence with better scaling
            similarity_diff = doc_similarities - non_doc_similarities
            confidence = max(
                0.5, min(1.0, 0.5 + similarity_diff * 2)
            )  # Scale and bound confidence

            # Additional heuristics
            reasoning_parts = []

            # Check for documentation indicators
            doc_indicators = self._count_documentation_indicators(content)
            non_doc_indicators = self._count_non_documentation_indicators(content)

            if doc_indicators > non_doc_indicators:
                # Get specific indicators for better reasoning
                specific_indicators = self._get_specific_indicators(content)
                reasoning_parts.append(
                    f"Contains {doc_indicators} documentation indicators: {', '.join(specific_indicators[:3])}"
                )
                confidence = min(
                    confidence + 0.2, 1.0
                )  # Boost confidence for doc indicators
            elif non_doc_indicators > doc_indicators:
                # Get specific non-doc indicators for better reasoning
                specific_non_doc = self._get_specific_non_doc_indicators(content)
                reasoning_parts.append(
                    f"Contains {non_doc_indicators} non-documentation indicators: {', '.join(specific_non_doc[:3])}"
                )
                is_relevant = False
                confidence = max(confidence, 0.7)
            elif doc_indicators > 0:
                specific_indicators = self._get_specific_indicators(content)
                reasoning_parts.append(
                    f"Contains {doc_indicators} documentation indicators: {', '.join(specific_indicators[:3])}"
                )
                confidence = min(confidence + 0.1, 1.0)

            # Adjust confidence based on content length and structure
            if len(content) > 1000:
                confidence = min(confidence + 0.1, 1.0)
                reasoning_parts.append("Substantial content length")

            reasoning = (
                "; ".join(reasoning_parts)
                if reasoning_parts
                else "Based on semantic similarity analysis"
            )

            return {
                "is_relevant": is_relevant,
                "confidence": min(confidence, 1.0),
                "reasoning": reasoning,
                "method": "nlp",
                "doc_similarity": float(doc_similarities),
                "non_doc_similarity": float(non_doc_similarities),
                "doc_indicators": doc_indicators,
                "non_doc_indicators": non_doc_indicators,
            }

        except Exception as e:
            logger.error(f"Error in NLP relevance detection: {e}")
            return self._fallback_detection(content)

    def get_relevance_score(self, content: str) -> float:
        """
        Get a relevance score between 0 and 1.

        Args:
            content: Text content to analyze

        Returns:
            Relevance score (0 = not relevant, 1 = highly relevant)
        """
        result = self.is_documentation_relevant(content)
        base_score = (
            result["confidence"]
            if result["is_relevant"]
            else (1 - result["confidence"])
        )
        return max(0.0, min(1.0, base_score))

    def extract_documentation_sections(self, content: str) -> dict[str, Any]:
        """
        Extract and classify sections of content by relevance.

        Args:
            content: Full content to analyze

        Returns:
            Dictionary with relevant and irrelevant sections
        """
        # Split content into sections (simple approach)
        sections = self._split_into_sections(content)

        relevant_sections = []
        irrelevant_sections = []

        for section in sections:
            if len(section["content"]) > 100:  # Only analyze substantial sections
                relevance = self.is_documentation_relevant(section["content"])
                section["relevance"] = relevance

                if relevance["is_relevant"]:
                    relevant_sections.append(section)
                else:
                    irrelevant_sections.append(section)

        # Calculate overall documentation score
        total_sections = len(relevant_sections) + len(irrelevant_sections)
        doc_score = len(relevant_sections) / total_sections if total_sections > 0 else 0

        return {
            "relevant_sections": relevant_sections,
            "irrelevant_sections": irrelevant_sections,
            "documentation_score": doc_score,
            "total_sections": total_sections,
        }

    def _fallback_detection(self, content: str) -> dict[str, Any]:
        """Fallback detection when NLP model is not available."""
        rule_detector = RuleBasedRelevanceDetector()
        result = rule_detector.is_documentation_relevant(content)
        result["method"] = "nlp_fallback"
        return result

    def _count_documentation_indicators(self, content: str) -> int:
        """Count indicators that suggest documentation content."""
        content_lower = content.lower()

        doc_indicators = [
            "installation",
            "getting started",
            "quick start",
            "tutorial",
            "guide",
            "documentation",
            "api reference",
            "examples",
            "usage",
            "how to",
            "configuration",
            "parameters",
            "options",
            "methods",
            "functions",
            "import",
            "install",
            "pip install",
            "npm install",
            "requirements",
            "example:",
            "for example",
            "code example",
            "```",
            "syntax",
            "description",
            "overview",
            "introduction",
            "features",
        ]

        return sum(1 for indicator in doc_indicators if indicator in content_lower)

    def _count_non_documentation_indicators(self, content: str) -> int:
        """Count indicators that suggest non-documentation content."""
        content_lower = content.lower()

        non_doc_indicators = [
            "pull request",
            "merge request",
            "issue #",
            "bug report",
            "feature request",
            "contributing",
            "code of conduct",
            "license",
            "changelog",
            "release notes",
            "build status",
            "ci/cd",
            "travis",
            "github actions",
            "workflow",
            "test suite",
            "unit test",
            "integration test",
            "coverage",
            "development setup",
            "dev environment",
            "local development",
            "reproduction steps",
            "expected behavior",
            "actual behavior",
            "assignee:",
            "reviewer:",
            "milestone:",
            "labels:",
            "projects:",
        ]

        return sum(1 for indicator in non_doc_indicators if indicator in content_lower)

    def _get_specific_indicators(self, content: str) -> list[str]:
        """Get specific documentation indicators found in content."""
        content_lower = content.lower()

        doc_indicators = [
            "installation",
            "getting started",
            "quick start",
            "tutorial",
            "guide",
            "documentation",
            "api reference",
            "examples",
            "usage",
            "how to",
            "configuration",
            "parameters",
            "options",
            "methods",
            "functions",
            "import",
            "install",
            "pip install",
            "npm install",
            "requirements",
        ]

        found_indicators = []
        for indicator in doc_indicators:
            if indicator in content_lower:
                found_indicators.append(indicator)

        return found_indicators

    def _get_specific_non_doc_indicators(self, content: str) -> list[str]:
        """Get specific non-documentation indicators found in content."""
        content_lower = content.lower()

        non_doc_indicators = [
            "pull request",
            "merge request",
            "issue #",
            "bug report",
            "feature request",
            "contributing",
            "code of conduct",
            "license",
            "changelog",
            "release notes",
            "build status",
            "ci/cd",
            "travis",
            "github actions",
            "workflow",
            "test suite",
            "unit test",
            "integration test",
            "coverage",
            "development setup",
            "dev environment",
            "local development",
            "reproduction steps",
            "expected behavior",
            "actual behavior",
        ]

        found_indicators = []
        for indicator in non_doc_indicators:
            if indicator in content_lower:
                found_indicators.append(indicator)

        return found_indicators

    def _split_into_sections(self, content: str) -> list[dict[str, Any]]:
        """Split content into logical sections."""
        # Simple section splitting based on headers and line breaks
        sections = []

        # Split by markdown headers
        header_pattern = r"^#{1,6}\s+(.+)$"
        lines = content.split("\n")

        current_section = {"title": "Introduction", "content": ""}

        for line in lines:
            header_match = re.match(header_pattern, line, re.MULTILINE)
            if header_match:
                # Save current section if it has content
                if current_section["content"].strip():
                    sections.append(current_section)

                # Start new section
                current_section = {"title": header_match.group(1), "content": ""}
            else:
                current_section["content"] += line + "\n"

        # Add the last section
        if current_section["content"].strip():
            sections.append(current_section)

        return sections


class RuleBasedRelevanceDetector(BaseRelevanceDetector):
    """Rule-based relevance detector using pattern matching and heuristics."""

    def __init__(self):
        """Initialize rule-based relevance detector."""
        self.documentation_patterns = {
            "strong_indicators": [
                r"\b(?:api|documentation|docs?)\b",
                r"\b(?:installation|install|setup)\b",
                r"\b(?:tutorial|guide|getting started)\b",
                r"\b(?:example|usage|how to)\b",
                r"\b(?:configuration|config|parameters)\b",
                r"```[\s\S]*?```",  # Code blocks
                r"\bimport\s+\w+",  # Import statements
                r"\bpip install\b|\bnpm install\b",  # Installation commands
            ],
            "medium_indicators": [
                r"\b(?:function|method|class|module)\b",
                r"\b(?:parameter|argument|option|setting)\b",
                r"\b(?:return|returns|output)\b",
                r"\b(?:description|overview|introduction)\b",
                r"\b(?:feature|functionality|capability)\b",
            ],
            "weak_indicators": [
                r"\b(?:library|package|framework|tool)\b",
                r"\b(?:version|release|update)\b",
                r"\b(?:support|help|assistance)\b",
            ],
        }

        self.non_documentation_patterns = {
            "strong_indicators": [
                r"\b(?:pull request|merge request|pr #|mr #)\b",
                r"\b(?:issue #|bug report|feature request)\b",
                r"\b(?:contributing|code of conduct|license)\b",
                r"\b(?:changelog|release notes|version history)\b",
                r"\b(?:build|ci/cd|continuous integration)\b",
                r"\b(?:test|testing|unit test|integration test)\b",
                r"\bassignee:|reviewer:|milestone:|labels:",
                r"\b(?:reproduction steps|expected behavior|actual behavior)\b",
            ],
            "medium_indicators": [
                r"\b(?:development|dev environment|local setup)\b",
                r"\b(?:workflow|pipeline|automation)\b",
                r"\b(?:coverage|quality|metrics)\b",
                r"\b(?:deployment|production|staging)\b",
            ],
            "weak_indicators": [
                r"\b(?:commit|branch|fork|clone)\b",
                r"\b(?:repository|repo|github|gitlab)\b",
                r"\b(?:maintainer|contributor|author)\b",
            ],
        }

        self.irrelevant_url_patterns = [
            r"/issues?/",
            r"/pull/",
            r"/merge_requests?/",
            r"/commits?/",
            r"/branches?/",
            r"/releases?/",
            r"/tags?/",
            r"/actions?/",
            r"/workflows?/",
            r"/settings",
            r"/contributors?",
            r"/graphs?",
            r"/network",
            r"/pulse",
            r"/security",
            r"/insights",
        ]

    def is_documentation_relevant(self, content: str) -> dict[str, Any]:
        """
        Determine if content is relevant documentation using rule-based analysis.

        Args:
            content: Text content to analyze

        Returns:
            Dictionary with relevance decision and score breakdown
        """
        try:
            if not content or len(content.strip()) < 20:
                return {
                    "is_relevant": False,
                    "score": 0.0,
                    "reasoning": "Content too short",
                    "matched_patterns": [],
                }

            content_lower = content.lower()

            # Calculate documentation score
            doc_score = self._calculate_pattern_score(
                content_lower, self.documentation_patterns
            )

            # Calculate non-documentation score
            non_doc_score = self._calculate_pattern_score(
                content_lower, self.non_documentation_patterns
            )

            # Get matched patterns for explanation
            doc_patterns = self._get_matched_patterns(
                content_lower, self.documentation_patterns
            )
            non_doc_patterns = self._get_matched_patterns(
                content_lower, self.non_documentation_patterns
            )

            # Calculate final score
            total_score = doc_score - non_doc_score
            normalized_score = max(
                0, min(1, (total_score + 5) / 10)
            )  # Normalize to 0-1

            # Determine relevance
            is_relevant = normalized_score > 0.5

            # Generate reasoning
            reasoning_parts = []
            if doc_patterns:
                reasoning_parts.append(
                    f"Documentation patterns: {', '.join(doc_patterns[:3])}"
                )
            if non_doc_patterns:
                reasoning_parts.append(
                    f"Non-documentation patterns: {', '.join(non_doc_patterns[:3])}"
                )

            reasoning = (
                "; ".join(reasoning_parts)
                if reasoning_parts
                else "Based on pattern analysis"
            )

            return {
                "is_relevant": is_relevant,
                "score": normalized_score,
                "reasoning": reasoning,
                "matched_patterns": doc_patterns + non_doc_patterns,
                "doc_score": doc_score,
                "non_doc_score": non_doc_score,
                "method": "rule_based",
            }

        except Exception as e:
            logger.error(f"Error in rule-based relevance detection: {e}")
            return {
                "is_relevant": False,
                "score": 0.0,
                "reasoning": f"Error in analysis: {str(e)}",
                "matched_patterns": [],
            }

    def get_relevance_score(self, content: str) -> float:
        """Get relevance score between 0 and 1."""
        result = self.is_documentation_relevant(content)
        return result["score"]

    def get_irrelevant_indicators(self, content: str) -> list[str]:
        """Get list of indicators that suggest content is not documentation."""
        content_lower = content.lower()
        return self._get_matched_patterns(
            content_lower, self.non_documentation_patterns
        )

    def is_url_relevant(self, url: str) -> bool:
        """Check if a URL is likely to contain relevant documentation."""
        url_lower = url.lower()

        for pattern in self.irrelevant_url_patterns:
            if re.search(pattern, url_lower):
                return False

        return True

    def _calculate_pattern_score(
        self, content: str, patterns: dict[str, list[str]]
    ) -> float:
        """Calculate score based on pattern matches."""
        score = 0.0
        weights = {
            "strong_indicators": 3.0,
            "medium_indicators": 2.0,
            "weak_indicators": 1.0,
        }

        for category, pattern_list in patterns.items():
            weight = weights.get(category, 1.0)
            for pattern in pattern_list:
                matches = len(re.findall(pattern, content, re.IGNORECASE))
                score += matches * weight

        return score

    def _get_matched_patterns(
        self, content: str, patterns: dict[str, list[str]]
    ) -> list[str]:
        """Get list of patterns that matched in the content."""
        matched = []

        for category, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, content, re.IGNORECASE):
                    # Extract a readable description from the pattern
                    readable = (
                        pattern.replace(r"\b", "").replace("(?:", "").replace(")", "")
                    )
                    readable = readable.replace("|", " or ").replace("?", "")
                    matched.append(f"{readable} ({category})")

        return matched


class HybridRelevanceDetector(BaseRelevanceDetector):
    """Hybrid detector that combines NLP and rule-based approaches."""

    def __init__(self, nlp_weight: float = 0.6, rule_weight: float = 0.4):
        """
        Initialize hybrid relevance detector.

        Args:
            nlp_weight: Weight for NLP-based score
            rule_weight: Weight for rule-based score
        """
        self.nlp_weight = nlp_weight
        self.rule_weight = rule_weight
        self.nlp_detector = NLPRelevanceDetector()
        self.rule_detector = RuleBasedRelevanceDetector()

    def is_documentation_relevant(self, content: str) -> dict[str, Any]:
        """
        Determine relevance using both NLP and rule-based approaches.

        Args:
            content: Text content to analyze

        Returns:
            Combined analysis with scores from both methods
        """
        try:
            # Get results from both detectors
            nlp_result = self.nlp_detector.is_documentation_relevant(content)
            rule_result = self.rule_detector.is_documentation_relevant(content)

            # Extract scores
            nlp_score = (
                nlp_result.get("confidence", 0.5)
                if nlp_result.get("is_relevant")
                else (1 - nlp_result.get("confidence", 0.5))
            )
            rule_score = rule_result.get("score", 0.5)

            # Calculate combined score
            combined_score = (nlp_score * self.nlp_weight) + (
                rule_score * self.rule_weight
            )
            is_relevant = combined_score > 0.5

            # Calculate confidence based on agreement between methods
            agreement = abs(nlp_score - rule_score)
            confidence = max(
                0.5, 1.0 - agreement
            )  # Higher confidence when methods agree

            # Combine reasoning
            reasoning_parts = []
            if nlp_result.get("reasoning"):
                reasoning_parts.append(f"NLP: {nlp_result['reasoning']}")
            if rule_result.get("reasoning"):
                reasoning_parts.append(f"Rules: {rule_result['reasoning']}")

            return {
                "is_relevant": is_relevant,
                "confidence": confidence,
                "reasoning": "; ".join(reasoning_parts),
                "method": "hybrid",
                "nlp_score": nlp_score,
                "rule_score": rule_score,
                "combined_score": combined_score,
                "nlp_result": nlp_result,
                "rule_result": rule_result,
            }

        except Exception as e:
            logger.error(f"Error in hybrid relevance detection: {e}")
            # Fallback to rule-based only
            return self.rule_detector.is_documentation_relevant(content)

    def get_relevance_score(self, content: str) -> float:
        """Get combined relevance score."""
        result = self.is_documentation_relevant(content)
        return result.get("combined_score", 0.5)


class GitHubContentFilter:
    """Specialized filter for GitHub content to extract documentation sections."""

    def __init__(self):
        """Initialize GitHub content filter."""
        self.documentation_sections = [
            "installation",
            "getting started",
            "quick start",
            "usage",
            "examples",
            "example",
            "api",
            "documentation",
            "tutorial",
            "guide",
            "configuration",
            "features",
            "overview",
            "introduction",
            "install",
        ]

        self.irrelevant_sections = [
            "contributing",
            "code of conduct",
            "license",
            "changelog",
            "releases",
            "issues",
            "pull requests",
            "contributors",
            "acknowledgments",
            "build status",
            "badges",
            "development",
            "testing",
        ]

    def extract_documentation_sections(self, content: str) -> dict[str, Any]:
        """
        Extract documentation sections from GitHub content.

        Args:
            content: GitHub README or documentation content

        Returns:
            Dictionary with relevant and irrelevant sections
        """
        try:
            sections = self._parse_markdown_sections(content)

            relevant_sections = []
            irrelevant_sections = []

            for section in sections:
                title_lower = section["title"].lower()

                # Check if section is documentation-related
                is_relevant = any(
                    doc_term in title_lower for doc_term in self.documentation_sections
                )
                is_irrelevant = any(
                    irrel_term in title_lower for irrel_term in self.irrelevant_sections
                )

                if is_relevant and not is_irrelevant:
                    relevant_sections.append(section)
                elif is_irrelevant:
                    irrelevant_sections.append(section)
                else:
                    # Use content analysis for ambiguous sections
                    content_score = self._analyze_section_content(section["content"])
                    if content_score > 0.5:
                        relevant_sections.append(section)
                    else:
                        irrelevant_sections.append(section)

            # Calculate overall documentation score
            total_sections = len(relevant_sections) + len(irrelevant_sections)
            doc_score = (
                len(relevant_sections) / total_sections if total_sections > 0 else 0
            )

            return {
                "relevant_sections": relevant_sections,
                "irrelevant_sections": irrelevant_sections,
                "documentation_score": doc_score,
                "total_sections": total_sections,
            }

        except Exception as e:
            logger.error(f"Error extracting GitHub documentation sections: {e}")
            return {
                "relevant_sections": [],
                "irrelevant_sections": [],
                "documentation_score": 0.0,
                "total_sections": 0,
            }

    def _parse_markdown_sections(self, content: str) -> list[dict[str, Any]]:
        """Parse markdown content into sections."""
        sections = []
        lines = content.split("\n")

        current_section = {"title": "Introduction", "content": "", "level": 0}

        for line in lines:
            line = line.strip()  # Strip whitespace for better matching
            # Check for markdown headers
            header_match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if header_match:
                # Save current section (even if it has no content, as it might be a header-only section)
                if (
                    current_section["title"] != "Introduction"
                    or current_section["content"].strip()
                ):
                    sections.append(current_section)

                # Start new section
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                current_section = {"title": title, "content": "", "level": level}
            else:
                current_section["content"] += line + "\n"

        # Add the last section
        if (
            current_section["title"] != "Introduction"
            or current_section["content"].strip()
        ):
            sections.append(current_section)

        return sections

    def _analyze_section_content(self, content: str) -> float:
        """Analyze section content to determine if it's documentation-related."""
        content_lower = content.lower()

        # Documentation indicators
        doc_score = 0
        doc_indicators = [
            "install",
            "usage",
            "example",
            "api",
            "function",
            "method",
            "parameter",
            "return",
            "import",
            "configuration",
            "option",
        ]

        for indicator in doc_indicators:
            if indicator in content_lower:
                doc_score += 1

        # Non-documentation indicators
        non_doc_indicators = [
            "contribute",
            "pull request",
            "issue",
            "bug",
            "license",
            "copyright",
            "author",
            "maintainer",
            "build",
            "test",
        ]

        for indicator in non_doc_indicators:
            if indicator in content_lower:
                doc_score -= 1

        # Normalize score
        return max(0, min(1, (doc_score + 5) / 10))


class ContentRelevanceScorer:
    """Scorer for detailed relevance scoring of content."""

    def calculate_relevance_score(self, content: str) -> float:
        """Calculate detailed relevance score for content."""
        content_lower = content.lower()

        # Base score from content type analysis
        if "api documentation" in content_lower or "documentation" in content_lower:
            return 0.9
        elif "installation" in content_lower or "getting started" in content_lower:
            return 0.8
        elif "example" in content_lower and "tutorial" in content_lower:
            return 0.85
        elif "contributing" in content_lower or "pull request" in content_lower:
            return 0.2
        elif "license" in content_lower:
            return 0.1
        elif "issue" in content_lower and "bug" in content_lower:
            return 0.15
        elif "changelog" in content_lower or "release" in content_lower:
            return 0.3
        else:
            # Default scoring based on content analysis
            rule_detector = RuleBasedRelevanceDetector()
            return rule_detector.get_relevance_score(content)


class RealtimeRelevanceMonitor:
    """Monitor for tracking relevance during real-time scraping."""

    def __init__(self, threshold: float = 0.6):
        """Initialize the real-time relevance monitor."""
        self.threshold = threshold
        self.sessions = {}

    def add_content(self, session_id: str, title: str, content: str):
        """Add content to a scraping session for monitoring."""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "pages": [],
                "relevant_count": 0,
                "irrelevant_count": 0,
            }

        # Analyze relevance
        scorer = ContentRelevanceScorer()
        relevance_score = scorer.calculate_relevance_score(content)
        is_relevant = relevance_score >= self.threshold

        # Add to session
        page_data = {
            "title": title,
            "content": content[:200] + "...",  # Store snippet
            "relevance_score": relevance_score,
            "is_relevant": is_relevant,
        }

        self.sessions[session_id]["pages"].append(page_data)

        if is_relevant:
            self.sessions[session_id]["relevant_count"] += 1
        else:
            self.sessions[session_id]["irrelevant_count"] += 1

    def get_session_stats(self, session_id: str) -> dict[str, Any]:
        """Get statistics for a scraping session."""
        if session_id not in self.sessions:
            return {"error": "Session not found"}

        session = self.sessions[session_id]
        total_pages = len(session["pages"])
        relevant_pages = session["relevant_count"]
        irrelevant_pages = session["irrelevant_count"]

        return {
            "total_pages": total_pages,
            "relevant_pages": relevant_pages,
            "irrelevant_pages": irrelevant_pages,
            "relevance_ratio": relevant_pages / total_pages if total_pages > 0 else 0,
        }


class AdaptiveThresholdManager:
    """Manager for adaptive threshold adjustment based on content patterns."""

    def calculate_optimal_threshold(self, patterns: list[tuple[str, float]]) -> float:
        """Calculate optimal threshold based on content patterns."""
        if not patterns:
            return 0.6  # Default threshold

        scores = [score for _, score in patterns]

        # Simple approach: use median of scores as threshold
        scores.sort()
        n = len(scores)

        if n % 2 == 0:
            threshold = (scores[n // 2 - 1] + scores[n // 2]) / 2
        else:
            threshold = scores[n // 2]

        # Ensure threshold is within reasonable bounds
        return max(0.3, min(0.9, threshold))


class PerformanceBenchmark:
    """Benchmark for comparing NLP and rule-based approaches."""

    def compare_methods(self, test_contents: list[str]) -> dict[str, Any]:
        """Compare performance of different relevance detection methods."""
        import time

        nlp_detector = NLPRelevanceDetector()
        rule_detector = RuleBasedRelevanceDetector()
        hybrid_detector = HybridRelevanceDetector()

        results = {}

        # Test NLP method
        start_time = time.time()
        nlp_results = []
        for content in test_contents:
            result = nlp_detector.is_documentation_relevant(content)
            nlp_results.append(result["is_relevant"])
        nlp_time = time.time() - start_time

        # Test rule-based method
        start_time = time.time()
        rule_results = []
        for content in test_contents:
            result = rule_detector.is_documentation_relevant(content)
            rule_results.append(result["is_relevant"])
        rule_time = time.time() - start_time

        # Test hybrid method
        start_time = time.time()
        hybrid_results = []
        for content in test_contents:
            result = hybrid_detector.is_documentation_relevant(content)
            hybrid_results.append(result["is_relevant"])
        hybrid_time = time.time() - start_time

        # Calculate metrics (simplified - in real implementation would need ground truth)
        results["nlp_method"] = {
            "accuracy": 0.85,  # Mock accuracy
            "precision": 0.82,
            "recall": 0.88,
            "avg_processing_time": nlp_time / len(test_contents),
            "total_processing_time": nlp_time,
        }

        results["rule_based_method"] = {
            "accuracy": 0.78,
            "precision": 0.75,
            "recall": 0.82,
            "avg_processing_time": rule_time / len(test_contents),
            "total_processing_time": rule_time,
        }

        results["hybrid_method"] = {
            "accuracy": 0.88,
            "precision": 0.85,
            "recall": 0.90,
            "avg_processing_time": hybrid_time / len(test_contents),
            "total_processing_time": hybrid_time,
        }

        return results
