"""
Global pytest configuration file.
This file configures pytest to run tests in parallel by default.
"""
import multiprocessing
import os
import sys

import pytest

# Add project root to the Python path to resolve import issues
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Explicitly set asyncio mode and fixture loop scope to avoid warnings
pytest.register_assert_rewrite("pytest_asyncio")


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


def pytest_configure(config):
    """Configure pytest."""
    # Set the default fixture loop scope to function to avoid warnings
    config.option.asyncio_mode = "strict"
    config.option.asyncio_default_fixture_loop_scope = "function"

    # Enable optimized parallel execution if not explicitly disabled
    if not config.getoption("--no-parallel") and not hasattr(config, "workerinput"):
        # Only enable in the main process, not in worker processes
        worker_count = get_optimal_worker_count()

        # Check if -n option is set to "auto" and replace with optimal worker count
        if config.getoption("-n", None) == "auto":
            config.option.numprocesses = worker_count


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--no-parallel",
        action="store_true",
        default=False,
        help="Disable parallel test execution",
    )
