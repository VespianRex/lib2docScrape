"""
Tests for the retry utilities.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.utils.retry import (
    RetryStrategy,
    ConstantDelay,
    ExponentialBackoff,
    LinearBackoff,
    RetryWithStrategy
)

def test_constant_delay():
    """Test constant delay strategy."""
    strategy = ConstantDelay(delay=2.0)
    
    # Check delays for different attempts
    assert strategy.get_delay(0) == 2.0
    assert strategy.get_delay(1) == 2.0
    assert strategy.get_delay(5) == 2.0
    
    # Check should_retry
    assert strategy.should_retry(0, 3) is True
    assert strategy.should_retry(2, 3) is True
    assert strategy.should_retry(3, 3) is False

def test_exponential_backoff():
    """Test exponential backoff strategy."""
    strategy = ExponentialBackoff(base_delay=1.0, max_delay=10.0, jitter=False)
    
    # Check delays for different attempts
    assert strategy.get_delay(0) == 1.0
    assert strategy.get_delay(1) == 2.0
    assert strategy.get_delay(2) == 4.0
    assert strategy.get_delay(3) == 8.0
    
    # Check max delay
    assert strategy.get_delay(10) == 10.0  # Should be capped at max_delay

def test_exponential_backoff_with_jitter():
    """Test exponential backoff strategy with jitter."""
    strategy = ExponentialBackoff(base_delay=1.0, max_delay=10.0, jitter=True)
    
    # Check that delays are within expected range
    for attempt in range(5):
        delay = strategy.get_delay(attempt)
        expected = min(1.0 * (2 ** attempt), 10.0)
        # With 20% jitter, the delay should be within 80-120% of expected
        assert 0.8 * expected <= delay <= 1.2 * expected

def test_linear_backoff():
    """Test linear backoff strategy."""
    strategy = LinearBackoff(base_delay=1.0, increment=2.0, max_delay=10.0)
    
    # Check delays for different attempts
    assert strategy.get_delay(0) == 1.0
    assert strategy.get_delay(1) == 3.0
    assert strategy.get_delay(2) == 5.0
    assert strategy.get_delay(3) == 7.0
    assert strategy.get_delay(4) == 9.0
    
    # Check max delay
    assert strategy.get_delay(5) == 10.0  # Should be capped at max_delay

@pytest.mark.asyncio
async def test_retry_async_success_first_try():
    """Test async retry with success on first try."""
    strategy = ConstantDelay(delay=0.1)
    retry = RetryWithStrategy(strategy, max_retries=3)
    
    # Create a mock operation that succeeds
    operation = AsyncMock(return_value="success")
    
    # Call the operation with retry
    result = await retry.retry_async(operation, "arg1", kwarg1="value1")
    
    # Check that the operation was called once
    operation.assert_called_once_with("arg1", kwarg1="value1")
    
    # Check the result
    assert result == "success"

@pytest.mark.asyncio
async def test_retry_async_success_after_retry():
    """Test async retry with success after retry."""
    strategy = ConstantDelay(delay=0.1)
    retry = RetryWithStrategy(strategy, max_retries=3)
    
    # Create a mock operation that fails twice then succeeds
    operation = AsyncMock(side_effect=[
        ValueError("First failure"),
        ValueError("Second failure"),
        "success"
    ])
    
    # Call the operation with retry
    result = await retry.retry_async(operation)
    
    # Check that the operation was called three times
    assert operation.call_count == 3
    
    # Check the result
    assert result == "success"

@pytest.mark.asyncio
async def test_retry_async_all_failures():
    """Test async retry with all failures."""
    strategy = ConstantDelay(delay=0.1)
    retry = RetryWithStrategy(strategy, max_retries=2)
    
    # Create a mock operation that always fails
    operation = AsyncMock(side_effect=ValueError("Failure"))
    
    # Call the operation with retry and expect exception
    with pytest.raises(ValueError, match="Failure"):
        await retry.retry_async(operation)
    
    # Check that the operation was called three times (initial + 2 retries)
    assert operation.call_count == 3

def test_retry_sync_success_first_try():
    """Test sync retry with success on first try."""
    strategy = ConstantDelay(delay=0.1)
    retry = RetryWithStrategy(strategy, max_retries=3)
    
    # Create a mock operation that succeeds
    operation = MagicMock(return_value="success")
    
    # Call the operation with retry
    result = retry.retry(operation, "arg1", kwarg1="value1")
    
    # Check that the operation was called once
    operation.assert_called_once_with("arg1", kwarg1="value1")
    
    # Check the result
    assert result == "success"

def test_retry_sync_success_after_retry():
    """Test sync retry with success after retry."""
    strategy = ConstantDelay(delay=0.1)
    retry = RetryWithStrategy(strategy, max_retries=3)
    
    # Create a mock operation that fails twice then succeeds
    operation = MagicMock(side_effect=[
        ValueError("First failure"),
        ValueError("Second failure"),
        "success"
    ])
    
    # Call the operation with retry
    result = retry.retry(operation)
    
    # Check that the operation was called three times
    assert operation.call_count == 3
    
    # Check the result
    assert result == "success"

def test_retry_sync_all_failures():
    """Test sync retry with all failures."""
    strategy = ConstantDelay(delay=0.1)
    retry = RetryWithStrategy(strategy, max_retries=2)
    
    # Create a mock operation that always fails
    operation = MagicMock(side_effect=ValueError("Failure"))
    
    # Call the operation with retry and expect exception
    with pytest.raises(ValueError, match="Failure"):
        retry.retry(operation)
    
    # Check that the operation was called three times (initial + 2 retries)
    assert operation.call_count == 3
