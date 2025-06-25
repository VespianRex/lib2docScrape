#!/bin/bash
# Simple script to run tests in parallel with optimal settings

# Get CPU count for optimal parallelization
CPU_COUNT=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)
WORKER_COUNT=$(( CPU_COUNT > 2 ? CPU_COUNT - 1 : CPU_COUNT ))

# Run tests with parallel workers
uv run pytest -n $WORKER_COUNT --dist=worksteal "$@"