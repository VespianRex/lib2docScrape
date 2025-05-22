"""
Tests for the circuit breaker utility.
"""
import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch

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

def test_half_open_state():
    """Test transition to half-open state."""
    cb = CircuitBreaker(failure_threshold=2, reset_timeout=0.1)
    
    # Trip the circuit breaker
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    
    # Wait for reset timeout
    time.sleep(0.2)
    
    # Check state - should be half-open after timeout
    assert not cb.is_open()  # is_open() checks and updates state
    assert cb.state == CircuitState.HALF_OPEN

def test_half_open_to_closed():
    """Test transition from half-open to closed."""
    cb = CircuitBreaker(failure_threshold=2, reset_timeout=0.1, half_open_max_calls=2)
    
    # Trip the circuit breaker
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    
    # Wait for reset timeout
    time.sleep(0.2)
    
    # Check state - should be half-open after timeout
    assert not cb.is_open()
    assert cb.state == CircuitState.HALF_OPEN
    
    # Record successful calls
    cb.record_success()
    assert cb.state == CircuitState.HALF_OPEN  # Still half-open
    
    cb.record_success()
    assert cb.state == CircuitState.CLOSED  # Now closed

def test_half_open_to_open():
    """Test transition from half-open to open on failure."""
    cb = CircuitBreaker(failure_threshold=2, reset_timeout=0.1)
    
    # Trip the circuit breaker
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    
    # Wait for reset timeout
    time.sleep(0.2)
    
    # Check state - should be half-open after timeout
    assert not cb.is_open()
    assert cb.state == CircuitState.HALF_OPEN
    
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
