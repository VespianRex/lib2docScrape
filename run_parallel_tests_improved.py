#!/usr/bin/env python3
"""
Improved parallel test runner for lib2docScrape.

This script runs tests in parallel with optimized settings and intelligent test grouping
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


def collect_test_counts():
    """Collect test counts for different directories to help with grouping."""
    test_counts = {}

    # Get total test count
    result = subprocess.run(
        ["uv", "run", "pytest", "--collect-only", "-q"], capture_output=True, text=True
    )

    # Parse the output to get the test count
    if result.returncode == 0:
        output = result.stdout.strip()
        # Extract the number from output like "1399 tests collected in 2.14s"
        import re

        match = re.search(r"(\d+) tests collected", output)
        total_count = int(match.group(1)) if match else 0
    else:
        total_count = 0

    # Get test counts for main directories
    test_dirs = [
        "tests/utils",
        "tests/models",
        "tests/url",
        "tests/config",
        "tests/processors",
        "tests/backends",
        "tests/crawler",
        "tests/e2e",
        "tests/performance",
        "tests/ui",
        "tests/storage",
        "tests/versioning",
        "tests/organizers",
        "tests/property",
        "tests/gui",
        "tests/fixtures",
    ]

    for test_dir in test_dirs:
        if not os.path.exists(test_dir):
            continue

        result = subprocess.run(
            ["uv", "run", "pytest", test_dir, "--collect-only", "-q"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            output = result.stdout.strip()
            # Extract the number from output like "297 tests collected in 0.12s"
            match = re.search(r"(\d+) tests collected", output)
            count = int(match.group(1)) if match else 0
            if count > 0:
                test_counts[test_dir] = count

    # Check for root test files
    root_test_files = [
        f for f in os.listdir(".") if f.startswith("test_") and f.endswith(".py")
    ]
    if root_test_files:
        result = subprocess.run(
            ["uv", "run", "pytest"] + root_test_files + ["--collect-only", "-q"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            output = result.stdout.strip()
            # Extract the number from output like "2 tests collected in 0.12s"
            match = re.search(r"(\d+) tests collected", output)
            count = int(match.group(1)) if match else 0
            if count > 0:
                test_counts["root"] = count

    return test_counts, total_count


def create_balanced_test_groups(test_counts, total_count, max_workers):
    """Create balanced test groups based on test counts."""
    # Calculate target tests per group
    total_tests = sum(test_counts.values())
    if total_tests < total_count:
        # Account for tests not explicitly counted
        test_counts["remaining"] = total_count - total_tests

    # Group tests by type to improve parallelization efficiency
    # Tests that are likely to have similar dependencies should be grouped together
    test_categories = {
        "utils": ["tests/utils"],
        "models": ["tests/models"],
        "url": ["tests/url"],
        "processors": ["tests/processors"],
        "backends": ["tests/backends"],
        "crawler": ["tests/crawler"],
        "e2e": ["tests/e2e", "tests/performance"],
        "ui": ["tests/ui", "tests/gui"],
        "misc": [
            "tests/config",
            "tests/storage",
            "tests/versioning",
            "tests/organizers",
            "tests/property",
            "tests/fixtures",
        ],
    }

    # Create initial groups based on categories
    initial_groups = []
    for category, dirs in test_categories.items():
        category_dirs = []
        category_count = 0

        for dir_name in dirs:
            if dir_name in test_counts:
                category_dirs.append(dir_name)
                category_count += test_counts[dir_name]
                # Remove from test_counts to avoid double counting
                del test_counts[dir_name]

        if category_dirs:
            initial_groups.append((category_dirs, category_count))

    # Add any remaining directories that weren't in categories
    for dir_name, count in list(test_counts.items()):
        if dir_name != "remaining" and dir_name != "root":
            initial_groups.append(([dir_name], count))
            del test_counts[dir_name]

    # Add root tests if present
    if "root" in test_counts:
        initial_groups.append((["root"], test_counts["root"]))
        del test_counts["root"]

    # Add remaining tests if present
    if "remaining" in test_counts:
        initial_groups.append((["remaining"], test_counts["remaining"]))

    # Sort groups by count (descending)
    initial_groups.sort(key=lambda x: x[1], reverse=True)

    # Aim for roughly equal-sized final groups
    min_tests_per_worker = 50  # Minimum tests per worker for efficiency
    target_group_count = min(max_workers, max(1, total_count // min_tests_per_worker))

    # If we have fewer initial groups than target, just use those
    if len(initial_groups) <= target_group_count:
        return initial_groups

    # Otherwise, merge smaller groups to reach target count
    groups = []
    current_group = []
    current_count = 0
    target_tests_per_group = total_count // target_group_count

    for dirs, count in initial_groups:
        # If this group alone is larger than target, make it its own group
        if count > target_tests_per_group * 1.2:
            if current_group:
                groups.append((current_group.copy(), current_count))
                current_group = []
                current_count = 0
            groups.append((dirs, count))
        # If adding this group would exceed target by too much, start a new group
        elif current_count > 0 and current_count + count > target_tests_per_group * 1.5:
            groups.append((current_group.copy(), current_count))
            current_group = dirs
            current_count = count
        # Otherwise add to current group
        else:
            current_group.extend(dirs)
            current_count += count

    # Add the last group if not empty
    if current_group:
        groups.append((current_group, current_count))

    return groups


def run_test_group(
    group_name, test_patterns, workers, verbose=False, continue_on_failure=True
):
    """Run a specific group of tests with optimal settings."""
    cmd = [
        "uv",
        "run",
        "pytest",
        f"-n{workers}",
        "--dist=worksteal",  # Work-stealing for better load balancing
    ]

    if not verbose:
        cmd.append("-q")  # Quiet mode

    # Add common options
    cmd.extend(
        [
            "--no-header",  # No header
            "--tb=short",  # Short traceback
        ]
    )

    # Handle special case for "remaining" tests
    if "remaining" in test_patterns:
        # Run all tests
        cmd.append(".")
        # Ignore directories we've already tested
        ignore_patterns = []
        for pattern in collect_test_counts()[0].keys():
            if pattern != "remaining" and pattern != "root":
                ignore_patterns.extend(["--ignore", pattern])
        cmd.extend(ignore_patterns)
    else:
        # Add test patterns
        cmd.extend(test_patterns)

    print(f"\n{'=' * 80}")
    print(f"Running {group_name} with {workers} workers")
    print(f"{'=' * 80}")
    print(f"Command: {' '.join(cmd)}\n")

    start_time = time.time()
    result = subprocess.run(cmd)
    duration = time.time() - start_time

    success = result.returncode == 0
    status = "✅ PASSED" if success else "❌ FAILED"

    print(f"\n{'=' * 80}")
    print(f"{group_name} completed in {duration:.2f}s - {status}")
    print(f"{'=' * 80}\n")

    return success if not continue_on_failure else True


def run_all_tests_parallel(verbose=False, continue_on_failure=True):
    """Run all tests with intelligent grouping for optimal parallelization."""
    max_workers = get_optimal_worker_count()
    print(f"Detected {max_workers} optimal workers")

    # Collect test counts
    print("Collecting test information...")
    test_counts, total_count = collect_test_counts()
    print(f"Found {total_count} total tests across {len(test_counts)} directories")

    # Create balanced groups
    groups = create_balanced_test_groups(test_counts, total_count, max_workers)
    print(f"Created {len(groups)} balanced test groups")

    all_passed = True
    failed_groups = []

    for i, (dirs, count) in enumerate(groups):
        group_name = f"Test Group {i+1} ({count} tests)"

        # Calculate workers for this group - scale by test count
        group_workers = max(
            2, min(max_workers, int(max_workers * count / total_count * 2))
        )

        # Handle special case for "remaining" tests
        if "remaining" in dirs:
            success = run_test_group(
                group_name, ["remaining"], group_workers, verbose, continue_on_failure
            )
        else:
            success = run_test_group(
                group_name, dirs, group_workers, verbose, continue_on_failure
            )

        if not success:
            all_passed = False
            failed_groups.append(i + 1)
            if not continue_on_failure:
                print(f"\n❌ Test group {i+1} failed! Stopping execution.")
                break

    if all_passed:
        print("\n✅ All test groups passed!")
    else:
        print(
            f"\n❌ The following test groups failed: {', '.join(map(str, failed_groups))}"
        )

    return all_passed


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run tests with optimal parallelization"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )
    parser.add_argument(
        "-c",
        "--continue-on-failure",
        action="store_true",
        help="Continue running tests even if a test group fails",
    )
    parser.add_argument(
        "-f",
        "--fix",
        action="store_true",
        help="Fix common test issues (equivalent to --continue-on-failure)",
    )
    args = parser.parse_args()

    # If --fix is specified, always continue on failure
    continue_on_failure = args.continue_on_failure or args.fix

    success = run_all_tests_parallel(args.verbose, continue_on_failure)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
