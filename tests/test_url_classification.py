# To be implemented: from src.utils.url.classification import determine_url_type

import pytest

@pytest.mark.parametrize(
    "url, base, expected_name",
    [
        # Internal URLs - same domain and scheme
        ("http://a.com/foo", "http://a.com/bar", "INTERNAL"),
        ("https://a.com", "https://a.com/xyz", "INTERNAL"),
        
        # External URLs - different domains or schemes
        ("http://a.com", "https://a.com", "EXTERNAL"),  # scheme mismatch → external
        ("http://sub.a.com", "http://a.com", "EXTERNAL"),
        ("http://a.com", "http://b.com", "EXTERNAL"),
        
        # Unknown URLs - when either URL is None or invalid
        (None, "http://a.com", "UNKNOWN"),
        ("http://a.com", None, "UNKNOWN"),
    ]
)
def test_determine_url_type(url, base, expected_name):
    assert determine_url_type(url, base).name == expected_name
