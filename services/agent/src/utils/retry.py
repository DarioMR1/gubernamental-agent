"""Retry utilities for the governmental agent."""

import asyncio
import logging
import random
from typing import Any, Awaitable, Callable, List, Optional, Type, TypeVar, Union
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


async def retry_with_backoff(
    func: Callable[..., Awaitable[T]],
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    exceptions: Optional[Union[Type[Exception], tuple[Type[Exception], ...]]] = None,
    *args: Any,
    **kwargs: Any
) -> T:
    """Retry an async function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_attempts: Maximum number of attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Factor to multiply delay by after each attempt
        jitter: Whether to add random jitter to delay
        exceptions: Exception types to catch and retry on. If None, catches all exceptions
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Result of the function call
        
    Raises:
        The last exception encountered if all attempts fail
    """
    if exceptions is None:
        exceptions = Exception
    
    last_exception = None
    
    for attempt in range(max_attempts):
        try:
            logger.debug(f"Attempt {attempt + 1}/{max_attempts} for {func.__name__}")
            result = await func(*args, **kwargs)
            
            if attempt > 0:
                logger.info(f"Function {func.__name__} succeeded on attempt {attempt + 1}")
            
            return result
            
        except exceptions as e:
            last_exception = e
            
            if attempt == max_attempts - 1:
                # Last attempt, don't wait
                logger.error(f"Function {func.__name__} failed on final attempt {attempt + 1}: {e}")
                break
            
            # Calculate delay for next attempt
            delay = min(base_delay * (backoff_factor ** attempt), max_delay)
            
            if jitter:
                # Add random jitter (±25%)
                jitter_range = delay * 0.25
                delay += random.uniform(-jitter_range, jitter_range)
            
            logger.warning(f"Function {func.__name__} failed on attempt {attempt + 1}: {e}. Retrying in {delay:.2f}s")
            await asyncio.sleep(delay)
    
    # All attempts failed, raise the last exception
    if last_exception:
        raise last_exception
    else:
        raise RuntimeError(f"Function {func.__name__} failed after {max_attempts} attempts")


def retry_on_failure(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    exceptions: Optional[Union[Type[Exception], tuple[Type[Exception], ...]]] = None
) -> Callable:
    """Decorator to retry async functions with exponential backoff.
    
    Args:
        max_attempts: Maximum number of attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Factor to multiply delay by after each attempt
        jitter: Whether to add random jitter to delay
        exceptions: Exception types to catch and retry on. If None, catches all exceptions
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            return await retry_with_backoff(
                func,
                max_attempts=max_attempts,
                base_delay=base_delay,
                max_delay=max_delay,
                backoff_factor=backoff_factor,
                jitter=jitter,
                exceptions=exceptions,
                *args,
                **kwargs
            )
        return wrapper
    return decorator


class RetryableError(Exception):
    """Exception that indicates the operation should be retried."""
    pass


class NonRetryableError(Exception):
    """Exception that indicates the operation should not be retried."""
    pass


async def retry_on_condition(
    func: Callable[..., Awaitable[T]],
    condition: Callable[[T], bool],
    max_attempts: int = 3,
    base_delay: float = 1.0,
    backoff_factor: float = 2.0,
    *args: Any,
    **kwargs: Any
) -> T:
    """Retry a function until a condition is met.
    
    Args:
        func: Async function to retry
        condition: Function that takes the result and returns True if retry is needed
        max_attempts: Maximum number of attempts
        base_delay: Initial delay between retries in seconds
        backoff_factor: Factor to multiply delay by after each attempt
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Result of the function call that satisfies the condition
        
    Raises:
        RuntimeError: If condition is never met after max_attempts
    """
    for attempt in range(max_attempts):
        try:
            result = await func(*args, **kwargs)
            
            if not condition(result):
                logger.debug(f"Condition satisfied on attempt {attempt + 1}")
                return result
            
            if attempt == max_attempts - 1:
                logger.error(f"Condition not satisfied after {max_attempts} attempts")
                raise RuntimeError(f"Condition not satisfied after {max_attempts} attempts")
            
            delay = base_delay * (backoff_factor ** attempt)
            logger.debug(f"Condition not satisfied on attempt {attempt + 1}, retrying in {delay}s")
            await asyncio.sleep(delay)
            
        except Exception as e:
            logger.error(f"Function failed on attempt {attempt + 1}: {e}")
            if attempt == max_attempts - 1:
                raise
            
            delay = base_delay * (backoff_factor ** attempt)
            await asyncio.sleep(delay)
    
    raise RuntimeError(f"Function failed after {max_attempts} attempts")


class CircuitBreaker:
    """Circuit breaker pattern implementation for preventing cascading failures."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 3,
        timeout_seconds: float = 60.0
    ):
        """Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            success_threshold: Number of successes needed to close circuit
            timeout_seconds: Timeout before allowing retry when circuit is open
        """
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout_seconds = timeout_seconds
        
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
        self.state = "closed"  # closed, open, half-open
    
    def _should_attempt_call(self) -> bool:
        """Check if call should be attempted based on circuit state."""
        if self.state == "closed":
            return True
        elif self.state == "open":
            import time
            if time.time() - self.last_failure_time > self.timeout_seconds:
                self.state = "half-open"
                self.success_count = 0
                return True
            return False
        else:  # half-open
            return True
    
    def _record_success(self) -> None:
        """Record successful call."""
        if self.state == "half-open":
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = "closed"
                self.failure_count = 0
        elif self.state == "closed":
            self.failure_count = 0
    
    def _record_failure(self) -> None:
        """Record failed call."""
        import time
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
    
    async def call(self, func: Callable[..., Awaitable[T]], *args: Any, **kwargs: Any) -> T:
        """Execute function through circuit breaker.
        
        Args:
            func: Function to execute
            *args: Arguments to pass to function
            **kwargs: Keyword arguments to pass to function
            
        Returns:
            Result of function call
            
        Raises:
            RuntimeError: If circuit is open
            Any exception raised by the function
        """
        if not self._should_attempt_call():
            raise RuntimeError("Circuit breaker is open")
        
        try:
            result = await func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise