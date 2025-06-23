"""Redis service module for handling Redis operations."""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisService:
    """Service for interacting with Redis."""

    def __init__(self) -> None:
        """Initialize Redis service without immediate connection."""
        self.redis: Optional[Redis] = None
        self._lock = asyncio.Lock()
        # Don't connect immediately - connect lazily when needed

    async def _get_redis_client(self) -> Optional[Redis]:
        """Get the Redis client, creating it if it doesn't exist."""
        async with self._lock:
            if self.redis is None:
                try:
                    self.redis = Redis.from_url(
                        settings.REDIS_URL, decode_responses=True
                    )
                    await self.redis.ping()
                except Exception as e:
                    logger.error(f"Error connecting to Redis: {e}")
                    self.redis = None
        return self.redis

    async def get_cached_price(self, symbol: str) -> Optional[float]:
        """Get cached price for a symbol."""
        redis = await self._get_redis_client()
        if not redis:
            return None

        try:
            key = f"price:{symbol}"
            data = await redis.get(key)
            if data:
                return float(data)
            return None
        except Exception as e:
            self._log_error("Redis err", e)
            return None

    async def cache_price(self, symbol: str, price: float) -> bool:
        """Cache price for a symbol."""
        redis = await self._get_redis_client()
        if not redis:
            return False

        try:
            key = f"price:{symbol}"
            ttl = settings.CACHE_TTL
            await redis.setex(key, ttl, str(price))  # Cache with configurable TTL
            return True
        except Exception as e:
            self._log_error("Redis err", e)
            return False

    async def store_price(self, symbol: str, price: float) -> bool:
        """Store price in Redis with timestamp."""
        redis = await self._get_redis_client()
        if not redis:
            return False

        try:
            timestamp = int(datetime.now().timestamp() * 1000)
            key = f"price:{symbol}:{timestamp}"
            data = json.dumps({"price": price, "timestamp": timestamp})
            await redis.set(key, data)
            return True
        except Exception as e:
            self._log_error("Redis err", e)
            return False

    async def get_price(self, symbol: str) -> Optional[float]:
        """Get latest price for a symbol."""
        redis = await self._get_redis_client()
        if not redis:
            return None

        try:
            key = f"price:{symbol}"
            data = await redis.get(key)
            if data:
                return float(data)
            return None
        except Exception as e:
            self._log_error("Redis err", e)
            return None

    async def set_price(self, symbol: str, price: float) -> bool:
        """Set price for a symbol."""
        redis = await self._get_redis_client()
        if not redis:
            return False

        try:
            key = f"price:{symbol}"
            await redis.set(key, str(price))
            return True
        except Exception as e:
            self._log_error("Redis err", e)
            return False

    async def delete_price(self, symbol: str) -> bool:
        """Delete price for a symbol."""
        redis = await self._get_redis_client()
        if not redis:
            return False

        try:
            key = f"price:{symbol}"
            await redis.delete(key)
            return True
        except Exception as e:
            self._log_error("Redis err", e)
            return False

    async def get_all_prices(self) -> Dict[str, float]:
        """Get all prices."""
        redis = await self._get_redis_client()
        if not redis:
            return {}

        try:
            prices: Dict[str, float] = {}
            async for key in redis.scan_iter("price:*"):
                data = await redis.get(key)
                if data:
                    symbol = key.split(":")[1]
                    prices[symbol] = float(data)
            return prices
        except Exception as e:
            self._log_error("Redis err", e)
            return {}

    async def clear_prices(self) -> bool:
        """Clear all prices."""
        redis = await self._get_redis_client()
        if not redis:
            return False

        try:
            async for key in redis.scan_iter("price:*"):
                await redis.delete(key)
            return True
        except Exception as e:
            self._log_error("Redis err", e)
            return False

    async def get_price_history(
        self, symbol: str, window: int = 3600
    ) -> List[Dict[str, Any]]:
        """Get price history for a symbol over a time window."""
        redis = await self._get_redis_client()
        if not redis:
            return []

        try:
            now = datetime.now()
            start_time = int((now.timestamp() - window) * 1000)
            end_time = int(now.timestamp() * 1000)
            pattern = f"price:{symbol}:*"
            keys = await redis.keys(pattern)
            prices = []
            for key in keys:
                if isinstance(key, bytes):
                    key = key.decode()
                timestamp_ms_str = key.split(":")[-1]
                if timestamp_ms_str.isdigit():
                    timestamp_ms = int(timestamp_ms_str)
                    if start_time <= timestamp_ms <= end_time:
                        data = await redis.get(key)
                        if data:
                            prices.append(json.loads(data))
            return sorted(prices, key=lambda x: x["timestamp"])
        except Exception as e:
            self._log_error("Redis err", e)
            return []

    async def get_latest_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest price for a symbol (async wrapper)."""
        price = await self.get_price(symbol)
        if price is not None:
            return {
                "symbol": symbol,
                "price": price,
                "timestamp": datetime.now().isoformat(),
            }
        return None

    async def store_job_status(self, job_id: str, status: Dict[str, Any]) -> None:
        """Store job status in Redis."""
        redis = await self._get_redis_client()
        if not redis:
            return

        try:
            key = f"job:{job_id}"
            await redis.set(key, json.dumps(status))
        except Exception as e:
            self._log_error("Redis err", e)

    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status from Redis."""
        redis = await self._get_redis_client()
        if not redis:
            return None

        try:
            key = f"job:{job_id}"
            data = await redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            self._log_error("Redis err", e)
            return None

    async def delete_job(self, job_id: str) -> None:
        """Delete job from Redis."""
        redis = await self._get_redis_client()
        if not redis:
            return

        try:
            key = f"job:{job_id}"
            await redis.delete(key)
        except Exception as e:
            self._log_error("Redis err", e)

    async def list_jobs(self) -> List[Dict[str, Any]]:
        """List all jobs from Redis."""
        redis = await self._get_redis_client()
        if not redis:
            return []

        try:
            jobs = []
            async for key in redis.scan_iter("job:*"):
                data = await redis.get(key)
                if data:
                    jobs.append(json.loads(data))
            return jobs
        except Exception as e:
            self._log_error("Redis err", e)
            return []

    def _log_error(self, msg: str, exc: Exception) -> None:
        """Log error with proper formatting."""
        logger.error(
            f"{msg}: {exc.__class__.__name__}: {str(exc)[:20]}... " f"{str(exc)[-40:]}"
        )

    async def store_price_data(self, symbol: str, price: float, timestamp: int) -> bool:
        """Store price data in a sorted set for history/statistics."""
        redis = await self._get_redis_client()
        if not redis:
            return False
        try:
            key = f"price_history:{symbol}"
            await redis.zadd(key, {price: timestamp})
            return True
        except Exception as e:
            self._log_error("Redis err", e)
            return False

    async def delete_price_data(self, symbol: str, window: int = 3600) -> int:
        """Delete price data in a time window."""
        redis = await self._get_redis_client()
        if not redis:
            return 0
        try:
            key = f"price_history:{symbol}"
            current_time = int(time.time())
            min_time = current_time - window
            return await redis.zremrangebyscore(key, min_time, current_time)
        except Exception as e:
            self._log_error("Redis err", e)
            return 0

    async def get_price_statistics(
        self, symbol: str, window: int = 3600
    ) -> Optional[dict]:
        """Get min, max, avg price for a symbol in a time window."""
        history = await self.get_price_history(symbol, window)
        if not history:
            return None
        prices = [item["price"] for item in history]
        return {
            "min": min(prices),
            "max": max(prices),
            "avg": sum(prices) / len(prices),
        }

    async def clear_all_data(self) -> bool:
        """Clear all price and job data from Redis."""
        redis = await self._get_redis_client()
        if not redis:
            return False
        try:
            await redis.flushdb()
            return True
        except Exception as e:
            self._log_error("Redis err", e)
            return False

    async def get_connection_info(self) -> dict:
        """Get Redis connection/server info."""
        redis = await self._get_redis_client()
        if not redis:
            return {"status": "disconnected"}
        try:
            info = await redis.info()
            return {
                "status": "connected",
                "version": info.get("redis_version"),
                "mode": info.get("redis_mode"),
            }
        except Exception as e:
            self._log_error("Redis conn err", e)
            return {"status": "error", "message": str(e)}

    async def ping(self) -> bool:
        """Ping Redis server."""
        redis = await self._get_redis_client()
        if not redis:
            return False
        try:
            return await redis.ping()
        except Exception as e:
            self._log_error("Redis err", e)
            return False
