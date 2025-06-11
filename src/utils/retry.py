"""
Retry utilities for handling transient failures.
"""

import logging
import random
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


class RetryStrategy(ABC):
    """Abstract base class for retry strategies."""

    @abstractmethod
    def get_delay(self, attempt: int) -> float:
        """
        Get the delay in seconds for a retry attempt.

        Args:
            attempt: The current attempt number (0-based)

        Returns:
            Delay in seconds
        """
        pass

    def should_retry(self, attempt: int, max_retries: int) -> bool:
        """
        Determine if another retry should be attempted.

        Args:
            attempt: The current attempt number (0-based)
            max_retries: Maximum number of retries

        Returns:
            True if another retry should be attempted
        """
        return attempt < max_retries


class ConstantDelay(RetryStrategy):
    """Retry strategy with constant delay between attempts."""

    def __init__(self, delay: float = 1.0):
        """
        Initialize with constant delay.

        Args:
            delay: Delay in seconds between attempts
        """
        self.delay = delay

    def get_delay(self, attempt: int) -> float:
        """Get constant delay."""
        return self.delay


class ExponentialBackoff(RetryStrategy):
    """Retry strategy with exponential backoff."""

    def __init__(
        self, base_delay: float = 1.0, max_delay: float = 60.0, jitter: bool = True
    ):
        """
        Initialize with exponential backoff parameters.

        Args:
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
            jitter: Whether to add jitter to the delay
        """
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """Get exponential backoff delay with optional jitter."""
        delay = min(self.base_delay * (2**attempt), self.max_delay)

        if self.jitter:
            # Add jitter of up to 20%
            jitter_amount = delay * 0.2
            delay += random.uniform(-jitter_amount, jitter_amount)

        return max(0, delay)  # Ensure delay is non-negative


class LinearBackoff(RetryStrategy):
    """Retry strategy with linear backoff."""

    def __init__(
        self, base_delay: float = 1.0, increment: float = 1.0, max_delay: float = 60.0
    ):
        """
        Initialize with linear backoff parameters.

        Args:
            base_delay: Base delay in seconds
            increment: Increment in seconds per attempt
            max_delay: Maximum delay in seconds
        """
        self.base_delay = base_delay
        self.increment = increment
        self.max_delay = max_delay

    def get_delay(self, attempt: int) -> float:
        """Get linear backoff delay."""
        return min(self.base_delay + (attempt * self.increment), self.max_delay)


class RetryWithStrategy:
    """Utility class for retrying operations with a specific strategy."""

    def __init__(
        self,
        strategy: RetryStrategy,
        max_retries: int = 3,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize with retry strategy.

        Args:
            strategy: Retry strategy to use
            max_retries: Maximum number of retries
            logger: Optional logger for retry attempts
        """
        self.strategy = strategy
        self.max_retries = max_retries
        self.logger = logger or logging.getLogger(__name__)

    async def retry_async(self, operation, *args, **kwargs):
        """
        Retry an async operation with the configured strategy.

        Args:
            operation: Async function to retry
            *args: Arguments to pass to the operation
            **kwargs: Keyword arguments to pass to the operation

        Returns:
            Result of the operation

        Raises:
            Exception: The last exception raised by the operation
        """
        import asyncio

        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                return await operation(*args, **kwargs)
            except Exception as e:
                last_exception = e
                self.logger.warning(
                    f"Attempt {attempt + 1}/{self.max_retries + 1} failed: {str(e)}"
                )

                if self.strategy.should_retry(attempt, self.max_retries):
                    delay = self.strategy.get_delay(attempt)
                    self.logger.debug(f"Retrying in {delay:.2f} seconds")
                    await asyncio.sleep(delay)
                else:
                    break

        raise last_exception

    def retry(self, operation, *args, **kwargs):
        """
        Retry a synchronous operation with the configured strategy.

        Args:
            operation: Function to retry
            *args: Arguments to pass to the operation
            **kwargs: Keyword arguments to pass to the operation

        Returns:
            Result of the operation

        Raises:
            Exception: The last exception raised by the operation
        """
        import time

        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                last_exception = e
                self.logger.warning(
                    f"Attempt {attempt + 1}/{self.max_retries + 1} failed: {str(e)}"
                )

                if self.strategy.should_retry(attempt, self.max_retries):
                    delay = self.strategy.get_delay(attempt)
                    self.logger.debug(f"Retrying in {delay:.2f} seconds")
                    time.sleep(delay)
                else:
                    break

        raise last_exception
