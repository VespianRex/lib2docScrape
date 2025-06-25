#!/usr/bin/env python3
"""
Dependency Parser for Multi-Library Documentation

Parses various dependency files (requirements.txt, package.json, Cargo.toml, etc.)
to extract library dependencies for comprehensive documentation generation.
"""

import json
import re
from pathlib import Path
from typing import Any, Optional

import toml


class DependencyParser:
    """Parser for extracting dependencies from various project files."""

    def __init__(self):
        """Initialize the dependency parser."""
        self.supported_formats = [
            "requirements.txt",
            "package.json",
            "Cargo.toml",
            "pyproject.toml",
            "setup.py",
            "Pipfile",
        ]

    def parse_requirements(self, content: str) -> list[dict[str, Any]]:
        """
        Parse Python requirements.txt file content.

        Args:
            content: Raw content of requirements.txt file

        Returns:
            List of dependency dictionaries with name, version, type
        """
        dependencies = []

        # Split content into lines and process each
        lines = content.strip().split("\n")

        for line in lines:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Parse dependency line
            dependency = self._parse_requirement_line(line)
            if dependency:
                dependencies.append(dependency)

        return dependencies

    def parse_package_json(self, content: str) -> list[dict[str, Any]]:
        """
        Parse Node.js package.json file content.

        Args:
            content: Raw JSON content of package.json file

        Returns:
            List of dependency dictionaries with name, version, type, dev flag
        """
        dependencies = []

        try:
            data = json.loads(content)

            # Parse production dependencies
            if "dependencies" in data:
                for name, version in data["dependencies"].items():
                    dependencies.append(
                        {
                            "name": name,
                            "version": version,
                            "type": "javascript",
                            "dev": False,
                            "source": "dependencies",
                        }
                    )

            # Parse development dependencies
            if "devDependencies" in data:
                for name, version in data["devDependencies"].items():
                    dependencies.append(
                        {
                            "name": name,
                            "version": version,
                            "type": "javascript",
                            "dev": True,
                            "source": "devDependencies",
                        }
                    )

            # Parse peer dependencies
            if "peerDependencies" in data:
                for name, version in data["peerDependencies"].items():
                    dependencies.append(
                        {
                            "name": name,
                            "version": version,
                            "type": "javascript",
                            "dev": False,
                            "source": "peerDependencies",
                        }
                    )

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in package.json: {e}")

        return dependencies

    def parse_cargo_toml(self, content: str) -> list[dict[str, Any]]:
        """
        Parse Rust Cargo.toml file content.

        Args:
            content: Raw TOML content of Cargo.toml file

        Returns:
            List of dependency dictionaries with name, version, type
        """
        dependencies = []

        try:
            data = toml.loads(content)

            # Parse dependencies
            if "dependencies" in data:
                for name, version_info in data["dependencies"].items():
                    if isinstance(version_info, str):
                        version = version_info
                    elif isinstance(version_info, dict):
                        version = version_info.get("version", "latest")
                    else:
                        version = "latest"

                    dependencies.append(
                        {
                            "name": name,
                            "version": version,
                            "type": "rust",
                            "dev": False,
                            "source": "dependencies",
                        }
                    )

            # Parse dev dependencies
            if "dev-dependencies" in data:
                for name, version_info in data["dev-dependencies"].items():
                    if isinstance(version_info, str):
                        version = version_info
                    elif isinstance(version_info, dict):
                        version = version_info.get("version", "latest")
                    else:
                        version = "latest"

                    dependencies.append(
                        {
                            "name": name,
                            "version": version,
                            "type": "rust",
                            "dev": True,
                            "source": "dev-dependencies",
                        }
                    )

        except toml.TomlDecodeError as e:
            raise ValueError(f"Invalid TOML in Cargo.toml: {e}")

        return dependencies

    def parse_pyproject_toml(self, content: str) -> list[dict[str, Any]]:
        """
        Parse Python pyproject.toml file content.

        Args:
            content: Raw TOML content of pyproject.toml file

        Returns:
            List of dependency dictionaries with name, version, type
        """
        dependencies = []

        try:
            data = toml.loads(content)

            # Parse project dependencies
            if "project" in data and "dependencies" in data["project"]:
                for dep_string in data["project"]["dependencies"]:
                    dependency = self._parse_requirement_line(dep_string)
                    if dependency:
                        dependencies.append(dependency)

            # Parse build system dependencies
            if "build-system" in data and "requires" in data["build-system"]:
                for dep_string in data["build-system"]["requires"]:
                    dependency = self._parse_requirement_line(dep_string)
                    if dependency:
                        dependency["source"] = "build-system"
                        dependencies.append(dependency)

        except toml.TomlDecodeError as e:
            raise ValueError(f"Invalid TOML in pyproject.toml: {e}")

        return dependencies

    def _parse_requirement_line(self, line: str) -> Optional[dict[str, Any]]:
        """
        Parse a single requirement line (e.g., 'requests>=2.28.0').

        Args:
            line: Single requirement line

        Returns:
            Dependency dictionary or None if invalid
        """
        # Remove inline comments
        line = line.split("#")[0].strip()

        if not line:
            return None

        # Handle git URLs and other complex formats
        if line.startswith("git+") or "://" in line:
            # Extract package name from URL
            if "#egg=" in line:
                name = line.split("#egg=")[1].split("&")[0]
                return {
                    "name": name,
                    "version": "git",
                    "type": "python",
                    "source": "git",
                    "url": line,
                }
            return None

        # Parse standard requirement format
        # Pattern: package_name[extras]>=version,<version
        pattern = r"^([a-zA-Z0-9_.-]+)(?:\[[^\]]*\])?([><=!~]+.*)?$"
        match = re.match(pattern, line)

        if match:
            name = match.group(1)
            version_spec = match.group(2) or ""

            return {
                "name": name,
                "version": version_spec,
                "type": "python",
                "source": "requirements",
            }

        return None

    def detect_project_type(self, file_list: list[str]) -> str:
        """
        Detect project type based on present files.

        Args:
            file_list: List of file names in the project

        Returns:
            Project type string ('python', 'javascript', 'rust', etc.)
        """
        file_set = set(file_list)

        # Python project indicators
        python_files = {
            "requirements.txt",
            "setup.py",
            "pyproject.toml",
            "Pipfile",
            "setup.cfg",
            "tox.ini",
        }
        if file_set & python_files:
            return "python"

        # JavaScript/Node.js project indicators
        js_files = {
            "package.json",
            "package-lock.json",
            "yarn.lock",
            "npm-shrinkwrap.json",
            "bower.json",
        }
        if file_set & js_files:
            return "javascript"

        # Rust project indicators
        rust_files = {"Cargo.toml", "Cargo.lock"}
        if file_set & rust_files:
            return "rust"

        # Go project indicators
        go_files = {"go.mod", "go.sum", "Gopkg.toml"}
        if file_set & go_files:
            return "go"

        # Java project indicators
        java_files = {"pom.xml", "build.gradle", "build.gradle.kts"}
        if file_set & java_files:
            return "java"

        # Default to unknown
        return "unknown"

    def parse_file(self, file_path: str, content: str) -> list[dict[str, Any]]:
        """
        Parse a dependency file based on its name/extension.

        Args:
            file_path: Path to the dependency file
            content: File content

        Returns:
            List of parsed dependencies
        """
        file_name = Path(file_path).name.lower()

        if file_name == "requirements.txt":
            return self.parse_requirements(content)
        elif file_name == "package.json":
            return self.parse_package_json(content)
        elif file_name == "cargo.toml":
            return self.parse_cargo_toml(content)
        elif file_name == "pyproject.toml":
            return self.parse_pyproject_toml(content)
        else:
            raise ValueError(f"Unsupported dependency file: {file_name}")
