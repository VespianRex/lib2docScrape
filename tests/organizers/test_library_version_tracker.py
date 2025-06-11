"""
Tests for the library version tracker.
"""

import os
import tempfile
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from src.organizers.library_version_tracker import (
    LibraryRegistry,
    LibraryVersionTracker,
)
from src.processors.content_processor import ProcessedContent


@pytest.fixture
def registry():
    """Create a library registry."""
    registry = LibraryRegistry()
    registry.add_library(
        name="test_lib",
        base_url="https://docs.test-lib.com",
        version_pattern=r"v?(\d+\.\d+\.\d+)",
        doc_paths=["docs", "api"],
    )
    registry.register_version(
        name="test_lib",
        version="1.0.0",
        doc_url="https://docs.test-lib.com/v1.0.0",
        release_date=datetime.now(timezone.utc),
        is_latest=False,
    )
    registry.register_version(
        name="test_lib",
        version="2.0.0",
        doc_url="https://docs.test-lib.com/v2.0.0",
        release_date=datetime.now(timezone.utc),
        is_latest=True,
    )
    return registry


@pytest.fixture
def tracker(registry):
    """Create a library version tracker."""
    return LibraryVersionTracker(registry)


@pytest.fixture
def processed_content():
    """Create a processed content object."""
    content = ProcessedContent()
    content.url = "https://docs.test-lib.com/v1.0.0/api/function"
    content.title = "Test Function"
    content.content = {
        "formatted_content": "# Test Function\n\nThis is a test function."
    }
    content.structure = [{"type": "heading", "level": 1, "title": "Test Function"}]
    content.headings = [
        {"level": 1, "text": "Test Function", "id": "", "type": "heading"}
    ]
    content.metadata = {"title": "Test Function"}
    content.assets = []
    return content


def test_registry_add_library():
    """Test adding a library to the registry."""
    registry = LibraryRegistry()
    registry.add_library(
        name="test_lib",
        base_url="https://docs.test-lib.com",
        version_pattern=r"v?(\d+\.\d+\.\d+)",
        doc_paths=["docs", "api"],
    )

    # Check that the library was added
    library = registry.get_library("test_lib")
    assert library is not None
    assert library["name"] == "test_lib"
    assert library["base_url"] == "https://docs.test-lib.com"
    assert library["version_pattern"] == r"v?(\d+\.\d+\.\d+)"
    assert library["doc_paths"] == ["docs", "api"]
    assert "versions" in library


def test_registry_register_version(registry):
    """Test registering a version in the registry."""
    # Register a new version
    registry.register_version(
        name="test_lib",
        version="3.0.0",
        doc_url="https://docs.test-lib.com/v3.0.0",
        release_date=datetime.now(timezone.utc),
        is_latest=True,
    )

    # Check that the version was added
    library = registry.get_library("test_lib")
    assert "3.0.0" in library["versions"]
    assert (
        library["versions"]["3.0.0"]["documentation_url"]
        == "https://docs.test-lib.com/v3.0.0"
    )
    assert library["versions"]["3.0.0"]["is_latest"] is True

    # Check that the previous latest version is no longer latest
    assert library["versions"]["2.0.0"]["is_latest"] is False


def test_registry_get_doc_url(registry):
    """Test getting a documentation URL from the registry."""
    # Get URL for a specific version
    url = registry.get_doc_url("test_lib", "1.0.0")
    assert url == "https://docs.test-lib.com/v1.0.0"

    # Get URL for a non-existent version (should return base URL)
    url = registry.get_doc_url("test_lib", "999.0.0")
    assert url == "https://docs.test-lib.com"

    # Get URL for a non-existent library
    url = registry.get_doc_url("non_existent_lib")
    assert url is None


def test_registry_verify_doc_site(registry):
    """Test verifying a documentation site."""
    # Valid URL with version
    is_valid, name, version = registry.verify_doc_site(
        "https://docs.test-lib.com/v1.0.0/api"
    )
    assert is_valid is True
    assert name == "test_lib"
    assert version == "1.0.0"

    # Valid URL without version
    is_valid, name, version = registry.verify_doc_site("https://docs.test-lib.com/api")
    assert is_valid is True
    assert name == "test_lib"
    assert version is None

    # Invalid URL
    is_valid, name, version = registry.verify_doc_site("https://example.com")
    assert is_valid is False
    assert name is None
    assert version is None


def test_registry_save_load():
    """Test saving and loading the registry."""
    # Create a registry
    registry = LibraryRegistry()
    registry.add_library(name="test_lib", base_url="https://docs.test-lib.com")

    # Save to a temporary file
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp:
        temp_path = temp.name

    try:
        registry.save_to_file(temp_path)

        # Load from the file
        loaded_registry = LibraryRegistry.load_from_file(temp_path)

        # Check that the loaded registry matches the original
        assert "test_lib" in loaded_registry.libraries
        assert (
            loaded_registry.libraries["test_lib"]["base_url"]
            == "https://docs.test-lib.com"
        )
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_tracker_add_documentation(tracker, processed_content):
    """Test adding documentation to the tracker."""
    # Add documentation
    doc_id = tracker.add_documentation("test_lib", "1.0.0", processed_content)

    # Check that the documentation was added
    assert "test_lib" in tracker.version_docs
    assert "1.0.0" in tracker.version_docs["test_lib"]
    assert doc_id in tracker.version_docs["test_lib"]["1.0.0"]
    assert (
        tracker.version_docs["test_lib"]["1.0.0"][doc_id]["url"]
        == processed_content.url
    )
    assert (
        tracker.version_docs["test_lib"]["1.0.0"][doc_id]["title"]
        == processed_content.title
    )


