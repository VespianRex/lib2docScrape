#!/usr/bin/env python3
"""
Simple optimized test runner that runs ALL 1323 tests with optimal parallelization.
No complex grouping - just run everything fast.
"""

import multiprocessing
import subprocess
import sys
import time
from pathlib import Path


def get_optimal_worker_count():
    """Calculate optimal number of workers based on CPU count."""
    cpu_count = multiprocessing.cpu_count()

    # For I/O bound tests, we can use more workers than CPU cores
    if cpu_count >= 16:
        return 12  # Leave some cores for system
    elif cpu_count >= 8:
        return max(6, int(cpu_count * 0.8))
    elif cpu_count >= 4:
        return max(4, cpu_count - 1)
    else:
        return max(2, cpu_count)


def run_all_tests():
    """Run all tests with optimal parallel settings."""
    workers = get_optimal_worker_count()

    cmd = [
        "uv",
        "run",
        "pytest",
        f"-n{workers}",
        "--dist=worksteal",
        "--tb=short",
        "--maxfail=20",  # Allow more failures before stopping
        "--durations=10",
        "-v",
        "tests/",  # Run ALL tests in the tests directory
    ]

    print(f"🚀 Running ALL tests with {workers} workers...")
    print(f"💻 System: {multiprocessing.cpu_count()} CPU cores detected")
    print(f"Command: {' '.join(cmd)}")
    print("=" * 80)

    start_time = time.time()
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    end_time = time.time()

    duration = end_time - start_time
    minutes = int(duration // 60)
    seconds = int(duration % 60)

    print("=" * 80)
    if result.returncode == 0:
        print(f"🎉 ALL TESTS PASSED in {minutes}m {seconds}s!")
    else:
        print(f"❌ Some tests failed. Total time: {minutes}m {seconds}s")

    print(f"⚡ Estimated speedup vs single-threaded: {workers}x")

    return result.returncode == 0


def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Usage: python3 run_all_tests_fast.py")
        print("Runs all 1323 tests with optimal parallelization")
        return

    success = run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
