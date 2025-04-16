#!/usr/bin/env python3
"""Test runner script for the documentation crawler system."""

import argparse
import logging
import os
import subprocess
import sys
import time
from typing import List, Optional, Tuple

import pytest


def setup_logging(level: str = "INFO") -> None:
    """
    Configure logging for the application.
    
    Args:
        level: The logging level to set (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")
    
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run tests for the documentation crawler system"
    )
    
    parser.add_argument(
        "-k", "--keyword",
        help="Only run tests which match the given substring expression"
    )
    
    parser.add_argument(
        "--unit",
        action="store_true",
        help="Run only unit tests"
    )
    
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run only integration tests"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Increase verbosity"
    )
    
    parser.add_argument(
        "--cov",
        action="store_true",
        help="Run tests with coverage report"
    )
    
    parser.add_argument(
        "--html",
        action="store_true",
        help="Generate HTML coverage report"
    )
    
    parser.add_argument(
        "-n", "--workers",
        type=int,
        default=0,
        help="Number of workers to use (0 for auto)"
    )
    
    parser.add_argument(
        "--no-warnings",
        action="store_true",
        help="Disable warning capture"
    )

    parser.add_argument(
        "--maxfail",
        type=int,
        default=0,
        help="Maximum number of failures before stopping"
    )
    
    return parser.parse_args()


def get_test_files(unit_only: bool = False, integration_only: bool = False) -> List[str]:
    """
    Get list of test files to run.
    
    Args:
        unit_only: Run only unit tests
        integration_only: Run only integration tests
        
    Returns:
        List of test file paths
    """
    test_dir = "tests"
    if not os.path.exists(test_dir):
        print(f"Error: Test directory '{test_dir}' not found")
        sys.exit(1)
    
    if integration_only:
        return [os.path.join(test_dir, "test_integration.py")]
    elif unit_only:
        return [
            os.path.join(test_dir, f)
            for f in os.listdir(test_dir)
            if f.startswith("test_") and f != "test_integration.py"
        ]
    else:
        return [
            os.path.join(test_dir, f)
            for f in os.listdir(test_dir)
            if f.startswith("test_")
        ]


def run_tests(
    files: List[str],
    args: argparse.Namespace
) -> Tuple[int, Optional[str]]:
    """
    Run pytest with specified arguments.
    
    Args:
        files: List of test files to run
        args: Parsed command line arguments
        
    Returns:
        Tuple of (exit code, coverage report path if generated)
    """
    pytest_args = files.copy()
    
    # Add verbosity
    if args.verbose:
        pytest_args.append("-v")
    
    # Add keyword filter
    if args.keyword:
        pytest_args.extend(["-k", args.keyword])
    
    # Add coverage options
    cov_report_path = None
    if args.cov:
        pytest_args.extend([
            "--cov=src",
            "--cov-report=term-missing"
        ])
        if args.html:
            cov_report_path = "htmlcov"
            pytest_args.append("--cov-report=html")
    
    # Add parallel execution
    if args.workers > 0:
        pytest_args.extend(["-n", str(args.workers)])
    
    # Add warning control
    if args.no_warnings:
        pytest_args.append("-p no:warnings")

    # Add maxfail option
    if args.maxfail > 0:
        pytest_args.extend(["--maxfail", str(args.maxfail)])
    
    # Run tests using uv
    command = ["uv", "pytest"] + pytest_args
    process = subprocess.run(command, capture_output=True, text=True)
    print(process.stdout)
    print(process.stderr)
    exit_code = process.returncode
    
    return exit_code, cov_report_path


def print_summary(
    start_time: float,
    exit_code: int,
    cov_report_path: Optional[str]
) -> None:
    """
    Print test execution summary.
    
    Args:
        start_time: Test start timestamp
        exit_code: Test execution exit code
        cov_report_path: Path to coverage report if generated
    """
    duration = time.time() - start_time
    
    print("\nTest Execution Summary")
    print("=====================")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Exit Code: {exit_code}")
    
    if exit_code == 0:
        print("Status: All tests passed")
    else:
        print("Status: Some tests failed")
    
    if cov_report_path:
        print(f"\nCoverage report generated in: {cov_report_path}")
        if os.path.exists(cov_report_path):
            print(f"Open {cov_report_path}/index.html in your browser to view the report")


def check_dependencies() -> None:
    """Check if all required dependencies are installed."""
    required = [
        "pytest",
        "pytest-asyncio",
        "pytest-cov",
        "pytest-xdist",
        "beautifulsoup4",
        "aiohttp",
        "pydantic"
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing.append(package)
    
    if missing:
        print("Error: Missing required dependencies:")
        for package in missing:
            print(f"  - {package}")
        print("\nInstall them using:")
        print(f"pip install {' '.join(missing)}")
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    setup_logging(level="DEBUG") # Enable debug logging for tests
    # Parse arguments
    args = parse_args()
    
    # Check dependencies
    check_dependencies()
    
    # Get test files
    files = get_test_files(
        unit_only=args.unit,
        integration_only=args.integration
    )
    
    if not files:
        print("Error: No test files found")
        sys.exit(1)
    
    # Print test plan
    print("\nTest Execution Plan")
    print("==================")
    print(f"Files to test: {len(files)}")
    for f in files:
        print(f"  - {f}")
    print(f"Coverage: {'Enabled' if args.cov else 'Disabled'}")
    print(f"Workers: {args.workers if args.workers > 0 else 'auto'}")
    print()
    
    # Run tests
    start_time = time.time()
    exit_code, cov_report_path = run_tests(files, args)
    
    # Print summary
    print_summary(start_time, exit_code, cov_report_path)
    
    # Exit with test result
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
