"""API router for stocks endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth import get_current_active_user
from app.models.user import User
from app.schemas.stock import (
    POPULAR_STOCKS,
    STOCK_CATEGORIES,
    StockDailyResponse,
    StockIntradayResponse,
    StockOverview,
    StockPopularResponse,
    StockQuote,
    StockSearchResponse,
    StockTrendingResponse,
)
from app.services.market_data import MarketDataService
from app.utils.data_parser import DataParser

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stocks", tags=["Stocks"])


@router.get("/search", response_model=StockSearchResponse)
async def search_stocks(
    keywords: str = Query(..., description="Keywords to search for stocks"),
    current_user: User = Depends(get_current_active_user),
):
    """Search for stock symbols."""
    try:
        market_service = MarketDataService()
        data = await market_service.search_symbol(keywords)

        results = DataParser.parse_search_results(data)
        return StockSearchResponse(results=results)

    except Exception as e:
        logger.error(f"Error searching stocks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search stocks: {str(e)}",
        )


@router.get("/quote/{symbol}", response_model=StockQuote)
async def get_stock_quote(
    symbol: str, current_user: User = Depends(get_current_active_user)
):
    """Get current stock quote."""
    try:
        market_service = MarketDataService()
        data = await market_service.get_stock_quote(symbol.upper())

        quote = DataParser.parse_stock_quote(data)
        return quote

    except Exception as e:
        logger.error(f"Error getting stock quote for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stock quote: {str(e)}",
        )


@router.get("/daily/{symbol}", response_model=StockDailyResponse)
async def get_stock_daily(
    symbol: str,
    outputsize: Optional[str] = Query("compact", description="compact or full"),
    current_user: User = Depends(get_current_active_user),
):
    """Get daily stock data."""
    try:
        market_service = MarketDataService()
        data = await market_service.get_stock_daily(symbol.upper(), outputsize)

        metadata = DataParser.get_metadata(data)
        time_series_data = DataParser.parse_daily_data(data)

        return StockDailyResponse(
            symbol=metadata["symbol"],
            last_refreshed=metadata["last_refreshed"],
            time_zone=metadata["time_zone"],
            data=time_series_data,
        )

    except Exception as e:
        logger.error(f"Error getting daily data for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get daily stock data: {str(e)}",
        )


@router.get("/intraday/{symbol}", response_model=StockIntradayResponse)
async def get_stock_intraday(
    symbol: str,
    interval: Optional[str] = Query(
        "5min", description="1min, 5min, 15min, 30min, 60min"
    ),
    outputsize: Optional[str] = Query("compact", description="compact or full"),
    current_user: User = Depends(get_current_active_user),
):
    """Get intraday stock data."""
    try:
        # Validate interval
        valid_intervals = ["1min", "5min", "15min", "30min", "60min"]
        if interval not in valid_intervals:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid interval. Must be one of: {', '.join(valid_intervals)}",
            )

        market_service = MarketDataService()
        data = await market_service.get_stock_intraday(
            symbol.upper(), interval, outputsize
        )

        metadata = DataParser.get_metadata(data)
        time_series_data = DataParser.parse_intraday_data(data, interval)

        return StockIntradayResponse(
            symbol=metadata["symbol"],
            last_refreshed=metadata["last_refreshed"],
            interval=interval,
            time_zone=metadata["time_zone"],
            data=time_series_data,
        )

    except Exception as e:
        logger.error(f"Error getting intraday data for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get intraday stock data: {str(e)}",
        )


@router.get("/popular", response_model=StockPopularResponse)
async def get_popular_stocks(current_user: User = Depends(get_current_active_user)):
    """Get list of popular stock symbols organized by categories."""
    return StockPopularResponse(
        popular_stocks=POPULAR_STOCKS,
        categories=STOCK_CATEGORIES,
        description="List of popular stock symbols organized by industry sectors",
    )


@router.get("/categories")
async def get_stock_categories(current_user: User = Depends(get_current_active_user)):
    """Get stock symbols organized by industry categories."""
    return {
        "categories": STOCK_CATEGORIES,
        "description": "Stock symbols organized by industry sectors",
    }


@router.get("/trending", response_model=StockTrendingResponse)
async def get_trending_stocks(
    limit: Optional[int] = Query(10, description="Number of stocks per category"),
    current_user: User = Depends(get_current_active_user),
):
    """Get trending stocks including gainers, losers, and high volume stocks."""
    try:
        market_service = MarketDataService()

        # Get quotes for popular stocks to determine trending
        trending_stocks = []
        gainers = []
        losers = []

        # Sample popular stocks for trending analysis
        sample_symbols = POPULAR_STOCKS[:30]  # Use first 30 for analysis

        for symbol in sample_symbols:
            try:
                quote_data = await market_service.get_stock_quote(symbol)
                quote = DataParser.parse_stock_quote(quote_data)

                # Create StockOverview from quote data
                stock_overview = StockOverview(
                    symbol=quote.symbol,
                    name=symbol,  # In real implementation, you'd get company name
                    current_price=quote.price,
                    change_24h=quote.change,
                    change_percent_24h=float(quote.change_percent.replace('%', '')),
                    volume_24h=quote.volume,
                    market_cap=None,  # Would need additional API call
                    exchange="NASDAQ"  # Default exchange
                )

                # Categorize based on performance
                change_percent = float(quote.change_percent.replace('%', ''))

                if change_percent >= 3.0:  # Gainers: +3% or more
                    gainers.append(stock_overview)
                elif change_percent <= -3.0:  # Losers: -3% or less
                    losers.append(stock_overview)

                # High volume stocks (trending)
                if quote.volume > 5000000:  # 5M+ volume
                    trending_stocks.append(stock_overview)

            except Exception as e:
                logger.warning(f"Failed to get quote for {symbol}: {e}")
                continue

        # Sort and limit results
        gainers.sort(key=lambda x: x.change_percent_24h or 0, reverse=True)
        losers.sort(key=lambda x: x.change_percent_24h or 0)
        trending_stocks.sort(key=lambda x: x.volume_24h or 0, reverse=True)

        return StockTrendingResponse(
            trending=trending_stocks[:limit],
            gainers=gainers[:limit],
            losers=losers[:limit],
        )

    except Exception as e:
        logger.error(f"Error getting trending stocks: {e}")
        # Return fallback data
        fallback_stocks = [
            StockOverview(
                symbol="AAPL",
                name="Apple Inc.",
                current_price=150.00,
                change_24h=2.50,
                change_percent_24h=1.69,
                volume_24h=50000000,
                exchange="NASDAQ"
            ),
            StockOverview(
                symbol="TSLA",
                name="Tesla Inc.",
                current_price=200.00,
                change_24h=-5.00,
                change_percent_24h=-2.44,
                volume_24h=30000000,
                exchange="NASDAQ"
            ),
        ]

        return StockTrendingResponse(
            trending=fallback_stocks,
            gainers=[fallback_stocks[0]],
            losers=[fallback_stocks[1]],
        )
