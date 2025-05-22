"""
Performance optimization utilities for the lib2docScrape system.
"""
import asyncio
import functools
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar, Union, cast

from pydantic import BaseModel, Field

from .error_handler import ErrorCategory, ErrorLevel, handle_error

logger = logging.getLogger(__name__)

T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])

class CacheStrategy(Enum):
    """Cache strategies for memoization."""
    LRU = "lru"
    FIFO = "fifo"
    LIFO = "lifo"
    TTL = "ttl"

class CacheConfig(BaseModel):
    """Configuration for caching."""
    strategy: CacheStrategy = CacheStrategy.LRU
    max_size: int = 128
    ttl: float = 300.0  # Time-to-live in seconds
    ignore_args: List[str] = Field(default_factory=list)
    ignore_kwargs: List[str] = Field(default_factory=list)

class RateLimitConfig(BaseModel):
    """Configuration for rate limiting."""
    max_calls: int = 10
    period: float = 1.0  # Period in seconds
    burst: int = 1  # Number of calls allowed to burst

class ThrottleConfig(BaseModel):
    """Configuration for throttling."""
    max_concurrency: int = 10
    timeout: float = 30.0  # Timeout in seconds

class PerformanceMetrics(BaseModel):
    """Performance metrics for a function."""
    name: str
    calls: int = 0
    errors: int = 0
    total_time: float = 0.0
    min_time: Optional[float] = None
    max_time: Optional[float] = None
    avg_time: float = 0.0
    last_call_time: Optional[float] = None
    cache_hits: int = 0
    cache_misses: int = 0

# Global metrics registry
_metrics_registry: Dict[str, PerformanceMetrics] = {}

def get_metrics(name: Optional[str] = None) -> Union[Dict[str, PerformanceMetrics], Optional[PerformanceMetrics]]:
    """
    Get performance metrics.
    
    Args:
        name: Optional name of the function to get metrics for
        
    Returns:
        Dictionary of metrics or a single metric
    """
    if name:
        return _metrics_registry.get(name)
    return _metrics_registry.copy()

def reset_metrics(name: Optional[str] = None) -> None:
    """
    Reset performance metrics.
    
    Args:
        name: Optional name of the function to reset metrics for
    """
    if name:
        if name in _metrics_registry:
            _metrics_registry[name] = PerformanceMetrics(name=name)
    else:
        _metrics_registry.clear()

def _update_metrics(name: str, elapsed: float, error: bool = False, cache_hit: bool = False) -> None:
    """
    Update performance metrics for a function.
    
    Args:
        name: Name of the function
        elapsed: Elapsed time in seconds
        error: Whether an error occurred
        cache_hit: Whether a cache hit occurred
    """
    if name not in _metrics_registry:
        _metrics_registry[name] = PerformanceMetrics(name=name)
        
    metrics = _metrics_registry[name]
    metrics.calls += 1
    metrics.total_time += elapsed
    
    if error:
        metrics.errors += 1
        
    if cache_hit:
        metrics.cache_hits += 1
    else:
        metrics.cache_misses += 1
        
    if metrics.min_time is None or elapsed < metrics.min_time:
        metrics.min_time = elapsed
        
    if metrics.max_time is None or elapsed > metrics.max_time:
        metrics.max_time = elapsed
        
    metrics.avg_time = metrics.total_time / metrics.calls
    metrics.last_call_time = time.time()

