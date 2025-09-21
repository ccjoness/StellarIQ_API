"""Business logic service for market_data operations."""

import logging
from typing import Any, Dict

from app.core.valkey import valkey_client
from app.services.alpha_vantage import AlphaVantageClient

logger = logging.getLogger(__name__)


class MarketDataService:
    """MarketDataService class."""

    def __init__(self):
        self.alpha_vantage = AlphaVantageClient()

    async def _get_cached_or_fetch(
            self, cache_key: str, fetch_func, *args, **kwargs
            ) -> Dict[str, Any]:
        """Get data from cache or fetch from API if not cached."""
        # Try to get from cache first
        cached_data = await valkey_client.get(cache_key)
        if cached_data:
            logger.info(f"Cache hit for key: {cache_key}")
            return cached_data

        # If not in cache, fetch from API
        logger.info(f"Cache miss for key: {cache_key}, fetching from API")
        try:
            data = await fetch_func(*args, **kwargs)
            # Cache the result
            await valkey_client.set(cache_key, data)
            return data
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            raise

    # Stock Data Methods
    async def get_stock_quote(self, symbol: str) -> Dict[str, Any]:
        """Get current stock quote with caching."""
        cache_key = valkey_client.stock_quote_key(symbol)
        logger.info(f"Getting stock quote for {symbol}")
        return await self._get_cached_or_fetch(
            cache_key, self.alpha_vantage.get_stock_quote, symbol
            )

    async def get_stock_trending(self, valkey_key: str = "stock_trending", limit: int = 10) -> Dict[str, Any]:
        """Get current stock quote with caching."""
        cache_key = valkey_client.stock_trending_key(valkey_key)
        logger.info(f"Getting trending stocks")
        return await self._get_cached_or_fetch(
            cache_key, self.alpha_vantage.get_stock_trending, limit
        )

    async def get_stock_daily(
            self, symbol: str, outputsize: str = "compact"
            ) -> Dict[str, Any]:
        """Get daily stock data with caching."""
        cache_key = valkey_client.stock_daily_key(symbol, outputsize)
        return await self._get_cached_or_fetch(
            cache_key, self.alpha_vantage.get_stock_daily, symbol, outputsize
            )

    async def get_stock_intraday(
            self, symbol: str, interval: str = "5min", outputsize: str = "compact"
            ) -> Dict[str, Any]:
        """Get intraday stock data with caching."""
        cache_key = valkey_client.stock_intraday_key(symbol, interval, outputsize)
        return await self._get_cached_or_fetch(
            cache_key,
            self.alpha_vantage.get_stock_intraday,
            symbol,
            interval,
            outputsize,
            )

    async def search_symbol(self, keywords: str) -> Dict[str, Any]:
        """Search for symbols with caching."""
        cache_key = valkey_client.search_key(keywords)
        return await self._get_cached_or_fetch(
            cache_key, self.alpha_vantage.search_symbol, keywords
            )

    # Cryptocurrency Methods
    async def get_crypto_daily(
            self, symbol: str, market: str = "USD"
            ) -> Dict[str, Any]:
        """Get daily crypto data with caching."""
        cache_key = valkey_client.crypto_daily_key(symbol, market)
        return await self._get_cached_or_fetch(
            cache_key, self.alpha_vantage.get_crypto_daily, symbol, market
            )

    async def get_crypto_intraday(
            self, symbol: str, market: str = "USD", interval: str = "5min"
            ) -> Dict[str, Any]:
        """Get intraday crypto data with caching."""
        cache_key = (
            f"crypto_intraday:symbol:{symbol}:market:{market}:interval:{interval}"
        )
        return await self._get_cached_or_fetch(
            cache_key, self.alpha_vantage.get_crypto_intraday, symbol, market, interval
            )

    async def get_crypto_weekly(
            self, symbol: str, market: str = "USD"
            ) -> Dict[str, Any]:
        """Get weekly crypto data with caching."""
        cache_key = f"crypto_weekly:symbol:{symbol}:market:{market}"
        return await self._get_cached_or_fetch(
            cache_key, self.alpha_vantage.get_crypto_weekly, symbol, market
            )

    async def get_crypto_monthly(
            self, symbol: str, market: str = "USD"
            ) -> Dict[str, Any]:
        """Get monthly crypto data with caching."""
        cache_key = f"crypto_monthly:symbol:{symbol}:market:{market}"
        return await self._get_cached_or_fetch(
            cache_key, self.alpha_vantage.get_crypto_monthly, symbol, market
            )

    async def get_crypto_exchange_rate(
            self, from_currency: str, to_currency: str = "USD"
            ) -> Dict[str, Any]:
        """Get crypto exchange rate with caching."""
        cache_key = valkey_client.crypto_rate_key(from_currency, to_currency)
        return await self._get_cached_or_fetch(
            cache_key,
            self.alpha_vantage.get_crypto_exchange_rate,
            from_currency,
            to_currency,
            )

    # Technical Indicators
    async def get_rsi(
            self,
            symbol: str,
            interval: str = "daily",
            time_period: int = 14,
            series_type: str = "close",
            ) -> Dict[str, Any]:
        """Get RSI indicator with caching."""
        cache_key = valkey_client.rsi_key(symbol, interval, time_period, series_type)
        return await self._get_cached_or_fetch(
            cache_key,
            self.alpha_vantage.get_rsi,
            symbol,
            interval,
            time_period,
            series_type,
            )

    async def get_macd(
            self, symbol: str, interval: str = "daily", series_type: str = "close"
            ) -> Dict[str, Any]:
        """Get MACD indicator with caching."""
        cache_key = valkey_client.macd_key(symbol, interval, series_type)
        return await self._get_cached_or_fetch(
            cache_key, self.alpha_vantage.get_macd, symbol, interval, series_type
            )

    async def get_stoch(self, symbol: str, interval: str = "daily") -> Dict[str, Any]:
        """Get Stochastic indicator with caching."""
        cache_key = valkey_client.stoch_key(symbol, interval)
        return await self._get_cached_or_fetch(
            cache_key, self.alpha_vantage.get_stoch, symbol, interval
            )

    async def get_bbands(
            self,
            symbol: str,
            interval: str = "daily",
            time_period: int = 20,
            series_type: str = "close",
            ) -> Dict[str, Any]:
        """Get Bollinger Bands indicator with caching."""
        cache_key = valkey_client.bbands_key(symbol, interval, time_period, series_type)
        return await self._get_cached_or_fetch(
            cache_key,
            self.alpha_vantage.get_bbands,
            symbol,
            interval,
            time_period,
            series_type,
            )

    async def invalidate_symbol_cache(self, symbol: str):
        """Invalidate all cached data for a symbol."""
        patterns = [
            f"stock_*:symbol:{symbol}:*",
            f"crypto_*:symbol:{symbol}:*",
            f"rsi:symbol:{symbol}:*",
            f"macd:symbol:{symbol}:*",
            f"stoch:symbol:{symbol}:*",
            f"bbands:symbol:{symbol}:*",
            ]

        for pattern in patterns:
            await valkey_client.delete_pattern(pattern)