def test_tracker_get_versions(tracker, processed_content):
    """Test getting versions from the tracker."""
    # Add documentation for multiple versions
    tracker.add_documentation("test_lib", "1.0.0", processed_content)
    tracker.add_documentation("test_lib", "2.0.0", processed_content)

    # Get versions
    versions = tracker.get_versions("test_lib")
    assert "1.0.0" in versions
    assert "2.0.0" in versions

    # Get versions for non-existent library
    versions = tracker.get_versions("non_existent_lib")
    assert versions == []


def test_tracker_get_documentation(tracker, processed_content):
    """Test getting documentation from the tracker."""
    # Add documentation
    doc_id = tracker.add_documentation("test_lib", "1.0.0", processed_content)

    # Get documentation
    docs = tracker.get_documentation("test_lib", "1.0.0")
    assert doc_id in docs
    assert docs[doc_id]["url"] == processed_content.url
    assert docs[doc_id]["title"] == processed_content.title

    # Get documentation for non-existent version
    docs = tracker.get_documentation("test_lib", "999.0.0")
    assert docs == {}

    # Get documentation for non-existent library
    docs = tracker.get_documentation("non_existent_lib", "1.0.0")
    assert docs == {}


def test_tracker_compare_versions(tracker, processed_content):
    """Test comparing versions."""
    # Add documentation for two versions
    tracker.add_documentation("test_lib", "1.0.0", processed_content)

    # Create a modified version of the content
    modified_content = ProcessedContent()
    modified_content.url = processed_content.url
    modified_content.title = processed_content.title
    modified_content.content = {
        "formatted_content": "# Test Function\n\nThis is a modified test function."
    }
    modified_content.structure = processed_content.structure
    modified_content.headings = processed_content.headings
    modified_content.metadata = processed_content.metadata
    modified_content.assets = processed_content.assets

    tracker.add_documentation("test_lib", "2.0.0", modified_content)

    # Compare versions
    diff = tracker.compare_versions("test_lib", "1.0.0", "2.0.0")

    # Check the diff
    assert diff.from_version == "1.0.0"
    assert diff.to_version == "2.0.0"
    assert len(diff.added_pages) == 0
    assert len(diff.removed_pages) == 0
    assert len(diff.modified_pages) == 1
    assert processed_content.url in diff.modified_pages
    assert processed_content.url in diff.diff_details

    # Check diff details
    assert "diff" in diff.diff_details[processed_content.url]
    assert "title1" in diff.diff_details[processed_content.url]
    assert "title2" in diff.diff_details[processed_content.url]


def test_tracker_is_newer_version():
    """Test checking if a version is newer."""
    tracker = LibraryVersionTracker()

    # Test with semver versions
    assert tracker.is_newer_version("1.0.0", "2.0.0") is True
    assert tracker.is_newer_version("2.0.0", "1.0.0") is False
    assert tracker.is_newer_version("1.0.0", "1.1.0") is True
    assert tracker.is_newer_version("1.1.0", "1.0.0") is False
    assert tracker.is_newer_version("1.0.0", "1.0.1") is True
    assert tracker.is_newer_version("1.0.1", "1.0.0") is False

    # Test with v prefix
    assert tracker.is_newer_version("v1.0.0", "v2.0.0") is True

    # Test with partial versions
    assert tracker.is_newer_version("1.0", "1.1") is True

    # Test with non-semver versions
    assert tracker.is_newer_version("a", "b") is True
    assert tracker.is_newer_version("b", "a") is False


@pytest.mark.skipif(
    not hasattr(LibraryVersionTracker, "generate_visual_diff"),
    reason="Visual diff not implemented",
)
def test_tracker_generate_visual_diff(tracker, processed_content):
    """Test generating a visual diff."""
    # Skip if visualization libraries are not available
    if not hasattr(tracker, "generate_visual_diff"):
        pytest.skip("Visual diff not implemented")

    # Mock the visualization libraries
    with (
        patch("src.organizers.library_version_tracker.HAS_VISUALIZATION", True),
        patch("src.organizers.library_version_tracker.nx.DiGraph"),
        patch("src.organizers.library_version_tracker.nx.spring_layout"),
        patch("src.organizers.library_version_tracker.nx.draw_networkx_nodes"),
        patch("src.organizers.library_version_tracker.nx.draw_networkx_edges"),
        patch("src.organizers.library_version_tracker.nx.draw_networkx_labels"),
        patch("src.organizers.library_version_tracker.plt.figure"),
        patch("src.organizers.library_version_tracker.plt.title"),
        patch("src.organizers.library_version_tracker.plt.axis"),
        patch("src.organizers.library_version_tracker.plt.savefig"),
        patch("src.organizers.library_version_tracker.plt.close"),
        patch("src.organizers.library_version_tracker.os.makedirs"),
    ):
        # Add documentation for two versions
        tracker.add_documentation("test_lib", "1.0.0", processed_content)

        # Create a modified version of the content
        modified_content = ProcessedContent()
        modified_content.url = processed_content.url
        modified_content.title = processed_content.title
        modified_content.content = {
            "formatted_content": "# Test Function\n\nThis is a modified test function."
        }
        modified_content.structure = processed_content.structure
        modified_content.headings = processed_content.headings
        modified_content.metadata = processed_content.metadata
        modified_content.assets = processed_content.assets

        tracker.add_documentation("test_lib", "2.0.0", modified_content)

        # Generate visual diff
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = tracker.generate_visual_diff(
                "test_lib", "1.0.0", "2.0.0", temp_dir
            )

            # Check that the output file path is returned
            assert output_file is not None
            assert output_file.endswith(".png")
            assert "test_lib_1.0.0_vs_2.0.0.png" in output_file
