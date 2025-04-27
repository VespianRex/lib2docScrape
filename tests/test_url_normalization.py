import pytest
from src.utils.url.normalization import normalize_hostname, normalize_path

# ------------ hostname -----------------
@pytest.mark.parametrize(
    "raw, expected",
    [
        ("EXAMPLE.com.",               "example.com"),
        ("müller.de",                  "xn--mller-kva.de"),   # IDN → punycode
        ("sub.Example.COM",            "sub.example.com"),
        ("2001:db8::1",                "2001:db8::1"),        # IPv6 literal preserved
        ("localhost",                  "localhost"),
        ("example.com",                "example.com"),
        ("www.example.co.uk",          "www.example.co.uk"),
        ("xn--mller-kva.de",           "xn--mller-kva.de"),   # Already punycode
    ]
)
def test_normalize_hostname_valid(raw, expected):
    assert normalize_hostname(raw) == expected

@pytest.mark.parametrize(
    "bad_hostname",
    [
        "",                              # empty
        "foo<>bar.com",                  # illegal chars
        "a"*64 + ".com",                 # label too long
        "example..com",                  # empty label (double dot)
        "-startdash.com",                # leading dash
        "enddash-.com",                  # trailing dash
        "a"*256,                         # total length too long
        "host_name.com",                 # underscore (not allowed in hostnames)
        "host name.com",                 # space (not allowed)
        ".startdot.com",                 # starting with dot
    ]
)
def test_normalize_hostname_invalid(bad_hostname):
    with pytest.raises(ValueError):
        normalize_hostname(bad_hostname)

# ------------ path -----------------
@pytest.mark.parametrize(
    "raw, expected",
    [
        ("",                "/"),
        ("/",               "/"),
        ("/foo/bar",        "/foo/bar"),
        ("foo/bar",         "/foo/bar"),      # Add leading slash
        ("/foo//bar",       "/foo/bar"),      # Collapse multiple slashes
        (".",               "/"),             # Treat single dot as root
        ("./foo",           "/foo"),          # Remove ./ prefix
        ("/foo/./bar",      "/foo/bar"),      # Remove /./ segments
        ("/foo/../bar",     "/bar"),          # Resolve parent directory
        ("/../foo",         "/foo"),          # Can't go above root
        ("/foo/%20bar",     "/foo/ bar"),     # URL decode
        ("/foo/bar/",       "/foo/bar/"),     # Preserve trailing slash
    ]
)
def test_normalize_path(raw, expected):
    assert normalize_path(raw) == expected
