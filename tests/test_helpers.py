import pytest
import time
import asyncio # Add asyncio import
from unittest.mock import patch, MagicMock
from urllib.parse import urlparse
import logging # Import logging

from src.utils.helpers import (
    # URLProcessor, # Removed as class was deleted
    RateLimiter,
    RetryStrategy,
    Timer,
    calculate_similarity,
    generate_checksum,
    setup_logging
)
from src.utils.url import URLInfo, URLType # Corrected import path
from src.organizers.doc_organizer import DocumentContent

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

    # Should take at least 0.5 seconds (2 requests allowed immediately, 1 delayed by ~0.5s)
    assert end_time - start_time >= 0.5 # Corrected assertion
    # Removed incorrect assertions checking for a non-existent .delay attribute

def test_retry_strategy():
    """Test retry strategy functionality."""
    strategy = RetryStrategy(max_retries=3, initial_delay=0.01, max_delay=0.1) # Use smaller delays for testing

    # Test successful retry
    mock_func_success = MagicMock()
    mock_func_success.side_effect = [ValueError("Attempt 1 failed"), ValueError("Attempt 2 failed"), "success"]

    attempt = 0
    last_exception = None
    result = None # Initialize result
    while attempt < strategy.max_retries:
        attempt += 1
        try:
            result = mock_func_success()
            last_exception = None # Reset exception on success
            break # Exit loop on success
        except Exception as e:
            last_exception = e
            # Check if the exception type should be retried (adjust as needed)
            # For testing, let's assume ValueError should be retried here.
            # In real usage, you might check specific network errors.
            if not isinstance(e, ValueError): # Example: only retry ValueErrors
                 break
            if attempt >= strategy.max_retries: # Check if max retries reached
                 break
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
            # Check if the exception type should be retried
            if not isinstance(e, ValueError):
                 break
            if attempt >= strategy.max_retries:
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
    result = None # Initialize result
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

# Mock time.time for Timer tests to make them deterministic
# Added a 6th value (100.5) to the side_effect list for the logging call in the second timer's exit
@patch('time.time', side_effect=[100.0, 100.1, 100.2, 100.3, 100.4, 100.5])
def test_timer(mock_time):
    """Test timer functionality."""
    timer = Timer("TestOp")

    # Test basic timing
    with timer:
        # time.sleep(0.1) # No actual sleep needed due to mock
        pass # Simulate work

    assert timer.duration == pytest.approx(0.1) # Check exact duration with approx
    assert timer.start_time == 100.0
    # assert timer.end_time == 100.1 # Timer doesn't store end_time

    # Timer doesn't have reset, create new instance
    timer2 = Timer("NestedOp")
    # Test sequential timing (not nested)
    with timer2:
         # time.sleep(0.1)
         pass

    assert timer2.duration == pytest.approx(0.1) # 100.4 - 100.3

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

def test_logging_setup(tmp_path):
    """Test logging setup functionality."""
    log_file = tmp_path / "test.log"

    # Test basic setup (console only)
    with patch('logging.basicConfig') as mock_basic_config, \
         patch('logging.StreamHandler') as mock_stream_handler, \
         patch('logging.FileHandler') as mock_file_handler: # Patch FileHandler too

        setup_logging(level="INFO")
        mock_basic_config.assert_called_once()
        args, kwargs = mock_basic_config.call_args
        assert kwargs['level'] == logging.INFO
        assert len(kwargs['handlers']) == 1 # Only console handler expected
        mock_stream_handler.assert_called_once()
        mock_file_handler.assert_not_called() # File handler shouldn't be called

    # Test with different log level
    with patch('logging.basicConfig') as mock_basic_config:
        setup_logging(level="DEBUG")
        args, kwargs = mock_basic_config.call_args
        assert kwargs['level'] == logging.DEBUG

    # Test with file output
    with patch('logging.basicConfig') as mock_basic_config, \
         patch('logging.StreamHandler'), \
         patch('logging.FileHandler') as mock_file_handler: # Patch FileHandler

        setup_logging(level="WARNING", log_file=str(log_file))
        mock_basic_config.assert_called_once()
        args, kwargs = mock_basic_config.call_args
        assert kwargs['level'] == logging.WARNING
        assert len(kwargs['handlers']) == 2 # Console and file handler expected
        mock_file_handler.assert_called_once_with(str(log_file))


# Test helper functions
def create_test_content(url, title, content, metadata=None):
    """
    Helper to create test document content that can be used in tests.
    
    This returns a DocumentContent object that wraps the dictionary and provides
    attribute-style access to match test expectations.
    
    Args:
        url: Document URL
        title: Document title
        content: Document content (text or dictionary)
        metadata: Optional metadata dictionary
        
    Returns:
        DocumentContent: Object with content attribute
    """
    data = {
        "url": url,
        "title": title,
        "content": content
    }
    
    if metadata:
        data.update(metadata)
        
    return DocumentContent(data)

def create_mock_response(status_code=200, content=None, url="https://example.com", 
                         headers=None, content_type="text/html"):
    """
    Create a mock HTTP response object for testing.
    
    Args:
        status_code: HTTP status code (default: 200)
        content: Response content (default: empty HTML)
        url: Response URL (default: example.com)
        headers: Response headers (default: basic headers)
        content_type: Content type (default: text/html)
        
    Returns:
        MagicMock: Mocked response object with appropriate attributes
    """
    if content is None:
        content = "<html><body>Test content</body></html>"
        
    if headers is None:
        headers = {'Content-Type': content_type}
    
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.content = content.encode('utf-8') if isinstance(content, str) else content
    mock_response.text = content if isinstance(content, str) else content.decode('utf-8')
    mock_response.url = url
    mock_response.headers = headers
    
    # Add common response methods
    mock_response.json.return_value = {} if content in (None, "") else {"data": "mock json data"}
    mock_response.raise_for_status.side_effect = None if status_code < 400 else Exception(f"HTTP Error: {status_code}")
    
    return mock_response

def create_test_url_info(url, url_type=URLType.INTERNAL, domain=None, path=None):
    """
    Create a URLInfo object for testing.
    
    Args:
        url: The URL string
        url_type: The URLType enum value (default: DOCUMENTATION)
        domain: Optional domain override
        path: Optional path override
        
    Returns:
        URLInfo: Configured URLInfo object
    """
    parsed = urlparse(url)
    url_info = URLInfo(url)
    url_info.url_type = url_type
    
    if domain:
        url_info.domain = domain
    else:
        url_info.domain = parsed.netloc
    
    if path:
        url_info.path = path
    else:
        url_info.path = parsed.path
        
    return url_info

def async_test(coro):
    """
    Decorator for running async tests without pytest.mark.asyncio.
    
    Args:
        coro: The coroutine function to test
        
    Returns:
        function: Wrapped test function
    """
    def wrapper(*args, **kwargs):
        return asyncio.run(coro(*args, **kwargs))
    return wrapper
