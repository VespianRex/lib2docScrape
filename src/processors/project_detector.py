#!/usr/bin/env python3
"""
Project Type Detector for Multi-Library Documentation

Automatically detects project type based on files and structure.
"""

import re
from pathlib import Path
from typing import Any


class ProjectTypeDetector:
    """Detector for automatically identifying project types and structures."""

    def __init__(self):
        """Initialize the project type detector."""
        self.type_indicators = {
            "python": {
                "files": [
                    "requirements.txt",
                    "setup.py",
                    "pyproject.toml",
                    "Pipfile",
                    "setup.cfg",
                    "tox.ini",
                    "pytest.ini",
                    "conftest.py",
                ],
                "extensions": [".py"],
                "directories": ["__pycache__", ".pytest_cache", "venv", "env"],
                "patterns": [r".*\.py$", r"requirements.*\.txt$"],
            },
            "javascript": {
                "files": [
                    "package.json",
                    "package-lock.json",
                    "yarn.lock",
                    "bower.json",
                    "npm-shrinkwrap.json",
                    ".npmrc",
                    "webpack.config.js",
                    "vite.config.js",
                ],
                "extensions": [".js", ".ts", ".jsx", ".tsx", ".mjs"],
                "directories": ["node_modules", "dist", "build"],
                "patterns": [r".*\.(js|ts|jsx|tsx|mjs)$"],
            },
            "rust": {
                "files": ["Cargo.toml", "Cargo.lock"],
                "extensions": [".rs"],
                "directories": ["target", "src"],
                "patterns": [r".*\.rs$"],
            },
            "go": {
                "files": ["go.mod", "go.sum", "Gopkg.toml", "Gopkg.lock"],
                "extensions": [".go"],
                "directories": ["vendor"],
                "patterns": [r".*\.go$"],
            },
            "java": {
                "files": [
                    "pom.xml",
                    "build.gradle",
                    "build.gradle.kts",
                    "settings.gradle",
                ],
                "extensions": [".java", ".kt", ".scala"],
                "directories": ["target", "build", ".gradle"],
                "patterns": [r".*\.(java|kt|scala)$"],
            },
            "csharp": {
                "files": ["*.csproj", "*.sln", "packages.config", "project.json"],
                "extensions": [".cs", ".vb"],
                "directories": ["bin", "obj", "packages"],
                "patterns": [r".*\.(cs|vb)$"],
            },
            "php": {
                "files": ["composer.json", "composer.lock"],
                "extensions": [".php"],
                "directories": ["vendor"],
                "patterns": [r".*\.php$"],
            },
            "ruby": {
                "files": ["Gemfile", "Gemfile.lock", "*.gemspec"],
                "extensions": [".rb"],
                "directories": ["vendor"],
                "patterns": [r".*\.rb$"],
            },
        }

    def detect_project_type(self, file_list: list[str]) -> str:
        """
        Detect project type based on file list.

        Args:
            file_list: List of file names/paths in the project

        Returns:
            Detected project type string
        """
        scores = {}

        # Calculate scores for each project type
        for project_type, indicators in self.type_indicators.items():
            score = self._calculate_type_score(file_list, indicators)
            scores[project_type] = score

        # Return the type with highest score
        if scores:
            best_type = max(scores, key=scores.get)
            if scores[best_type] > 0:
                return best_type

        return "unknown"

    def detect_multiple_types(self, file_list: list[str]) -> list[dict[str, Any]]:
        """
        Detect multiple project types (for polyglot projects).

        Args:
            file_list: List of file names/paths in the project

        Returns:
            List of detected types with confidence scores
        """
        results = []

        for project_type, indicators in self.type_indicators.items():
            score = self._calculate_type_score(file_list, indicators)
            if score > 0:
                confidence = min(score / 10.0, 1.0)  # Normalize to 0-1
                results.append(
                    {"type": project_type, "confidence": confidence, "score": score}
                )

        # Sort by confidence
        results.sort(key=lambda x: x["confidence"], reverse=True)
        return results

    def _calculate_type_score(
        self, file_list: list[str], indicators: dict[str, list[str]]
    ) -> int:
        """Calculate score for a specific project type."""
        score = 0
        file_set = set(file_list)

        # Check for specific files
        for file_name in indicators.get("files", []):
            if file_name in file_set:
                score += 5
            elif any(self._matches_pattern(f, file_name) for f in file_list):
                score += 3

        # Check for file extensions
        extensions = indicators.get("extensions", [])
        for file_path in file_list:
            file_ext = Path(file_path).suffix.lower()
            if file_ext in extensions:
                score += 1

        # Check for directories
        for dir_name in indicators.get("directories", []):
            if dir_name in file_set or any(dir_name in f for f in file_list):
                score += 2

        # Check patterns
        for pattern in indicators.get("patterns", []):
            pattern_matches = sum(1 for f in file_list if re.match(pattern, f))
            score += pattern_matches

        return score

    def _matches_pattern(self, file_name: str, pattern: str) -> bool:
        """Check if file name matches a pattern (supports wildcards)."""
        if "*" in pattern:
            # Convert glob pattern to regex
            regex_pattern = pattern.replace("*", ".*")
            return bool(re.match(regex_pattern, file_name))
        return file_name == pattern

    def analyze_project_structure(self, file_list: list[str]) -> dict[str, Any]:
        """
        Analyze project structure and provide detailed information.

        Args:
            file_list: List of file names/paths in the project

        Returns:
            Detailed project structure analysis
        """
        detected_types = self.detect_multiple_types(file_list)
        primary_type = detected_types[0]["type"] if detected_types else "unknown"

        analysis = {
            "primary_type": primary_type,
            "detected_types": detected_types,
            "is_polyglot": len(detected_types) > 1,
            "file_count": len(file_list),
            "structure_analysis": self._analyze_structure(file_list),
            "dependency_files": self._find_dependency_files(file_list),
            "documentation_files": self._find_documentation_files(file_list),
        }

        return analysis

    def _analyze_structure(self, file_list: list[str]) -> dict[str, Any]:
        """Analyze the overall project structure."""
        structure = {
            "has_src_directory": any("src/" in f for f in file_list),
            "has_lib_directory": any("lib/" in f for f in file_list),
            "has_test_directory": any(
                any(test_dir in f for test_dir in ["test/", "tests/", "__tests__/"])
                for f in file_list
            ),
            "has_docs_directory": any("docs/" in f for f in file_list),
            "has_examples_directory": any("examples/" in f for f in file_list),
            "directory_depth": max(f.count("/") for f in file_list) if file_list else 0,
            "total_files": len(file_list),
        }

        return structure

    def _find_dependency_files(self, file_list: list[str]) -> list[dict[str, str]]:
        """Find dependency management files."""
        dependency_patterns = {
            "requirements.txt": "python",
            "package.json": "javascript",
            "Cargo.toml": "rust",
            "go.mod": "go",
            "pom.xml": "java",
            "build.gradle": "java",
            "composer.json": "php",
            "Gemfile": "ruby",
            "pyproject.toml": "python",
            "Pipfile": "python",
        }

        found_files = []
        for file_path in file_list:
            file_name = Path(file_path).name
            if file_name in dependency_patterns:
                found_files.append(
                    {
                        "file": file_path,
                        "type": dependency_patterns[file_name],
                        "name": file_name,
                    }
                )

        return found_files

    def _find_documentation_files(self, file_list: list[str]) -> list[str]:
        """Find documentation files."""
        doc_patterns = [
            r"README.*",
            r"CHANGELOG.*",
            r"CONTRIBUTING.*",
            r"LICENSE.*",
            r".*\.md$",
            r".*\.rst$",
            r"docs/.*",
            r"documentation/.*",
        ]

        doc_files = []
        for file_path in file_list:
            file_name = Path(file_path).name
            if any(
                re.match(pattern, file_name, re.IGNORECASE) for pattern in doc_patterns
            ):
                doc_files.append(file_path)
            elif any(
                doc_dir in file_path.lower() for doc_dir in ["docs/", "documentation/"]
            ):
                doc_files.append(file_path)

        return doc_files

    def suggest_missing_files(
        self, file_list: list[str], project_type: str
    ) -> list[dict[str, str]]:
        """
        Suggest missing files that are common for the project type.

        Args:
            file_list: Current file list
            project_type: Detected project type

        Returns:
            List of suggested files to add
        """
        suggestions = []
        file_set = set(file_list)

        common_files = {
            "python": [
                ("README.md", "Project documentation"),
                ("requirements.txt", "Python dependencies"),
                ("setup.py", "Package setup script"),
                (".gitignore", "Git ignore file"),
                ("tests/", "Test directory"),
                ("LICENSE", "License file"),
            ],
            "javascript": [
                ("README.md", "Project documentation"),
                ("package.json", "Node.js dependencies"),
                (".gitignore", "Git ignore file"),
                ("src/", "Source code directory"),
                ("tests/", "Test directory"),
                ("LICENSE", "License file"),
            ],
            "rust": [
                ("README.md", "Project documentation"),
                ("Cargo.toml", "Rust dependencies"),
                (".gitignore", "Git ignore file"),
                ("src/", "Source code directory"),
                ("tests/", "Test directory"),
                ("LICENSE", "License file"),
            ],
        }

        if project_type in common_files:
            for file_name, description in common_files[project_type]:
                if file_name not in file_set and not any(
                    file_name in f for f in file_list
                ):
                    suggestions.append(
                        {
                            "file": file_name,
                            "description": description,
                            "priority": "high"
                            if file_name in ["README.md", "LICENSE"]
                            else "medium",
                        }
                    )

        return suggestions
