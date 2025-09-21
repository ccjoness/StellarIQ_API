"""API router for stocks endpoints."""
import json
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
    TrendingStock,
    )
from app.services.market_data import MarketDataService
from app.utils.data_parser import DataParser
import humanize
from yahooquery import Ticker


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


def parse_stock_trending(data: dict) -> TrendingStock:
    """Parse trending stock data."""
    try:
        parsed_date = (DataParser.parse_stock_trending(data))
        return TrendingStock(
            ticker=parsed_date.ticker,
            price=float(parsed_date.price),
            change_amount=float(parsed_date.change_amount),
            change_percentage=round(float(parsed_date.change_percentage.replace("%", "")), 2),
            volume=humanize.intword(parsed_date.volume)
            )
    except Exception as e:
        logger.warning(f"Failed to parse trending stock: {e}")


@router.get("/trending", response_model=StockTrendingResponse)
async def get_trending_stocks(
        limit: Optional[int] = Query(30, description="Number of stocks per category"),
        current_user: User = Depends(get_current_active_user),
        ):
    """Get trending stocks including gainers, losers, and high volume stocks."""
    try:
        market_service = MarketDataService()
        trending_data = await market_service.get_stock_trending(limit=limit)
        ticker_list = []
        ticker_symbol_to_name_dict = {}
        for top in trending_data.get("top_gainers", []):
            ticker_list.append(top.get("ticker", ""))
        for loser in trending_data.get("top_losers", []):
            ticker_list.append(loser.get("ticker", ""))
        for traded in trending_data.get("most_actively_traded", []):
            ticker_list.append(traded.get("ticker", ""))

        all_symbols = " ".join(ticker_list)
        ticker_info = Ticker(all_symbols)
        ticker_info_dict = ticker_info.price
        ticker_symbol_to_name_dict = {}

        for ticker in ticker_list:
            try:
                longName = ticker_info_dict[ticker]['longName']
            except KeyError:
                longName = ticker
            ticker_symbol_to_name_dict[ticker] = longName

        top_gainers = []
        top_losers = []
        most_actively_traded = []

        for top in trending_data.get("top_gainers", []):
            try:
                top_gainers.append(DataParser.parse_stock_trending(top, ticker_symbol_to_name_dict))
            except Exception as e:
                logger.warning(f"Failed to parse trending stock: {e}")
                continue

        for loser in trending_data.get("top_losers", []):
            try:
                top_losers.append(DataParser.parse_stock_trending(loser, ticker_symbol_to_name_dict))
            except Exception as e:
                logger.warning(f"Failed to parse trending stock: {e}")
                continue

        for traded in trending_data.get("most_actively_traded", []):
            try:
                most_actively_traded.append(DataParser.parse_stock_trending(traded, ticker_symbol_to_name_dict))
            except Exception as e:
                logger.warning(f"Failed to parse trending stock: {e}")
                continue

        # Sort and limit results
        top_gainers_sorted = sorted(top_gainers, key=lambda x: x.change_percentage or 0, reverse=True)
        top_losers_sorted = sorted(top_losers, key=lambda x: x.change_percentage or 0, reverse=True)
        most_actively_traded_sorted = sorted(most_actively_traded, key=lambda x: x.volume or 0, reverse=True)

        return StockTrendingResponse(
            metadata=trending_data.get("metadata"),
            last_updated=trending_data.get("last_updated"),
            trending=most_actively_traded_sorted,
            gainers=top_gainers_sorted,
            losers=top_losers_sorted,
            )

        # return StockTrendingResponse(
        #     metadata="",
        #     last_updated="",
        #     trending=[],
        #     gainers=[],
        #     losers=[],
        #     )

    except Exception as e:
        logger.error(f"Error getting trending stocks: {e}")

        return StockTrendingResponse(
            metadata="",
            last_updated="",
            trending=[],
            gainers=[],
            losers=[],
            )
