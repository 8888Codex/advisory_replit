"""
Circuit Breaker Pattern for External API Calls
Prevents cascading failures by stopping requests to failing services.
"""
from datetime import datetime, timedelta
from typing import Callable, Optional, Any
from enum import Enum
from logger import logger
import asyncio

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"  # Failing, reject requests
    HALF_OPEN = "HALF_OPEN"  # Testing if service recovered


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open and request is rejected"""
    pass


class CircuitBreaker:
    """
    Circuit breaker for external API calls.
    
    States:
    - CLOSED: Normal operation, all requests pass through
    - OPEN: Service is failing, reject all requests
    - HALF_OPEN: Testing if service recovered, allow 1 request
    
    Transitions:
    - CLOSED -> OPEN: After failure_threshold consecutive failures
    - OPEN -> HALF_OPEN: After timeout_seconds elapsed
    - HALF_OPEN -> CLOSED: If test request succeeds
    - HALF_OPEN -> OPEN: If test request fails
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        timeout_seconds: int = 300,
        fallback: Optional[Callable] = None,
    ):
        """
        Args:
            name: Name of the circuit (for logging)
            failure_threshold: Number of failures before opening circuit
            timeout_seconds: Seconds to wait before testing recovery
            fallback: Optional fallback function to call when circuit is open
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout = timedelta(seconds=timeout_seconds)
        self.fallback = fallback
        
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.successes = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_state_change: datetime = datetime.now()
    
    def _transition_to(self, new_state: CircuitState):
        """Transition to a new state with logging"""
        if self.state != new_state:
            old_state = self.state
            self.state = new_state
            self.last_state_change = datetime.now()
            
            logger.warning(
                f"Circuit breaker state changed: {self.name}",
                old_state=old_state.value,
                new_state=new_state.value,
                failures=self.failures,
                successes=self.successes,
            )
    
    def record_success(self):
        """Record a successful call"""
        self.successes += 1
        self.failures = 0  # Reset failure count
        
        if self.state == CircuitState.HALF_OPEN:
            # Test passed, close the circuit
            self._transition_to(CircuitState.CLOSED)
            logger.info(f"Circuit breaker recovered: {self.name}")
    
    def record_failure(self):
        """Record a failed call"""
        self.failures += 1
        self.last_failure_time = datetime.now()
        
        logger.warning(
            f"Circuit breaker recorded failure: {self.name}",
            failures=self.failures,
            threshold=self.failure_threshold,
            state=self.state.value,
        )
        
        if self.state == CircuitState.HALF_OPEN:
            # Test failed, reopen the circuit
            self._transition_to(CircuitState.OPEN)
        
        elif self.failures >= self.failure_threshold:
            # Too many failures, open the circuit
            if self.state != CircuitState.OPEN:
                self._transition_to(CircuitState.OPEN)
    
    def can_attempt(self) -> bool:
        """Check if we can attempt a call"""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.HALF_OPEN:
            return True
        
        if self.state == CircuitState.OPEN:
            # Check if timeout has passed
            if self.last_failure_time:
                time_since_failure = datetime.now() - self.last_failure_time
                if time_since_failure >= self.timeout:
                    # Transition to half-open for testing
                    self._transition_to(CircuitState.HALF_OPEN)
                    logger.info(f"Circuit breaker testing recovery: {self.name}")
                    return True
            return False
        
        return False
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function through the circuit breaker.
        
        Args:
            func: Async function to call
            *args, **kwargs: Arguments to pass to the function
        
        Returns:
            Result from the function
        
        Raises:
            CircuitBreakerOpenError: If circuit is open and no fallback provided
        """
        if not self.can_attempt():
            logger.warning(
                f"Circuit breaker is open, rejecting call: {self.name}",
                state=self.state.value,
                last_failure=self.last_failure_time.isoformat() if self.last_failure_time else None,
            )
            
            # Try fallback if available
            if self.fallback:
                logger.info(f"Using fallback for {self.name}")
                try:
                    if asyncio.iscoroutinefunction(self.fallback):
                        return await self.fallback(*args, **kwargs)
                    else:
                        return self.fallback(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Fallback failed for {self.name}", error=str(e))
                    raise
            
            raise CircuitBreakerOpenError(
                f"Service {self.name} is temporarily unavailable. "
                f"Please try again in a few minutes."
            )
        
        # Attempt the call
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            self.record_success()
            return result
        
        except Exception as e:
            self.record_failure()
            raise
    
    def get_status(self) -> dict:
        """Get current circuit breaker status"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failures": self.failures,
            "successes": self.successes,
            "threshold": self.failure_threshold,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_state_change": self.last_state_change.isoformat(),
        }


# Global circuit breakers for external APIs
perplexity_circuit = CircuitBreaker(
    name="Perplexity API",
    failure_threshold=5,
    timeout_seconds=300,  # 5 minutes
)

youtube_circuit = CircuitBreaker(
    name="YouTube API",
    failure_threshold=5,
    timeout_seconds=300,
)

unsplash_circuit = CircuitBreaker(
    name="Unsplash API",
    failure_threshold=5,
    timeout_seconds=300,
)


__all__ = [
    "CircuitBreaker",
    "CircuitBreakerOpenError",
    "CircuitState",
    "perplexity_circuit",
    "youtube_circuit",
    "unsplash_circuit",
]

