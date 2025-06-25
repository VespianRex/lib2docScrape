#!/usr/bin/env python3
"""
Script to measure test execution times and identify the slowest tests.
"""

import re
import subprocess
from pathlib import Path


def run_tests_with_timing():
    """Run tests and capture timing information."""
    print("🔍 Running tests to measure execution times...")

    cmd = [
        "uv",
        "run",
        "pytest",
        "--durations=50",  # Show top 50 slowest tests
        "-v",
        "--tb=no",  # No tracebacks to keep output clean
        "-x",  # Stop on first failure to get timing data faster
        "tests/",
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        return result.stdout, result.stderr

    except subprocess.TimeoutExpired:
        print("⚠️  Test run timed out, but we can still analyze partial results")
        return "", ""


def parse_timing_data(stdout):
    """Parse pytest timing output to find slowest tests."""
    print("\n📊 Analyzing test timing data...")

    # Look for the durations section
    lines = stdout.split("\n")
    timing_section = False
    slow_tests = []

    for line in lines:
        if "slowest durations" in line.lower():
            timing_section = True
            continue
        elif timing_section and line.strip() == "":
            break
        elif timing_section and line.strip():
            # Parse lines like: "2.50s call     tests/some/test.py::test_function"
            match = re.match(r"(\d+\.\d+)s\s+\w+\s+(.+)", line.strip())
            if match:
                duration = float(match.group(1))
                test_name = match.group(2)
                slow_tests.append((duration, test_name))

    return sorted(slow_tests, reverse=True)


def identify_slow_tests():
    """Run a quick test to identify slow tests."""
    print("🚀 Quick test run to identify slow tests...")

    # Run a subset of tests first to get timing data
    cmd = [
        "uv",
        "run",
        "pytest",
        "--durations=20",
        "-v",
        "--tb=no",
        "--maxfail=5",
        "tests/test_helpers.py",
        "tests/utils/test_circuit_breaker.py",
        "tests/utils/test_performance.py",
        "tests/e2e/",
        "tests/performance/",
    ]

    try:
        result = subprocess.run(
            cmd, cwd=Path(__file__).parent, capture_output=True, text=True, timeout=120
        )

        print("📋 Test output captured, analyzing...")
        return parse_timing_data(result.stdout)

    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return []


def main():
    """Main function to identify and report slow tests."""
    print("🔍 SLOW TEST IDENTIFICATION")
    print("=" * 50)

    slow_tests = identify_slow_tests()

    if not slow_tests:
        print("❌ No timing data found. Let me check specific known slow tests...")

        # Check known potentially slow test patterns
        known_slow_patterns = [
            "tests/e2e/",
            "tests/performance/",
            "tests/test_helpers.py::test_rate_limiter",
            "tests/utils/test_circuit_breaker.py",
            "tests/utils/test_performance.py",
            "tests/test_integration*.py",
        ]

        print("\n🎯 Known potentially slow test areas:")
        for pattern in known_slow_patterns:
            print(f"  • {pattern}")

        return

    print(f"\n🐌 TOP {min(10, len(slow_tests))} SLOWEST TESTS:")
    print("-" * 60)

    for i, (duration, test_name) in enumerate(slow_tests[:10], 1):
        print(f"{i:2d}. {duration:6.2f}s - {test_name}")

    print("\n📈 ANALYSIS:")
    print(f"  • Total tests analyzed: {len(slow_tests)}")

    if slow_tests:
        total_slow_time = sum(duration for duration, _ in slow_tests[:5])
        print(f"  • Top 5 tests total time: {total_slow_time:.2f}s")
        print(f"  • Average of top 5: {total_slow_time/5:.2f}s")

        if slow_tests[0][0] > 1.0:
            print(
                f"  • Slowest test is {slow_tests[0][0]:.2f}s - significant optimization opportunity!"
            )

    print("\n🎯 NEXT STEPS:")
    print("  1. Examine the top 5 slowest tests")
    print("  2. Look for sleep() calls, network requests, or heavy computation")
    print("  3. Add mocking or reduce test scope")
    print("  4. Consider splitting large tests into smaller ones")


if __name__ == "__main__":
    main()
