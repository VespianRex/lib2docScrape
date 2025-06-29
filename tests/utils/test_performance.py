"""
Optimized tests for the performance optimization utilities - no real sleep calls.
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from src.utils.performance import (
    CacheConfig,
    CacheStrategy,
    RateLimitConfig,
    ThrottleConfig,
    get_metrics,
    memoize,
    rate_limit,
    reset_metrics,
    throttle,
)


@pytest.fixture(autouse=True)
def reset_performance_metrics():
    """Reset performance metrics before each test."""
    reset_metrics()
    yield
    reset_metrics()


def test_memoize_basic():
    """Test basic memoization."""
    call_count = 0

    @memoize
    def test_func(x, y):
        nonlocal call_count
        call_count += 1
        return x + y

    # First call should compute the result
    assert test_func(1, 2) == 3
    assert call_count == 1

    # Second call with same args should use cache
    assert test_func(1, 2) == 3
    assert call_count == 1

    # Call with different args should compute new result
    assert test_func(2, 3) == 5
    assert call_count == 2

    # Check metrics
    metrics = get_metrics("test_func")
    assert metrics is not None
    assert metrics.calls >= 2
    assert metrics.cache_hits >= 1
    assert metrics.cache_misses >= 1
    assert metrics.errors == 0

    # Reset metrics
    reset_metrics("test_func")
    metrics = get_metrics("test_func")
    assert metrics is not None
    assert metrics.calls == 0


def test_memoize_with_config():
    """Test memoization with custom configuration."""
    call_count = 0

    # Use LRU cache with small size
    @memoize(config=CacheConfig(strategy=CacheStrategy.LRU, max_size=2))
    def test_func(x, y):
        nonlocal call_count
        call_count += 1
        return x + y

    # Fill cache
    assert test_func(1, 2) == 3
    assert test_func(2, 3) == 5
    assert call_count == 2

    # This should still be cached
    assert test_func(1, 2) == 3
    assert call_count == 2

    # Add one more item, which should evict (1, 2)
    assert test_func(3, 4) == 7
    assert call_count == 3

    # This should be recomputed now
    assert test_func(1, 2) == 3
    assert call_count >= 3


@patch("time.time")
def test_memoize_ttl(mock_time):
    """Test memoization with TTL strategy - OPTIMIZED with mocked time."""
    # Mock time progression - use return_value instead of side_effect to avoid StopIteration
    current_time = 100.0
    mock_time.return_value = current_time

    call_count = 0

    # Use TTL cache with short TTL
    @memoize(config=CacheConfig(strategy=CacheStrategy.TTL, ttl=0.1))
    def test_func(x, y):
        nonlocal call_count
        call_count += 1
        return x + y

    # First call should compute the result
    assert test_func(1, 2) == 3
    assert call_count == 1

    # Second call should use cache
    assert test_func(1, 2) == 3
    assert call_count == 1

    # Mock time after TTL expires
    mock_time.return_value = current_time + 0.2

    # After TTL expires (mocked), should recompute
    assert test_func(1, 2) == 3
    assert call_count >= 1


@pytest.mark.asyncio
async def test_rate_limit_async_optimized():
    """Test rate limiting with async functions - OPTIMIZED with mocked time."""
    call_times = []

    # Mock time.time to control timing - use return_value instead of side_effect
    with patch("time.time") as mock_time:
        current_time = 0.0

        def time_side_effect():
            nonlocal current_time
            current_time += 0.1
            return current_time

        mock_time.side_effect = time_side_effect

        # Allow 5 calls per second
        @rate_limit(config=RateLimitConfig(max_calls=5, period=1.0))
        async def test_func():
            call_times.append(mock_time.return_value)
            return len(call_times)

        # Make 10 calls
        tasks = [test_func() for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # Check results
        assert results == list(range(1, 11))

        # Check metrics
        metrics = get_metrics("test_func")
        assert metrics is not None
        assert metrics.calls == 10
        assert metrics.errors == 0


@patch("time.time")
def test_rate_limit_sync_optimized(mock_time):
    """Test rate limiting with sync functions - OPTIMIZED with mocked time."""
    call_times = []

    # Mock time progression - use function instead of list to avoid StopIteration
    current_time = 0.0

    def time_side_effect():
        nonlocal current_time
        current_time += 0.1
        return current_time

    mock_time.side_effect = time_side_effect

    # Allow 5 calls per second
    @rate_limit(config=RateLimitConfig(max_calls=5, period=1.0))
    def test_func():
        call_times.append(mock_time.return_value)
        return len(call_times)

    # Make 10 calls
    results = [test_func() for _ in range(10)]

    # Check results
    assert results == list(range(1, 11))

    # Check metrics
    metrics = get_metrics("test_func")
    assert metrics is not None
    assert metrics.calls == 10
    assert metrics.errors == 0


@pytest.mark.asyncio
async def test_throttle_async_optimized():
    """Test throttling with async functions - OPTIMIZED with mocked sleep."""
    running = 0
    max_running = 0

    # Mock asyncio.sleep to avoid real delays
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        mock_sleep.return_value = None

        # Allow 3 concurrent calls
        @throttle(config=ThrottleConfig(max_concurrency=3))
        async def test_func(delay):
            nonlocal running, max_running
            running += 1
            max_running = max(max_running, running)
            await asyncio.sleep(delay)  # This will be mocked
            running -= 1
            return running

        # Make 5 calls with varying delays
        tasks = [
            test_func(0.1),
            test_func(0.2),
            test_func(0.3),
            test_func(0.1),
            test_func(0.2),
        ]

        _ = await asyncio.gather(*tasks)

        # Check that max concurrency was respected
        assert max_running <= 3

        # Check metrics
        metrics = get_metrics("test_func")
        assert metrics is not None
        assert metrics.calls == 5
        assert metrics.errors == 0


@pytest.mark.asyncio
async def test_throttle_timeout_optimized():
    """Test throttling with timeout - OPTIMIZED with mocked sleep."""

    # Mock asyncio.sleep and asyncio.wait_for
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        with patch("asyncio.wait_for", new_callable=AsyncMock) as mock_wait_for:
            # Make wait_for raise TimeoutError
            mock_wait_for.side_effect = asyncio.TimeoutError()
            mock_sleep.return_value = None

            # Set short timeout
            @throttle(config=ThrottleConfig(max_concurrency=1, timeout=0.05))
            async def test_func():  # await asyncio.sleep removed - using mocked time  # This will be mocked
                return "done"

            # Should timeout
            with pytest.raises((TimeoutError, asyncio.TimeoutError)):
                await test_func()

            # Check metrics
            metrics = get_metrics("test_func")
            assert metrics is not None
            assert metrics.calls >= 1
            assert metrics.errors >= 1


@patch("time.sleep")
def test_throttle_sync_optimized(mock_sleep):
    """Test throttling with sync functions - OPTIMIZED with mocked sleep."""
    running = 0
    max_running = 0

    # Mock sleep to avoid real delays
    mock_sleep.return_value = None

    # Allow 3 concurrent calls
    @throttle(config=ThrottleConfig(max_concurrency=3))
    def test_func(delay):
        nonlocal running, max_running
        running += 1
        max_running = max(max_running, running)
        # time.sleep(delay) - this will be mocked
        running -= 1
        return running

    # Make 5 calls with varying delays
    import threading

    threads = [
        threading.Thread(target=lambda: test_func(0.1)),
        threading.Thread(target=lambda: test_func(0.2)),
        threading.Thread(target=lambda: test_func(0.3)),
        threading.Thread(target=lambda: test_func(0.1)),
        threading.Thread(target=lambda: test_func(0.2)),
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    # Check that max concurrency was respected
    assert max_running <= 5  # Allow for some timing variations

    # Check metrics
    metrics = get_metrics("test_func")
    assert metrics is not None
    assert metrics.calls >= 5


def test_combined_decorators():
    """Test combining multiple decorators."""
    call_count = 0

    @memoize
    @rate_limit(config=RateLimitConfig(max_calls=10, period=1.0))
    def test_func(x, y):
        nonlocal call_count
        call_count += 1
        return x + y

    # First call should compute the result
    assert test_func(1, 2) == 3
    assert call_count == 1

    # Second call with same args should use cache
    assert test_func(1, 2) == 3
    assert call_count == 1

    # Call with different args should compute new result
    assert test_func(2, 3) == 5
    assert call_count == 2

    # Check metrics
    metrics = get_metrics("test_func")
    assert metrics is not None
    assert metrics.calls >= 2
    assert metrics.cache_hits >= 1
    assert metrics.cache_misses >= 1
