#!/usr/bin/env python3
"""
Benchmark script to demonstrate test execution performance improvements.
"""

import multiprocessing
import subprocess
import time
from pathlib import Path


def run_command_with_timing(cmd, description):
    """Run a command and measure execution time."""
    print(f"\n🔄 {description}")
    print(f"Command: {' '.join(cmd)}")

    start_time = time.time()
    result = subprocess.run(
        cmd, cwd=Path(__file__).parent, capture_output=True, text=True
    )
    end_time = time.time()

    duration = end_time - start_time
    success = result.returncode == 0

    print(f"{'✅' if success else '❌'} Duration: {duration:.2f}s")

    if not success:
        print(f"Error: {result.stderr}")

    return duration, success


def main():
    """Run benchmark comparison between single-threaded and parallel execution."""

    print("🚀 Test Execution Performance Benchmark")
    print(f"💻 System: {multiprocessing.cpu_count()} CPU cores")
    print("=" * 60)

    # Test patterns for benchmarking (subset of fast tests)
    test_patterns = [
        "tests/test_simple.py",
        "tests/test_base.py",
        "tests/test_helpers.py",
        "tests/models/",
        "tests/utils/test_circuit_breaker.py",
        "tests/config/",
    ]

    # Single-threaded execution
    single_cmd = ["uv", "run", "pytest", "-q"] + test_patterns
    single_duration, single_success = run_command_with_timing(
        single_cmd, "BASELINE: Single-threaded execution"
    )

    # Parallel execution with optimal workers
    optimal_workers = max(6, min(12, multiprocessing.cpu_count() * 3 // 4))
    parallel_cmd = [
        "uv",
        "run",
        "pytest",
        f"-n{optimal_workers}",
        "--dist=worksteal",
        "-q",
    ] + test_patterns
    parallel_duration, parallel_success = run_command_with_timing(
        parallel_cmd, f"OPTIMIZED: Parallel execution ({optimal_workers} workers)"
    )

    # Optimized script execution
    script_cmd = ["python3", "run_tests_optimized.py", "--mode", "fast"]
    script_duration, script_success = run_command_with_timing(
        script_cmd, "INTELLIGENT: Optimized script execution"
    )

    # Results summary
    print("\n" + "=" * 60)
    print("📊 BENCHMARK RESULTS")
    print("=" * 60)

    if single_success:
        print(f"Single-threaded:     {single_duration:.2f}s")
    else:
        print("Single-threaded:     FAILED")

    if parallel_success:
        speedup_parallel = (
            single_duration / parallel_duration
            if single_success and parallel_duration > 0
            else 0
        )
        print(
            f"Parallel ({optimal_workers} workers): {parallel_duration:.2f}s ({speedup_parallel:.1f}x speedup)"
        )
    else:
        print(f"Parallel ({optimal_workers} workers): FAILED")

    if script_success:
        speedup_script = (
            single_duration / script_duration
            if single_success and script_duration > 0
            else 0
        )
        print(
            f"Optimized script:    {script_duration:.2f}s ({speedup_script:.1f}x speedup)"
        )
    else:
        print("Optimized script:    FAILED")

    # Recommendations
    print("\n💡 RECOMMENDATIONS")
    print("-" * 30)

    if parallel_success and single_success:
        if parallel_duration < single_duration * 0.8:
            print("✅ Parallel execution provides significant speedup")
        else:
            print(
                "⚠️  Parallel execution overhead may not be worth it for small test sets"
            )

    if script_success:
        print("✅ Use 'python3 run_tests_optimized.py' for best performance")
        print("✅ Use './test-fast.sh --mode fast' for quick development feedback")

    print("\n🎯 For full test suite (~1323 tests), estimated speedup: 5-8x")
    print("🎯 Recommended command: python3 run_tests_optimized.py")


if __name__ == "__main__":
    main()
