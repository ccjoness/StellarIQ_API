"""API router for indicators endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth import get_current_active_user
from app.models.user import User
from app.schemas.indicators import (
    BollingerBandsResponse,
    MACDResponse,
    MarketCondition,
    RSIResponse,
    StochResponse,
    TechnicalAnalysisSummary,
)
from app.services.market_data import MarketDataService
from app.utils.technical_analysis import TechnicalAnalyzer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/indicators", tags=["Technical Indicators"])


@router.get("/rsi/{symbol}", response_model=RSIResponse)
async def get_rsi(
    symbol: str,
    interval: Optional[str] = Query(
        "daily", description="1min, 5min, 15min, 30min, 60min, daily, weekly, monthly"
    ),
    time_period: Optional[int] = Query(
        14, description="Number of periods for RSI calculation"
    ),
    series_type: Optional[str] = Query("close", description="open, high, low, close"),
    current_user: User = Depends(get_current_active_user),
):
    """Get RSI (Relative Strength Index) indicator."""
    try:
        market_service = MarketDataService()
        data = await market_service.get_rsi(
            symbol.upper(), interval, time_period, series_type
        )

        metadata = TechnicalAnalyzer.get_indicator_metadata(data)
        rsi_data = TechnicalAnalyzer.parse_rsi_data(data)
        condition, analysis = TechnicalAnalyzer.analyze_rsi(rsi_data)

        return RSIResponse(
            symbol=metadata["symbol"],
            interval=metadata["interval"],
            time_period=int(metadata.get("time_period", time_period)),
            series_type=metadata["series_type"],
            last_refreshed=metadata["last_refreshed"],
            data=rsi_data,
            current_condition=condition,
            analysis=analysis,
        )

    except Exception as e:
        logger.error(f"Error getting RSI for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get RSI data: {str(e)}",
        )


@router.get("/macd/{symbol}", response_model=MACDResponse)
async def get_macd(
    symbol: str,
    interval: Optional[str] = Query(
        "daily", description="1min, 5min, 15min, 30min, 60min, daily, weekly, monthly"
    ),
    series_type: Optional[str] = Query("close", description="open, high, low, close"),
    current_user: User = Depends(get_current_active_user),
):
    """Get MACD (Moving Average Convergence Divergence) indicator."""
    try:
        market_service = MarketDataService()
        data = await market_service.get_macd(symbol.upper(), interval, series_type)

        metadata = TechnicalAnalyzer.get_indicator_metadata(data)
        macd_data = TechnicalAnalyzer.parse_macd_data(data)
        condition, analysis = TechnicalAnalyzer.analyze_macd(macd_data)

        return MACDResponse(
            symbol=metadata["symbol"],
            interval=metadata["interval"],
            series_type=metadata["series_type"],
            last_refreshed=metadata["last_refreshed"],
            data=macd_data,
            current_condition=condition,
            analysis=analysis,
        )

    except Exception as e:
        logger.error(f"Error getting MACD for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get MACD data: {str(e)}",
        )


@router.get("/stoch/{symbol}", response_model=StochResponse)
async def get_stochastic(
    symbol: str,
    interval: Optional[str] = Query(
        "daily", description="1min, 5min, 15min, 30min, 60min, daily, weekly, monthly"
    ),
    current_user: User = Depends(get_current_active_user),
):
    """Get Stochastic oscillator indicator."""
    try:
        market_service = MarketDataService()
        data = await market_service.get_stoch(symbol.upper(), interval)

        metadata = TechnicalAnalyzer.get_indicator_metadata(data)
        stoch_data = TechnicalAnalyzer.parse_stoch_data(data)
        condition, analysis = TechnicalAnalyzer.analyze_stoch(stoch_data)

        return StochResponse(
            symbol=metadata["symbol"],
            interval=metadata["interval"],
            last_refreshed=metadata["last_refreshed"],
            data=stoch_data,
            current_condition=condition,
            analysis=analysis,
        )

    except Exception as e:
        logger.error(f"Error getting Stochastic for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get Stochastic data: {str(e)}",
        )


@router.get("/bbands/{symbol}", response_model=BollingerBandsResponse)
async def get_bollinger_bands(
    symbol: str,
    interval: Optional[str] = Query(
        "daily", description="1min, 5min, 15min, 30min, 60min, daily, weekly, monthly"
    ),
    time_period: Optional[int] = Query(
        20, description="Number of periods for Bollinger Bands calculation"
    ),
    series_type: Optional[str] = Query("close", description="open, high, low, close"),
    current_user: User = Depends(get_current_active_user),
):
    """Get Bollinger Bands indicator."""
    try:
        market_service = MarketDataService()
        data = await market_service.get_bbands(
            symbol.upper(), interval, time_period, series_type
        )

        metadata = TechnicalAnalyzer.get_indicator_metadata(data)
        bbands_data = TechnicalAnalyzer.parse_bbands_data(data)
        condition, analysis = TechnicalAnalyzer.analyze_bbands(bbands_data)

        return BollingerBandsResponse(
            symbol=metadata["symbol"],
            interval=metadata["interval"],
            time_period=int(metadata.get("time_period", time_period)),
            series_type=metadata["series_type"],
            last_refreshed=metadata["last_refreshed"],
            data=bbands_data,
            current_condition=condition,
            analysis=analysis,
        )

    except Exception as e:
        logger.error(f"Error getting Bollinger Bands for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get Bollinger Bands data: {str(e)}",
        )


@router.get("/analysis/{symbol}", response_model=TechnicalAnalysisSummary)
async def get_technical_analysis_summary(
    symbol: str,
    interval: Optional[str] = Query("daily", description="daily, weekly, monthly"),
    current_user: User = Depends(get_current_active_user),
):
    """Get comprehensive technical analysis summary for a symbol."""
    try:
        market_service = MarketDataService()

        # Fetch all indicators
        rsi_data = await market_service.get_rsi(symbol.upper(), interval)
        macd_data = await market_service.get_macd(symbol.upper(), interval)
        stoch_data = await market_service.get_stoch(symbol.upper(), interval)
        bbands_data = await market_service.get_bbands(symbol.upper(), interval)

        # Parse and analyze each indicator
        rsi_parsed = TechnicalAnalyzer.parse_rsi_data(rsi_data)
        macd_parsed = TechnicalAnalyzer.parse_macd_data(macd_data)
        stoch_parsed = TechnicalAnalyzer.parse_stoch_data(stoch_data)
        bbands_parsed = TechnicalAnalyzer.parse_bbands_data(bbands_data)

        rsi_condition, _ = TechnicalAnalyzer.analyze_rsi(rsi_parsed)
        macd_condition, _ = TechnicalAnalyzer.analyze_macd(macd_parsed)
        stoch_condition, _ = TechnicalAnalyzer.analyze_stoch(stoch_parsed)
        bbands_condition, _ = TechnicalAnalyzer.analyze_bbands(bbands_parsed)

        # Calculate overall condition and confidence
        conditions = [rsi_condition, macd_condition, stoch_condition, bbands_condition]
        oversold_count = conditions.count(MarketCondition.OVERSOLD)
        overbought_count = conditions.count(MarketCondition.OVERBOUGHT)

        if oversold_count >= 2:
            overall_condition = MarketCondition.OVERSOLD
            confidence = oversold_count / 4
            recommendation = (
                "Consider buying - multiple indicators suggest oversold conditions"
            )
        elif overbought_count >= 2:
            overall_condition = MarketCondition.OVERBOUGHT
            confidence = overbought_count / 4
            recommendation = (
                "Consider selling - multiple indicators suggest overbought conditions"
            )
        else:
            overall_condition = MarketCondition.NEUTRAL
            confidence = 0.5
            recommendation = "Hold - mixed signals from technical indicators"

        return TechnicalAnalysisSummary(
            symbol=symbol.upper(),
            rsi_condition=rsi_condition,
            macd_condition=macd_condition,
            stoch_condition=stoch_condition,
            bbands_condition=bbands_condition,
            overall_condition=overall_condition,
            confidence_score=confidence,
            recommendation=recommendation,
        )

    except Exception as e:
        logger.error(f"Error getting technical analysis for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get technical analysis: {str(e)}",
        )
