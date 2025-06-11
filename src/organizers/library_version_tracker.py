"""
Library version tracking module for managing documentation from different library versions.
"""

import difflib
import json
import logging
import os
import re
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

try:
    import semver
except ImportError:
    # Fallback implementation if semver is not available
    class semver:
        @staticmethod
        def compare(v1, v2):
            """Simple version comparison."""
            v1_parts = [int(x) for x in v1.split(".")]
            v2_parts = [int(x) for x in v2.split(".")]

            for i in range(max(len(v1_parts), len(v2_parts))):
                v1_part = v1_parts[i] if i < len(v1_parts) else 0
                v2_part = v2_parts[i] if i < len(v2_parts) else 0

                if v1_part < v2_part:
                    return -1
                elif v1_part > v2_part:
                    return 1

            return 0


try:
    import matplotlib.pyplot as plt
    import networkx as nx

    HAS_VISUALIZATION = True
except ImportError:
    HAS_VISUALIZATION = False
from pydantic import BaseModel, Field

from ..processors.content_processor import ProcessedContent

logger = logging.getLogger(__name__)


class LibraryVersionInfo(BaseModel):
    """Information about a library version."""

    name: str
    version: str
    release_date: Optional[datetime] = None
    documentation_url: str
    is_latest: bool = False
    is_stable: bool = True
    is_deprecated: bool = False
    supported_until: Optional[datetime] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class VersionDiff(BaseModel):
    """Represents differences between two library versions."""

    from_version: str
    to_version: str
    added_pages: list[str] = Field(default_factory=list)
    removed_pages: list[str] = Field(default_factory=list)
    modified_pages: list[str] = Field(default_factory=list)
    diff_details: dict[str, Any] = Field(default_factory=dict)
    summary: dict[str, Any] = Field(default_factory=dict)
    breaking_changes: list[dict[str, Any]] = Field(default_factory=list)
    api_changes: list[dict[str, Any]] = Field(default_factory=list)
    visual_diff_path: Optional[str] = None


