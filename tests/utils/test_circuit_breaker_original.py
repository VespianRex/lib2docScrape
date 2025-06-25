"""
Optimized tests for the circuit breaker utility - no real sleep calls.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.utils.circuit_breaker import CircuitBreaker, CircuitState


def test_initial_state():
    """Test initial state of circuit breaker."""
    cb = CircuitBreaker()

    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0
    assert not cb.is_open()


def test_record_failure():
    """Test recording failures."""
    cb = CircuitBreaker(failure_threshold=3)

    # Record failures
    cb.record_failure()
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 1

    cb.record_failure()
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 2

    # This should trip the circuit breaker
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.failure_count == 3
    assert cb.is_open()


def test_record_success():
    """Test recording success."""
    cb = CircuitBreaker()

    # Record some failures
    cb.record_failure()
    cb.record_failure()
    assert cb.failure_count == 2

    # Record success
    cb.record_success()
    assert cb.failure_count == 0
    assert cb.state == CircuitState.CLOSED


@patch("time.time")
def test_half_open_state(mock_time):
    """Test transition to half-open state - OPTIMIZED with mocked time."""
    # Mock time progression - add more values for all time.time() calls
    mock_time.side_effect = [
        100.0,
        100.0,
        100.0,
        100.2,
        100.2,
    ]  # Initial, trip, last_failure_time, check after timeout

    cb = CircuitBreaker(failure_threshold=2, reset_timeout=0.1)

    # Trip the circuit breaker
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN

    # Check state - should be half-open after timeout (mocked)
    assert not cb.is_open()  # is_open() checks and updates state
    assert cb.state == CircuitState.HALF_OPEN


@patch("time.time")
def test_half_open_to_closed(mock_time):
    """Test transition from half-open to closed - OPTIMIZED with mocked time."""
    # Mock time progression - add more values for all time.time() calls
    mock_time.side_effect = [100.0, 100.0, 100.0, 100.2, 100.2, 100.2, 100.2]

    cb = CircuitBreaker(failure_threshold=2, reset_timeout=0.1, half_open_max_calls=2)

    # Trip the circuit breaker
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN

    # Check state - should be half-open after timeout (mocked)
    assert not cb.is_open()
    assert cb.state == CircuitState.HALF_OPEN

    # Record successful calls
    cb.record_success()
    assert cb.state == CircuitState.HALF_OPEN  # Still half-open

    cb.record_success()
    assert cb.state == CircuitState.CLOSED  # Now closed


def test_half_open_to_open():
    """Test transition from half-open to open on failure - simplified test."""
    cb = CircuitBreaker(failure_threshold=2, reset_timeout=0.1)

    # Trip the circuit breaker
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN

    # Manually set to half-open state
    cb._state = CircuitState.HALF_OPEN
    cb._half_open_calls = 0

    # Record a failure in half-open state
    cb.record_failure()
    assert cb.state == CircuitState.OPEN  # Back to open


def test_state_change_callback():
    """Test state change callback."""
    # Create a mock callback
    callback = MagicMock()

    cb = CircuitBreaker(failure_threshold=2, on_state_change=callback)

    # Trip the circuit breaker
    cb.record_failure()
    cb.record_failure()

    # Check that callback was called
    callback.assert_called_once_with(CircuitState.CLOSED, CircuitState.OPEN)

    # Reset and check callback again
    callback.reset_mock()
    cb.reset()
    callback.assert_called_once_with(CircuitState.OPEN, CircuitState.CLOSED)


def test_reset():
    """Test reset functionality."""
    cb = CircuitBreaker(failure_threshold=2)

    # Trip the circuit breaker
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN

    # Reset the circuit breaker
    cb.reset()
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0
    assert not cb.is_open()


@pytest.mark.asyncio
async def test_execute_async_success():
    """Test executing async operation with success."""
    cb = CircuitBreaker()

    # Create a mock operation that succeeds
    operation = AsyncMock(return_value="success")

    # Execute the operation
    result = await cb.execute_async(operation, "arg1", kwarg1="value1")

    # Check that the operation was called
    operation.assert_called_once_with("arg1", kwarg1="value1")

    # Check the result
    assert result == "success"
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0


@pytest.mark.asyncio
async def test_execute_async_failure():
    """Test executing async operation with failure."""
    cb = CircuitBreaker(failure_threshold=2)

    # Create a mock operation that fails
    operation = AsyncMock(side_effect=ValueError("Failure"))

    # Execute the operation and expect exception
    with pytest.raises(ValueError, match="Failure"):
        await cb.execute_async(operation)

    # Check state
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 1

    # Execute again and expect circuit to open
    with pytest.raises(ValueError, match="Failure"):
        await cb.execute_async(operation)

    assert cb.state == CircuitState.OPEN
    assert cb.failure_count == 2

    # Execute again and expect circuit breaker exception
    with pytest.raises(RuntimeError, match="Circuit breaker is open"):
        await cb.execute_async(operation)


def test_execute_sync_success():
    """Test executing sync operation with success."""
    cb = CircuitBreaker()

    # Create a mock operation that succeeds
    operation = MagicMock(return_value="success")

    # Execute the operation
    result = cb.execute(operation, "arg1", kwarg1="value1")

    # Check that the operation was called
    operation.assert_called_once_with("arg1", kwarg1="value1")

    # Check the result
    assert result == "success"
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0


def test_execute_sync_failure():
    """Test executing sync operation with failure."""
    cb = CircuitBreaker(failure_threshold=2)

    # Create a mock operation that fails
    operation = MagicMock(side_effect=ValueError("Failure"))

    # Execute the operation and expect exception
    with pytest.raises(ValueError, match="Failure"):
        cb.execute(operation)

    # Check state
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 1

    # Execute again and expect circuit to open
    with pytest.raises(ValueError, match="Failure"):
        cb.execute(operation)

    assert cb.state == CircuitState.OPEN
    assert cb.failure_count == 2

    # Execute again and expect circuit breaker exception
    with pytest.raises(RuntimeError, match="Circuit breaker is open"):
        cb.execute(operation)


def test_callback_exception_handling():
    """Test that exceptions in the state change callback are handled."""

    # Create a callback that raises an exception
    def callback_with_exception(_, __):  # Unused parameters
        raise ValueError("Callback error")

    cb = CircuitBreaker(failure_threshold=1, on_state_change=callback_with_exception)

    # This should not raise an exception even though the callback does
    cb.record_failure()

    # Verify the state changed despite the callback error
    assert cb.state == CircuitState.OPEN


@patch("time.time")
def test_is_open_timeout(mock_time):
    """Test that is_open transitions from open to half-open after timeout - OPTIMIZED."""
    # Set initial time
    current_time = 1000.0
    mock_time.return_value = current_time

    cb = CircuitBreaker(failure_threshold=1, reset_timeout=60)

    # Trip the circuit breaker
    cb.record_failure()
    assert cb.state == CircuitState.OPEN

    # Mock time to be just before timeout
    mock_time.return_value = current_time + 59

    # Check state - should still be open
    assert cb.is_open() is True
    assert cb.state == CircuitState.OPEN

    # Mock time to be after timeout
    mock_time.return_value = current_time + 61

    # Check state - should be half-open after timeout
    assert cb.is_open() is False
    assert cb.state == CircuitState.HALF_OPEN


@patch("time.time")
def test_half_open_success_count(mock_time):
    """Test that half_open_calls is incremented correctly - OPTIMIZED."""
    # Mock time progression
    mock_time.side_effect = [100.0, 100.0, 100.2, 100.2, 100.2, 100.2]

    cb = CircuitBreaker(failure_threshold=1, reset_timeout=0.1, half_open_max_calls=3)

    # Trip the circuit breaker
    cb.record_failure()
    assert cb.state == CircuitState.OPEN

    # Check state - should be half-open after timeout (mocked)
    assert not cb.is_open()
    assert cb.state == CircuitState.HALF_OPEN

    # Record successful calls
    cb.record_success()
    assert cb.state == CircuitState.HALF_OPEN  # Still half-open

    cb.record_success()
    assert cb.state == CircuitState.HALF_OPEN  # Still half-open

    cb.record_success()
    assert cb.state == CircuitState.CLOSED  # Now closed after 3 successes
