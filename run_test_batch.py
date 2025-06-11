#!/usr/bin/env python3
"""
Simple script to run tests in batches and capture results.
"""

import subprocess
import time


def run_test_batch(test_pattern, timeout=60):
    """Run a batch of tests with timeout."""
    cmd = ["uv", "run", "pytest", test_pattern, "--tb=line", "-v", "--no-header"]

    print(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd="/home/alex/DEV/lib2docScrape",
        )

        print(f"Return code: {result.returncode}")
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print(f"Test batch timed out after {timeout} seconds")
        return False
    except Exception as e:
        print(f"Error running tests: {e}")
        return False


if __name__ == "__main__":
    test_batches = [
        "tests/test_conftest.py::test_mock_success_backend_crawl",
        "tests/test_crawler.py::test_generate_search_queries_library_without_version",
        "tests/test_crawler.py::test_generate_search_queries_non_library_type",
        "tests/test_crawler.py::test_generate_search_queries_attribute_error_on_version",
    ]

    for batch in test_batches:
        print(f"\n{'=' * 60}")
        print(f"Testing: {batch}")
        print("=" * 60)

        success = run_test_batch(batch, timeout=60)
        print(f"Batch result: {'PASS' if success else 'FAIL'}")

        time.sleep(2)  # Brief pause between batches
