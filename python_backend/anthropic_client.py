"""
Resilient Anthropic API Client
Provides retry logic, circuit breaker, timeout handling, and fallback models.
"""
import os
import asyncio
from typing import Optional, Any, Dict
from datetime import datetime, timedelta
from anthropic import AsyncAnthropic, APIError, RateLimitError, APITimeoutError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
from logger import logger
from env_validator import get_config_int, get_config_float

class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass

class CircuitBreaker:
    """
    Simple circuit breaker for API calls.
    States: CLOSED (normal), OPEN (failing), HALF_OPEN (testing)
    """
    
    def __init__(self, failure_threshold: int = 5, timeout_seconds: int = 300):
        self.failure_threshold = failure_threshold
        self.timeout = timedelta(seconds=timeout_seconds)
        self.failures = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def record_success(self):
        """Record a successful call"""
        self.failures = 0
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            logger.info("Circuit breaker closed - API recovered")
    
    def record_failure(self):
        """Record a failed call"""
        self.failures += 1
        self.last_failure_time = datetime.now()
        
        if self.failures >= self.failure_threshold:
            if self.state != "OPEN":
                self.state = "OPEN"
                logger.error(
                    "Circuit breaker opened - API failing",
                    failures=self.failures,
                    threshold=self.failure_threshold,
                )
    
    def can_attempt(self) -> bool:
        """Check if we can attempt a call"""
        if self.state == "CLOSED":
            return True
        
        if self.state == "OPEN":
            # Check if timeout has passed
            if self.last_failure_time:
                time_since_failure = datetime.now() - self.last_failure_time
                if time_since_failure > self.timeout:
                    self.state = "HALF_OPEN"
                    logger.info("Circuit breaker half-open - testing API")
                    return True
            return False
        
        if self.state == "HALF_OPEN":
            return True
        
        return False


