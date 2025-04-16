# URL Handling in lib2docScrape

This document provides comprehensive guidance on using the URL handling functionality in the lib2docScrape library, now implemented in a modular structure under `src/utils/url/`.

## Overview

The `URLInfo` class (available via `from src.utils.url import URLInfo`) provides a secure, immutable representation of URLs. It integrates modular functions for validation, normalization, and security checks, designed to prevent common web vulnerabilities while providing a rich API for URL inspection.

Key features include:
- **Comprehensive security validation**: Protection against XSS, SQL injection, path traversal using rules defined in `src.utils.url.security`.
- **Proper normalization**: IDN handling, path normalization, query parameter handling according to standards, implemented in `src.utils.url.normalization`.
- **Immutable design**: Thread-safe after initialization.
- **Enhanced domain parsing**: Accurate subdomain, domain, and TLD extraction (using `tldextract` library if available).
- **Clear separation of concerns**: Logic is divided into modules (`info`, `validation`, `normalization`, `security`, `types`).

## Basic Usage

```python
from src.utils.url import URLInfo, URLType # Import from the url package

# Create a URLInfo object
url_info = URLInfo("https://www.example.co.uk/path?query=value")

# Check if URL is valid
if url_info.is_valid:
    # Access normalized URL
    print(url_info.normalized_url)  # 'https://www.example.co.uk/path?query=value'

    # Access URL components (normalized)
    print(url_info.scheme)          # 'https'
    print(url_info.netloc)          # 'www.example.co.uk'
    print(url_info.hostname)        # 'www.example.co.uk'
    print(url_info.path)            # '/path'
    print(url_info.query)           # 'query=value'
    print(url_info.port)            # None (port is from original parse)
    print(url_info.fragment)        # '' (fragment is from raw url)
else:
    print(f"Invalid URL: {url_info.error_message}")

# Access raw url
print(url_info.raw_url) # 'https://www.example.co.uk/path?query=value'
```

## Domain Information

The `URLInfo` class provides detailed domain information, leveraging the `tldextract` library when available:

```python
from src.utils.url import URLInfo

url_info = URLInfo("https://blog.example.co.uk/path")

if url_info.is_valid:
    # Access domain components using tldextract results
    print(url_info.hostname)           # 'blog.example.co.uk' (normalized hostname)
    print(url_info.registered_domain) # 'example.co.uk' (domain + suffix)
    print(url_info.subdomain)        # 'blog'
    print(url_info.domain)           # 'example' (the base domain part)
    print(url_info.suffix)           # 'co.uk' (the public suffix)
    print(url_info.tld)              # 'co.uk' (alias for suffix)

    # Access structured domain parts dictionary
    parts = url_info.domain_parts
    print(parts['subdomain'])        # 'blog'
    print(parts['domain'])           # 'example'
    print(parts['suffix'])           # 'co.uk'
    print(parts['registered_domain']) # 'example.co.uk'
```

## Query Parameter Access

```python
from src.utils.url import URLInfo

url = URLInfo("https://example.com/search?q=test&sort=date&q=another")

if url.is_valid:
    # Access query parameters as a dictionary of lists
    params = url.query_params
    assert params['q'] == ['test', 'another']  # Multiple values for same parameter
    assert params['sort'] == ['date']
```

## Handling Relative URLs

You can resolve relative URLs by providing a base URL during initialization:

```python
from src.utils.url import URLInfo

base_url = "https://example.com/docs/page.html"
relative_url = "../images/logo.png"

# URLInfo handles the resolution using urljoin internally
url_info = URLInfo(relative_url, base_url=base_url)

if url_info.is_valid:
    print(url_info.normalized_url)   # 'https://example.com/images/logo.png'
```

## URL Type Classification

Determine if a URL is internal or external relative to a base URL:

```python
from src.utils.url import URLInfo, URLType

base_url = "https://example.com/docs/"
internal_url = "/about"
external_url = "https://github.com"

internal_info = URLInfo(internal_url, base_url=base_url)
external_info = URLInfo(external_url, base_url=base_url)

print(internal_info.url_type == URLType.INTERNAL)  # True
print(external_info.url_type == URLType.EXTERNAL)  # True
```

