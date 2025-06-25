#!/usr/bin/env python3
"""
Optimized test runner for lib2docScrape test suite.
This script runs tests with optimal parallelization and grouping strategies.
"""

import argparse
import multiprocessing
import subprocess
import sys
import time
from pathlib import Path


def get_optimal_worker_count():
    """Calculate optimal number of workers based on CPU count and test characteristics."""
    cpu_count = multiprocessing.cpu_count()

    # For I/O bound tests (which most of our tests are), we can use more workers
    # than CPU cores. However, we need to balance with memory usage and system stability.
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

    cmd = [
        "uv",
        "run",
        "pytest",
        f"-n{workers}",
        "--dist=worksteal",  # Work-stealing for better load balancing
        "--tb=short",  # Shorter tracebacks for parallel runs
        "--maxfail=5",  # Stop after 5 failures to save time
    ]

    if extra_args:
        cmd.extend(extra_args)

    # Add test patterns
    for pattern in test_patterns:
        cmd.append(pattern)

    print(f"\n🚀 Running {group_name} tests with {workers} workers...")
    print(f"Command: {' '.join(cmd)}")

    start_time = time.time()
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    end_time = time.time()

    duration = end_time - start_time
    print(f"✅ {group_name} completed in {duration:.2f}s")

    return result.returncode == 0


