import pytest

from src.utils.url.factory import create_url_info  # Added import for factory


@pytest.mark.parametrize(
    "url, base, expected_name",
    [
        # Internal URLs - same domain and scheme
        ("http://a.com/foo", "http://a.com/bar", "INTERNAL"),
        ("https://a.com", "https://a.com/xyz", "INTERNAL"),
        # External URLs - different domains or schemes
        ("http://a.com", "https://a.com", "EXTERNAL"),  # scheme mismatch → external
        (
            "http://sub.a.com",
            "http://a.com",
            "INTERNAL",
        ),  # Same registered domain -> INTERNAL
        (
            "http://a.com",
            "http://b.com",
            "EXTERNAL",
        ),  # Different registered domain -> EXTERNAL
        # Unknown/External URLs
        (None, "http://a.com", "UNKNOWN"),  # Invalid URL -> UNKNOWN
        ("http://a.com", None, "EXTERNAL"),  # Valid URL, no base -> EXTERNAL
    ],
)
def test_determine_url_type(url, base, expected_name):
    info = create_url_info(url, base_url=base)
    assert info.url_type.name == expected_name
