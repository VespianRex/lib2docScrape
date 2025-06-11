"""
Version management for library documentation.
"""

import datetime
import json
import logging
import os
import re
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from ..utils.error_handler import ErrorCategory, ErrorLevel, handle_error

logger = logging.getLogger(__name__)

try:
    import difflib

    import semver

    SEMVER_AVAILABLE = True
except ImportError:
    logger.warning("semver package not available. Version parsing will be limited.")
    SEMVER_AVAILABLE = False


class VersionChangeType(Enum):
    """Types of changes between versions."""

    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


class VersionDiffFormat(Enum):
    """Formats for version diffs."""

    UNIFIED = "unified"
    CONTEXT = "context"
    HTML = "html"
    JSON = "json"


class VersionInfo(BaseModel):
    """Information about a library version."""

    version: str
    release_date: Optional[datetime.datetime] = None
    is_prerelease: bool = False
    is_stable: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentVersion(BaseModel):
    """Version information for a document."""

    document_id: str
    version: str
    content_hash: str
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class VersionDiff(BaseModel):
    """Difference between two versions of a document."""

    document_id: str
    old_version: str
    new_version: str
    change_type: VersionChangeType
    diff_content: str
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class VersionConfig(BaseModel):
    """Configuration for version management."""

    storage_dir: str = "version_history"
    max_versions: int = 10
    diff_format: VersionDiffFormat = VersionDiffFormat.UNIFIED
    store_full_content: bool = True
    compress_old_versions: bool = True
    track_metadata_changes: bool = True
    auto_detect_version: bool = True
    version_pattern: str = r"(\d+\.\d+\.\d+)"


