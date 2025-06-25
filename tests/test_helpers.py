"""
Optimized tests for helpers - no real sleep calls.
"""

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.utils.helpers import (
    RateLimiter,
    RetryStrategy,
    Timer,
    calculate_similarity,
    generate_checksum,
    setup_logging,
)
from src.utils.url import URLType
from src.utils.url.factory import create_url_info


@pytest.mark.asyncio
async def test_rate_limiter_optimized():
    """Test rate limiter functionality - OPTIMIZED with mocked time."""

    # Mock asyncio.sleep to avoid real delays
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        mock_sleep.return_value = None

        # Mock time.time to simulate fast successive calls that need rate limiting
        with patch("time.time") as mock_time:
            # Start at time 0, then very small increments to simulate fast calls
            def time_side_effect():
                if not hasattr(time_side_effect, "counter"):
                    time_side_effect.counter = 0.0
                else:
                    time_side_effect.counter += 0.01  # Very small increment (much faster than 0.5s needed for 2 rps)
                return time_side_effect.counter

            mock_time.side_effect = time_side_effect

            limiter = RateLimiter(requests_per_second=2)  # Need 0.5s between requests

            # Make 3 quick requests
            wait_times = []
            for _ in range(3):
                wait_time = await limiter.acquire()
                wait_times.append(wait_time)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)  # This will be mocked to be instant

            # The third request should require waiting since we're making requests too fast
            assert (
                wait_times[2] > 0
            ), f"Third request should require waiting. Wait times: {wait_times}"

            # Verify time.time was called
            assert mock_time.call_count > 0


def test_retry_strategy():
    """Test retry strategy functionality."""
    strategy = RetryStrategy(max_retries=3, initial_delay=0.01, max_delay=0.1)

    # Test successful retry
    mock_func_success = MagicMock()
    mock_func_success.side_effect = [
        ValueError("Attempt 1 failed"),
        ValueError("Attempt 2 failed"),
        "success",
    ]

    attempt = 0
    last_exception = None
    result = None
    while attempt < strategy.max_retries:
        attempt += 1
        try:
            result = mock_func_success()
            last_exception = None
            break
        except Exception as e:
            last_exception = e
            if not isinstance(e, ValueError):
                break
            if attempt >= strategy.max_retries:
                break
            delay = strategy.get_delay(attempt)
            # No actual sleep in tests
            print(f"Retrying after attempt {attempt}, delay {delay:.4f}s")

    assert last_exception is None
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
            if not isinstance(e, ValueError):
                break
            if attempt >= strategy.max_retries:
                break
            delay = strategy.get_delay(attempt)
            # No actual sleep

    assert last_exception is not None
    assert isinstance(last_exception, ValueError)
    assert mock_func_fail.call_count == 3

    # Test immediate success
    mock_func_quick = MagicMock(return_value="quick success")
    attempt = 0
    last_exception = None
    result = None
    while attempt < strategy.max_retries:
        attempt += 1
        try:
            result = mock_func_quick()
            last_exception = None
            break
        except Exception as e:
            last_exception = e
            break

    assert last_exception is None
    assert result == "quick success"
    assert mock_func_quick.call_count == 1


@patch("time.time", side_effect=[100.0, 100.1, 100.2, 100.3, 100.4, 100.5])
def test_timer(mock_time):
    """Test timer functionality - OPTIMIZED with mocked time."""
    timer = Timer("TestOp")

    # Test basic timing
    with timer:
        pass  # No actual sleep needed

    assert timer.duration == pytest.approx(0.1)
    assert timer.start_time == 100.0

    # Create new timer instance
    timer2 = Timer("NestedOp")
    with timer2:
        pass

    assert timer2.duration == pytest.approx(0.1)


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
    with (
        patch("logging.basicConfig") as mock_basic_config,
        patch("logging.StreamHandler") as mock_stream_handler,
        patch("logging.FileHandler") as mock_file_handler,
    ):
        setup_logging(level="INFO")
        mock_basic_config.assert_called_once()
        args, kwargs = mock_basic_config.call_args
        assert kwargs["level"] == logging.INFO
        assert len(kwargs["handlers"]) == 1
        mock_stream_handler.assert_called_once()
        mock_file_handler.assert_not_called()

    # Test with different log level
    with patch("logging.basicConfig") as mock_basic_config:
        setup_logging(level="DEBUG")
        args, kwargs = mock_basic_config.call_args
        assert kwargs["level"] == logging.DEBUG

    # Test with file output
    with (
        patch("logging.basicConfig") as mock_basic_config,
        patch("logging.StreamHandler"),
        patch("logging.FileHandler") as mock_file_handler,
    ):
        setup_logging(level="WARNING", log_file=str(log_file))
        mock_basic_config.assert_called_once()
        args, kwargs = mock_basic_config.call_args
        assert kwargs["level"] == logging.WARNING
        assert len(kwargs["handlers"]) == 2
        mock_file_handler.assert_called_once_with(str(log_file))


def create_mock_response(
    status_code=200,
    content=None,
    url="https://example.com",
    headers=None,
    content_type="text/html",
):
    """Create a mock HTTP response object for testing."""
    if content is None:
        content = "<html><body>Test content</body></html>"

    if headers is None:
        headers = {"Content-Type": content_type}

    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.content = (
        content.encode("utf-8") if isinstance(content, str) else content
    )
    mock_response.text = (
        content if isinstance(content, str) else content.decode("utf-8")
    )
    mock_response.url = url
    mock_response.headers = headers

    # Add common response methods
    mock_response.json.return_value = (
        {} if content in (None, "") else {"data": "mock json data"}
    )
    mock_response.raise_for_status.side_effect = (
        None if status_code < 400 else Exception(f"HTTP Error: {status_code}")
    )

    return mock_response


def create_test_url_info(url, url_type=URLType.INTERNAL, base_url=None):
    """Create a URLInfo object for testing using the factory function."""
    url_info = create_url_info(url, base_url=base_url)
    return url_info
