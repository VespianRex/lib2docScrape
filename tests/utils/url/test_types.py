"""Tests for the URL types module."""

from src.utils.url.types import URLType


def test_url_type_enum():
    """Test the URLType enumeration."""
    # Test that the enumeration has the expected values
    assert URLType.INTERNAL is not None
    assert URLType.EXTERNAL is not None
    assert URLType.UNKNOWN is not None

    # Test that the enumeration values are distinct
    assert URLType.INTERNAL != URLType.EXTERNAL
    assert URLType.INTERNAL != URLType.UNKNOWN
    assert URLType.EXTERNAL != URLType.UNKNOWN

    # Test string representation
    assert str(URLType.INTERNAL) == "URLType.INTERNAL"
    assert str(URLType.EXTERNAL) == "URLType.EXTERNAL"
    assert str(URLType.UNKNOWN) == "URLType.UNKNOWN"
