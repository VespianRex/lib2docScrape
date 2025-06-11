#!/usr/bin/env python
"""
Benchmark script for URL handling performance comparison.

This script compares the performance of the original URL handling implementation
with the new tldextract-based implementation.
"""

import random
import string
import sys
import time
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.helpers import URLInfo as NewURLInfo  # noqa: E402

# Import the original implementation directly
# Adjust the import path if needed
try:
    from src.utils.url_info import URLInfo as OldURLInfo
except ImportError:
    print("Original URL implementation not found, skipping comparison")
    OldURLInfo = None


# URL Generation Functions
def generate_random_string(length=10):
    """Generate a random string of fixed length."""
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for _ in range(length))


def generate_test_urls(count=1000):
    """Generate a list of test URLs for benchmarking."""
    urls = []

    # Simple URLs
    for i in range(count // 4):
        urls.append(f"https://example.com/path{i}")

    # URLs with query parameters
    for _i in range(count // 4):
        params = "&".join([f"param{j}=value{j}" for j in range(random.randint(1, 5))])
        urls.append(f"https://example.com/search?{params}")

    # URLs with subdomains
    for i in range(count // 4):
        subdomain = generate_random_string(random.randint(3, 8))
        urls.append(f"https://{subdomain}.example.com/page{i}.html")

    # URLs with various TLDs
    tlds = ["com", "org", "net", "co.uk", "io", "dev", "app"]
    for _i in range(count // 4):
        tld = random.choice(tlds)
        domain = generate_random_string(random.randint(5, 10))
        urls.append(f"https://{domain}.{tld}/index.html")

    return urls


def benchmark_implementation(implementation_class, urls, name="Implementation"):
    """Benchmark a URL handling implementation."""
    print(f"Benchmarking {name}...")

    start_time = time.time()
    valid_count = 0
    invalid_count = 0

    for url in urls:
        try:
            url_info = implementation_class(url)
            if url_info.is_valid:
                valid_count += 1
            else:
                invalid_count += 1
        except Exception as e:
            invalid_count += 1
            print(f"Error processing {url}: {e}")

    end_time = time.time()
    total_time = end_time - start_time

    print(f"{name} Results:")
    print(f"  Total URLs processed: {len(urls)}")
    print(f"  Valid URLs: {valid_count}")
    print(f"  Invalid URLs: {invalid_count}")
    print(f"  Total time: {total_time:.4f} seconds")
    print(f"  Average time per URL: {(total_time / len(urls)) * 1000:.4f} ms")
    print("")

    return total_time


def main():
    """Run the benchmark comparison."""
    print("URL Handling Performance Benchmark")
    print("=" * 40)

    # Number of URLs to test
    url_count = 1000
    print(f"Generating {url_count} test URLs...")
    urls = generate_test_urls(url_count)

    # Benchmark both implementations
    results = {}

    # New implementation
    results["new"] = benchmark_implementation(
        NewURLInfo, urls, "New Implementation (tldextract)"
    )

    # Original implementation (if available)
    if OldURLInfo:
        results["old"] = benchmark_implementation(
            OldURLInfo, urls, "Original Implementation"
        )

        # Compare results
        if results["old"] > 0:  # Avoid division by zero
            speedup = results["old"] / results["new"]
            percent_change = (results["old"] - results["new"]) / results["old"] * 100
            print("Performance Comparison:")
            print(f"  Speedup factor: {speedup:.2f}x")
            print(f"  Performance improvement: {percent_change:.2f}%")

    print("Benchmark complete!")


if __name__ == "__main__":
    main()
