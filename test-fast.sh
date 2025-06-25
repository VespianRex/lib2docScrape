#!/bin/bash
# Quick test runner with optimal parallelization

set -e

echo "🚀 Running optimized test suite..."
echo "💻 System: $(nproc) CPU cores detected"

# Run the optimized test runner
python3 run_tests_optimized.py "$@"