## Security Features

The URL handling logic incorporates multiple layers of security checks defined in `src.utils.url.security` and applied during validation (`src.utils.url.validation`):

1.  **Scheme Validation**: Only allows schemes defined in `URLSecurityConfig.ALLOWED_SCHEMES`.
2.  **Netloc/Host Validation**: Checks for missing hosts, disallowed auth info, private/loopback IPs, valid domain labels, and IDN encoding.
3.  **Port Validation**: Ensures port is within the valid range (0-65535).
4.  **Path Validation**: Checks max length, invalid characters, and path traversal attempts (`../`).
5.  **Query Validation**: Checks max length and invalid characters.
6.  **Pattern Matching**: Scans decoded path and query for XSS, SQLi, Cmd Injection, Null Byte patterns, and disallowed schemes (`javascript:`, `data:`).

```python
from src.utils.url import URLInfo

# Examples of security validation
dangerous_url = "javascript:alert('XSS')"
url_info = URLInfo(dangerous_url)
print(url_info.is_valid)  # False
print(url_info.error_message) # Likely 'Disallowed scheme: javascript' or 'Invalid scheme: javascript'

# Path traversal attempt
traversal_url = "https://example.com/../../../etc/passwd"
url_info = URLInfo(traversal_url)
print(url_info.is_valid)  # False
print(url_info.error_message) # Likely 'Directory traversal attempt'
```

## Performance Considerations

- URLInfo objects are immutable after creation.
- `functools.cached_property` is used for expensive calculations like domain parsing.
- Normalization and validation functions leverage caching (`functools.lru_cache`) where appropriate (e.g., `normalize_hostname`).
- Domain parsing with `tldextract` (if installed) adds a small overhead but provides accurate results; a basic fallback is used otherwise.

## Dependencies

- **Required**: Python 3.7+, idna
- **Optional**: tldextract (for enhanced domain parsing, recommended)

## Installation

To use the enhanced domain parsing features, install tldextract:

```bash
# Using pip
pip install tldextract>=3.4.0

# Or using uv
uv pip install tldextract>=3.4.0
```

## Best Practices

1.  Always check `url_info.is_valid` before relying on URL components from `url_info`.
2.  Use `url_info.normalized_url` for storage and comparison of valid URLs.
3.  Leverage immutability for thread safety.
4.  Check `url_info.error_message` when validation fails to understand the reason.
5.  Handle URLs that might contain IDN (International Domain Names) using the built-in support.
6.  Install `tldextract` for accurate domain parsing.

## Error Handling

```python
from src.utils.url import URLInfo

url_str = "http://example.com:99999" # Invalid port
url_info = URLInfo(url_str)

if not url_info.is_valid:
    print(f"URL validation failed for '{url_str}': {url_info.error_message}")
    # Output: URL validation failed for 'http://example.com:99999': Invalid port: 99999
```

## Migrating from Previous Version

If you were using the previous monolithic `URLInfo` class (previously located at `src/utils/url_info.py` or potentially accessed via `src/utils/helpers.py`), migrating involves changing the import path and understanding the structure.

**Previous Import (Example):**
```python
# Might have been:
# from src.utils.helpers import URLInfo, URLType
# or
# from src.utils.url_info import URLInfo, URLType
```

**New Import:**
```python
from src.utils.url import URLInfo, URLType # Import from the package __init__
```

**Key Changes:**
-   The core logic is now split into modules within `src/utils/url/`.
-   The main `URLInfo` class resides in `src/utils/url/info.py` but is exposed via `src/utils/url/__init__.py`.
-   Functionality remains largely the same, but the internal organization is modular.
-   The non-standard `URLInfo.from_cache()` method mentioned in older docs is not part of this implementation. Standard instantiation handles URL processing.
-   URL manipulation methods (`with_scheme`, `join`, etc.) are not currently implemented directly on the `URLInfo` class in `info.py` but could be added in the future if needed.

Your existing code using `URLInfo` should primarily require only an import path update, assuming the public properties (`normalized_url`, `scheme`, `is_valid`, `domain`, `suffix`, etc.) remain consistent.
