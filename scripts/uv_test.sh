#!/bin/bash
# UV Test Runner Script
# This script ensures all test commands use UV package manager

set -e

echo "============================================"
echo "Running tests with UV package manager"
echo "============================================"

# Check UV is available
echo "Checking UV version..."
uv --version

# Run tests with coverage using UV
echo "Running full test suite with coverage..."
uv run coverage run -m pytest tests/ -v

# Generate coverage report
echo "Generating coverage report..."
uv run coverage report

# Generate HTML coverage report
echo "Generating HTML coverage report..."
uv run coverage html

echo "============================================"
echo "Tests completed. Check htmlcov/index.html for detailed coverage report."
echo "============================================"
