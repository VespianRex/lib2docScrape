"""Tests for the URL factory module."""

from unittest.mock import patch

from src.utils.url.factory import create_url_info
from src.utils.url.types import URLType


def test_create_url_info_none():
    """Test create_url_info with None URL."""
    url_info = create_url_info(None)
    assert url_info is not None
    assert url_info.is_valid is False
    assert url_info.error_message == "URL cannot be None or empty"
    assert url_info.normalized_url == ""
    assert url_info.url_type == URLType.UNKNOWN


def test_create_url_info_empty():
    """Test create_url_info with empty URL."""
    url_info = create_url_info("")
    assert url_info is not None
    assert url_info.is_valid is False
    assert url_info.error_message == "URL cannot be None or empty"
    assert url_info.normalized_url == ""
    assert url_info.url_type == URLType.UNKNOWN


def test_create_url_info_valid():
    """Test create_url_info with valid URL."""
    url_info = create_url_info("https://example.com/path")
    assert url_info is not None
    assert url_info.is_valid is True
    assert url_info.error_message is None
    assert url_info.normalized_url == "https://example.com/path"
    assert url_info.url_type == URLType.EXTERNAL


def test_create_url_info_with_base_url():
    """Test create_url_info with relative URL and base URL."""
    url_info = create_url_info("path", "https://example.com")
    assert url_info is not None
    assert url_info.is_valid is True
    assert url_info.error_message is None
    assert url_info.normalized_url == "https://example.com/path"
    assert url_info.url_type == URLType.INTERNAL


def test_create_url_info_with_fragment():
    """Test create_url_info with URL containing fragment."""
    url_info = create_url_info("https://example.com/path#fragment")
    assert url_info is not None
    assert url_info.is_valid is True
    assert url_info.error_message is None
    assert url_info.normalized_url == "https://example.com/path"
    assert url_info._original_fragment == "fragment"


def test_create_url_info_with_control_chars():
    """Test create_url_info with URL containing control characters."""
    url_info = create_url_info("https://example.com/path\x01")
    assert url_info is not None
    assert url_info.is_valid is False
    assert "control characters" in url_info.error_message.lower()


def test_create_url_info_with_null_byte():
    """Test create_url_info with URL containing null byte."""
    url_info = create_url_info("https://example.com/path%00")
    assert url_info is not None
    assert url_info.is_valid is False
    assert "Null byte" in url_info.error_message


def test_create_url_info_invalid_port():
    """Test create_url_info with URL containing invalid port."""
    url_info = create_url_info("https://example.com:70000/path")
    assert url_info is not None
    assert url_info.is_valid is False
    assert (
        "Invalid port" in url_info.error_message
        or "Port out of range" in url_info.error_message
    )


@patch("src.utils.url.factory.resolve_url")
def test_create_url_info_resolution_error(mock_resolve_url):
    """Test create_url_info with URL resolution error."""
    mock_resolve_url.side_effect = ValueError("Resolution error")

    url_info = create_url_info("path", "https://example.com")
    assert url_info is not None
    assert url_info.is_valid is False
    assert (
        "URL resolution failed" in url_info.error_message
        or "Resolution error" in url_info.error_message
    )


@patch("src.utils.url.factory.normalize_url")
def test_create_url_info_normalization_error(mock_normalize_url):
    """Test create_url_info with URL normalization error."""
    mock_normalize_url.side_effect = ValueError("Normalization error")

    url_info = create_url_info("https://example.com/path")
    assert url_info is not None
    assert url_info.is_valid is False
    assert "URL normalization failed" in url_info.error_message


@patch("src.utils.url.factory.validate_url")
def test_create_url_info_validation_error(mock_validate_url):
    """Test create_url_info with URL validation error."""
    # First call is pre-normalization validation, second is post-normalization
    mock_validate_url.side_effect = [(False, "Validation error"), (True, None)]

    url_info = create_url_info("https://example.com/path")
    assert url_info is not None
    assert url_info.is_valid is False
    assert url_info.error_message == "Validation error"


def test_create_url_info_with_trailing_slash():
    """Test create_url_info with URL containing trailing slash."""
    url_info = create_url_info("https://example.com/path/")
    assert url_info is not None
    assert url_info.is_valid is True
    assert url_info.error_message is None
    assert url_info.normalized_url == "https://example.com/path/"
    assert url_info._original_path_had_trailing_slash is True


def test_create_url_info_without_trailing_slash():
    """Test create_url_info with URL not containing trailing slash."""
    url_info = create_url_info("https://example.com/path")
    assert url_info is not None
    assert url_info.is_valid is True
    assert url_info.error_message is None
    assert url_info.normalized_url == "https://example.com/path"
    assert url_info._original_path_had_trailing_slash is False


def test_create_url_info_with_query():
    """Test create_url_info with URL containing query parameters."""
    url_info = create_url_info("https://example.com/path?param=value")
    assert url_info is not None
    assert url_info.is_valid is True
    assert url_info.error_message is None
    assert url_info.normalized_url == "https://example.com/path?param=value"
    assert url_info.query == "param=value"


def test_create_url_info_with_invalid_base():
    """Test create_url_info with invalid base URL."""
    url_info = create_url_info("path", "invalid://example.com")
    assert url_info is not None
    assert url_info.is_valid is False


@patch("src.utils.url.factory.extract_domain_parts")
def test_create_url_info_domain_extraction(mock_extract_domain_parts):
    """Test create_url_info with domain extraction."""
    mock_extract_domain_parts.return_value = {
        "subdomain": None,
        "domain": "example",
        "suffix": "com",
        "registered_domain": "example.com",
    }

    url_info = create_url_info("https://example.com/path")
    assert url_info is not None
    assert url_info.is_valid is True
    assert url_info.error_message is None
    assert url_info.normalized_url == "https://example.com/path"
    assert url_info.url_type == URLType.EXTERNAL

    # Verify extract_domain_parts was called
    mock_extract_domain_parts.assert_called()


@patch("src.utils.url.factory.determine_url_type")
def test_create_url_info_type_determination(mock_determine_url_type):
    """Test create_url_info with URL type determination."""
    mock_determine_url_type.return_value = URLType.EXTERNAL

    url_info = create_url_info("https://example.com/path")
    assert url_info is not None
    assert url_info.is_valid is True
    assert url_info.error_message is None
    assert url_info.normalized_url == "https://example.com/path"
    assert url_info.url_type == URLType.EXTERNAL

    # Verify determine_url_type was called
    mock_determine_url_type.assert_called_once()


def test_create_url_info_with_exception():
    """Test create_url_info with unexpected exception."""
    with patch("src.utils.url.factory.normalize_url") as mock_normalize_url:
        mock_normalize_url.side_effect = Exception("Unexpected error")

        url_info = create_url_info("https://example.com/path")
        assert url_info is not None
        assert url_info.is_valid is False
        assert "Unexpected error" in url_info.error_message