class ResilientAnthropicClient:
    """
    Wrapper around AsyncAnthropic with resilience features:
    - Automatic retry with exponential backoff
    - Circuit breaker to prevent cascading failures
    - Configurable timeouts
    - Fallback to cheaper Haiku model
    - Structured logging
    """
    
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        
        self.client = AsyncAnthropic(api_key=api_key)
        
        # Get configuration from environment
        self.timeout = get_config_int("ANTHROPIC_TIMEOUT", 60)
        self.max_retries = get_config_int("ANTHROPIC_MAX_RETRIES", 3)
        self.retry_delay = get_config_float("ANTHROPIC_RETRY_DELAY", 1.0)
        
        # Circuit breaker configuration
        circuit_threshold = get_config_int("CIRCUIT_BREAKER_THRESHOLD", 5)
        circuit_timeout = get_config_int("CIRCUIT_BREAKER_TIMEOUT", 300)
        self.circuit_breaker = CircuitBreaker(circuit_threshold, circuit_timeout)
        
        # Model fallback
        self.primary_model = "claude-sonnet-4-20250514"
        self.fallback_model = "claude-3-5-haiku-20241022"
        
        logger.info(
            "Anthropic client initialized",
            timeout=self.timeout,
            max_retries=self.max_retries,
            primary_model=self.primary_model,
        )
    
    async def create_message(
        self,
        messages: list,
        model: Optional[str] = None,
        system: Optional[str] = None,
        max_tokens: int = 8000,
        temperature: float = 1.0,
        **kwargs
    ) -> Any:
        """
        Create a message with retry logic and circuit breaker.
        
        Args:
            messages: List of message dictionaries
            model: Model to use (defaults to primary_model)
            system: System prompt
            max_tokens: Maximum tokens in response
            temperature: Temperature for randomness
            **kwargs: Additional arguments for Claude API
        
        Returns:
            Message response from Claude
        
        Raises:
            CircuitBreakerOpenError: If circuit breaker is open
            APIError: If all retries fail
        """
        # Check circuit breaker
        if not self.circuit_breaker.can_attempt():
            raise CircuitBreakerOpenError(
                "Circuit breaker is open. API is experiencing issues. "
                "Please try again in a few minutes."
            )
        
        model = model or self.primary_model
        attempt = 0
        last_error = None
        
        while attempt < self.max_retries:
            attempt += 1
            
            try:
                logger.debug(
                    "Calling Anthropic API",
                    attempt=attempt,
                    model=model,
                    max_tokens=max_tokens,
                )
                
                # Make API call with timeout
                response = await asyncio.wait_for(
                    self.client.messages.create(
                        model=model,
                        messages=messages,
                        system=system,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        **kwargs
                    ),
                    timeout=self.timeout
                )
                
                # Success - record and return
                self.circuit_breaker.record_success()
                logger.debug("Anthropic API call successful", attempt=attempt)
                return response
            
            except APITimeoutError as e:
                last_error = e
                logger.warning(
                    "Anthropic API timeout",
                    attempt=attempt,
                    max_retries=self.max_retries,
                    timeout=self.timeout,
                )
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** (attempt - 1))
                    await asyncio.sleep(delay)
            
            except RateLimitError as e:
                last_error = e
                logger.warning(
                    "Anthropic API rate limit",
                    attempt=attempt,
                    max_retries=self.max_retries,
                )
                # Rate limit - wait longer before retry
                if attempt < self.max_retries:
                    delay = self.retry_delay * (4 ** (attempt - 1))
                    await asyncio.sleep(delay)
            
            except APIError as e:
                last_error = e
                logger.error(
                    "Anthropic API error",
                    attempt=attempt,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                
                # For server errors, retry
                if hasattr(e, 'status_code') and e.status_code >= 500:
                    if attempt < self.max_retries:
                        delay = self.retry_delay * (2 ** (attempt - 1))
                        await asyncio.sleep(delay)
                    continue
                
                # For client errors (4xx), don't retry
                self.circuit_breaker.record_failure()
                raise
            
            except asyncio.TimeoutError as e:
                last_error = e
                logger.warning(
                    "Anthropic API call timeout (asyncio)",
                    attempt=attempt,
                    timeout=self.timeout,
                )
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** (attempt - 1))
                    await asyncio.sleep(delay)
            
            except Exception as e:
                last_error = e
                logger.error(
                    "Unexpected error calling Anthropic API",
                    error=str(e),
                    error_type=type(e).__name__,
                )
                self.circuit_breaker.record_failure()
                raise
        
        # All retries failed
        self.circuit_breaker.record_failure()
        
        # Try fallback to Haiku if primary model failed
        if model != self.fallback_model:
            logger.warning(
                "All retries failed, attempting fallback to Haiku",
                primary_model=model,
                fallback_model=self.fallback_model,
            )
            try:
                return await self.create_message(
                    messages=messages,
                    model=self.fallback_model,
                    system=system,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )
            except Exception as e:
                logger.error("Fallback to Haiku also failed", error=str(e))
        
        # Final failure
        error_msg = f"Failed to get response from Anthropic API after {self.max_retries} attempts"
        if last_error:
            error_msg += f": {str(last_error)}"
        
        logger.error(error_msg)
        raise APIError(error_msg)
    
    async def create_message_stream(
        self,
        messages: list,
        model: Optional[str] = None,
        system: Optional[str] = None,
        max_tokens: int = 8000,
        temperature: float = 1.0,
        **kwargs
    ):
        """
        Create a streaming message response.
        Note: Streaming doesn't support retry as elegantly.
        """
        if not self.circuit_breaker.can_attempt():
            raise CircuitBreakerOpenError(
                "Circuit breaker is open. API is experiencing issues."
            )
        
        model = model or self.primary_model
        
        try:
            logger.debug("Starting Anthropic streaming call", model=model)
            
            async with self.client.messages.stream(
                model=model,
                messages=messages,
                system=system,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            ) as stream:
                self.circuit_breaker.record_success()
                async for chunk in stream:
                    yield chunk
        
        except Exception as e:
            logger.error("Streaming error", error=str(e))
            self.circuit_breaker.record_failure()
            raise


# Global singleton instance
_anthropic_client: Optional[ResilientAnthropicClient] = None

def get_anthropic_client() -> ResilientAnthropicClient:
    """Get the global resilient Anthropic client instance"""
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = ResilientAnthropicClient()
    return _anthropic_client


__all__ = [
    "ResilientAnthropicClient",
    "get_anthropic_client",
    "CircuitBreakerOpenError",
]

