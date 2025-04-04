import pytest
import time
import asyncio # Add asyncio import
from unittest.mock import patch, MagicMock
from urllib.parse import urlparse

from src.utils.helpers import (
    # URLProcessor, # Removed as class was deleted
    RateLimiter,
    RetryStrategy,
    Timer,
    calculate_similarity,
    generate_checksum,
    setup_logging
)

# test_url_processor removed as the tested class URLProcessor was removed from helpers.py
# URL processing is now handled by URLInfo in src/utils/url_info.py and tested in test_url_handling.py

@pytest.mark.asyncio
async def test_rate_limiter(): # Make test async
    """Test rate limiter functionality."""
    limiter = RateLimiter(requests_per_second=2)
    
    start_time = asyncio.get_event_loop().time() # Use event loop time
    
    # Make 3 requests
    for _ in range(3):
        wait_time = await limiter.acquire() # Add await
        await asyncio.sleep(wait_time) # Use asyncio.sleep
    
    end_time = asyncio.get_event_loop().time() # Use event loop time
    
    # Should take at least 1 second (2 requests allowed immediately, 1 delayed)
    assert end_time - start_time >= 1.0
    
    # Test with different rates
    fast_limiter = RateLimiter(requests_per_second=10)
    slow_limiter = RateLimiter(requests_per_second=0.5)
    
    assert fast_limiter.delay == 0.1  # 1/10 second
    assert slow_limiter.delay == 2.0  # 1/0.5 = 2 seconds

def test_retry_strategy():
    """Test retry strategy functionality."""
    strategy = RetryStrategy(max_retries=3, initial_delay=0.01, max_delay=0.1) # Use smaller delays for testing

    # Test successful retry
    mock_func_success = MagicMock()
    mock_func_success.side_effect = [ValueError("Attempt 1 failed"), ValueError("Attempt 2 failed"), "success"]
    
    attempt = 0
    last_exception = None
    while attempt < strategy.max_retries:
        attempt += 1
        try:
            result = mock_func_success()
            last_exception = None # Reset exception on success
            break # Exit loop on success
        except Exception as e:
            last_exception = e
            if not strategy.should_retry(attempt, e):
                 break # Don't retry if strategy says no
            delay = strategy.get_delay(attempt)
            # time.sleep(delay) # Don't actually sleep in tests
            print(f"Retrying after attempt {attempt}, delay {delay:.4f}s") # Optional debug

    assert last_exception is None # Should succeed eventually
    assert result == "success"
    assert mock_func_success.call_count == 3

    # Test max retries exceeded
    mock_func_fail = MagicMock()
    mock_func_fail.side_effect = ValueError("Persistent failure")

    attempt = 0
    last_exception = None
    while attempt < strategy.max_retries:
        attempt += 1
        try:
            mock_func_fail()
            last_exception = None
            break
        except Exception as e:
            last_exception = e
            if not strategy.should_retry(attempt, e):
                 break
            delay = strategy.get_delay(attempt)
            # time.sleep(delay)

    assert last_exception is not None # Should have failed
    assert isinstance(last_exception, ValueError)
    assert mock_func_fail.call_count == 3 # Max retries reached

    # Test immediate success
    mock_func_quick = MagicMock(return_value="quick success")
    attempt = 0
    last_exception = None
    while attempt < strategy.max_retries:
        attempt += 1
        try:
            result = mock_func_quick()
            last_exception = None
            break
        except Exception as e:
             last_exception = e
             # This part shouldn't be reached in this case
             break

    assert last_exception is None
    assert result == "quick success"
    assert mock_func_quick.call_count == 1

def test_timer():
    """Test timer functionality."""
    timer = Timer()
    
    # Test basic timing
    with timer:
        time.sleep(0.1)
    
    assert timer.duration >= 0.1 # Use duration property
    assert timer.start_time is not None
    assert timer.end_time is not None
    
    # Test reset
    timer.reset()
    assert timer.duration == 0 # Use duration property
    assert timer.start_time is None
    assert timer.end_time is None
    
    # Test nested timing
    with timer:
        with timer:  # Should work with nested contexts
            time.sleep(0.1)
    
    assert timer.duration >= 0.1 # Use duration property

def test_similarity_calculation():
    """Test content similarity calculation."""
    text1 = "This is a test document about Python programming"
    text2 = "This is a test document about Python coding"
    text3 = "Something completely different"
    
    # Similar texts should have high similarity
    assert calculate_similarity(text1, text2) > 0.8
    
    # Different texts should have low similarity
    assert calculate_similarity(text1, text3) < 0.5
    
    # Same text should have perfect similarity
    assert calculate_similarity(text1, text1) == 1.0
    
    # Empty texts should handle gracefully
    assert calculate_similarity("", "") == 1.0
    assert calculate_similarity(text1, "") == 0.0

def test_checksum_generation():
    """Test checksum generation."""
    content = "Test content for checksum"
    
    # Test basic checksum
    checksum1 = generate_checksum(content)
    assert isinstance(checksum1, str)
    assert len(checksum1) > 0
    
    # Test consistency
    checksum2 = generate_checksum(content)
    assert checksum1 == checksum2
    
    # Test different content
    checksum3 = generate_checksum("Different content")
    assert checksum1 != checksum3
    
    # Test empty content
    empty_checksum = generate_checksum("")
    assert isinstance(empty_checksum, str)
    assert len(empty_checksum) > 0

def test_logging_setup():
    """Test logging setup functionality."""
    with patch('logging.getLogger') as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        # Test basic setup
        logger = setup_logging()
        assert logger is None # Function returns None
        assert mock_logger.setLevel.called
        assert mock_logger.addHandler.called
        
        # Test with different log level
        logger = setup_logging(log_level="DEBUG")
        mock_logger.setLevel.assert_called_with("DEBUG")
        
        # Test with file output
        with patch('logging.FileHandler') as mock_file_handler:
            logger = setup_logging(log_file="test.log")
            mock_file_handler.assert_called_once_with("test.log")
