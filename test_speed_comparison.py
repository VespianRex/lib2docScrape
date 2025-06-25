#!/usr/bin/env python3
"""
Compare test execution speed before and after optimization.
"""

import subprocess
import time
from pathlib import Path


def run_test_with_timing(test_path, description):
    """Run a specific test and measure execution time."""
    print(f"\n🔄 Running {description}...")

    cmd = ["uv", "run", "pytest", test_path, "-v", "--tb=no"]

    start_time = time.time()
    result = subprocess.run(
        cmd, cwd=Path(__file__).parent, capture_output=True, text=True
    )
    end_time = time.time()

    duration = end_time - start_time
    success = result.returncode == 0

    status = "✅ PASSED" if success else "❌ FAILED"
    print(f"{status} {description}: {duration:.2f}s")

    return duration, success


def main():
    """Compare test speeds."""
    print("🚀 TEST SPEED COMPARISON")
    print("=" * 50)

    # Test the known slow tests
    slow_tests = [
        (
            "tests/utils/test_circuit_breaker.py::test_half_open_state",
            "Circuit Breaker (with real sleep)",
        ),
        (
            "tests/utils/test_circuit_breaker.py::test_half_open_to_closed",
            "Circuit Breaker (with real sleep)",
        ),
        (
            "tests/utils/test_circuit_breaker.py::test_half_open_success_count",
            "Circuit Breaker (with real sleep)",
        ),
        ("tests/test_helpers.py::test_rate_limiter", "Rate Limiter (with real sleep)"),
        (
            "tests/utils/test_performance.py::test_memoize_ttl",
            "Performance TTL (with real sleep)",
        ),
    ]

    total_time = 0
    passed_tests = 0

    for test_path, description in slow_tests:
        try:
            duration, success = run_test_with_timing(test_path, description)
            total_time += duration
            if success:
                passed_tests += 1
        except Exception as e:
            print(f"❌ Error running {description}: {e}")

    print("\n📊 RESULTS:")
    print(f"  • Total time for {len(slow_tests)} slow tests: {total_time:.2f}s")
    print(f"  • Passed tests: {passed_tests}/{len(slow_tests)}")
    print(f"  • Average time per test: {total_time/len(slow_tests):.2f}s")

    print("\n💡 OPTIMIZATION IMPACT:")
    print("  • These tests contain real sleep() calls")
    print("  • Circuit breaker tests: ~0.2s sleep each")
    print("  • Rate limiter test: ~0.5s sleep")
    print("  • Performance TTL test: ~0.2s sleep")
    print("  • Total sleep time: ~1.1s per test run")

    print("\n🎯 OPTIMIZATION POTENTIAL:")
    print("  • Replace sleep() with mocked time")
    print("  • Expected speedup: 5-10x faster")
    print("  • Estimated optimized time: ~0.2-0.5s total")

    # Test a few fast tests for comparison
    print("\n🏃 FAST TESTS (for comparison):")
    fast_tests = [
        ("tests/test_simple.py", "Simple test"),
        ("tests/test_base.py", "Base test"),
    ]

    fast_total = 0
    for test_path, description in fast_tests:
        try:
            duration, success = run_test_with_timing(test_path, description)
            fast_total += duration
        except Exception as e:
            print(f"❌ Error running {description}: {e}")

    if fast_total > 0:
        print("\n📈 COMPARISON:")
        print(f"  • Slow tests average: {total_time/len(slow_tests):.2f}s")
        print(f"  • Fast tests average: {fast_total/len(fast_tests):.2f}s")
        print(
            f"  • Slow tests are {(total_time/len(slow_tests))/(fast_total/len(fast_tests)):.1f}x slower"
        )


if __name__ == "__main__":
    main()
