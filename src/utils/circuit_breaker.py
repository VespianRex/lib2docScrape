"""
Circuit breaker pattern implementation for handling service failures.
"""
import logging
import time
from enum import Enum
from typing import Callable, Optional

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation, requests pass through
    OPEN = "open"      # Failing state, requests are blocked
    HALF_OPEN = "half_open"  # Testing state, limited requests pass through

class CircuitBreaker:
    """
    Implementation of the circuit breaker pattern.
    
    The circuit breaker prevents cascading failures by stopping requests
    to a failing service after a threshold of failures is reached.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout: float = 60.0,
        half_open_max_calls: int = 1,
        on_state_change: Optional[Callable[[CircuitState, CircuitState], None]] = None
    ):
        """
        Initialize the circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening the circuit
            reset_timeout: Time in seconds before attempting to close the circuit
            half_open_max_calls: Maximum number of calls allowed in half-open state
            on_state_change: Optional callback for state changes
        """
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_max_calls = half_open_max_calls
        self.on_state_change = on_state_change
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0
        self._half_open_calls = 0
        
    @property
    def state(self) -> CircuitState:
        """Get the current state of the circuit breaker."""
        return self._state
        
    @property
    def failure_count(self) -> int:
        """Get the current failure count."""
        return self._failure_count
        
    def _change_state(self, new_state: CircuitState) -> None:
        """
        Change the circuit breaker state.
        
        Args:
            new_state: New state to transition to
        """
        if self._state != new_state:
            old_state = self._state
            self._state = new_state
            logger.info(f"Circuit breaker state changed from {old_state.value} to {new_state.value}")
            
            if self.on_state_change:
                try:
                    self.on_state_change(old_state, new_state)
                except Exception as e:
                    logger.error(f"Error in state change callback: {str(e)}")
                    
    def is_open(self) -> bool:
        """
        Check if the circuit is open (failing).
        
        Returns:
            True if the circuit is open
        """
        # Check if we should transition from open to half-open
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time >= self.reset_timeout:
                self._change_state(CircuitState.HALF_OPEN)
                self._half_open_calls = 0
                
        return self._state == CircuitState.OPEN
        
    def record_success(self) -> None:
        """Record a successful operation."""
        if self._state == CircuitState.HALF_OPEN:
            self._half_open_calls += 1
            
            # If we've had enough successful calls in half-open state,
            # transition back to closed
            if self._half_open_calls >= self.half_open_max_calls:
                self._change_state(CircuitState.CLOSED)
                self._failure_count = 0
                
        elif self._state == CircuitState.CLOSED:
            # Reset failure count on success in closed state
            self._failure_count = 0
            
    def record_failure(self) -> None:
        """Record a failed operation."""
        self._last_failure_time = time.time()
        
        if self._state == CircuitState.HALF_OPEN:
            # Any failure in half-open state opens the circuit again
            self._change_state(CircuitState.OPEN)
            
        elif self._state == CircuitState.CLOSED:
            self._failure_count += 1
            
            # If we've reached the failure threshold, open the circuit
            if self._failure_count >= self.failure_threshold:
                self._change_state(CircuitState.OPEN)
                
    async def execute_async(self, operation, *args, **kwargs):
        """
        Execute an async operation with circuit breaker protection.
        
        Args:
            operation: Async function to execute
            *args: Arguments to pass to the operation
            **kwargs: Keyword arguments to pass to the operation
            
        Returns:
            Result of the operation
            
        Raises:
            Exception: If the circuit is open or the operation fails
        """
        if self.is_open():
            raise RuntimeError("Circuit breaker is open")
            
        try:
            result = await operation(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise
            
    def execute(self, operation, *args, **kwargs):
        """
        Execute a synchronous operation with circuit breaker protection.
        
        Args:
            operation: Function to execute
            *args: Arguments to pass to the operation
            **kwargs: Keyword arguments to pass to the operation
            
        Returns:
            Result of the operation
            
        Raises:
            Exception: If the circuit is open or the operation fails
        """
        if self.is_open():
            raise RuntimeError("Circuit breaker is open")
            
        try:
            result = operation(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise
            
    def reset(self) -> None:
        """Reset the circuit breaker to closed state."""
        self._change_state(CircuitState.CLOSED)
        self._failure_count = 0
        self._last_failure_time = 0
        self._half_open_calls = 0
