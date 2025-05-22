# URL Handling Migration Guide

This guide provides examples for migrating to the current modular URL handling implementation located in `src/utils/url/`, from older implementations (like the previous monolithic `URLInfo` class).

## Import Statement

The primary way to access the URL handling functionality is now through the `src.utils.url` package.

**Old Import (Example):**
```python
# Might have been:
# from src.utils.helpers import URLInfo, URLType
# or
# from src.utils.url_info import URLInfo, URLType # Monolithic version
```

**New Import:**
```python
from src.utils.url import URLInfo, URLType # Import from the url package __init__
```
*Note: If your code imports `URLInfo` from `src.utils.helpers`, it might still work due to the adapter (`URLProcessor`) in `helpers.py`, but it's recommended to update imports to use `src.utils.url` directly for clarity and future consistency.*

## Common Operations Migration

### Basic URL Parsing and Validation

**Original (Monolithic/Helper):**
```python
# Assuming import from helpers or old url_info
url_info = URLInfo("https://example.com/path")
if url_info.is_valid:
    normalized = url_info.normalized_url
    scheme = url_info.scheme
    domain = url_info.domain # Might have been just hostname
```

**New Modular:**
```python
from src.utils.url import URLInfo # Correct import

url_info = URLInfo("https://example.com/path")
if url_info.is_valid:
    normalized = url_info.normalized_url # "https://example.com/"
    scheme = url_info.scheme           # "https"
    hostname = url_info.hostname       # "example.com"

    # New/Updated properties using tldextract (if available):
    registered_domain = url_info.registered_domain # "example.com"
    domain = url_info.domain                 # "example" (the base part)
    suffix = url_info.suffix                 # "com"
    subdomain = url_info.subdomain           # ""
```
*Key Change: Access domain parts more reliably using `hostname`, `registered_domain`, `domain`, `subdomain`, and `suffix` properties.*

### Working with Subdomains

**Original (Manual Parsing):**
```python
# Had to manually parse the hostname
url_info = URLInfo("https://blog.example.co.uk")
hostname = url_info.domain # Or url_info.hostname
# Manual splitting was unreliable for complex TLDs
# subdomain = hostname.split(".")[0] if hostname.count(".") > 1 else ""
```

**New Modular:**
```python
from src.utils.url import URLInfo

url_info = URLInfo("https://blog.example.co.uk")
if url_info.is_valid:
    subdomain = url_info.subdomain  # "blog"
    domain = url_info.domain        # "example"
    suffix = url_info.suffix        # "co.uk"
    registered_domain = url_info.registered_domain # "example.co.uk"
```
*Key Change: Direct access to accurately parsed `subdomain`, `domain`, `suffix`, and `registered_domain` via tldextract.*

### URL Type Determination

**Original (Via Helpers):**
```python
from src.utils.helpers import URLInfo, URLType # Old import path

base_url = "https://example.com"
url = "https://example.com/path"

url_info = URLInfo(url, base_url=base_url)
is_internal = url_info.url_type == URLType.INTERNAL
```

**New Modular:**
```python
from src.utils.url import URLInfo, URLType # Correct import

base_url = "https://example.com"
url = "https://example.com/path"

url_info = URLInfo(url, base_url=base_url)
is_internal = url_info.url_type == URLType.INTERNAL # Logic remains the same
```
*Key Change: Update the import path.*

### Working with International Domain Names (IDN)

**Original:**
```python
url_info = URLInfo("https://ünicode.com")
# Produced punycode but domain parsing might be less reliable
```

**New Modular:**
```python
from src.utils.url import URLInfo

url_info = URLInfo("https://ünicode.com")
if url_info.is_valid:
    # Normalization handles Punycode correctly
    print(url_info.normalized_url)  # "https://xn--nicode-2ya.com/"
    # Domain properties use tldextract for better parsing
    print(url_info.hostname)          # "xn--nicode-2ya.com" (Punycode form)
    print(url_info.registered_domain) # "xn--nicode-2ya.com"
    print(url_info.domain)            # "xn--nicode-2ya"
    print(url_info.suffix)            # "com"
```
*Key Change: Consistent handling via normalization and tldextract.*

### Security Validation

The security validation logic remains integrated within the `URLInfo` initialization process via the `src.utils.url.validation` module.

**Original:**
```python
dangerous_url = "javascript:alert('XSS')"
url_info = URLInfo(dangerous_url)
if not url_info.is_valid:
    print(f"Rejected URL: {url_info.error_message}")
```

**New Modular:**
```python
from src.utils.url import URLInfo # Correct import

dangerous_url = "javascript:alert('XSS')"
url_info = URLInfo(dangerous_url)
if not url_info.is_valid:
    print(f"Rejected URL: {url_info.error_message}") # Same API for checking validity
```
*Key Change: Update the import path.*

## Architecture Diagram

A Mermaid diagram illustrating the architecture of the modular URL handling system is planned for this section. The content for this diagram was expected from `cline_docs/nextSteps.md` (lines 42-69) but was not found in that location.

## Advanced Use Cases

Examples remain largely the same, just ensure the correct import path is used.

### Extracting All Valid URLs from Text

```python
from src.utils.url import URLInfo # Correct import
import re # Example regex import

# Dummy function for finding potential URLs
def find_urls_in_text(text):
    # A simple regex example, consider more robust ones
    url_pattern = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+')
    return url_pattern.findall(text)

def extract_valid_urls(text):
    """Extract and validate all URLs from text."""
    potential_urls = find_urls_in_text(text)

    valid_urls = []
    for url in potential_urls:
        url_info = URLInfo(url) # Use the new URLInfo
        if url_info.is_valid:
            valid_urls.append(url_info.normalized_url)

    return valid_urls
```

### Creating a Domain Filter

```python
from src.utils.url import URLInfo # Correct import

class DomainFilter:
    """Filter URLs based on domain patterns."""

    def __init__(self, allowed_registered_domains):
        # Filter based on registered_domain for better accuracy
        self.allowed_domains = set(allowed_registered_domains)

    def is_allowed(self, url):
        """Check if URL's registered domain is in the allowed set."""
        url_info = URLInfo(url)
        if not url_info.is_valid:
            return False

        # Use the registered_domain property
        return url_info.registered_domain in self.allowed_domains

# Example Usage
filt = DomainFilter(["example.com", "example.co.uk"])
print(filt.is_allowed("https://www.example.com/page"))      # True
print(filt.is_allowed("https://sub.example.co.uk/other")) # True
print(filt.is_allowed("https://example.org"))             # False
```

## When to Update Your Code

Prioritize updating your code if:
1.  You were importing from `src.utils.url_info` or `src.utils.url_info_tldextract`.
2.  You need reliable subdomain/registered domain/suffix parsing (leveraging `tldextract`).
3.  You want to ensure usage of the latest standardized validation and normalization logic.

The adapter in `src/utils/helpers.py` provides some backward compatibility if your code imports `URLInfo` from there, but direct imports from `src.utils.url` are preferred going forward.