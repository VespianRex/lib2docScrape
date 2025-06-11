import pytest

from src.utils.url.normalization import normalize_hostname, normalize_path


# ------------ hostname -----------------
@pytest.mark.parametrize(
    "raw, expected",
    [
        ("EXAMPLE.com.", "example.com"),
        ("müller.de", "xn--mller-kva.de"),  # IDN → punycode
        ("sub.Example.COM", "sub.example.com"),
        ("2001:db8::1", "2001:db8::1"),  # IPv6 literal preserved
        ("localhost", "localhost"),
        ("example.com", "example.com"),
        ("www.example.co.uk", "www.example.co.uk"),
        ("xn--mller-kva.de", "xn--mller-kva.de"),  # Already punycode
    ],
)
def test_normalize_hostname_valid(raw, expected):
    assert normalize_hostname(raw) == expected


@pytest.mark.parametrize(
    "bad_hostname",
    [
        "",  # empty
        "foo<>bar.com",  # illegal chars
        "a" * 64 + ".com",  # label too long
        "example..com",  # empty label (double dot)
        "-startdash.com",  # leading dash
        "enddash-.com",  # trailing dash
        "a" * 256,  # total length too long
        "host_name.com",  # underscore (not allowed in hostnames)
        "host name.com",  # space (not allowed)
        ".startdot.com",  # starting with dot
    ],
)
def test_normalize_hostname_invalid(bad_hostname):
    with pytest.raises(ValueError):
        normalize_hostname(bad_hostname)


# ------------ path -----------------


# Shared test cases for path normalization
def path_normalization_cases():
    return [
        ("", "/"),
        ("/", "/"),
        ("/foo/bar", "/foo/bar"),
        ("foo/bar", "foo/bar"),  # Should remain relative
        ("/foo//bar", "/foo/bar"),  # Collapse multiple slashes
        (".", "."),  # Treat single dot as relative current dir
        ("./foo", "foo"),  # Should resolve to relative path
        ("/foo/./bar", "/foo/bar"),  # Remove /./ segments
        ("/foo/../bar", "/bar"),  # Resolve parent directory
        ("/../foo", "/foo"),  # Can't go above root
        ("/foo/%20bar", "/foo/%20bar"),  # Preserve percent encoding
        ("/foo/bar/", "/foo/bar"),  # Trailing slash removed by default
        # Additional test cases
        ("path/to/resource", "path/to/resource"),  # Should remain relative
        ("/path with spaces", "/path%20with%20spaces"),  # Spaces get encoded
        ("/ümlaut", "/%C3%BCmlaut"),  # Unicode gets encoded
        ("/path/./to/../resource", "/path/resource"),  # Complex path resolution
    ]


@pytest.mark.parametrize("raw, expected", path_normalization_cases())
def test_normalize_path(raw, expected):
    """Tests various path normalization cases."""
    assert normalize_path(raw) == expected
