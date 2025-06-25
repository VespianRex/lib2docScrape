#!/bin/bash
# Simple optimized test runner - just run all tests fast
# Usage: ./run_tests_simple.sh

echo "🚀 Running all 1323 tests with optimal parallelization..."
echo "💻 System: $(nproc) CPU cores detected"

# Calculate optimal workers (75% of CPU cores for 16+ core systems)
CORES=$(nproc)
if [ $CORES -ge 16 ]; then
    WORKERS=12
elif [ $CORES -ge 8 ]; then
    WORKERS=$((CORES * 4 / 5))
elif [ $CORES -ge 4 ]; then
    WORKERS=$((CORES - 1))
else
    WORKERS=$CORES
fi

echo "🎯 Using $WORKERS workers"
echo "=" * 60

# Run all tests with optimal settings
time uv run pytest \
    -n$WORKERS \
    --dist=worksteal \
    --tb=short \
    --maxfail=20 \
    --durations=10 \
    tests/

echo ""
echo "🎉 Test execution complete!"
echo "⚡ Estimated speedup vs single-threaded: ${WORKERS}x"