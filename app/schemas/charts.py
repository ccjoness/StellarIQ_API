"""Pydantic schemas for charts data models."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class CandlestickData(BaseModel):

    """CandlestickData class."""

    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class LineChartData(BaseModel):

    """LineChartData class."""

    timestamp: str
    value: float


class TechnicalIndicatorOverlay(BaseModel):

    """TechnicalIndicatorOverlay class."""

    rsi: Optional[List[LineChartData]] = None
    macd: Optional[List[LineChartData]] = None
    macd_signal: Optional[List[LineChartData]] = None
    macd_histogram: Optional[List[LineChartData]] = None
    stoch_k: Optional[List[LineChartData]] = None
    stoch_d: Optional[List[LineChartData]] = None
    bb_upper: Optional[List[LineChartData]] = None
    bb_middle: Optional[List[LineChartData]] = None
    bb_lower: Optional[List[LineChartData]] = None


class ChartDataResponse(BaseModel):

    """ChartDataResponse class."""

    symbol: str
    interval: str
    last_refreshed: str
    time_zone: str
    candlestick_data: List[CandlestickData]
    indicators: Optional[TechnicalIndicatorOverlay] = None
    metadata: Dict[str, Any]


class ChartRequest(BaseModel):

    """ChartRequest class."""

    symbol: str
    interval: Optional[
        str
    ] = "daily"  # 1min, 5min, 15min, 30min, 60min, daily, weekly, monthly
    outputsize: Optional[str] = "compact"  # compact or full
    include_indicators: Optional[bool] = True
    indicators: Optional[List[str]] = [
        "rsi",
        "macd",
        "bbands",
    ]  # Which indicators to include


class MultiSymbolChartData(BaseModel):

    """MultiSymbolChartData class."""

    symbols: List[str]
    chart_data: Dict[str, ChartDataResponse]


class PriceComparisonData(BaseModel):

    """PriceComparisonData class."""

    timestamp: str
    prices: Dict[str, float]  # symbol -> price


class ComparisonChartResponse(BaseModel):

    """ComparisonChartResponse class."""

    symbols: List[str]
    interval: str
    data: List[PriceComparisonData]
    base_date: str
    normalized: bool = False  # Whether prices are normalized to percentage change
