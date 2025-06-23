"""Rate limiting module using Redis."""

import asyncio
import logging
import time
from typing import Optional

from fastapi import HTTPException, Request, status
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter using Redis for distributed rate limiting."""

    def __init__(self, redis_client: Redis):
        """
        Initialize rate limiter.

        Args:
            redis_client: Redis client instance
        """
        self.redis = redis_client

    async def is_rate_limited(
        self, key: str, max_requests: int = 100, window_seconds: int = 60
    ) -> bool:
        """
        Check if a request should be rate limited.

        Args:
            key: Unique identifier for the rate limit (e.g., user ID, IP)
            max_requests: Maximum number of requests allowed in the window
            window_seconds: Time window in seconds

        Returns:
            True if rate limited, False otherwise
        """
        try:
            current_time = int(time.time())
            window_start = current_time - window_seconds

            # Use Redis sorted set to track requests with timestamps
            pipe = self.redis.pipeline()

            # Remove old entries outside the window
            pipe.zremrangebyscore(key, 0, window_start)

            # Count current requests in window
            pipe.zcard(key)

            # Add current request
            pipe.zadd(key, {str(current_time): current_time})

            # Set expiration on the key
            pipe.expire(key, window_seconds)

            results = await pipe.execute()
            current_requests = results[1]  # zcard result

            if current_requests >= max_requests:
                logger.warning(f"Rate limit exceeded for key: {key}")
                return True

            return False

        except Exception as e:
            logger.warning(f"Error checking rate limit: {e}")
            # On Redis error, allow the request (fail open)
            return False

    async def get_remaining_requests(
        self, key: str, max_requests: int = 100, window_seconds: int = 60
    ) -> int:
        """
        Get remaining requests for a key.

        Args:
            key: Unique identifier for the rate limit
            max_requests: Maximum number of requests allowed
            window_seconds: Time window in seconds

        Returns:
            Number of remaining requests
        """
        try:
            current_time = int(time.time())
            window_start = current_time - window_seconds

            # Remove old entries and count current ones
            await self.redis.zremrangebyscore(key, 0, window_start)
            current_requests = await self.redis.zcard(key)

            return max(0, max_requests - current_requests)

        except Exception as e:
            logger.warning(f"Error getting remaining requests: {e}")
            return max_requests  # Return max on error


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> Optional[RateLimiter]:
    """Get the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        logger.warning("Rate limiter not initialized. Call init_rate_limiter() first.")
        return None
    return _rate_limiter


async def init_rate_limiter(redis_url: str = "redis://localhost:6379/0"):
    """Initialize the global rate limiter."""
    global _rate_limiter
    try:
        redis_client = Redis.from_url(redis_url)
        # Test the connection with timeout
        await asyncio.wait_for(redis_client.ping(), timeout=2.0)
        _rate_limiter = RateLimiter(redis_client)
        logger.info("Rate limiter initialized successfully")
    except asyncio.TimeoutError:
        logger.warning("Redis connection timeout, rate limiter not initialized")
        _rate_limiter = None
    except Exception as e:
        logger.warning(f"Failed to initialize rate limiter: {e}")
        # Don't raise the exception, just log it
        # This allows the app to continue running even if Redis is not available
        _rate_limiter = None


async def rate_limit_middleware(
    request: Request, 
    max_requests: int = None, 
    window_seconds: int = None
):
    """
    Rate limiting middleware for FastAPI.

    Args:
        request: FastAPI request object
        max_requests: Maximum requests per window (uses settings if not provided)
        window_seconds: Time window in seconds (uses settings if not provided)

    Raises:
        HTTPException: If rate limit exceeded
    """
    from app.core.config import settings
    
    # Use settings defaults if not provided
    if max_requests is None:
        max_requests = settings.RATE_LIMIT_REQUESTS
    if window_seconds is None:
        window_seconds = settings.RATE_LIMIT_WINDOW
    
    try:
        rate_limiter = get_rate_limiter()

        # If rate limiter is not initialized, allow request to pass through
        if rate_limiter is None:
            logger.debug(
                "Rate limiter not initialized, allowing request to pass through"
            )
            return

        # Use client IP as rate limit key (in production, use user ID if authenticated)
        # Handle cases where request.client is None (like in test environments)
        client_ip = request.client.host if request.client else "test-client"
        rate_limit_key = f"rate_limit:{client_ip}"

        # Check if rate limited with timeout
        try:
            is_limited = await asyncio.wait_for(
                rate_limiter.is_rate_limited(
                    rate_limit_key, max_requests, window_seconds
                ),
                timeout=1.0,
            )

            if is_limited:
                remaining = await asyncio.wait_for(
                    rate_limiter.get_remaining_requests(
                        rate_limit_key, max_requests, window_seconds
                    ),
                    timeout=1.0,
                )

                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Rate limit exceeded",
                        "retry_after": window_seconds,
                        "remaining_requests": remaining,
                    },
                )
        except asyncio.TimeoutError:
            logger.warning("Rate limit check timeout, allowing request")
            return

    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Rate limiting error: {e}")
        # Continue on error (fail open)


# Rate limit decorator for specific endpoints
def rate_limit(max_requests: int = None, window_seconds: int = None):
    """Apply rate limiting to specific endpoints."""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            from app.core.config import settings
            
            # Use settings defaults if not provided
            limit_requests = max_requests if max_requests is not None else settings.RATE_LIMIT_REQUESTS
            limit_window = window_seconds if window_seconds is not None else settings.RATE_LIMIT_WINDOW
            
            # Extract request from kwargs or args
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                for value in kwargs.values():
                    if isinstance(value, Request):
                        request = value
                        break

            if request:
                await rate_limit_middleware(request, limit_requests, limit_window)

            return await func(*args, **kwargs)

        return wrapper

    return decorator