def run_all_tests_parallel():
    """Run all tests with intelligent grouping for optimal parallelization."""

    # Test groups organized by characteristics and dependencies
    test_groups = [
        {
            "name": "Unit Tests (Fast)",
            "patterns": [
                "tests/test_simple.py",
                "tests/test_base.py",
                "tests/test_helpers.py",
                "tests/test_conftest.py",
                "tests/test_feature_flags.py",
                "tests/models/",
                "tests/utils/",
                "tests/url/",
                "tests/config/",
            ],
            "workers": get_optimal_worker_count(),
            "args": ["--durations=5"],
        },
        {
            "name": "Content Processing",
            "patterns": [
                "tests/test_content_processor*.py",
                "tests/test_processor.py",
                "tests/test_quality.py",
                "tests/test_link_processor.py",
                "tests/processors/",
                "tests/test_content_processing_improvements.py",
            ],
            "workers": max(4, get_optimal_worker_count() // 2),
            "args": [],
        },
        {
            "name": "Crawler Core",
            "patterns": [
                "tests/test_crawler.py",
                "tests/test_crawler_main.py",
                "tests/test_crawler_module*.py",
                "tests/test_crawler_config.py",
                "tests/test_crawler_cleanup.py",
                "tests/test_crawler_documentation.py",
                "tests/test_crawler_fetch_and_process_with_backend.py",
                "tests/test_crawler_find_links_recursive.py",
                "tests/test_crawler_generate_search_queries.py",
                "tests/test_crawler_initialize_crawl_queue.py",
                "tests/test_crawler_original*.py",
                "tests/test_crawler_process_*.py",
                "tests/test_crawler_sequential.py",
                "tests/test_crawler_setup_backends.py",
                "tests/test_crawler_src*.py",
                "tests/test_crawler_url_handling.py",
                "tests/crawler/",
            ],
            "workers": max(6, get_optimal_worker_count() // 2),
            "args": [],
        },
        {
            "name": "Backend Tests",
            "patterns": [
                "tests/backends/",
                "tests/test_backend_*.py",
                "tests/test_scrapy_backend.py",
                "tests/test_crawl4ai*.py",
                "tests/test_http_mocking.py",
            ],
            "workers": max(4, get_optimal_worker_count() // 3),
            "args": ["--timeout=60"],
        },
        {
            "name": "Integration Tests",
            "patterns": [
                "tests/test_integration*.py",
                "tests/test_crawler_crawl_integration.py",
                "tests/test_url_handling_integration.py",
                "tests/test_backend_selector_integration.py",
                "tests/test_main*.py",
            ],
            "workers": max(2, get_optimal_worker_count() // 4),
            "args": ["--timeout=120"],
        },
        {
            "name": "GUI & UI Tests",
            "patterns": [
                "tests/test_gui*.py",
                "tests/ui/",
            ],
            "workers": max(2, get_optimal_worker_count() // 4),
            "args": ["--timeout=60"],
        },
        {
            "name": "URL Processing",
            "patterns": [
                "tests/test_url_*.py",
            ],
            "workers": max(4, get_optimal_worker_count() // 3),
            "args": [],
        },
        {
            "name": "Advanced & Edge Cases",
            "patterns": [
                "tests/test_crawler_advanced.py",
                "tests/test_crawler_edge_cases.py",
                "tests/test_content_processor_edge.py",
                "tests/test_content_processor_advanced.py",
                "tests/test_integration_advanced.py",
                "tests/test_url_security_extra.py",
                "tests/test_url_normalization_idn.py",
                "tests/test_url_parsing_windows.py",
            ],
            "workers": max(3, get_optimal_worker_count() // 3),
            "args": ["--timeout=90"],
        },
        {
            "name": "Specialized & Storage",
            "patterns": [
                "tests/test_organizer.py",
                "tests/organizers/",
                "tests/storage/",
                "tests/versioning/",
                "tests/property/",
            ],
            "workers": max(3, get_optimal_worker_count() // 3),
            "args": [],
        },
        {
            "name": "Performance & E2E",
            "patterns": [
                "tests/performance/",
                "tests/e2e/",
                "tests/test_backend_performance_tracker.py",
            ],
            "workers": max(2, get_optimal_worker_count() // 6),
            "args": ["--timeout=300", "-v"],
        },
    ]

    print(f"🔧 Detected {multiprocessing.cpu_count()} CPU cores")
    print(f"🎯 Optimal worker count: {get_optimal_worker_count()}")

    total_start = time.time()
    failed_groups = []

    for group in test_groups:
        success = run_test_group(
            group["name"],
            group["patterns"],
            group.get("workers"),
            group.get("args", []),
        )

        if not success:
            failed_groups.append(group["name"])
            print(f"❌ {group['name']} failed!")
        else:
            print(f"✅ {group['name']} passed!")

    total_end = time.time()
    total_duration = total_end - total_start

    print(f"\n📊 Total execution time: {total_duration:.2f}s")

    if failed_groups:
        print(f"❌ Failed groups: {', '.join(failed_groups)}")
        return False
    else:
        print("🎉 All test groups passed!")
        return True


def run_fast_subset():
    """Run a fast subset of tests for quick feedback."""
    patterns = [
        "tests/test_simple.py",
        "tests/test_base.py",
        "tests/test_helpers.py",
        "tests/models/",
        "tests/utils/test_circuit_breaker.py",
        "tests/config/",
    ]

    return run_test_group(
        "Fast Subset",
        patterns,
        workers=get_optimal_worker_count(),
        extra_args=["--durations=5", "--tb=line"],
    )


def run_single_threaded():
    """Run tests single-threaded for debugging."""
    cmd = ["uv", "run", "pytest", "-v", "--tb=long", "--durations=10", "tests/"]

    print("🐛 Running tests single-threaded for debugging...")
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(
        description="Optimized test runner for lib2docScrape"
    )
    parser.add_argument(
        "--mode",
        choices=["all", "fast", "debug"],
        default="all",
        help="Test execution mode",
    )
    parser.add_argument(
        "--workers", type=int, help="Override number of workers (default: auto-detect)"
    )
    parser.add_argument("--pattern", help="Run specific test pattern")

    args = parser.parse_args()

    if args.pattern:
        # Run specific pattern
        workers = args.workers or get_optimal_worker_count()
        success = run_test_group("Custom Pattern", [args.pattern], workers)
        sys.exit(0 if success else 1)

    if args.mode == "fast":
        success = run_fast_subset()
    elif args.mode == "debug":
        success = run_single_threaded()
    else:  # all
        success = run_all_tests_parallel()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
