# Test Suite Optimization Guide

This document explains the optimized test execution setup for the lib2docScrape project, designed to significantly reduce test execution time through intelligent parallelization and grouping.

## Quick Start

### Fastest Option (Recommended)
```bash
# Run optimized test suite with intelligent grouping
python3 run_tests_optimized.py

# Or use the shell wrapper
./test-fast.sh
```

### Alternative Options
```bash
# Fast subset for quick feedback
python3 run_tests_optimized.py --mode fast

# Single-threaded for debugging
python3 run_tests_optimized.py --mode debug

# Manual parallel execution
uv run pytest -n auto --dist=worksteal
```

## Performance Improvements

### Before Optimization
- **Single-threaded execution**: ~15-20 minutes for full suite
- **No test grouping**: All tests run sequentially
- **No optimization for test characteristics**: CPU and I/O bound tests mixed

### After Optimization
- **Parallel execution**: 12-14 workers on 16-core system
- **Intelligent grouping**: Tests grouped by characteristics and dependencies
- **Estimated speedup**: 5-8x faster execution time
- **Work-stealing distribution**: Better load balancing across workers

## Optimization Strategy

### 1. Worker Count Calculation
```python
def get_optimal_worker_count():
    cpu_count = multiprocessing.cpu_count()
    
    if cpu_count >= 16:
        return max(12, int(cpu_count * 0.75))  # 75% of cores
    elif cpu_count >= 8:
        return max(6, int(cpu_count * 0.8))   # 80% of cores
    elif cpu_count >= 4:
        return min(cpu_count, 6)              # All cores, capped at 6
    else:
        return max(2, cpu_count)              # Minimum 2 workers
```

### 2. Test Grouping Strategy

Tests are intelligently grouped based on their characteristics:

#### Group 1: Unit Tests (Fast) - 12 workers
- Simple unit tests with minimal dependencies
- Fast execution, high parallelization benefit
- Examples: `test_simple.py`, `models/`, `utils/`

#### Group 2: Content Processing - 6 workers
- CPU-intensive content processing tests
- Moderate parallelization to avoid CPU contention
- Examples: `test_content_processor*.py`, `processors/`

#### Group 3: Crawler Core - 6 workers
- I/O bound crawler functionality tests
- Good parallelization for network operations
- Examples: `test_crawler.py`, `crawler/`

#### Group 4: Backend Tests - 4 workers
- Network I/O with external dependencies
- Conservative parallelization for stability
- Examples: `backends/`, `test_backend_*.py`

#### Group 5: Integration Tests - 2 workers
- Complex interactions between components
- Low parallelization to avoid race conditions
- Examples: `test_integration*.py`

#### Group 6: GUI Tests - 2 workers
- UI tests that can be flaky in parallel
- Conservative approach for reliability
- Examples: `gui/`, `test_gui*.py`

#### Group 7: Advanced & Edge Cases - 3 workers
- Complex scenarios and edge cases
- Moderate parallelization
- Examples: `test_*_advanced.py`, `test_*_edge*.py`

#### Group 8: Performance & E2E - 2 workers
- Resource-intensive tests
- Minimal parallelization to avoid interference
- Examples: `performance/`, `e2e/`

### 3. Configuration Optimizations

#### pytest.ini Configuration
```ini
[tool:pytest]
# Work-stealing distribution for better load balancing
addopts = --dist=worksteal --tb=short --maxfail=10 --durations=10

# Timeout configuration
timeout = 300
timeout_method = thread

# Warning suppression for cleaner output
filterwarnings = ignore::DeprecationWarning
```

#### pyproject.toml Integration
- Comprehensive test markers for filtering
- Optimized asyncio configuration
- Warning suppression for parallel execution

## Usage Examples

### Run Full Optimized Suite
```bash
python3 run_tests_optimized.py
```
Expected output:
```
🔧 Detected 16 CPU cores
🎯 Optimal worker count: 12
🚀 Running Unit Tests (Fast) tests with 12 workers...
✅ Unit Tests (Fast) completed in 3.2s
🚀 Running Content Processing tests with 6 workers...
✅ Content Processing completed in 8.5s
...
📊 Total execution time: 45.3s
🎉 All test groups passed!
```

