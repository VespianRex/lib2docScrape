import pytest
import time
from unittest.mock import patch, MagicMock
from urllib.parse import urlparse

from src.utils.helpers import (
    URLProcessor,
    RateLimiter,
    RetryStrategy,
    Timer,
    calculate_similarity,
    generate_checksum,
    setup_logging
)

def test_url_processor():
    """Test URL processor functionality."""
    processor = URLProcessor()
    
    # Test URL normalization
    assert processor.normalize_url("HTTP://Example.COM/path") == "http://example.com/path"
    assert processor.normalize_url("https://docs.python.org/3/") == "https://docs.python.org/3"
    assert processor.normalize_url("example.com") == "http://example.com"
    
    # Test URL type determination
    assert processor._determine_url_type("https://docs.python.org") == "documentation"
    assert processor._determine_url_type("https://github.com/user/repo") == "repository"
    assert processor._determine_url_type("https://example.com/blog") == "unknown"
    
    # Test URL validation
    assert processor.is_valid_url("https://example.com")
    assert not processor.is_valid_url("not_a_url")
    assert not processor.is_valid_url("ftp://example.com")  # unsupported protocol
    
    # Test domain extraction
    assert processor.get_domain("https://docs.python.org/3/") == "docs.python.org"
    assert processor.get_domain("http://sub.example.com/path") == "sub.example.com"

def test_rate_limiter():
    """Test rate limiter functionality."""
    limiter = RateLimiter(requests_per_second=2)
    
    start_time = time.time()
    
    # Make 3 requests
    for _ in range(3):
        limiter.wait()
    
    end_time = time.time()
    
    # Should take at least 1 second (2 requests allowed immediately, 1 delayed)
    assert end_time - start_time >= 1.0
    
    # Test with different rates
    fast_limiter = RateLimiter(requests_per_second=10)
    slow_limiter = RateLimiter(requests_per_second=0.5)
    
    assert fast_limiter.delay == 0.1  # 1/10 second
    assert slow_limiter.delay == 2.0  # 1/0.5 = 2 seconds

def test_retry_strategy():
    """Test retry strategy functionality."""
    strategy = RetryStrategy(max_retries=3, base_delay=1)
    
    # Test successful retry
    mock_func = MagicMock()
    mock_func.side_effect = [ValueError, ValueError, "success"]
    
    result = strategy.execute(mock_func)
    assert result == "success"
    assert mock_func.call_count == 3
    
    # Test max retries exceeded
    mock_func.reset_mock()
    mock_func.side_effect = ValueError
    
    with pytest.raises(ValueError):
        strategy.execute(mock_func)
    assert mock_func.call_count == 3
    
    # Test immediate success
    mock_func.reset_mock()
    mock_func.return_value = "quick success"
    
    result = strategy.execute(mock_func)
    assert result == "quick success"
    assert mock_func.call_count == 1

def test_timer():
    """Test timer functionality."""
    timer = Timer()
    
    # Test basic timing
    with timer:
        time.sleep(0.1)
    
    assert timer.elapsed >= 0.1
    assert timer.start_time is not None
    assert timer.end_time is not None
    
    # Test reset
    timer.reset()
    assert timer.elapsed == 0
    assert timer.start_time is None
    assert timer.end_time is None
    
    # Test nested timing
    with timer:
        with timer:  # Should work with nested contexts
            time.sleep(0.1)
    
    assert timer.elapsed >= 0.1

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
        assert logger == mock_logger
        assert mock_logger.setLevel.called
        assert mock_logger.addHandler.called
        
        # Test with different log level
        logger = setup_logging(log_level="DEBUG")
        mock_logger.setLevel.assert_called_with("DEBUG")
        
        # Test with file output
        with patch('logging.FileHandler') as mock_file_handler:
            logger = setup_logging(log_file="test.log")
            mock_file_handler.assert_called_once_with("test.log")
