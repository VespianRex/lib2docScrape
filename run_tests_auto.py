#!/usr/bin/env python3
"""
Default test runner for lib2docScrape.

This script runs tests with optimal parallelization settings.
It's the recommended way to run tests for the project.

Usage:
    uv run python run_tests_auto.py [pytest_args]

Examples:
    # Run all tests with optimal parallelization
    uv run python run_tests_auto.py

    # Run specific tests
    uv run python run_tests_auto.py tests/utils/

    # Run tests with specific options
    uv run python run_tests_auto.py -v tests/utils/

    # Disable parallel execution
    uv run python run_tests_auto.py --no-parallel
"""

import subprocess
import sys


def main():
    """Run tests with optimal settings."""
    # Base command
    cmd = ["uv", "run", "pytest"]

    # Add any arguments passed to this script
    cmd.extend(sys.argv[1:])

    # Run the tests
    result = subprocess.run(cmd)

    # Return the exit code
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
