"""Tests for the domain_parser module."""

from types import MappingProxyType
from unittest.mock import MagicMock, patch

import pytest

from src.utils.url.domain_parser import TLDEXTRACT_AVAILABLE, extract_domain_parts


def test_extract_domain_parts_none():
    """Test extract_domain_parts with None hostname."""
    result = extract_domain_parts(None)
    assert isinstance(result, MappingProxyType)
    assert result["subdomain"] is None
    assert result["domain"] is None
    assert result["suffix"] is None
    assert result["registered_domain"] is None


def test_extract_domain_parts_empty():
    """Test extract_domain_parts with empty hostname."""
    result = extract_domain_parts("")
    assert isinstance(result, MappingProxyType)
    assert result["subdomain"] is None
    assert result["domain"] is None
    assert result["suffix"] is None
    assert result["registered_domain"] is None


def test_extract_domain_parts_ip():
    """Test extract_domain_parts with IP address."""
    result = extract_domain_parts("192.168.1.1")
    assert isinstance(result, MappingProxyType)
    assert result["subdomain"] is None
    assert result["domain"] == "192.168.1.1"
    assert result["suffix"] is None
    assert result["registered_domain"] == "192.168.1.1"


def test_extract_domain_parts_localhost():
    """Test extract_domain_parts with localhost."""
    result = extract_domain_parts("localhost")
    assert isinstance(result, MappingProxyType)
    assert result["subdomain"] is None
    assert result["domain"] == "localhost"
    assert result["suffix"] is None
    assert result["registered_domain"] == "localhost"


@pytest.mark.skipif(not TLDEXTRACT_AVAILABLE, reason="tldextract not available")
def test_extract_domain_parts_with_tldextract():
    """Test extract_domain_parts with tldextract available."""
    # Test with a simple domain
    result = extract_domain_parts("example.com")
    assert isinstance(result, MappingProxyType)
    assert result["subdomain"] is None
    assert result["domain"] == "example"
    assert result["suffix"] == "com"
    assert result["registered_domain"] == "example.com"

    # Test with a subdomain
    result = extract_domain_parts("sub.example.com")
    assert isinstance(result, MappingProxyType)
    assert result["subdomain"] == "sub"
    assert result["domain"] == "example"
    assert result["suffix"] == "com"
    assert result["registered_domain"] == "example.com"

    # Test with multiple subdomain levels
    result = extract_domain_parts("a.b.example.com")
    assert isinstance(result, MappingProxyType)
    assert result["subdomain"] == "a.b"
    assert result["domain"] == "example"
    assert result["suffix"] == "com"
    assert result["registered_domain"] == "example.com"

    # Test with a complex TLD
    result = extract_domain_parts("example.co.uk")
    assert isinstance(result, MappingProxyType)
    assert result["subdomain"] is None
    assert result["domain"] == "example"
    assert result["suffix"] == "co.uk"
    assert result["registered_domain"] == "example.co.uk"


@pytest.mark.skipif(TLDEXTRACT_AVAILABLE, reason="tldextract is available")
def test_extract_domain_parts_without_tldextract():
    """Test extract_domain_parts without tldextract available."""
    # Test with a simple domain
    result = extract_domain_parts("example.com")
    assert isinstance(result, MappingProxyType)
    assert result["subdomain"] is None
    assert result["domain"] == "example"
    assert result["suffix"] == "com"
    assert result["registered_domain"] == "example.com"

    # Test with a subdomain
    result = extract_domain_parts("sub.example.com")
    assert isinstance(result, MappingProxyType)
    assert result["subdomain"] == "sub"
    assert result["domain"] == "example"
    assert result["suffix"] == "com"
    assert result["registered_domain"] == "example.com"


@patch("src.utils.url.domain_parser.tldextract")
def test_extract_domain_parts_tldextract_exception(mock_tldextract):
    """Test extract_domain_parts when tldextract raises an exception."""
    # Mock tldextract to raise an exception
    mock_extract = MagicMock(side_effect=Exception("Test exception"))
    mock_tldextract.extract = mock_extract

    # Test with a domain that would cause tldextract to fall back to basic split
    result = extract_domain_parts("example.com")
    assert isinstance(result, MappingProxyType)
    assert result["subdomain"] is None
    assert result["domain"] == "example"
    assert result["suffix"] == "com"
    assert result["registered_domain"] == "example.com"

    # Verify tldextract.extract was called
    mock_extract.assert_called_once()


def test_extract_domain_parts_single_label():
    """Test extract_domain_parts with a single label domain."""
    result = extract_domain_parts("example")
    assert isinstance(result, MappingProxyType)
    assert result["subdomain"] is None
    assert result["domain"] == "example"
    assert result["suffix"] is None
    assert result["registered_domain"] == "example"


@patch("src.utils.url.domain_parser.TLDEXTRACT_AVAILABLE", True)
@patch("src.utils.url.domain_parser.tldextract")
def test_extract_domain_parts_with_mocked_tldextract(mock_tldextract):
    """Test extract_domain_parts with mocked tldextract."""
    # Create a mock for the extract result
    mock_extract_result = MagicMock()
    mock_extract_result.subdomain = "sub"
    mock_extract_result.domain = "example"
    mock_extract_result.suffix = "com"
    mock_extract_result.registered_domain = "example.com"

    # Set up the mock to return our mock result
    mock_tldextract.extract.return_value = mock_extract_result

    # Test with a domain
    result = extract_domain_parts("sub.example.com")
    assert isinstance(result, MappingProxyType)
    assert result["subdomain"] == "sub"
    assert result["domain"] == "example"
    assert result["suffix"] == "com"
    assert result["registered_domain"] == "example.com"

    # Verify tldextract.extract was called with the right parameters
    mock_tldextract.extract.assert_called_once_with(
        "sub.example.com", include_psl_private_domains=True
    )


@patch("src.utils.url.domain_parser.tldextract")
def test_unexpected_exception(mock_tldextract):
    """Test handling of unexpected exceptions in extract_domain_parts."""
    # Mock tldextract to raise an unexpected exception
    mock_tldextract.extract.side_effect = Exception("Unexpected error")

    # Call the function and verify it falls back to basic parsing
    result = extract_domain_parts("example.com")
    assert isinstance(result, MappingProxyType)
    # Should fall back to basic parsing when tldextract fails
    assert result["domain"] == "example"
    assert result["suffix"] == "com"