def memoize(func: Optional[F] = None, *, config: Optional[CacheConfig] = None) -> Callable[[F], F]:
    """
    Memoize a function to cache its results.
    
    Args:
        func: Function to memoize
        config: Optional cache configuration
        
    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        cache_config = config or CacheConfig()
        
        # Create cache based on strategy
        if cache_config.strategy == CacheStrategy.LRU:
            from functools import lru_cache
            cached_func = lru_cache(maxsize=cache_config.max_size)(func)
        elif cache_config.strategy == CacheStrategy.TTL:
            try:
                from cachetools import TTLCache
                cache = TTLCache(maxsize=cache_config.max_size, ttl=cache_config.ttl)
            except ImportError:
                logger.warning("cachetools not available, falling back to LRU cache")
                from functools import lru_cache
                cached_func = lru_cache(maxsize=cache_config.max_size)(func)
                
                @functools.wraps(func)
                def wrapper(*args: Any, **kwargs: Any) -> Any:
                    start_time = time.time()
                    try:
                        result = cached_func(*args, **kwargs)
                        elapsed = time.time() - start_time
                        _update_metrics(func.__name__, elapsed, cache_hit=True)
                        return result
                    except Exception as e:
                        elapsed = time.time() - start_time
                        _update_metrics(func.__name__, elapsed, error=True)
                        raise
                        
                return cast(F, wrapper)
                
            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                start_time = time.time()
                
                # Create cache key
                key_args = args
                key_kwargs = {k: v for k, v in kwargs.items() if k not in cache_config.ignore_kwargs}
                
                try:
                    cache_key = hash((key_args, frozenset(key_kwargs.items())))
                    
                    # Check cache
                    if cache_key in cache:
                        result = cache[cache_key]
                        elapsed = time.time() - start_time
                        _update_metrics(func.__name__, elapsed, cache_hit=True)
                        return result
                        
                    # Call function
                    result = func(*args, **kwargs)
                    
                    # Update cache
                    cache[cache_key] = result
                    
                    elapsed = time.time() - start_time
                    _update_metrics(func.__name__, elapsed, cache_hit=False)
                    return result
                except Exception as e:
                    elapsed = time.time() - start_time
                    _update_metrics(func.__name__, elapsed, error=True)
                    raise
                    
            return cast(F, wrapper)
        else:
            # Default to LRU cache
            from functools import lru_cache
            cached_func = lru_cache(maxsize=cache_config.max_size)(func)
            
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            
            # Track cache hits by checking if the result is already computed
            cache_info = getattr(cached_func, "cache_info", None)
            hits_before = cache_info().hits if cache_info else 0
            
            try:
                result = cached_func(*args, **kwargs)
                
                # Check if it was a cache hit
                hits_after = cache_info().hits if cache_info else 0
                cache_hit = hits_after > hits_before
                
                elapsed = time.time() - start_time
                _update_metrics(func.__name__, elapsed, cache_hit=cache_hit)
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                _update_metrics(func.__name__, elapsed, error=True)
                raise
                
        # Add cache_info method if available
        if hasattr(cached_func, "cache_info"):
            wrapper.cache_info = cached_func.cache_info  # type: ignore
            
        # Add cache_clear method if available
        if hasattr(cached_func, "cache_clear"):
            wrapper.cache_clear = cached_func.cache_clear  # type: ignore
            
        return cast(F, wrapper)
        
    if func is None:
        return decorator
    return decorator(func)

def rate_limit(func: Optional[F] = None, *, config: Optional[RateLimitConfig] = None) -> Callable[[F], F]:
    """
    Rate limit a function.
    
    Args:
        func: Function to rate limit
        config: Optional rate limit configuration
        
    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        rate_config = config or RateLimitConfig()
        
        # Use token bucket algorithm for rate limiting
        tokens = rate_config.max_calls
        last_refill = time.time()
        lock = asyncio.Lock()
        
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal tokens, last_refill
            
            async with lock:
                # Refill tokens
                now = time.time()
                elapsed = now - last_refill
                new_tokens = int(elapsed * rate_config.max_calls / rate_config.period)
                
                if new_tokens > 0:
                    tokens = min(tokens + new_tokens, rate_config.max_calls)
                    last_refill = now
                    
                # Check if we have tokens
                if tokens < 1:
                    # Calculate wait time
                    wait_time = rate_config.period / rate_config.max_calls
                    logger.debug(f"Rate limit exceeded for {func.__name__}, waiting {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)
                    
                    # Refill tokens after waiting
                    now = time.time()
                    elapsed = now - last_refill
                    new_tokens = int(elapsed * rate_config.max_calls / rate_config.period)
                    
                    if new_tokens > 0:
                        tokens = min(tokens + new_tokens, rate_config.max_calls)
                        last_refill = now
                        
                # Use a token
                tokens -= 1
                
            # Call function
            start_time = time.time()
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                    
                elapsed = time.time() - start_time
                _update_metrics(func.__name__, elapsed)
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                _update_metrics(func.__name__, elapsed, error=True)
                raise
                
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal tokens, last_refill
            
            # Refill tokens
            now = time.time()
            elapsed = now - last_refill
            new_tokens = int(elapsed * rate_config.max_calls / rate_config.period)
            
            if new_tokens > 0:
                tokens = min(tokens + new_tokens, rate_config.max_calls)
                last_refill = now
                
            # Check if we have tokens
            if tokens < 1:
                # Calculate wait time
                wait_time = rate_config.period / rate_config.max_calls
                logger.debug(f"Rate limit exceeded for {func.__name__}, waiting {wait_time:.2f}s")
                time.sleep(wait_time)
                
                # Refill tokens after waiting
                now = time.time()
                elapsed = now - last_refill
                new_tokens = int(elapsed * rate_config.max_calls / rate_config.period)
                
                if new_tokens > 0:
                    tokens = min(tokens + new_tokens, rate_config.max_calls)
                    last_refill = now
                    
            # Use a token
            tokens -= 1
            
            # Call function
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                _update_metrics(func.__name__, elapsed)
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                _update_metrics(func.__name__, elapsed, error=True)
                raise
                
        # Return appropriate wrapper based on whether the function is async
        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        return cast(F, sync_wrapper)
        
    if func is None:
        return decorator
    return decorator(func)

def throttle(func: Optional[F] = None, *, config: Optional[ThrottleConfig] = None) -> Callable[[F], F]:
    """
    Throttle a function to limit concurrency.
    
    Args:
        func: Function to throttle
        config: Optional throttle configuration
        
    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        throttle_config = config or ThrottleConfig()
        semaphore = asyncio.Semaphore(throttle_config.max_concurrency)
        
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            async with semaphore:
                start_time = time.time()
                try:
                    if asyncio.iscoroutinefunction(func):
                        result = await asyncio.wait_for(
                            func(*args, **kwargs),
                            timeout=throttle_config.timeout
                        )
                    else:
                        result = await asyncio.to_thread(func, *args, **kwargs)
                        
                    elapsed = time.time() - start_time
                    _update_metrics(func.__name__, elapsed)
                    return result
                except asyncio.TimeoutError:
                    elapsed = time.time() - start_time
                    _update_metrics(func.__name__, elapsed, error=True)
                    raise TimeoutError(f"Function {func.__name__} timed out after {throttle_config.timeout}s")
                except Exception as e:
                    elapsed = time.time() - start_time
                    _update_metrics(func.__name__, elapsed, error=True)
                    raise
                    
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # For sync functions, use a thread pool
            with ThreadPoolExecutor(max_workers=throttle_config.max_concurrency) as executor:
                start_time = time.time()
                try:
                    future = executor.submit(func, *args, **kwargs)
                    result = future.result(timeout=throttle_config.timeout)
                    
                    elapsed = time.time() - start_time
                    _update_metrics(func.__name__, elapsed)
                    return result
                except TimeoutError:
                    elapsed = time.time() - start_time
                    _update_metrics(func.__name__, elapsed, error=True)
                    raise TimeoutError(f"Function {func.__name__} timed out after {throttle_config.timeout}s")
                except Exception as e:
                    elapsed = time.time() - start_time
                    _update_metrics(func.__name__, elapsed, error=True)
                    raise
                    
        # Return appropriate wrapper based on whether the function is async
        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        return cast(F, sync_wrapper)
        
    if func is None:
        return decorator
    return decorator(func)
