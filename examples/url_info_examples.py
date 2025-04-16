"""
URLInfo Usage Examples

This file demonstrates common usage patterns for the URLInfo class.
"""

from src.utils.url_info import URLInfo, URLType

def basic_usage_example():
    """Basic usage of URLInfo."""
    print("\n=== Basic Usage ===")
    
    # Create a URLInfo instance
    url = URLInfo("https://www.example.com/path?param=value#fragment")
    
    # Check if URL is valid
    if url.is_valid:
        print(f"Raw URL: {url.raw_url}")
        print(f"Normalized URL: {url.normalized_url}")
        
        # Access components
        print(f"Scheme: {url.scheme}")
        print(f"Domain: {url.domain}")
        print(f"Path: {url.path}")
        print(f"Query: {url.query}")
        print(f"Fragment: {url.fragment}")
    else:
        print(f"URL validation failed: {url.error_message}")

def domain_parsing_example():
    """Example of domain parsing capabilities."""
    print("\n=== Domain Parsing ===")
    
    # Create a URLInfo instance with a complex domain
    url = URLInfo("https://blog.subdomain.example.co.uk/path")
    
    # Access domain components
    print(f"Full domain: {url.domain}")
    print(f"Root domain: {url.root_domain}")
    print(f"Subdomain: {url.subdomain}")
    print(f"TLD: {url.tld}")
    
    # Access structured domain parts
    parts = url.domain_parts
    print(f"Domain parts: {parts}")

def url_manipulation_example():
    """Example of URL manipulation methods."""
    print("\n=== URL Manipulation ===")
    
    # Create a base URL
    url = URLInfo("https://example.com/original/path?a=1&b=2")
    print(f"Original URL: {url}")
    
    # Change scheme
    http_url = url.with_scheme("http")
    print(f"After scheme change: {http_url}")
    
    # Change path
    path_url = url.with_path("/new/path")
    print(f"After path change: {path_url}")
    
    # Add query parameters
    params_url = url.with_query_params({'c': '3', 'a': 'updated'})
    print(f"After adding/updating params: {params_url}")
    
    # Remove query parameters
    no_params_url = url.without_query_params(['a'])
    print(f"After removing params: {no_params_url}")
    
    # Join paths
    joined_url = url.join("subpath")
    print(f"After joining path: {joined_url}")
    
    # Chaining operations
    modified_url = url.with_scheme("http").with_path("/api").with_query_params({"format": "json"})
    print(f"After chained operations: {modified_url}")
    
    # Original is unchanged
    print(f"Original URL (unchanged): {url}")

def security_validation_example():
    """Example of security validation features."""
    print("\n=== Security Validation ===")
    
    # Valid URL
    valid_url = URLInfo("https://example.com/path")
    print(f"Valid URL: {valid_url.is_valid}")
    
    # URLs with security issues
    security_tests = [
        "javascript:alert(1)",                       # JavaScript scheme
        "https://example.com/<script>alert(1)</script>",  # XSS attempt
        "https://example.com/path?id=1' OR '1'='1",  # SQLi attempt
        "https://example.com/../../etc/passwd",      # Path traversal
        "https://example.com/path?cmd=cat%20/etc/passwd|ls",  # Command injection
        "https://example.com/path%00.txt"            # Null byte injection
    ]
    
    for test_url in security_tests:
        url = URLInfo(test_url)
        status = "VALID" if url.is_valid else "INVALID"
        print(f"URL: {test_url}")
        print(f"Status: {status}")
        if not url.is_valid:
            print(f"Error: {url.error_message}")
        print("-" * 50)

def performance_caching_example():
    """Example demonstrating caching for performance."""
    print("\n=== Performance Caching ===")
    
    import time
    
    # Generate test URLs
    test_urls = [f"https://example{i}.com/path" for i in range(5)]
    
    # Without caching
    start_time = time.time()
    for _ in range(1000):
        for url_str in test_urls:
            url = URLInfo(url_str)
            _ = url.normalized_url
    regular_time = time.time() - start_time
    
    # With caching
    start_time = time.time()
    for _ in range(1000):
        for url_str in test_urls:
            url = URLInfo.from_cache(url_str)
            _ = url.normalized_url
    cached_time = time.time() - start_time
    
    print(f"Time without caching: {regular_time:.4f} seconds")
    print(f"Time with caching: {cached_time:.4f} seconds")
    print(f"Performance improvement: {(regular_time/cached_time):.2f}x faster")

def type_determination_example():
    """Example of URL type determination."""
    print("\n=== URL Type Determination ===")
    
    base_url = "https://example.com/base"
    
    # Test URLs
    urls = [
        "https://example.com/page",           # Internal
        "https://example.com/path?q=value",   # Internal
        "https://subdomain.example.com/page", # External (different domain)
        "http://example.com/page",            # External (different scheme)
        "https://other-site.com/page",        # External
        "/relative/path",                     # Internal (relative)
    ]
    
    for url_str in urls:
        url = URLInfo(url_str, base_url=base_url)
        if url.url_type == URLType.INTERNAL:
            type_str = "INTERNAL"
        elif url.url_type == URLType.EXTERNAL:
            type_str = "EXTERNAL"
        else:
            type_str = "UNKNOWN"
        print(f"URL: {url_str}")
        print(f"Type: {type_str}")
        print("-" * 30)

def run_all_examples():
    """Run all examples."""
    basic_usage_example()
    domain_parsing_example()
    url_manipulation_example()
    security_validation_example()
    performance_caching_example()
    type_determination_example()

if __name__ == "__main__":
    run_all_examples()