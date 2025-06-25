#!/usr/bin/env python3
"""
Enhanced GitHub Repository Analysis
Comprehensive repository structure detection and documentation mapping.
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class SourcePriority(Enum):
    """Priority levels for documentation sources."""

    CRITICAL = 5  # README, main API docs
    HIGH = 4  # API reference, tutorials
    MEDIUM = 3  # Examples, guides
    LOW = 2  # Contributing, changelog
    MINIMAL = 1  # License, config files


class DocumentationType(Enum):
    """Types of documentation content."""

    PRIMARY = "primary_documentation"  # README, main docs
    API = "api_documentation"  # API reference
    TUTORIAL = "tutorial"  # Tutorials, guides
    EXAMPLE = "code_example"  # Code examples
    META = "meta_documentation"  # Contributing, changelog
    LEGAL = "legal"  # License, terms
    CONFIG = "configuration"  # Setup, config files
    MEDIA = "media"  # Images, videos


@dataclass
class RepositoryStructure:
    """Repository structure information."""

    repo_url: str
    has_readme: bool = False
    has_docs_folder: bool = False
    has_wiki: bool = False
    has_examples: bool = False
    documentation_system: str = "custom"
    primary_language: str = "unknown"
    documentation_files: list[str] = field(default_factory=list)
    example_files: list[str] = field(default_factory=list)
    config_files: list[str] = field(default_factory=list)
    total_files: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "repo_url": self.repo_url,
            "has_readme": self.has_readme,
            "has_docs_folder": self.has_docs_folder,
            "has_wiki": self.has_wiki,
            "has_examples": self.has_examples,
            "documentation_system": self.documentation_system,
            "primary_language": self.primary_language,
            "documentation_files": self.documentation_files,
            "example_files": self.example_files,
            "config_files": self.config_files,
            "total_files": self.total_files,
        }


@dataclass
class DocumentationMap:
    """Comprehensive documentation mapping."""

    primary_docs: list[str] = field(default_factory=list)
    api_docs: list[str] = field(default_factory=list)
    tutorials: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    meta_docs: list[str] = field(default_factory=list)
    media_files: list[str] = field(default_factory=list)
    total_files: int = 0
    total_documentation_size: int = 0
    estimated_read_time: int = 0  # minutes

    def calculate_statistics(self) -> dict[str, Any]:
        """Calculate documentation statistics."""
        return {
            "total_files": len(self.primary_docs)
            + len(self.api_docs)
            + len(self.tutorials)
            + len(self.examples),
            "api_coverage": len(self.api_docs),
            "tutorial_coverage": len(self.tutorials),
            "example_coverage": len(self.examples),
            "primary_coverage": len(self.primary_docs),
        }


@dataclass
class SourcePriorityInfo:
    """Source priority information."""

    priority: SourcePriority
    reasoning: str
    confidence: float
    doc_type: DocumentationType


class EnhancedGitHubAnalyzer:
    """Enhanced GitHub repository analyzer for comprehensive documentation discovery."""

    def __init__(self):
        """Initialize the enhanced analyzer."""
        self.documentation_patterns = {
            "readme": [r"readme\.md$", r"readme\.rst$", r"readme\.txt$", r"readme$"],
            "api_docs": [
                r"api\.md$",
                r"reference\.md$",
                r"docs/api/",
                r"docs/reference/",
            ],
            "tutorials": [r"tutorial", r"guide", r"getting.?started", r"quickstart"],
            "examples": [r"example", r"demo", r"sample"],
            "contributing": [r"contributing\.md$", r"contribute\.md$"],
            "changelog": [r"changelog\.md$", r"history\.md$", r"releases\.md$"],
            "license": [r"license", r"copying", r"copyright"],
            "config": [
                r"setup\.py$",
                r"requirements\.txt$",
                r"pyproject\.toml$",
                r"package\.json$",
                r"makefile$",
                r"dockerfile$",
            ],
        }

        self.source_priorities = {
            "readme": SourcePriority.CRITICAL,
            "api_docs": SourcePriority.HIGH,
            "tutorials": SourcePriority.HIGH,
            "examples": SourcePriority.MEDIUM,
            "contributing": SourcePriority.LOW,
            "changelog": SourcePriority.LOW,
            "license": SourcePriority.MINIMAL,
            "config": SourcePriority.MINIMAL,
        }

        self.doc_systems = {
            "sphinx": [r"conf\.py$", r"index\.rst$", r"makefile$"],
            "mkdocs": [r"mkdocs\.yml$", r"mkdocs\.yaml$"],
            "gitbook": [r"book\.json$", r"summary\.md$"],
            "docusaurus": [r"docusaurus\.config\.js$", r"sidebars\.js$"],
            "vuepress": [r"\.vuepress/config\.js$"],
            "docsify": [r"index\.html$", r"_sidebar\.md$"],
        }

    def analyze_repository_structure(
        self, repo_url: str, file_tree: list[str] = None
    ) -> RepositoryStructure:
        """
        Analyze complete repository structure for documentation.

        Args:
            repo_url: Repository URL
            file_tree: List of file paths in repository

        Returns:
            RepositoryStructure with comprehensive analysis
        """
        if file_tree is None:
            file_tree = self._fetch_repository_file_tree(repo_url)

        structure = RepositoryStructure(repo_url=repo_url)
        structure.total_files = len(file_tree)

        # Detect basic structure
        structure.has_readme = self._has_readme(file_tree)
        structure.has_docs_folder = self._has_docs_folder(file_tree)
        structure.has_examples = self._has_examples(file_tree)
        structure.has_wiki = self._has_wiki(repo_url)  # Would need API call

        # Detect documentation system
        structure.documentation_system = self.detect_documentation_system(file_tree)

        # Classify files
        structure.documentation_files = self._find_documentation_files(file_tree)
        structure.example_files = self._find_example_files(file_tree)
        structure.config_files = self._find_config_files(file_tree)

        # Detect primary language
        structure.primary_language = self._detect_primary_language(file_tree)

        logger.info(
            f"Analyzed repository {repo_url}: {len(structure.documentation_files)} docs, "
            f"{len(structure.example_files)} examples, system: {structure.documentation_system}"
        )

        return structure

    def create_documentation_map(
        self, files_with_content: dict[str, dict[str, Any]]
    ) -> DocumentationMap:
        """
        Create comprehensive documentation map from files with content.

        Args:
            files_with_content: Dict mapping file paths to content metadata

        Returns:
            DocumentationMap with categorized files
        """
        doc_map = DocumentationMap()
        total_size = 0

        for file_path, metadata in files_with_content.items():
            file_type = self._classify_file_type(file_path)
            content_size = metadata.get("size", 0)
            total_size += content_size

            if file_type == DocumentationType.PRIMARY:
                doc_map.primary_docs.append(file_path)
            elif file_type == DocumentationType.API:
                doc_map.api_docs.append(file_path)
            elif file_type == DocumentationType.TUTORIAL:
                doc_map.tutorials.append(file_path)
            elif file_type == DocumentationType.EXAMPLE:
                doc_map.examples.append(file_path)
            elif file_type == DocumentationType.META:
                doc_map.meta_docs.append(file_path)
            elif file_type == DocumentationType.MEDIA:
                doc_map.media_files.append(file_path)

        doc_map.total_files = len(files_with_content)
        doc_map.total_documentation_size = total_size
        doc_map.estimated_read_time = self._estimate_read_time(total_size)

        return doc_map

    def assign_source_priorities(
        self, sources: list[dict[str, Any]]
    ) -> dict[str, SourcePriorityInfo]:
        """
        Assign intelligent priorities to documentation sources.

        Args:
            sources: List of source information dicts

        Returns:
            Dict mapping source paths to priority information
        """
        priorities = {}

        for source in sources:
            path = source["path"]
            source_type = source.get("type", "unknown")
            size = source.get("size", 0)

            # Determine base priority from type
            base_priority = self.source_priorities.get(
                source_type, SourcePriority.MEDIUM
            )

            # Adjust priority based on content characteristics
            adjusted_priority, reasoning = self._adjust_priority_by_content(
                base_priority, path, size, source_type
            )

            # Calculate confidence based on multiple factors
            confidence = self._calculate_priority_confidence(path, source_type, size)

            # Determine documentation type
            doc_type = self._classify_file_type(path)

            priorities[path] = SourcePriorityInfo(
                priority=adjusted_priority,
                reasoning=reasoning,
                confidence=confidence,
                doc_type=doc_type,
            )

        return priorities

    def generate_crawl_targets(
        self, structure: RepositoryStructure
    ) -> list[dict[str, Any]]:
        """
        Generate optimized crawl targets based on repository structure.

        Args:
            structure: Repository structure analysis

        Returns:
            List of crawl target configurations
        """
        targets = []
        base_url = structure.repo_url

        # Main repository target
        targets.append(
            {
                "url": base_url,
                "type": "repository_main",
                "depth": 2,
                "priority": SourcePriority.HIGH.value,
                "include_patterns": [r"/README", r".*\.md$"],
                "exclude_patterns": [r"/\.git/", r"/node_modules/", r"/__pycache__/"],
            }
        )

        # Docs folder target
        if structure.has_docs_folder:
            targets.append(
                {
                    "url": f"{base_url}/tree/main/docs",
                    "type": "docs_folder",
                    "depth": 3,
                    "priority": SourcePriority.HIGH.value,
                    "include_patterns": [r".*\.md$", r".*\.rst$", r".*\.txt$"],
                    "exclude_patterns": [r"/\.git/", r"/_build/"],
                }
            )

        # Examples target
        if structure.has_examples:
            targets.append(
                {
                    "url": f"{base_url}/tree/main/examples",
                    "type": "examples",
                    "depth": 2,
                    "priority": SourcePriority.MEDIUM.value,
                    "include_patterns": [r".*\.py$", r".*\.js$", r".*\.md$"],
                    "exclude_patterns": [r"/__pycache__/", r"/node_modules/"],
                }
            )

        # Wiki target
        if structure.has_wiki:
            targets.append(
                {
                    "url": f"{base_url}/wiki",
                    "type": "wiki",
                    "depth": 2,
                    "priority": SourcePriority.MEDIUM.value,
                    "include_patterns": [r".*"],
                    "exclude_patterns": [],
                }
            )

        return targets

    def detect_documentation_system(self, file_list: list[str]) -> str:
        """
        Detect the documentation system used in the repository.

        Args:
            file_list: List of file paths

        Returns:
            Documentation system name
        """
        file_list_lower = [f.lower() for f in file_list]

        for system, patterns in self.doc_systems.items():
            for pattern in patterns:
                if any(re.search(pattern, f, re.IGNORECASE) for f in file_list_lower):
                    return system

        # Check for common documentation patterns
        if any("docs/" in f for f in file_list):
            return "custom"

        return "basic"

    def classify_file_types(self, file_list: list[str]) -> dict[str, DocumentationType]:
        """
        Classify file types for documentation analysis.

        Args:
            file_list: List of file paths

        Returns:
            Dict mapping file paths to documentation types
        """
        classifications = {}

        for file_path in file_list:
            classifications[file_path] = self._classify_file_type(file_path)

        return classifications

    def assess_documentation_quality(self, doc_map: DocumentationMap) -> dict[str, Any]:
        """
        Assess documentation quality and completeness.

        Args:
            doc_map: Documentation map

        Returns:
            Quality assessment results
        """
        stats = doc_map.calculate_statistics()

        # Calculate completeness score
        completeness_factors = {
            "has_primary": min(len(doc_map.primary_docs), 1),
            "has_api": min(len(doc_map.api_docs), 1),
            "has_tutorials": min(len(doc_map.tutorials), 1),
            "has_examples": min(len(doc_map.examples), 1),
        }
        completeness_score = sum(completeness_factors.values()) / len(
            completeness_factors
        )

        # Calculate quality score based on content volume and diversity
        quality_factors = {
            "content_volume": min(
                doc_map.total_documentation_size / 10000, 1
            ),  # Normalize to 10KB
            "file_diversity": min(
                stats["total_files"] / 10, 1
            ),  # Normalize to 10 files
            "read_time": min(
                doc_map.estimated_read_time / 30, 1
            ),  # Normalize to 30 minutes
        }
        quality_score = sum(quality_factors.values()) / len(quality_factors)

        # Identify missing components
        missing_components = []
        if not doc_map.primary_docs:
            missing_components.append("Primary documentation (README)")
        if not doc_map.api_docs:
            missing_components.append("API documentation")
        if not doc_map.tutorials:
            missing_components.append("Tutorials or guides")
        if not doc_map.examples:
            missing_components.append("Code examples")

        # Generate recommendations
        recommendations = self._generate_quality_recommendations(
            doc_map, missing_components
        )

        return {
            "completeness_score": completeness_score,
            "quality_score": quality_score,
            "coverage_areas": {
                "primary": len(doc_map.primary_docs),
                "api": len(doc_map.api_docs),
                "tutorials": len(doc_map.tutorials),
                "examples": len(doc_map.examples),
            },
            "missing_components": missing_components,
            "recommendations": recommendations,
            "total_files": stats["total_files"],
            "estimated_read_time": doc_map.estimated_read_time,
        }

    def discover_nested_structure(self, file_list: list[str]) -> dict[str, Any]:
        """
        Discover nested documentation structure.

        Args:
            file_list: List of file paths

        Returns:
            Nested structure analysis
        """
        nested_map = {}

        # Group files by documentation directories (including subdirectories)
        for file_path in file_list:
            if "/" in file_path:
                parts = file_path.split("/")

                # Handle docs/ subdirectories as separate categories
                if parts[0] == "docs" and len(parts) > 2:
                    subdir = parts[1]  # user-guide, api, tutorials, etc.
                    if subdir not in nested_map:
                        nested_map[subdir] = {
                            "files": [],
                            "subdirs": set(),
                            "max_depth": 0,
                        }

                    nested_map[subdir]["files"].append(file_path)
                    nested_map[subdir]["max_depth"] = max(
                        nested_map[subdir]["max_depth"],
                        len(parts) - 2,  # Depth relative to docs/subdir/
                    )

                    if len(parts) > 3:
                        nested_map[subdir]["subdirs"].add(parts[2])

                # Handle top-level documentation directories
                elif parts[0] in [
                    "docs",
                    "documentation",
                    "guides",
                    "tutorials",
                    "examples",
                ]:
                    top_dir = parts[0]
                    if top_dir not in nested_map:
                        nested_map[top_dir] = {
                            "files": [],
                            "subdirs": set(),
                            "max_depth": 0,
                        }

                    nested_map[top_dir]["files"].append(file_path)
                    nested_map[top_dir]["max_depth"] = max(
                        nested_map[top_dir]["max_depth"], len(parts) - 1
                    )

                    if len(parts) > 2:
                        nested_map[top_dir]["subdirs"].add(parts[1])

        # Convert sets to lists for JSON serialization
        for dir_info in nested_map.values():
            dir_info["subdirs"] = list(dir_info["subdirs"])

        return nested_map

    def analyze_wiki_structure(self, wiki_info: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze GitHub wiki structure.

        Args:
            wiki_info: Wiki information from GitHub API

        Returns:
            Wiki analysis results
        """
        if not wiki_info.get("has_wiki", False):
            return {"has_wiki": False}

        wiki_pages = wiki_info.get("wiki_pages", [])

        # Categorize wiki pages
        page_categories = {
            "home": [],
            "documentation": [],
            "guides": [],
            "faq": [],
            "other": [],
        }

        total_size = 0
        for page in wiki_pages:
            title = page.get("title", "").lower()
            size = page.get("size", 0)
            total_size += size

            if "home" in title:
                page_categories["home"].append(page)
            elif any(word in title for word in ["install", "setup", "config"]):
                page_categories["documentation"].append(page)
            elif any(word in title for word in ["guide", "tutorial", "how"]):
                page_categories["guides"].append(page)
            elif "faq" in title or "question" in title:
                page_categories["faq"].append(page)
            else:
                page_categories["other"].append(page)

        return {
            "has_wiki": True,
            "total_pages": len(wiki_pages),
            "total_size": total_size,
            "page_categories": page_categories,
            "crawl_priority": SourcePriority.MEDIUM.value,
        }

    def analyze_with_relevance_context(
        self, content: str, file_path: str, repository_context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Analyze content with repository context for enhanced relevance detection.

        Args:
            content: File content
            file_path: Path to file in repository
            repository_context: Repository context information

        Returns:
            Enhanced relevance analysis
        """
        # Get base relevance score from existing system
        try:
            from .relevance_detection import GitHubContentFilter

            github_filter = GitHubContentFilter()
            base_result = github_filter.extract_documentation_sections(content)
            base_score = base_result.get("documentation_score", 0.5)
        except ImportError:
            base_score = 0.5

        # Apply context boost based on file location and type
        context_boost = 0.0
        file_type = repository_context.get("type", "unknown")

        if file_type == "api_documentation":
            context_boost = 0.2
        elif file_type == "tutorial":
            context_boost = 0.15
        elif "docs/" in file_path:
            context_boost = 0.1
        elif file_path.lower().startswith("readme"):
            context_boost = 0.25

        # Calculate file type confidence
        file_type_confidence = self._calculate_file_type_confidence(file_path, content)

        # Combine scores
        final_score = min(base_score + context_boost, 1.0)

        return {
            "relevance_score": final_score,
            "base_score": base_score,
            "context_boost": context_boost,
            "file_type_confidence": file_type_confidence,
            "file_type": file_type,
            "reasoning": f"Base: {base_score:.2f}, Context boost: {context_boost:.2f}, Final: {final_score:.2f}",
        }

    # Private helper methods

    def _fetch_repository_file_tree(self, repo_url: str) -> list[str]:
        """Fetch repository file tree (would use GitHub API in real implementation)."""
        # Mock implementation - in real version would use GitHub API
        return []

    def _has_readme(self, file_list: list[str]) -> bool:
        """Check if repository has README file."""
        return any(re.search(r"readme\.", f, re.IGNORECASE) for f in file_list)

    def _has_docs_folder(self, file_list: list[str]) -> bool:
        """Check if repository has docs folder."""
        return any(f.startswith("docs/") for f in file_list)

    def _has_examples(self, file_list: list[str]) -> bool:
        """Check if repository has examples."""
        return any("example" in f.lower() for f in file_list)

    def _has_wiki(self, repo_url: str) -> bool:
        """Check if repository has wiki (would use GitHub API)."""
        # Mock implementation - in real version would check GitHub API
        return False

    def _find_documentation_files(self, file_list: list[str]) -> list[str]:
        """Find documentation files in repository."""
        doc_files = []
        for file_path in file_list:
            if any(
                re.search(pattern, file_path, re.IGNORECASE)
                for patterns in self.documentation_patterns.values()
                for pattern in patterns
            ):
                if file_path.endswith((".md", ".rst", ".txt")):
                    doc_files.append(file_path)
        return doc_files

    def _find_example_files(self, file_list: list[str]) -> list[str]:
        """Find example files in repository."""
        return [f for f in file_list if "example" in f.lower() or "demo" in f.lower()]

    def _find_config_files(self, file_list: list[str]) -> list[str]:
        """Find configuration files in repository."""
        config_files = []
        for file_path in file_list:
            if any(
                re.search(pattern, file_path, re.IGNORECASE)
                for pattern in self.documentation_patterns["config"]
            ):
                config_files.append(file_path)
        return config_files

    def _detect_primary_language(self, file_list: list[str]) -> str:
        """Detect primary programming language."""
        extensions = {}
        for file_path in file_list:
            if "." in file_path:
                ext = file_path.split(".")[-1].lower()
                extensions[ext] = extensions.get(ext, 0) + 1

        if not extensions:
            return "unknown"

        # Map extensions to languages
        lang_map = {
            "py": "python",
            "js": "javascript",
            "ts": "typescript",
            "java": "java",
            "cpp": "cpp",
            "c": "c",
            "go": "go",
            "rs": "rust",
            "rb": "ruby",
            "php": "php",
        }

        most_common_ext = max(extensions, key=extensions.get)
        return lang_map.get(most_common_ext, most_common_ext)

    def _classify_file_type(self, file_path: str) -> DocumentationType:
        """Classify file type for documentation purposes."""
        file_lower = file_path.lower()

        if re.search(r"readme\.", file_lower):
            return DocumentationType.PRIMARY
        elif "api" in file_lower or "reference" in file_lower:
            return DocumentationType.API
        elif any(word in file_lower for word in ["tutorial", "guide", "getting"]):
            return DocumentationType.TUTORIAL
        elif any(word in file_lower for word in ["example", "demo", "sample"]):
            return DocumentationType.EXAMPLE
        elif any(
            word in file_lower for word in ["contributing", "changelog", "history"]
        ):
            return DocumentationType.META
        elif any(word in file_lower for word in ["license", "copying"]):
            return DocumentationType.LEGAL
        elif any(ext in file_lower for ext in [".png", ".jpg", ".gif", ".mp4", ".svg"]):
            return DocumentationType.MEDIA
        elif any(word in file_lower for word in ["setup", "config", "requirements"]):
            return DocumentationType.CONFIG
        else:
            return DocumentationType.PRIMARY

    def _adjust_priority_by_content(
        self, base_priority: SourcePriority, path: str, size: int, source_type: str
    ) -> tuple[SourcePriority, str]:
        """Adjust priority based on content characteristics."""
        adjusted = base_priority
        reasoning = f"Base priority for {source_type}"

        # Boost priority for substantial content
        if size > 5000:  # Large files likely more important
            if adjusted.value < SourcePriority.HIGH.value:
                adjusted = SourcePriority(adjusted.value + 1)
                reasoning += ", boosted for substantial content"

        # Boost priority for API documentation
        if "api" in path.lower() or "reference" in path.lower():
            adjusted = SourcePriority.HIGH
            reasoning += ", boosted for API documentation"

        # Lower priority for very small files
        if size < 100:
            if adjusted.value > SourcePriority.MINIMAL.value:
                adjusted = SourcePriority(adjusted.value - 1)
                reasoning += ", lowered for minimal content"

        return adjusted, reasoning

    def _calculate_priority_confidence(
        self, path: str, source_type: str, size: int
    ) -> float:
        """Calculate confidence in priority assignment."""
        confidence = 0.5  # Base confidence

        # Higher confidence for clear patterns
        if any(pattern in path.lower() for pattern in ["readme", "api", "docs/"]):
            confidence += 0.3

        # Higher confidence for substantial content
        if size > 1000:
            confidence += 0.2

        # Lower confidence for ambiguous files
        if source_type == "unknown":
            confidence -= 0.2

        return min(max(confidence, 0.0), 1.0)

    def _estimate_read_time(self, total_size: int) -> int:
        """Estimate reading time in minutes based on content size."""
        # Assume average reading speed of 200 words per minute
        # and average of 5 characters per word
        words = total_size / 5
        return max(int(words / 200), 1)

    def _generate_quality_recommendations(
        self, doc_map: DocumentationMap, missing_components: list[str]
    ) -> list[str]:
        """Generate recommendations for improving documentation quality."""
        recommendations = []

        if not doc_map.primary_docs:
            recommendations.append("Add a comprehensive README.md file")

        if not doc_map.api_docs:
            recommendations.append("Create API documentation or reference guide")

        if not doc_map.tutorials:
            recommendations.append("Add tutorials or getting started guides")

        if not doc_map.examples:
            recommendations.append("Include code examples and demos")

        if doc_map.estimated_read_time < 5:
            recommendations.append("Expand documentation content for better coverage")

        return recommendations

    def _calculate_file_type_confidence(self, file_path: str, content: str) -> float:
        """Calculate confidence in file type classification."""
        confidence = 0.5

        # Path-based confidence
        if "docs/" in file_path:
            confidence += 0.2
        if "api" in file_path.lower():
            confidence += 0.3
        if file_path.lower().startswith("readme"):
            confidence += 0.4

        # Content-based confidence (basic heuristics)
        if len(content) > 1000:
            confidence += 0.1
        if "```" in content or ".. code-block::" in content:
            confidence += 0.1

        return min(confidence, 1.0)
