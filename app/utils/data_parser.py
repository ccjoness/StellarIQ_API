"""Utility functions for data_parser operations."""

import logging
from typing import Any, Dict, List

from app.schemas.crypto import CryptoExchangeRate, CryptoTimeSeriesData
from app.schemas.stock import StockQuote, StockSearchResult, TimeSeriesData

logger = logging.getLogger(__name__)


class DataParser:

    """DataParser class."""

    @staticmethod
    def parse_stock_quote(data: Dict[str, Any]) -> StockQuote:
        """Parse Alpha Vantage global quote response."""
        try:
            quote_data = data.get("Global Quote", {})
            return StockQuote(
                symbol=quote_data.get("01. symbol", ""),
                open=float(quote_data.get("02. open", 0)),
                high=float(quote_data.get("03. high", 0)),
                low=float(quote_data.get("04. low", 0)),
                price=float(quote_data.get("05. price", 0)),
                volume=int(quote_data.get("06. volume", 0)),
                latest_trading_day=quote_data.get("07. latest trading day", ""),
                previous_close=float(quote_data.get("08. previous close", 0)),
                change=float(quote_data.get("09. change", 0)),
                change_percent=quote_data.get("10. change percent", "0%"),
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing stock quote: {e}")
            raise ValueError("Invalid stock quote data format")

    @staticmethod
    def parse_search_results(data: Dict[str, Any]) -> List[StockSearchResult]:
        """Parse Alpha Vantage symbol search response."""
        try:
            results = []
            best_matches = data.get("bestMatches", [])

            for match in best_matches:
                result = StockSearchResult(
                    symbol=match.get("1. symbol", ""),
                    name=match.get("2. name", ""),
                    type=match.get("3. type", ""),
                    region=match.get("4. region", ""),
                    market_open=match.get("5. marketOpen", ""),
                    market_close=match.get("6. marketClose", ""),
                    timezone=match.get("7. timezone", ""),
                    currency=match.get("8. currency", ""),
                    match_score=float(match.get("9. matchScore", 0)),
                )
                results.append(result)

            return results
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing search results: {e}")
            raise ValueError("Invalid search results data format")

    @staticmethod
    def parse_time_series(
        data: Dict[str, Any], series_key: str
    ) -> List[TimeSeriesData]:
        """Parse Alpha Vantage time series data."""
        try:
            results = []
            time_series = data.get(series_key, {})

            for timestamp, values in time_series.items():
                result = TimeSeriesData(
                    timestamp=timestamp,
                    open=float(values.get("1. open", 0)),
                    high=float(values.get("2. high", 0)),
                    low=float(values.get("3. low", 0)),
                    close=float(values.get("4. close", 0)),
                    volume=int(values.get("5. volume", 0)),
                )
                results.append(result)

            # Sort by timestamp (most recent first)
            results.sort(key=lambda x: x.timestamp, reverse=True)
            return results
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing time series data: {e}")
            raise ValueError("Invalid time series data format")

    @staticmethod
    def parse_daily_data(data: Dict[str, Any]) -> List[TimeSeriesData]:
        """Parse daily time series data."""
        return DataParser.parse_time_series(data, "Time Series (Daily)")

    @staticmethod
    def parse_intraday_data(
        data: Dict[str, Any], interval: str
    ) -> List[TimeSeriesData]:
        """Parse intraday time series data."""
        series_key = f"Time Series ({interval})"
        return DataParser.parse_time_series(data, series_key)

    @staticmethod
    def get_metadata(data: Dict[str, Any]) -> Dict[str, str]:
        """Extract metadata from Alpha Vantage response."""
        metadata = data.get("Meta Data", {})
        return {
            "symbol": metadata.get("2. Symbol", ""),
            "last_refreshed": metadata.get("3. Last Refreshed", ""),
            "time_zone": metadata.get("5. Time Zone", ""),
            "interval": metadata.get("4. Interval", ""),
        }

    @staticmethod
    def parse_crypto_exchange_rate(data: Dict[str, Any]) -> CryptoExchangeRate:
        """Parse Alpha Vantage crypto exchange rate response."""
        try:
            rate_data = data.get("Realtime Currency Exchange Rate", {})
            return CryptoExchangeRate(
                from_currency_code=rate_data.get("1. From_Currency Code", ""),
                from_currency_name=rate_data.get("2. From_Currency Name", ""),
                to_currency_code=rate_data.get("3. To_Currency Code", ""),
                to_currency_name=rate_data.get("4. To_Currency Name", ""),
                exchange_rate=float(rate_data.get("5. Exchange Rate", 0)),
                last_refreshed=rate_data.get("6. Last Refreshed", ""),
                time_zone=rate_data.get("7. Time Zone", ""),
                bid_price=float(rate_data.get("8. Bid Price", 0))
                if rate_data.get("8. Bid Price")
                else None,
                ask_price=float(rate_data.get("9. Ask Price", 0))
                if rate_data.get("9. Ask Price")
                else None,
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing crypto exchange rate: {e}")
            raise ValueError("Invalid crypto exchange rate data format")

    @staticmethod
    def parse_crypto_daily_data(data: Dict[str, Any]) -> List[CryptoTimeSeriesData]:
        """Parse crypto daily time series data."""
        try:
            results = []
            time_series = data.get("Time Series (Digital Currency Daily)", {})

            for timestamp, values in time_series.items():
                result = CryptoTimeSeriesData(
                    timestamp=timestamp,
                    open_usd=float(values.get("1a. open (USD)", 0)),
                    high_usd=float(values.get("2a. high (USD)", 0)),
                    low_usd=float(values.get("3a. low (USD)", 0)),
                    close_usd=float(values.get("4a. close (USD)", 0)),
                    volume=float(values.get("5. volume", 0)),
                    market_cap_usd=float(values.get("6. market cap (USD)", 0)),
                )
                results.append(result)

            # Sort by timestamp (most recent first)
            results.sort(key=lambda x: x.timestamp, reverse=True)
            return results
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing crypto daily data: {e}")
            raise ValueError("Invalid crypto daily data format")

    @staticmethod
    def get_crypto_metadata(data: Dict[str, Any]) -> Dict[str, str]:
        """Extract metadata from crypto response."""
        metadata = data.get("Meta Data", {})
        return {
            "symbol": metadata.get("2. Digital Currency Code", ""),
            "name": metadata.get("3. Digital Currency Name", ""),
            "market": metadata.get("4. Market Code", ""),
            "last_refreshed": metadata.get("5. Last Refreshed", ""),
            "time_zone": metadata.get("6. Time Zone", ""),
        }

    @staticmethod
    def parse_crypto_intraday_data(
        data: Dict[str, Any], interval: str
    ) -> List[CryptoTimeSeriesData]:
        """Parse crypto intraday time series data."""
        try:
            results = []
            time_series_key = f"Time Series Crypto ({interval})"
            time_series = data.get(time_series_key, {})

            for timestamp, values in time_series.items():
                result = CryptoTimeSeriesData(
                    timestamp=timestamp,
                    open_usd=float(values.get("1. open", 0)),
                    high_usd=float(values.get("2. high", 0)),
                    low_usd=float(values.get("3. low", 0)),
                    close_usd=float(values.get("4. close", 0)),
                    volume=float(values.get("5. volume", 0)),
                    market_cap_usd=0,  # Not available in intraday data
                )
                results.append(result)

            # Sort by timestamp (most recent first)
            results.sort(key=lambda x: x.timestamp, reverse=True)
            return results
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing crypto intraday data: {e}")
            raise ValueError("Invalid crypto intraday data format")

    @staticmethod
    def parse_crypto_quote(data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse crypto exchange rate as a quote."""
        try:
            rate_data = data.get("Realtime Currency Exchange Rate", {})
            return {
                "symbol": rate_data.get("1. From_Currency Code", ""),
                "name": rate_data.get("2. From_Currency Name", ""),
                "price": float(rate_data.get("5. Exchange Rate", 0)),
                "last_updated": rate_data.get("6. Last Refreshed", ""),
                "bid_price": float(rate_data.get("8. Bid Price", 0))
                if rate_data.get("8. Bid Price")
                else None,
                "ask_price": float(rate_data.get("9. Ask Price", 0))
                if rate_data.get("9. Ask Price")
                else None,
            }
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing crypto quote: {e}")
            raise ValueError("Invalid crypto quote data format")
