#!/usr/bin/env python3
"""
Quick Test Performance Analysis Script

This script runs all tests with timing data and provides a simple analysis
of the slowest tests across the entire test suite.
"""

import re
import subprocess
import time
from pathlib import Path


def run_all_tests_with_timing():
    """Run all tests and capture timing information."""
    print("🚀 Running entire test suite with timing analysis...")

    # Run pytest with durations for all tests
    cmd = [
        "uv",
        "run",
        "pytest",
        "--durations=50",  # Show top 50 durations
        "--tb=no",  # No traceback for faster execution
        "-q",  # Quiet mode
        "--disable-warnings",
        "tests/",
    ]

    print(f"Running command: {' '.join(cmd)}")
    start_time = time.time()

    try:
        result = subprocess.run(
            cmd,
            cwd=Path("."),
            capture_output=True,
            text=True,
            timeout=1200,  # 20 minute timeout
        )

        total_time = time.time() - start_time
        print(f"✅ Tests completed in {total_time:.2f} seconds")
        print(f"Return code: {result.returncode}")

        return {
            "total_time": total_time,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    except subprocess.TimeoutExpired:
        print("❌ Tests timed out after 20 minutes!")
        return None
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return None


def parse_durations(output):
    """Parse duration information from pytest output."""
    durations = []

    # Look for duration lines like "0.12s call     tests/test_file.py::test_name"
    duration_pattern = r"(\d+\.\d+)s\s+(\w+)\s+(tests/[^:]+::[^\s]+)"

    in_durations_section = False
    for line in output.split("\n"):
        # Look for the durations section
        if "slowest durations" in line.lower():
            in_durations_section = True
            continue

        # Stop at empty line or next section
        if in_durations_section and (not line.strip() or line.startswith("=")):
            break

        if in_durations_section:
            match = re.search(duration_pattern, line)
            if match:
                duration = float(match.group(1))
                phase = match.group(2)  # call, setup, teardown
                test_name = match.group(3)
                durations.append((test_name, duration, phase))

    return durations


def analyze_results(results):
    """Analyze the test results and provide insights."""
    if not results:
        print("❌ No results to analyze")
        return

    print("\n📊 TEST SUITE ANALYSIS")
    print("=" * 50)
    print(f"Total execution time: {results['total_time']:.2f} seconds")
    print(f"Exit code: {results['return_code']}")

    # Parse durations
    durations = parse_durations(results["stdout"])

    if not durations:
        print("⚠️  No duration data found in output")
        print("\nRaw output sample:")
        print(results["stdout"][-500:])  # Last 500 chars
        return

    print(f"\n🐌 TOP {len(durations)} SLOWEST TESTS:")
    print("-" * 70)

    for i, (test_name, duration, phase) in enumerate(durations):
        # Extract just the test file and function name for readability
        if "::" in test_name:
            file_part = test_name.split("/")[-1].split("::")[0]
            func_part = test_name.split("::")[-1]
            short_name = f"{file_part}::{func_part}"
        else:
            short_name = test_name

        print(f"{i+1:2d}. {duration:6.2f}s ({phase:8s}) {short_name}")

    # Categorize slow tests
    very_slow = [d for d in durations if d[1] > 5.0]
    slow = [d for d in durations if 1.0 < d[1] <= 5.0]
    moderate = [d for d in durations if 0.5 < d[1] <= 1.0]

    print("\n📈 PERFORMANCE CATEGORIES:")
    print(f"Very slow (>5s):     {len(very_slow)} tests")
    print(f"Slow (1-5s):         {len(slow)} tests")
    print(f"Moderate (0.5-1s):   {len(moderate)} tests")
    print(f"Fast (<0.5s):        {50 - len(durations)} or more tests")

    # Show test count summary from output
    lines = results["stdout"].split("\n")
    for line in lines:
        if " passed" in line and (
            "failed" in line or "error" in line or "skipped" in line
        ):
            print(f"\n📋 TEST SUMMARY: {line.strip()}")
            break
        elif " passed in " in line and "failed" not in line:
            print(f"\n📋 TEST SUMMARY: {line.strip()}")
            break


def main():
    """Main execution function."""
    print("🎯 Quick Test Suite Performance Analysis")
    print("=" * 50)

    # Run tests
    results = run_all_tests_with_timing()

    # Analyze results
    analyze_results(results)

    if results and results["return_code"] != 0:
        print("\n⚠️  Some tests failed. Check stderr for details:")
        if results.get("stderr"):
            print(results["stderr"][-500:])  # Last 500 chars


if __name__ == "__main__":
    main()
