"""
Tests for the version management system.
"""
import os
import shutil
import tempfile
from datetime import datetime, timedelta

import pytest

from src.versioning.version_manager import (
    VersionManager,
    VersionConfig,
    VersionDiffFormat,
    VersionChangeType,
    DocumentVersion
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def version_manager(temp_dir):
    """Create a version manager for testing."""
    config = VersionConfig(
        storage_dir=os.path.join(temp_dir, "versions"),
        max_versions=5,
        store_full_content=True,
        auto_detect_version=True
    )
    return VersionManager(config)

def test_version_manager_init(temp_dir):
    """Test VersionManager initialization."""
    # Test with default config
    manager = VersionManager()
    assert manager.config.storage_dir == "version_history"
    assert manager.config.max_versions == 10
    assert manager.config.store_full_content is True
    
    # Test with custom config
    config = VersionConfig(
        storage_dir=os.path.join(temp_dir, "custom_versions"),
        max_versions=3,
        store_full_content=False
    )
    manager = VersionManager(config)
    assert manager.config.storage_dir == os.path.join(temp_dir, "custom_versions")
    assert manager.config.max_versions == 3
    assert manager.config.store_full_content is False
    assert os.path.exists(os.path.join(temp_dir, "custom_versions"))

def test_detect_version():
    """Test version detection from content."""
    manager = VersionManager()
    
    # Test with version in content
    content = "This is documentation for library v1.2.3 which was released yesterday."
    version = manager.detect_version(content)
    assert version == "1.2.3"
    
    # Test with version in different format
    content = "Library version: 2.0.0-beta.1"
    version = manager.detect_version(content)
    assert version == "2.0.0"
    
    # Test with no version
    content = "This is documentation with no version information."
    version = manager.detect_version(content)
    assert version is None
    
    # Test with custom pattern
    manager.config.version_pattern = r'version: (\d+\.\d+)'
    content = "Library version: 2.1"
    version = manager.detect_version(content)
    assert version is None  # Doesn't match semver pattern
    
    # Disable auto-detection
    manager.config.auto_detect_version = False
    content = "This is documentation for library v1.2.3."
    version = manager.detect_version(content)
    assert version is None

def test_add_version(version_manager):
    """Test adding a new version."""
    # Add first version
    doc_id = "test_doc"
    content1 = "This is version 1.0.0 of the document."
    version1 = version_manager.add_version(doc_id, content1, "1.0.0")
    
    assert version1.document_id == doc_id
    assert version1.version == "1.0.0"
    assert version1.content_hash == version_manager._compute_content_hash(content1)
    
    # Verify version was added
    versions = version_manager.get_versions(doc_id)
    assert len(versions) == 1
    assert versions[0].version == "1.0.0"
    
    # Add second version
    content2 = "This is version 1.1.0 of the document with some changes."
    version2 = version_manager.add_version(doc_id, content2, "1.1.0")
    
    assert version2.version == "1.1.0"
    
    # Verify both versions exist
    versions = version_manager.get_versions(doc_id)
    assert len(versions) == 2
    assert versions[0].version == "1.0.0"
    assert versions[1].version == "1.1.0"
    
    # Add duplicate content
    version3 = version_manager.add_version(doc_id, content2, "1.1.0-duplicate")
    
    # Should return existing version
    assert version3.version == "1.1.0"
    assert len(version_manager.get_versions(doc_id)) == 2
    
    # Test auto-detection
    content4 = "This is version 1.2.0 with auto-detection."
    version4 = version_manager.add_version(doc_id, content4)
    
    assert version4.version == "1.2.0"
    assert len(version_manager.get_versions(doc_id)) == 3

def test_version_limit(version_manager):
    """Test version limit enforcement."""
    doc_id = "test_doc"
    
    # Add more versions than the limit
    for i in range(10):
        content = f"This is version 1.0.{i} of the document."
        version_manager.add_version(doc_id, content, f"1.0.{i}")
        
    # Verify only max_versions are kept
    versions = version_manager.get_versions(doc_id)
    assert len(versions) == version_manager.config.max_versions
    
    # Verify oldest versions were removed
    assert versions[0].version == "1.0.5"
    assert versions[-1].version == "1.0.9"

def test_get_latest_version(version_manager):
    """Test getting the latest version."""
    doc_id = "test_doc"
    
    # Add versions
    for i in range(3):
        content = f"This is version 1.0.{i} of the document."
        version_manager.add_version(doc_id, content, f"1.0.{i}")
        
    # Get latest version
    latest = version_manager.get_latest_version(doc_id)
    assert latest is not None
    assert latest.version == "1.0.2"
    
    # Test with non-existent document
    latest = version_manager.get_latest_version("nonexistent")
    assert latest is None

def test_compare_versions(version_manager):
    """Test comparing versions."""
    doc_id = "test_doc"
    
    # Add versions
    content1 = "This is the first line.\nThis is the second line."
    content2 = "This is the first line.\nThis is the modified second line."
    
    version_manager.add_version(doc_id, content1, "1.0.0")
    version_manager.add_version(doc_id, content2, "1.1.0")
    
    # Compare versions with unified diff
    diff = version_manager.compare_versions(doc_id, "1.0.0", "1.1.0", VersionDiffFormat.UNIFIED)
    assert diff is not None
    assert diff.document_id == doc_id
    assert diff.old_version == "1.0.0"
    assert diff.new_version == "1.1.0"
    assert diff.change_type == VersionChangeType.MODIFIED
    assert "-This is the second line." in diff.diff_content
    assert "+This is the modified second line." in diff.diff_content
    
    # Compare versions with context diff
    diff = version_manager.compare_versions(doc_id, "1.0.0", "1.1.0", VersionDiffFormat.CONTEXT)
    assert diff is not None
    assert "- This is the second line." in diff.diff_content
    assert "+ This is the modified second line." in diff.diff_content
    
    # Compare versions with HTML diff
    diff = version_manager.compare_versions(doc_id, "1.0.0", "1.1.0", VersionDiffFormat.HTML)
    assert diff is not None
    assert "<html>" in diff.diff_content
    assert "This is the second line" in diff.diff_content
    assert "This is the modified second line" in diff.diff_content
    
    # Compare versions with JSON diff
    diff = version_manager.compare_versions(doc_id, "1.0.0", "1.1.0", VersionDiffFormat.JSON)
    assert diff is not None
    assert "changes" in diff.diff_content
    
    # Compare identical versions
    version_manager.add_version(doc_id, content2, "1.1.1")
    diff = version_manager.compare_versions(doc_id, "1.1.0", "1.1.1")
    assert diff is not None
    assert diff.change_type == VersionChangeType.UNCHANGED
    
    # Compare non-existent versions
    diff = version_manager.compare_versions(doc_id, "1.0.0", "nonexistent")
    assert diff is None
    
    # Test with store_full_content disabled
    version_manager.config.store_full_content = False
    diff = version_manager.compare_versions(doc_id, "1.0.0", "1.1.0")
    assert diff is None

def test_save_and_load_versions(temp_dir):
    """Test saving and loading versions."""
    # Create a manager and add versions
    config = VersionConfig(storage_dir=os.path.join(temp_dir, "versions"))
    manager1 = VersionManager(config)
    
    doc_id = "test_doc"
    manager1.add_version(doc_id, "Content 1", "1.0.0")
    manager1.add_version(doc_id, "Content 2", "1.1.0")
    
    # Create a new manager with the same storage dir
    manager2 = VersionManager(config)
    
    # Verify versions were loaded
    versions = manager2.get_versions(doc_id)
    assert len(versions) == 2
    assert versions[0].version == "1.0.0"
    assert versions[1].version == "1.1.0"
    
    # Verify content was loaded
    content = manager2._get_content(doc_id, "1.0.0")
    assert content == "Content 1"
    
    content = manager2._get_content(doc_id, "1.1.0")
    assert content == "Content 2"