class VersionManager:
    """
    Manage versions of library documentation.

    This class provides methods for tracking, comparing, and managing
    different versions of library documentation.
    """

    def __init__(self, config: Optional[VersionConfig] = None):
        """
        Initialize the version manager.

        Args:
            config: Optional configuration for version management
        """
        self.config = config or VersionConfig()
        self.versions: dict[str, list[DocumentVersion]] = {}

        # Create storage directory if it doesn't exist
        os.makedirs(self.config.storage_dir, exist_ok=True)

        # Load existing versions
        self._load_versions()

    def _load_versions(self) -> None:
        """Load existing versions from storage."""
        try:
            index_path = os.path.join(self.config.storage_dir, "version_index.json")
            if os.path.exists(index_path):
                with open(index_path) as f:
                    data = json.load(f)

                for doc_id, versions in data.items():
                    self.versions[doc_id] = [
                        DocumentVersion(
                            document_id=doc_id,
                            version=v["version"],
                            content_hash=v["content_hash"],
                            timestamp=datetime.datetime.fromisoformat(v["timestamp"]),
                            metadata=v["metadata"],
                        )
                        for v in versions
                    ]

                logger.info(
                    f"Loaded version history for {len(self.versions)} documents"
                )
        except Exception as e:
            error_details = {"storage_dir": self.config.storage_dir}
            handle_error(
                e,
                "VersionManager",
                "_load_versions",
                details=error_details,
                level=ErrorLevel.WARNING,
                category=ErrorCategory.RESOURCE,
            )
            logger.warning(f"Failed to load version history: {str(e)}")

    def _save_versions(self) -> None:
        """Save versions to storage."""
        try:
            index_path = os.path.join(self.config.storage_dir, "version_index.json")

            # Convert to serializable format
            data = {}
            for doc_id, versions in self.versions.items():
                data[doc_id] = [
                    {
                        "version": v.version,
                        "content_hash": v.content_hash,
                        "timestamp": v.timestamp.isoformat(),
                        "metadata": v.metadata,
                    }
                    for v in versions
                ]

            with open(index_path, "w") as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved version history for {len(self.versions)} documents")
        except Exception as e:
            error_details = {"storage_dir": self.config.storage_dir}
            handle_error(
                e,
                "VersionManager",
                "_save_versions",
                details=error_details,
                level=ErrorLevel.ERROR,
                category=ErrorCategory.RESOURCE,
            )
            logger.error(f"Failed to save version history: {str(e)}")

    def _compute_content_hash(self, content: str) -> str:
        """
        Compute a hash of the content.

        Args:
            content: Content to hash

        Returns:
            Hash of the content
        """
        import hashlib

        return hashlib.sha256(content.encode()).hexdigest()

    def _get_content_path(self, doc_id: str, version: str) -> str:
        """
        Get the path to the content file for a document version.

        Args:
            doc_id: Document ID
            version: Version string

        Returns:
            Path to the content file
        """
        return os.path.join(self.config.storage_dir, doc_id, f"{version}.txt")

    def _store_content(self, doc_id: str, version: str, content: str) -> None:
        """
        Store content for a document version.

        Args:
            doc_id: Document ID
            version: Version string
            content: Content to store
        """
        if not self.config.store_full_content:
            return

        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.join(self.config.storage_dir, doc_id), exist_ok=True)

            # Write content to file
            content_path = self._get_content_path(doc_id, version)
            with open(content_path, "w") as f:
                f.write(content)

            logger.debug(f"Stored content for {doc_id} version {version}")
        except Exception as e:
            error_details = {"doc_id": doc_id, "version": version}
            handle_error(
                e,
                "VersionManager",
                "_store_content",
                details=error_details,
                level=ErrorLevel.ERROR,
                category=ErrorCategory.RESOURCE,
            )
            logger.error(
                f"Failed to store content for {doc_id} version {version}: {str(e)}"
            )

    def _get_content(self, doc_id: str, version: str) -> Optional[str]:
        """
        Get content for a document version.

        Args:
            doc_id: Document ID
            version: Version string

        Returns:
            Content of the document version, or None if not found
        """
        if not self.config.store_full_content:
            return None

        try:
            content_path = self._get_content_path(doc_id, version)
            if os.path.exists(content_path):
                with open(content_path) as f:
                    return f.read()
            return None
        except Exception as e:
            error_details = {"doc_id": doc_id, "version": version}
            handle_error(
                e,
                "VersionManager",
                "_get_content",
                details=error_details,
                level=ErrorLevel.WARNING,
                category=ErrorCategory.RESOURCE,
            )
            logger.warning(
                f"Failed to get content for {doc_id} version {version}: {str(e)}"
            )
            return None

    def detect_version(self, content: str) -> Optional[str]:
        """
        Detect version from content.

        Args:
            content: Content to detect version from

        Returns:
            Detected version, or None if not found
        """
        if not self.config.auto_detect_version:
            return None

        # Try to find version using regex pattern
        match = re.search(self.config.version_pattern, content)
        if match:
            version_str = match.group(1)

            # Validate version if semver is available
            if SEMVER_AVAILABLE:
                try:
                    semver.parse(version_str)
                    return version_str
                except ValueError:
                    pass
            else:
                # Basic validation
                if re.match(r"^\d+\.\d+\.\d+", version_str):
                    return version_str

        return None

    def add_version(
        self,
        doc_id: str,
        content: str,
        version: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> DocumentVersion:
        """
        Add a new version of a document.

        Args:
            doc_id: Document ID
            content: Document content
            version: Version string (auto-detected if None)
            metadata: Optional metadata

        Returns:
            Document version information
        """
        # Compute content hash
        content_hash = self._compute_content_hash(content)

        # Get existing versions for this document
        doc_versions = self.versions.get(doc_id, [])

        # Check if this content already exists
        for existing in doc_versions:
            if existing.content_hash == content_hash:
                logger.info(
                    f"Content for {doc_id} already exists with version {existing.version}"
                )
                return existing

        # Auto-detect version if not provided
        if version is None:
            version = self.detect_version(content)
            if version is None:
                # Generate version based on timestamp
                version = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        # Create document version
        doc_version = DocumentVersion(
            document_id=doc_id,
            version=version,
            content_hash=content_hash,
            timestamp=datetime.datetime.now(),
            metadata=metadata or {},
        )

        # Store content
        self._store_content(doc_id, version, content)

        # Add to versions
        if doc_id not in self.versions:
            self.versions[doc_id] = []
        self.versions[doc_id].append(doc_version)

        # Sort versions
        self.versions[doc_id].sort(key=lambda v: v.timestamp)

        # Limit number of versions
        if len(self.versions[doc_id]) > self.config.max_versions:
            # Remove oldest versions
            to_remove = self.versions[doc_id][: -self.config.max_versions]
            self.versions[doc_id] = self.versions[doc_id][-self.config.max_versions :]

            # Remove content files
            for old_version in to_remove:
                content_path = self._get_content_path(doc_id, old_version.version)
                if os.path.exists(content_path):
                    os.remove(content_path)

        # Save versions
        self._save_versions()

        logger.info(f"Added version {version} for {doc_id}")
        return doc_version

    def get_versions(self, doc_id: str) -> list[DocumentVersion]:
        """
        Get all versions of a document.

        Args:
            doc_id: Document ID

        Returns:
            List of document versions
        """
        return self.versions.get(doc_id, [])

    def get_latest_version(self, doc_id: str) -> Optional[DocumentVersion]:
        """
        Get the latest version of a document.

        Args:
            doc_id: Document ID

        Returns:
            Latest document version, or None if not found
        """
        versions = self.get_versions(doc_id)
        if versions:
            return versions[-1]
        return None

    def compare_versions(
        self,
        doc_id: str,
        old_version: str,
        new_version: str,
        format: Optional[VersionDiffFormat] = None,
    ) -> Optional[VersionDiff]:
        """
        Compare two versions of a document.

        Args:
            doc_id: Document ID
            old_version: Old version string
            new_version: New version string
            format: Diff format (defaults to config setting)

        Returns:
            Version diff, or None if versions not found
        """
        if not self.config.store_full_content:
            logger.warning("Cannot compare versions: store_full_content is disabled")
            return None

        # Get content for both versions
        old_content = self._get_content(doc_id, old_version)
        new_content = self._get_content(doc_id, new_version)

        if old_content is None or new_content is None:
            logger.warning(f"Cannot compare versions: content not found for {doc_id}")
            return None

        # Determine change type
        if old_content == new_content:
            change_type = VersionChangeType.UNCHANGED
        else:
            change_type = VersionChangeType.MODIFIED

        # Generate diff
        format = format or self.config.diff_format

        if format == VersionDiffFormat.UNIFIED:
            diff = difflib.unified_diff(
                old_content.splitlines(),
                new_content.splitlines(),
                fromfile=f"{doc_id} {old_version}",
                tofile=f"{doc_id} {new_version}",
                lineterm="",
            )
            diff_content = "\n".join(diff)
        elif format == VersionDiffFormat.CONTEXT:
            diff = difflib.context_diff(
                old_content.splitlines(),
                new_content.splitlines(),
                fromfile=f"{doc_id} {old_version}",
                tofile=f"{doc_id} {new_version}",
                lineterm="",
            )
            diff_content = "\n".join(diff)
        elif format == VersionDiffFormat.HTML:
            diff = difflib.HtmlDiff().make_file(
                old_content.splitlines(),
                new_content.splitlines(),
                f"{doc_id} {old_version}",
                f"{doc_id} {new_version}",
            )
            diff_content = diff
        elif format == VersionDiffFormat.JSON:
            # Simple JSON diff
            diff_content = json.dumps(
                {
                    "old_version": old_version,
                    "new_version": new_version,
                    "changes": [
                        {
                            "type": "removed"
                            if line.startswith("-")
                            else "added"
                            if line.startswith("+")
                            else "context",
                            "line": line[1:].strip()
                            if line.startswith(("+", "-"))
                            else line.strip(),
                        }
                        for line in difflib.unified_diff(
                            old_content.splitlines(),
                            new_content.splitlines(),
                            fromfile="",
                            tofile="",
                            lineterm="",
                        )
                        if not line.startswith(("---", "+++", "@@"))
                    ],
                },
                indent=2,
            )
        else:
            raise ValueError(f"Unsupported diff format: {format}")

        # Create diff object
        return VersionDiff(
            document_id=doc_id,
            old_version=old_version,
            new_version=new_version,
            change_type=change_type,
            diff_content=diff_content,
            metadata={},
        )
