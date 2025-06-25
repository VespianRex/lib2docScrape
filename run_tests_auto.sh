#!/bin/bash
# Simple wrapper for the auto-parallel test runner

# Run the Python script with UV
uv run python run_tests_auto.py "$@"