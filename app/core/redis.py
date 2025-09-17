import json
import logging
from typing import Any, Optional

import redis.asyncio as redis

from config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    def __init__(self):
        self.redis_url = settings.redis_url
        self.ttl = settings.cache_ttl_seconds
        self._redis = None

    async def get_redis(self):
        """Get Redis connection."""
        if self._redis is None:
            self._redis = redis.from_url(self.redis_url, decode_responses=True)
        return self._redis

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()

    def _generate_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate cache key from parameters."""
        key_parts = [prefix]
        for key, value in sorted(kwargs.items()):
            key_parts.append(f"{key}:{value}")
        return ":".join(key_parts)

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            redis_client = await self.get_redis()
            value = await redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        try:
            redis_client = await self.get_redis()
            ttl = ttl or self.ttl
            serialized_value = json.dumps(value, default=str)
            await redis_client.setex(key, ttl, serialized_value)
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            redis_client = await self.get_redis()
            await redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> bool:
        """Delete keys matching pattern."""
        try:
            redis_client = await self.get_redis()
            keys = await redis_client.keys(pattern)
            if keys:
                await redis_client.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Error deleting pattern from cache: {e}")
            return False

    # Cache key generators for different data types
    def stock_quote_key(self, symbol: str) -> str:
        return self._generate_cache_key("stock_quote", symbol=symbol)

    def stock_daily_key(self, symbol: str, outputsize: str = "compact") -> str:
        return self._generate_cache_key(
            "stock_daily", symbol=symbol, outputsize=outputsize
        )

    def stock_intraday_key(
        self, symbol: str, interval: str = "5min", outputsize: str = "compact"
    ) -> str:
        return self._generate_cache_key(
            "stock_intraday", symbol=symbol, interval=interval, outputsize=outputsize
        )

    def crypto_daily_key(self, symbol: str, market: str = "USD") -> str:
        return self._generate_cache_key("crypto_daily", symbol=symbol, market=market)

    def crypto_rate_key(self, from_currency: str, to_currency: str = "USD") -> str:
        return self._generate_cache_key(
            "crypto_rate", from_currency=from_currency, to_currency=to_currency
        )

    def rsi_key(
        self,
        symbol: str,
        interval: str = "daily",
        time_period: int = 14,
        series_type: str = "close",
    ) -> str:
        return self._generate_cache_key(
            "rsi",
            symbol=symbol,
            interval=interval,
            time_period=time_period,
            series_type=series_type,
        )

    def macd_key(
        self, symbol: str, interval: str = "daily", series_type: str = "close"
    ) -> str:
        return self._generate_cache_key(
            "macd", symbol=symbol, interval=interval, series_type=series_type
        )

    def stoch_key(self, symbol: str, interval: str = "daily") -> str:
        return self._generate_cache_key("stoch", symbol=symbol, interval=interval)

    def bbands_key(
        self,
        symbol: str,
        interval: str = "daily",
        time_period: int = 20,
        series_type: str = "close",
    ) -> str:
        return self._generate_cache_key(
            "bbands",
            symbol=symbol,
            interval=interval,
            time_period=time_period,
            series_type=series_type,
        )

    def search_key(self, keywords: str) -> str:
        return self._generate_cache_key("search", keywords=keywords)


# Global Redis client instance
redis_client = RedisClient()
