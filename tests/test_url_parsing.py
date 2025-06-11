import pytest

from src.utils.url.parsing import resolve_url


@pytest.mark.parametrize(
    "relative, base, expected",
    [
        ("//example.com/foo", "https://host.com/base/", "https://example.com/foo"),
        ("foo/bar", "http://host.com/base/", "http://host.com/base/foo/bar"),
        ("www.foo.com", None, "http://www.foo.com"),  # default scheme added
        ("/abs/path", "http://host.com/dir/", "http://host.com/abs/path"),
    ],
)
def test_resolve_success(relative, base, expected):
    assert resolve_url(relative, base) == expected


@pytest.mark.parametrize(
    "bad_url", [" javascript:alert(1)", "data:text/html;base64...", "vbscript:foo"]
)
def test_blocked_schemes(bad_url):
    assert resolve_url(bad_url.strip(), None) is None
