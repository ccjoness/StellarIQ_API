"""API router for charts endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth import get_current_active_user
from app.models.user import User
from app.schemas.charts import (
    ChartDataResponse,
    ComparisonChartResponse,
    MultiSymbolChartData,
)
from app.services.market_data import MarketDataService
from app.utils.chart_formatter import ChartFormatter
from app.utils.data_parser import DataParser
from app.utils.technical_analysis import TechnicalAnalyzer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/charts", tags=["Charts"])


@router.get("/candlestick/{symbol}", response_model=ChartDataResponse)
async def get_candlestick_chart(
    symbol: str,
    interval: Optional[str] = Query(
        "daily", description="1min, 5min, 15min, 30min, 60min, daily, weekly, monthly"
    ),
    market_type: Optional[str] = Query("stock", description="stock or crypto"),
    outputsize: Optional[str] = Query("compact", description="compact or full"),
    include_indicators: Optional[bool] = Query(
        True, description="Include technical indicators"
    ),
    indicators: Optional[str] = Query(
        "rsi,macd,bbands", description="Comma-separated list of indicators"
    ),
    current_user: User = Depends(get_current_active_user),
):
    """Get candlestick chart data with optional technical indicators."""
    try:
        market_service = MarketDataService()

        # Get price data based on market type
        if market_type.lower() == "crypto":
            # Cryptocurrency data
            if interval == "daily":
                price_data = await market_service.get_crypto_daily(symbol.upper())
                metadata = DataParser.get_crypto_metadata(price_data)
                time_series_data = DataParser.parse_crypto_daily_data(price_data)
            else:
                # Validate intraday intervals for crypto
                valid_intervals = ["1min", "5min", "15min", "30min", "60min"]
                if interval not in valid_intervals:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid interval for crypto intraday data. Must be one of: {', '.join(valid_intervals)}",
                    )
                price_data = await market_service.get_crypto_intraday(
                    symbol.upper(), "USD", interval
                )
                metadata = DataParser.get_crypto_metadata(price_data)
                time_series_data = DataParser.parse_crypto_intraday_data(
                    price_data, interval
                )
        else:
            # Stock data (default)
            if interval == "daily":
                price_data = await market_service.get_stock_daily(
                    symbol.upper(), outputsize
                )
                metadata = DataParser.get_metadata(price_data)
                time_series_data = DataParser.parse_daily_data(price_data)
            else:
                # Validate intraday intervals for stocks
                valid_intervals = ["1min", "5min", "15min", "30min", "60min"]
                if interval not in valid_intervals:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid interval for stock intraday data. Must be one of: {', '.join(valid_intervals)}",
                    )
                price_data = await market_service.get_stock_intraday(
                    symbol.upper(), interval, outputsize
                )
                metadata = DataParser.get_metadata(price_data)
                time_series_data = DataParser.parse_intraday_data(price_data, interval)

        # Format candlestick data
        candlestick_data = ChartFormatter.format_candlestick_data(time_series_data)

        # Limit data points for mobile performance
        candlestick_data = ChartFormatter.limit_data_points(candlestick_data, 200)

        # Get technical indicators if requested
        technical_overlay = None
        if include_indicators and indicators:
            indicator_list = [ind.strip().lower() for ind in indicators.split(",")]

            rsi_data = None
            macd_data = None
            stoch_data = None
            bbands_data = None

            try:
                if "rsi" in indicator_list:
                    rsi_response = await market_service.get_rsi(
                        symbol.upper(), interval
                    )
                    rsi_data = TechnicalAnalyzer.parse_rsi_data(rsi_response)

                if "macd" in indicator_list:
                    macd_response = await market_service.get_macd(
                        symbol.upper(), interval
                    )
                    macd_data = TechnicalAnalyzer.parse_macd_data(macd_response)

                if "stoch" in indicator_list:
                    stoch_response = await market_service.get_stoch(
                        symbol.upper(), interval
                    )
                    stoch_data = TechnicalAnalyzer.parse_stoch_data(stoch_response)

                if "bbands" in indicator_list:
                    bbands_response = await market_service.get_bbands(
                        symbol.upper(), interval
                    )
                    bbands_data = TechnicalAnalyzer.parse_bbands_data(bbands_response)

                technical_overlay = ChartFormatter.create_technical_overlay(
                    rsi_data, macd_data, stoch_data, bbands_data
                )

            except Exception as e:
                logger.warning(f"Failed to get some indicators for {symbol}: {e}")
                # Continue without indicators rather than failing

        return ChartDataResponse(
            symbol=metadata["symbol"],
            interval=interval,
            last_refreshed=metadata["last_refreshed"],
            time_zone=metadata["time_zone"],
            candlestick_data=candlestick_data,
            indicators=technical_overlay,
            metadata={
                "data_points": len(candlestick_data),
                "indicators_included": indicators if include_indicators else None,
                "outputsize": outputsize,
            },
        )

    except Exception as e:
        logger.error(f"Error getting chart data for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chart data: {str(e)}",
        )


@router.get("/comparison", response_model=ComparisonChartResponse)
async def get_comparison_chart(
    symbols: str = Query(..., description="Comma-separated list of symbols (max 5)"),
    interval: Optional[str] = Query("daily", description="daily, weekly, monthly"),
    normalize: Optional[bool] = Query(
        False, description="Normalize to percentage change"
    ),
    outputsize: Optional[str] = Query("compact", description="compact or full"),
    current_user: User = Depends(get_current_active_user),
):
    """Get comparison chart data for multiple symbols."""
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(",")]

        if len(symbol_list) > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 5 symbols allowed for comparison",
            )

        if len(symbol_list) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least 2 symbols required for comparison",
            )

        market_service = MarketDataService()
        symbols_data = {}

        # Fetch data for all symbols
        for symbol in symbol_list:
            try:
                if interval == "daily":
                    price_data = await market_service.get_stock_daily(
                        symbol, outputsize
                    )
                    time_series_data = DataParser.parse_daily_data(price_data)
                else:
                    # For weekly/monthly, use daily data (Alpha Vantage API limitation)
                    price_data = await market_service.get_stock_daily(
                        symbol, outputsize
                    )
                    time_series_data = DataParser.parse_daily_data(price_data)

                symbols_data[symbol] = time_series_data

            except Exception as e:
                logger.warning(f"Failed to get data for {symbol}: {e}")
                # Continue with other symbols

        if not symbols_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No data found for any of the requested symbols",
            )

        # Create comparison data
        comparison_data = ChartFormatter.create_price_comparison_data(
            symbols_data, normalize
        )

        # Limit data points for mobile performance
        comparison_data = ChartFormatter.limit_data_points(comparison_data, 200)

        return ComparisonChartResponse(
            symbols=list(symbols_data.keys()),
            interval=interval,
            data=comparison_data,
            base_date=comparison_data[-1].timestamp if comparison_data else "",
            normalized=normalize,
        )

    except Exception as e:
        logger.error(f"Error getting comparison chart: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get comparison chart: {str(e)}",
        )


@router.get("/multi/{symbols}", response_model=MultiSymbolChartData)
async def get_multi_symbol_charts(
    symbols: str,
    interval: Optional[str] = Query("daily", description="daily, weekly, monthly"),
    include_indicators: Optional[bool] = Query(
        False, description="Include technical indicators"
    ),
    current_user: User = Depends(get_current_active_user),
):
    """Get chart data for multiple symbols (for dashboard view)."""
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(",")]

        if len(symbol_list) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 10 symbols allowed",
            )

        market_service = MarketDataService()
        chart_data = {}

        for symbol in symbol_list:
            try:
                # Get basic price data
                price_data = await market_service.get_stock_daily(symbol, "compact")
                metadata = DataParser.get_metadata(price_data)
                time_series_data = DataParser.parse_daily_data(price_data)

                # Format candlestick data (limited for dashboard)
                candlestick_data = ChartFormatter.format_candlestick_data(
                    time_series_data
                )
                candlestick_data = ChartFormatter.limit_data_points(
                    candlestick_data, 50
                )  # Fewer points for dashboard

                # Get indicators if requested (simplified for dashboard)
                technical_overlay = None
                if include_indicators:
                    try:
                        rsi_response = await market_service.get_rsi(symbol, interval)
                        rsi_data = TechnicalAnalyzer.parse_rsi_data(rsi_response)
                        technical_overlay = ChartFormatter.create_technical_overlay(
                            rsi_data=rsi_data
                        )
                    except Exception as e:
                        logger.warning(f"Failed to get indicators for {symbol}: {e}")

                chart_data[symbol] = ChartDataResponse(
                    symbol=symbol,
                    interval=interval,
                    last_refreshed=metadata["last_refreshed"],
                    time_zone=metadata["time_zone"],
                    candlestick_data=candlestick_data,
                    indicators=technical_overlay,
                    metadata={"data_points": len(candlestick_data)},
                )

            except Exception as e:
                logger.warning(f"Failed to get chart data for {symbol}: {e}")
                # Continue with other symbols

        return MultiSymbolChartData(
            symbols=list(chart_data.keys()), chart_data=chart_data
        )

    except Exception as e:
        logger.error(f"Error getting multi-symbol charts: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get multi-symbol charts: {str(e)}",
        )
