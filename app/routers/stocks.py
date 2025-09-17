import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth import get_current_active_user
from app.models.user import User
from app.schemas.stock import (
    StockDailyResponse,
    StockIntradayResponse,
    StockQuote,
    StockSearchResponse,
    StockSearchResult,
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
