import httpx
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from config import settings
import logging

logger = logging.getLogger(__name__)

class AlphaVantageClient:
    def __init__(self):
        self.base_url = settings.alpha_vantage_base_url
        self.api_key = settings.alpha_vantage_api_key
        self.rate_limit_per_minute = settings.alpha_vantage_rate_limit_per_minute
        self.last_request_time = None
        self.request_count = 0
        self.request_times = []

    async def _rate_limit(self):
        """Implement rate limiting."""
        now = datetime.now()
        
        # Remove requests older than 1 minute
        self.request_times = [
            req_time for req_time in self.request_times 
            if now - req_time < timedelta(minutes=1)
        ]
        
        # If we've hit the rate limit, wait
        if len(self.request_times) >= self.rate_limit_per_minute:
            sleep_time = 60 - (now - self.request_times[0]).total_seconds()
            if sleep_time > 0:
                logger.info(f"Rate limit reached, sleeping for {sleep_time} seconds")
                await asyncio.sleep(sleep_time)
        
        self.request_times.append(now)

    async def _make_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a request to Alpha Vantage API with rate limiting."""
        await self._rate_limit()
        
        params["apikey"] = self.api_key

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.base_url, params=params, timeout=30.0)
                response.raise_for_status()
                data = response.json()
                
                # Check for API errors
                if "Error Message" in data:
                    raise Exception(f"Alpha Vantage API Error: {data['Error Message']}")
                
                if "Note" in data:
                    raise Exception(f"Alpha Vantage API Note: {data['Note']}")
                
                return data
                
            except httpx.HTTPError as e:
                logger.error(f"HTTP error occurred: {e}")
                raise Exception(f"Failed to fetch data from Alpha Vantage: {str(e)}")
            except Exception as e:
                logger.error(f"Error making request to Alpha Vantage: {e}")
                raise

    # Stock Data Methods
    async def get_stock_intraday(self, symbol: str, interval: str = "5min", outputsize: str = "compact") -> Dict[str, Any]:
        """Get intraday stock data."""
        params = {
            "function": "TIME_SERIES_INTRADAY",
            "symbol": symbol,
            "interval": interval,
            "outputsize": outputsize
        }
        return await self._make_request(params)

    async def get_stock_daily(self, symbol: str, outputsize: str = "compact") -> Dict[str, Any]:
        """Get daily stock data."""
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": outputsize
        }
        return await self._make_request(params)

    async def get_stock_quote(self, symbol: str) -> Dict[str, Any]:
        """Get current stock quote."""
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol
        }
        return await self._make_request(params)

    async def search_symbol(self, keywords: str) -> Dict[str, Any]:
        """Search for stock symbols."""
        params = {
            "function": "SYMBOL_SEARCH",
            "keywords": keywords
        }
        return await self._make_request(params)

    # Cryptocurrency Methods
    async def get_crypto_daily(self, symbol: str, market: str = "USD") -> Dict[str, Any]:
        """Get daily cryptocurrency data."""
        params = {
            "function": "DIGITAL_CURRENCY_DAILY",
            "symbol": symbol,
            "market": market
        }
        return await self._make_request(params)

    async def get_crypto_intraday(self, symbol: str, market: str = "USD", interval: str = "5min") -> Dict[str, Any]:
        """Get intraday cryptocurrency data."""
        params = {
            "function": "CRYPTO_INTRADAY",
            "symbol": symbol,
            "market": market,
            "interval": interval
        }
        return await self._make_request(params)

    async def get_crypto_exchange_rate(self, from_currency: str, to_currency: str = "USD") -> Dict[str, Any]:
        """Get cryptocurrency exchange rate."""
        params = {
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": from_currency,
            "to_currency": to_currency
        }
        return await self._make_request(params)

    async def get_crypto_weekly(self, symbol: str, market: str = "USD") -> Dict[str, Any]:
        """Get weekly cryptocurrency data."""
        params = {
            "function": "DIGITAL_CURRENCY_WEEKLY",
            "symbol": symbol,
            "market": market
        }
        return await self._make_request(params)

    async def get_crypto_monthly(self, symbol: str, market: str = "USD") -> Dict[str, Any]:
        """Get monthly cryptocurrency data."""
        params = {
            "function": "DIGITAL_CURRENCY_MONTHLY",
            "symbol": symbol,
            "market": market
        }
        return await self._make_request(params)

    # Technical Indicators
    async def get_rsi(self, symbol: str, interval: str = "daily", time_period: int = 14, series_type: str = "close") -> Dict[str, Any]:
        """Get RSI indicator."""
        params = {
            "function": "RSI",
            "symbol": symbol,
            "interval": interval,
            "time_period": time_period,
            "series_type": series_type
        }
        return await self._make_request(params)

    async def get_macd(self, symbol: str, interval: str = "daily", series_type: str = "close") -> Dict[str, Any]:
        """Get MACD indicator."""
        params = {
            "function": "MACD",
            "symbol": symbol,
            "interval": interval,
            "series_type": series_type
        }
        return await self._make_request(params)

    async def get_stoch(self, symbol: str, interval: str = "daily") -> Dict[str, Any]:
        """Get Stochastic indicator."""
        params = {
            "function": "STOCH",
            "symbol": symbol,
            "interval": interval
        }
        return await self._make_request(params)

    async def get_bbands(self, symbol: str, interval: str = "daily", time_period: int = 20, series_type: str = "close") -> Dict[str, Any]:
        """Get Bollinger Bands indicator."""
        params = {
            "function": "BBANDS",
            "symbol": symbol,
            "interval": interval,
            "time_period": time_period,
            "series_type": series_type
        }
        return await self._make_request(params)
