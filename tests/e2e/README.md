# E2E Tests for lib2docScrape

This directory contains end-to-end tests that validate the complete functionality of the lib2docScrape system.

## Test Modes

### Fast Mode (Default)
- **Uses mock backends** for ultra-fast testing
- **Disables DuckDuckGo** to prevent network calls
- **Reduced scope** (fewer pages, iterations)
- **Ideal for development** and CI/CD pipelines

```bash
# Fast mode (default)
pytest tests/e2e/
```

### Real-World Mode
- **Makes actual network requests** to real websites
- **Tests real functionality** end-to-end
- **Slower but more realistic** testing
- **Ideal for release validation**

```bash
# Real-world mode
E2E_FAST_MODE=false E2E_MOCK_NETWORK=false pytest tests/e2e/
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `E2E_FAST_MODE` | `true` | Enable fast mode with reduced scope |
| `E2E_MOCK_NETWORK` | `true` | Use mock network responses |
| `E2E_TIMEOUT` | `60` | Test timeout in seconds |
| `E2E_MAX_CONCURRENT` | `3` | Max concurrent tests |
| `SKIP_REAL_WORLD_TESTS` | `false` | Skip real network tests |
| `SKIP_SLOW_TESTS` | `false` | Skip slow tests |

## Performance Optimization

### Parallel Execution
```bash
# Run with 2 workers for faster execution
pytest tests/e2e/ -n 2

# Auto-detect optimal worker count
pytest tests/e2e/ -n auto
```

### Selective Testing
```bash
# Run only performance benchmarks
pytest tests/e2e/test_performance_benchmarks.py

# Run only real-world crawling tests
pytest tests/e2e/test_real_world_crawling.py

# Skip slow tests
pytest tests/e2e/ -m "not slow"
```

## Test Files

- **`test_performance_benchmarks.py`** - Performance and memory benchmarks
- **`test_real_world_crawling.py`** - Real website crawling validation
- **`test_sites.py`** - Test site configurations and management
- **`conftest.py`** - Test fixtures and configuration

## Performance Results

### Before Optimization
- Tests would **hang indefinitely** due to DuckDuckGo network calls
- Real-world tests were extremely slow

### After Optimization
- **Fast mode**: ~23 seconds for all 9 tests (with parallel execution)
- **Real-world mode**: ~31 seconds for all 9 tests
- **No hanging** or timeout issues
- **Both mock and real options** available

## Usage Examples

```bash
# Development workflow (fast)
pytest tests/e2e/ -v

# CI/CD pipeline (fast, parallel)
pytest tests/e2e/ -n auto --tb=short

# Release validation (real-world)
E2E_FAST_MODE=false pytest tests/e2e/ -n 2

# Debug specific test
pytest tests/e2e/test_performance_benchmarks.py::test_single_site_performance -v -s
```
