"""
Tests for the URL types module.
"""

from src.utils.url.types import URLType


def test_url_type_enum():
    """Test that URLType has the expected values."""
    assert URLType.INTERNAL != URLType.EXTERNAL
    assert URLType.INTERNAL != URLType.UNKNOWN
    assert URLType.EXTERNAL != URLType.UNKNOWN

    # Test enum values are unique
    types = {URLType.INTERNAL, URLType.EXTERNAL, URLType.UNKNOWN}
    assert len(types) == 3