### Run Fast Subset for Development
```bash
python3 run_tests_optimized.py --mode fast
```
Runs only the fastest tests for quick feedback during development.

### Run Specific Test Pattern
```bash
python3 run_tests_optimized.py --pattern "tests/test_crawler*.py"
```

### Debug Mode (Single-threaded)
```bash
python3 run_tests_optimized.py --mode debug
```
Useful when you need to debug test failures without parallel execution complexity.

## Manual Parallel Execution

If you prefer to use pytest directly:

```bash
# Auto-detect optimal worker count
uv run pytest -n auto --dist=worksteal

# Specify worker count manually
uv run pytest -n 12 --dist=worksteal

# Run specific test groups with custom settings
uv run pytest -n 6 --dist=worksteal tests/backends/ --timeout=60
```

## Performance Monitoring

### Built-in Duration Reporting
The optimized runner includes `--durations=10` to show the slowest tests:

```
======= slowest 10 durations =======
2.50s call     tests/e2e/test_real_world.py::test_complex_site
1.20s call     tests/performance/test_benchmarks.py::test_large_dataset
0.80s call     tests/integration/test_full_pipeline.py::test_end_to_end
...
```

### Custom Performance Analysis
```bash
# Show all test durations
uv run pytest --durations=0

# Profile specific test groups
uv run pytest tests/performance/ --durations=0 -v
```

## Troubleshooting

### Common Issues

#### 1. "Too many open files" Error
```bash
# Increase file descriptor limit
ulimit -n 4096
```

#### 2. Memory Issues with High Worker Count
```bash
# Reduce worker count manually
python3 run_tests_optimized.py --workers 6
```

#### 3. Flaky Tests in Parallel Mode
```bash
# Run problematic tests single-threaded
uv run pytest tests/problematic_test.py -v
```

#### 4. Async Event Loop Issues
The configuration includes proper asyncio settings, but if you encounter issues:
```bash
# Check for event loop conflicts
uv run pytest tests/async_test.py --asyncio-mode=strict
```

### Performance Tuning

#### System-Specific Optimization
```python
# Edit run_tests_optimized.py to adjust for your system
def get_optimal_worker_count():
    # Customize based on your hardware
    return min(your_optimal_count, multiprocessing.cpu_count())
```

#### Test-Specific Timeouts
```python
# Add to test groups in run_tests_optimized.py
"args": ["--timeout=120"]  # Longer timeout for slow tests
```

## Integration with CI/CD

### GitHub Actions Example
```yaml
- name: Run optimized tests
  run: |
    python3 run_tests_optimized.py --mode all
    
- name: Run fast tests for PR validation
  run: |
    python3 run_tests_optimized.py --mode fast
```

### Local Development Workflow
```bash
# Quick feedback during development
./test-fast.sh --mode fast

# Full validation before commit
./test-fast.sh

# Debug specific failures
python3 run_tests_optimized.py --mode debug --pattern "tests/failing_test.py"
```

## Monitoring and Metrics

The optimized runner provides detailed timing information:
- Individual group execution times
- Total execution time
- Failed group identification
- Worker utilization feedback

This helps identify bottlenecks and further optimization opportunities.

## Future Improvements

1. **Dynamic worker allocation** based on test characteristics
2. **Test result caching** for unchanged code
3. **Distributed testing** across multiple machines
4. **Smart test selection** based on code changes
5. **Performance regression detection**

## Contributing

When adding new tests, consider:
1. **Test characteristics**: Is it CPU-bound, I/O-bound, or integration?
2. **Appropriate grouping**: Which test group should it belong to?
3. **Parallel safety**: Can it run safely in parallel with other tests?
4. **Resource requirements**: Does it need special timeout or worker settings?

Update the test groups in `run_tests_optimized.py` accordingly.