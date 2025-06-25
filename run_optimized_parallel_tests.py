#!/usr/bin/env python3
"""
Optimized parallel test runner for lib2docScrape.

This script runs tests in parallel with optimized settings and test grouping
to maximize performance and minimize test execution time.
"""

import argparse
import multiprocessing
import os
import subprocess
import sys
import time


def get_optimal_worker_count():
    """Calculate optimal number of workers based on CPU count and system resources."""
    cpu_count = multiprocessing.cpu_count()

    # For I/O bound tests (which most of our tests are), we can use more workers
    # than CPU cores. However, we need to balance with memory usage.
    if cpu_count >= 16:
        # High-end systems: use 75% of cores, leaving some for system processes
        return max(12, int(cpu_count * 0.75))
    elif cpu_count >= 8:
        # Mid-range systems: use 80% of cores
        return max(6, int(cpu_count * 0.8))
    elif cpu_count >= 4:
        # Lower-end systems: use all cores but cap at reasonable limit
        return min(cpu_count, 6)
    else:
        # Very low-end systems: use available cores
        return max(2, cpu_count)


def run_test_group(group_name, test_patterns, workers=None, extra_args=None):
    """Run a specific group of tests with optimal settings."""
    if workers is None:
        workers = get_optimal_worker_count()

    # Check if test patterns exist
    valid_patterns = []
    for pattern in test_patterns:
        # For directory patterns, check if they exist
        if pattern.endswith("/"):
            if os.path.isdir(pattern):
                valid_patterns.append(pattern)
        else:
            # For file patterns, use glob to check if any files match
            import glob

            if glob.glob(pattern):
                valid_patterns.append(pattern)

    if not valid_patterns:
        print(f"\n{'=' * 80}")
        print(f"Skipping {group_name} - no matching test files found")
        print(f"{'=' * 80}\n")
        return True  # Consider it a success if no tests to run

    cmd = [
        "uv",
        "run",
        "pytest",
        f"-n{workers}",
        "--dist=worksteal",  # Work-stealing for better load balancing
        "--tb=short",  # Shorter tracebacks for parallel runs
    ]

    # Add test patterns
    cmd.extend(valid_patterns)

    # Add extra args if provided
    if extra_args:
        cmd.extend(extra_args)

    print(f"\n{'=' * 80}")
    print(f"Running {group_name} with {workers} workers")
    print(f"{'=' * 80}")
    print(f"Command: {' '.join(cmd)}\n")

    start_time = time.time()
    result = subprocess.run(cmd)
    duration = time.time() - start_time

    print(f"\n{'=' * 80}")
    print(
        f"{group_name} completed in {duration:.2f}s with exit code {result.returncode}"
    )
    print(f"{'=' * 80}\n")

    # Exit code 5 in pytest means no tests were collected, which is not a failure
    return result.returncode == 0 or result.returncode == 5


def run_all_tests_parallel():
    """Run all tests with intelligent grouping for optimal parallelization."""

    # Test groups organized by characteristics and dependencies
    test_groups = [
        {
            "name": "Fast Unit Tests",
            "patterns": [
                "tests/utils/",
                "tests/models/",
                "tests/url/",
                "tests/config/",
            ],
            "workers": get_optimal_worker_count(),
            "args": ["--durations=5"],
        },
        {
            "name": "Content Processing Tests",
            "patterns": [
                "tests/processors/",
                "tests/test_content_processor*.py",
                "tests/test_processor.py",
                "tests/test_quality.py",
                "tests/test_link_processor.py",
                "tests/test_content_processing_improvements.py",
            ],
            "workers": max(4, get_optimal_worker_count() // 2),
            "args": [],
        },
        {
            "name": "Backend Tests",
            "patterns": [
                "tests/backends/",
                "tests/test_backend_*.py",
            ],
            "workers": max(4, get_optimal_worker_count() // 2),
            "args": [],
        },
        {
            "name": "Crawler Tests",
            "patterns": [
                "tests/crawler/",
                "tests/test_crawler*.py",
            ],
            "workers": max(3, get_optimal_worker_count() // 3),
            "args": [],
        },
        {
            "name": "UI and Integration Tests",
            "patterns": [
                "tests/ui/",
                "tests/test_ui*.py",
                "tests/test_integration*.py",
                "tests/test_gui*.py",
            ],
            "workers": max(2, get_optimal_worker_count() // 4),
            "args": [],
        },
        {
            "name": "E2E and Performance Tests",
            "patterns": [
                "tests/e2e/",
                "tests/performance/",
                "tests/test_performance*.py",
            ],
            "workers": max(2, get_optimal_worker_count() // 4),
            "args": [],
        },
        {
            "name": "Remaining Tests",
            "patterns": [
                "tests/test_*.py",
                "tests/*/test_*.py",
            ],
            "workers": get_optimal_worker_count(),
            "args": [
                "--ignore=tests/utils/",
                "--ignore=tests/models/",
                "--ignore=tests/url/",
                "--ignore=tests/config/",
                "--ignore=tests/processors/",
                "--ignore=tests/backends/",
                "--ignore=tests/crawler/",
                "--ignore=tests/ui/",
                "--ignore=tests/e2e/",
                "--ignore=tests/performance/",
            ],
        },
    ]

    results = []

    for group in test_groups:
        success = run_test_group(
            group["name"], group["patterns"], group.get("workers"), group.get("args")
        )
        results.append(success)

    # Check if all test groups passed
    all_passed = all(results)

    if all_passed:
        print("\n✅ All test groups passed!")
    else:
        print("\n❌ Some test groups failed!")

    return all_passed


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run tests with optimal parallelization"
    )
    parser.add_argument("--group", help="Run only a specific test group")
    parser.add_argument(
        "--list-groups", action="store_true", help="List available test groups"
    )
    parser.add_argument("--workers", type=int, help="Override number of workers")
    args = parser.parse_args()

    success = run_all_tests_parallel()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
