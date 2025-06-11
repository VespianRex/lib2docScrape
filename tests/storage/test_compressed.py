"""
Tests for compressed storage.
"""

import os
import tempfile

import pytest

from src.storage.compressed.storage import (
    CompressedStorage,
    CompressionConfig,
    CompressionFormat,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def storage():
    """Create a compressed storage instance for testing."""
    config = CompressionConfig(
        format=CompressionFormat.GZIP,
        level=9,
        use_for_text=True,
        use_for_binary=True,
        metadata_compression=True,
    )
    return CompressedStorage(config=config)


def test_compress_decompress_data(storage):
    """Test compressing and decompressing binary data."""
    # Create test data
    data = b"Hello, world!" * 1000  # Make it large enough to compress

    # Compress data
    compressed = storage.compress_data(data)

    # Check that compression worked
    assert len(compressed) < len(data)

    # Decompress data
    decompressed = storage.decompress_data(compressed)

    # Check that decompression worked
    assert decompressed == data


def test_compress_decompress_text(storage):
    """Test compressing and decompressing text data."""
    # Create test data
    text = "Hello, world!" * 1000  # Make it large enough to compress

    # Compress text
    compressed = storage.compress_text(text)

    # Check that compression worked
    assert len(compressed) < len(text.encode("utf-8"))

    # Decompress text
    decompressed = storage.decompress_text(compressed)

    # Check that decompression worked
    assert decompressed == text


def test_save_load_json(storage, temp_dir):
    """Test saving and loading JSON data."""
    # Create test data large enough to trigger compression
    data = {
        "name": "Test",
        "values": list(range(1000)),  # Large enough to trigger compression
        "nested": {"a": 1, "b": 2},
        "description": "A" * 500,  # Add more data to ensure compression
    }

    # Save data
    file_path = os.path.join(temp_dir, "test.json")
    storage.save_json(data, file_path)

    # Check that file exists
    format_str = (
        storage.config.format
        if isinstance(storage.config.format, str)
        else storage.config.format.value
    )
    compressed_path = f"{file_path}.{format_str}"
    assert os.path.exists(compressed_path)

    # Load data
    loaded = storage.load_json(file_path)

    # Check that loaded data matches original
    assert loaded == data


def test_save_load_pickle(storage, temp_dir):
    """Test saving and loading pickled data."""
    # Create test data large enough to trigger compression
    data = {
        "name": "Test",
        "values": list(range(1000)),  # Large enough to trigger compression
        "nested": {"a": 1, "b": 2},
        "description": "A" * 500,  # Add more data to ensure compression
    }

    # Save data
    file_path = os.path.join(temp_dir, "test.pkl")
    storage.save_pickle(data, file_path)

    # Check that file exists
    format_str = (
        storage.config.format
        if isinstance(storage.config.format, str)
        else storage.config.format.value
    )
    compressed_path = f"{file_path}.{format_str}"
    assert os.path.exists(compressed_path)

    # Load data
    loaded = storage.load_pickle(file_path)

    # Check that loaded data matches original
    assert loaded == data


def test_no_compression(temp_dir):
    """Test storage without compression."""
    # Create storage with compression disabled
    config = CompressionConfig(
        format=CompressionFormat.NONE,
        use_for_text=False,
        use_for_binary=False,
        metadata_compression=False,
    )
    storage = CompressedStorage(config=config)

    # Create test data
    data = {"name": "Test", "values": [1, 2, 3, 4, 5]}

    # Save data
    file_path = os.path.join(temp_dir, "test.json")
    storage.save_json(data, file_path)

    # Check that file exists (without compression extension)
    assert os.path.exists(file_path)

    # Load data
    loaded = storage.load_json(file_path)

    # Check that loaded data matches original
    assert loaded == data


def test_different_compression_formats(temp_dir):
    """Test different compression formats."""
    # Create test data
    data = {
        "name": "Test",
        "values": [1, 2, 3, 4, 5] * 100,  # Make it large enough to compress
    }

    # Test each compression format
    for format in CompressionFormat:
        if format == CompressionFormat.NONE:
            continue

        # Create storage with this format
        config = CompressionConfig(format=format)
        storage = CompressedStorage(config=config)

        # Save data
        format_str = format.value  # CompressionFormat enum has .value attribute
        file_path = os.path.join(temp_dir, f"test_{format_str}.json")
        storage.save_json(data, file_path)

        # Check that file exists
        compressed_path = f"{file_path}.{format_str}"
        assert os.path.exists(compressed_path)

        # Load data
        loaded = storage.load_json(file_path)

        # Check that loaded data matches original
        assert loaded == data


def test_small_data_no_compression(storage):
    """Test that small data is not compressed."""
    # Create small test data
    data = b"Hello"  # Smaller than min_size_for_compression

    # Compress data
    compressed_data, was_compressed = storage.compress_data(data)

    # Check that compression was skipped
    assert not was_compressed
    assert compressed_data == data


def test_load_nonexistent_file(storage, temp_dir):
    """Test loading a nonexistent file."""
    # Try to load nonexistent file
    file_path = os.path.join(temp_dir, "nonexistent.json")

    # Should raise FileNotFoundError
    with pytest.raises(FileNotFoundError):
        storage.load_json(file_path)