class LibraryRegistry(BaseModel):
    """Registry of known libraries and their documentation URLs."""

    libraries: dict[str, dict[str, Any]] = Field(default_factory=dict)

    def add_library(
        self,
        name: str,
        base_url: str,
        version_pattern: str = None,
        doc_paths: list[str] = None,
    ) -> None:
        """
        Add a library to the registry.

        Args:
            name: Library name
            base_url: Base URL for the library's documentation
            version_pattern: Regex pattern to extract version from URL
            doc_paths: List of common documentation paths
        """
        self.libraries[name] = {
            "name": name,
            "base_url": base_url,
            "version_pattern": version_pattern or r"v?(\d+\.\d+\.\d+)",
            "doc_paths": doc_paths or ["docs", "documentation", "api", "reference"],
            "versions": {},
        }

    def get_library(self, name: str) -> Optional[dict[str, Any]]:
        """Get library information by name."""
        return self.libraries.get(name)

    def get_doc_url(self, name: str, version: Optional[str] = None) -> Optional[str]:
        """
        Get the documentation URL for a library.

        Args:
            name: Library name
            version: Optional version string

        Returns:
            Documentation URL or None if not found
        """
        library = self.get_library(name)
        if not library:
            return None

        base_url = library["base_url"]

        # If version is specified, try to find the specific version URL
        if version and version in library.get("versions", {}):
            return library["versions"][version].get("documentation_url", base_url)

        # Otherwise return the base URL
        return base_url

    def register_version(
        self,
        name: str,
        version: str,
        doc_url: str,
        release_date: Optional[datetime] = None,
        is_latest: bool = False,
    ) -> None:
        """
        Register a specific library version.

        Args:
            name: Library name
            version: Version string
            doc_url: Documentation URL for this version
            release_date: Optional release date
            is_latest: Whether this is the latest version
        """
        library = self.get_library(name)
        if not library:
            # Create the library entry if it doesn't exist
            self.add_library(name, doc_url)
            library = self.get_library(name)

        # Add the version
        if "versions" not in library:
            library["versions"] = {}

        library["versions"][version] = {
            "version": version,
            "documentation_url": doc_url,
            "release_date": release_date,
            "is_latest": is_latest,
        }

        # If this is the latest version, update other versions
        if is_latest:
            for ver, info in library["versions"].items():
                if ver != version:
                    info["is_latest"] = False

    def verify_doc_site(self, url: str) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Verify if a URL is a known documentation site.

        Args:
            url: URL to verify

        Returns:
            Tuple of (is_valid, library_name, version)
        """
        for name, library in self.libraries.items():
            base_url = library["base_url"]

            # Check if URL matches the base URL pattern
            if base_url in url:
                # Try to extract version using the version pattern
                version_pattern = library.get("version_pattern")
                if version_pattern:
                    match = re.search(version_pattern, url)
                    if match:
                        version = match.group(1)
                        return True, name, version

                # No version found but URL matches base
                return True, name, None

        return False, None, None

    def save_to_file(self, filepath: str) -> None:
        """Save the registry to a JSON file."""
        with open(filepath, "w") as f:
            # Convert to dict for serialization
            data = {"libraries": self.libraries}

            # Handle datetime objects
            json.dump(data, f, indent=2, default=str)

    @classmethod
    def load_from_file(cls, filepath: str) -> "LibraryRegistry":
        """Load the registry from a JSON file."""
        try:
            with open(filepath) as f:
                data = json.load(f)
                return cls(**data)
        except (FileNotFoundError, json.JSONDecodeError):
            # Return empty registry if file doesn't exist or is invalid
            return cls()


class LibraryVersionTracker:
    """
    Tracks and manages documentation for different library versions.
    Provides version comparison and diff functionality.
    """

    def __init__(self, registry: Optional[LibraryRegistry] = None):
        """
        Initialize the library version tracker.

        Args:
            registry: Optional library registry
        """
        self.registry = registry or LibraryRegistry()
        self.version_docs: dict[str, dict[str, dict[str, Any]]] = {}

    def add_documentation(
        self, library_name: str, version: str, processed_content: ProcessedContent
    ) -> str:
        """
        Add documentation for a specific library version.

        Args:
            library_name: Library name
            version: Version string
            processed_content: Processed documentation content

        Returns:
            Document ID
        """
        # Generate a unique ID for this document
        doc_id = str(uuid4())

        # Ensure library exists in version_docs
        if library_name not in self.version_docs:
            self.version_docs[library_name] = {}

        # Ensure version exists for this library
        if version not in self.version_docs[library_name]:
            self.version_docs[library_name][version] = {}

        # Store the processed content
        self.version_docs[library_name][version][doc_id] = {
            "url": processed_content.url,
            "title": processed_content.title,
            "content": asdict(processed_content),
            "timestamp": datetime.now(timezone.utc),
        }

        # Register the version in the registry if not already registered
        library = self.registry.get_library(library_name)
        if not library or version not in library.get("versions", {}):
            self.registry.register_version(
                library_name,
                version,
                processed_content.url,
                release_date=datetime.now(timezone.utc),
            )

        return doc_id

    def get_versions(self, library_name: str) -> list[str]:
        """
        Get all versions for a library.

        Args:
            library_name: Library name

        Returns:
            List of version strings
        """
        if library_name not in self.version_docs:
            return []

        return list(self.version_docs[library_name].keys())

    def get_documentation(self, library_name: str, version: str) -> dict[str, Any]:
        """
        Get all documentation for a specific library version.

        Args:
            library_name: Library name
            version: Version string

        Returns:
            Dictionary of document IDs to content
        """
        if library_name not in self.version_docs:
            return {}

        if version not in self.version_docs[library_name]:
            return {}

        return self.version_docs[library_name][version]

    def compare_versions(
        self, library_name: str, version1: str, version2: str
    ) -> VersionDiff:
        """
        Compare documentation between two library versions.

        Args:
            library_name: Library name
            version1: First version string
            version2: Second version string

        Returns:
            VersionDiff object with differences
        """
        if library_name not in self.version_docs:
            return VersionDiff(from_version=version1, to_version=version2)

        if (
            version1 not in self.version_docs[library_name]
            or version2 not in self.version_docs[library_name]
        ):
            return VersionDiff(from_version=version1, to_version=version2)

        docs1 = self.version_docs[library_name][version1]
        docs2 = self.version_docs[library_name][version2]

        # Get URLs for each version
        urls1 = {doc["url"] for doc in docs1.values()}
        urls2 = {doc["url"] for doc in docs2.values()}

        # Find added, removed, and common URLs
        added_urls = urls2 - urls1
        removed_urls = urls1 - urls2
        common_urls = urls1 & urls2

        # Find modified pages by comparing content
        modified_urls = []
        diff_details = {}

        for url in common_urls:
            # Find the documents with this URL in each version
            doc1 = next((doc for doc in docs1.values() if doc["url"] == url), None)
            doc2 = next((doc for doc in docs2.values() if doc["url"] == url), None)

            if doc1 and doc2:
                # Compare content
                content1 = (
                    doc1["content"].get("content", {}).get("formatted_content", "")
                )
                content2 = (
                    doc2["content"].get("content", {}).get("formatted_content", "")
                )

                if content1 != content2:
                    modified_urls.append(url)

                    # Generate diff
                    diff = difflib.unified_diff(
                        content1.splitlines(),
                        content2.splitlines(),
                        fromfile=f"{url} ({version1})",
                        tofile=f"{url} ({version2})",
                        lineterm="",
                    )

                    diff_details[url] = {
                        "diff": list(diff),
                        "title1": doc1["title"],
                        "title2": doc2["title"],
                    }

        return VersionDiff(
            from_version=version1,
            to_version=version2,
            added_pages=list(added_urls),
            removed_pages=list(removed_urls),
            modified_pages=modified_urls,
            diff_details=diff_details,
        )

    def is_newer_version(self, version1: str, version2: str) -> bool:
        """
        Check if version2 is newer than version1.

        Args:
            version1: First version string
            version2: Second version string

        Returns:
            True if version2 is newer than version1
        """
        try:
            # Clean version strings to ensure they're semver compatible
            v1 = self._clean_version(version1)
            v2 = self._clean_version(version2)

            # Compare using semver
            return semver.compare(v2, v1) > 0
        except ValueError:
            # Fall back to string comparison if semver parsing fails
            return version2 > version1

    def _clean_version(self, version: str) -> str:
        """
        Clean a version string to make it semver compatible.

        Args:
            version: Version string

        Returns:
            Cleaned version string
        """
        # Remove 'v' prefix if present
        if version.startswith("v"):
            version = version[1:]

        # Ensure there are at least three parts (major.minor.patch)
        parts = version.split(".")
        while len(parts) < 3:
            parts.append("0")

        # Join back together
        return ".".join(parts)

    def generate_visual_diff(
        self, library_name: str, version1: str, version2: str, output_dir: str = None
    ) -> Optional[str]:
        """
        Generate a visual diff between two library versions.

        Args:
            library_name: Library name
            version1: First version string
            version2: Second version string
            output_dir: Optional output directory for the visual diff

        Returns:
            Path to the visual diff file or None if visualization is not available
        """
        if not HAS_VISUALIZATION:
            logger.warning(
                "Visualization libraries (matplotlib, networkx) not available"
            )
            return None

        # Compare versions
        diff = self.compare_versions(library_name, version1, version2)

        # Create output directory if it doesn't exist
        if output_dir is None:
            output_dir = os.path.join(os.getcwd(), "diffs")

        os.makedirs(output_dir, exist_ok=True)

        # Create a graph
        G = nx.DiGraph()

        # Add nodes for each version
        G.add_node(version1, label=f"{library_name} {version1}")
        G.add_node(version2, label=f"{library_name} {version2}")

        # Add edge between versions
        G.add_edge(version1, version2)

        # Add nodes for added, removed, and modified pages
        for url in diff.added_pages:
            node_id = f"added_{hash(url) % 10000}"
            G.add_node(node_id, label=os.path.basename(url), color="green")
            G.add_edge(version2, node_id)

        for url in diff.removed_pages:
            node_id = f"removed_{hash(url) % 10000}"
            G.add_node(node_id, label=os.path.basename(url), color="red")
            G.add_edge(version1, node_id)

        for url in diff.modified_pages:
            node_id = f"modified_{hash(url) % 10000}"
            G.add_node(node_id, label=os.path.basename(url), color="orange")
            G.add_edge(version1, node_id)
            G.add_edge(version2, node_id)

        # Create the visualization
        plt.figure(figsize=(12, 8))

        # Get node colors
        node_colors = []
        for node in G.nodes():
            if node == version1 or node == version2:
                node_colors.append("lightblue")
            else:
                node_colors.append(G.nodes[node].get("color", "gray"))

        # Get node labels
        node_labels = {node: G.nodes[node].get("label", node) for node in G.nodes()}

        # Draw the graph
        pos = nx.spring_layout(G, seed=42)
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=500, alpha=0.8)
        nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.5)
        nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=8)

        plt.title(f"{library_name}: {version1} vs {version2}")
        plt.axis("off")

        # Save the visualization
        output_file = os.path.join(
            output_dir, f"{library_name}_{version1}_vs_{version2}.png"
        )
        plt.savefig(output_file, dpi=300, bbox_inches="tight")
        plt.close()

        # Update the diff with the visual diff path
        diff.visual_diff_path = output_file

        return output_file

    def detect_breaking_changes(
        self, library_name: str, version1: str, version2: str
    ) -> list[dict[str, Any]]:
        """
        Detect potential breaking changes between two library versions.

        Args:
            library_name: Library name
            version1: First version string
            version2: Second version string

        Returns:
            List of potential breaking changes
        """
        # Compare versions
        diff = self.compare_versions(library_name, version1, version2)

        breaking_changes = []

        # Check for removed pages (potential API removals)
        for url in diff.removed_pages:
            breaking_changes.append(
                {
                    "type": "removed_page",
                    "url": url,
                    "description": f"Page removed in {version2}",
                }
            )

        # Check for modified pages with potential breaking changes
        for url in diff.modified_pages:
            if url not in diff.diff_details:
                continue

            diff_lines = diff.diff_details[url].get("diff", [])

            # Look for patterns that might indicate breaking changes
            for line in diff_lines:
                if line.startswith("-") and not line.startswith("---"):
                    # Check for patterns that might indicate breaking changes
                    if re.search(
                        r"def\s+\w+|class\s+\w+|function\s+\w+|method\s+\w+", line
                    ):
                        breaking_changes.append(
                            {
                                "type": "removed_api",
                                "url": url,
                                "line": line,
                                "description": f"Potential API removal: {line.strip()}",
                            }
                        )
                    elif "deprecated" in line.lower():
                        breaking_changes.append(
                            {
                                "type": "deprecation",
                                "url": url,
                                "line": line,
                                "description": f"Potential deprecation: {line.strip()}",
                            }
                        )
                    elif "breaking" in line.lower() or "break" in line.lower():
                        breaking_changes.append(
                            {
                                "type": "explicit_breaking",
                                "url": url,
                                "line": line,
                                "description": f"Explicit breaking change mention: {line.strip()}",
                            }
                        )

        return breaking_changes
