"""Pydantic schemas for indicators data models."""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class MarketCondition(str, Enum):

    """MarketCondition class."""

    OVERSOLD = "oversold"
    OVERBOUGHT = "overbought"
    NEUTRAL = "neutral"


class RSIData(BaseModel):

    """RSIData class."""

    timestamp: str
    rsi: float


class RSIResponse(BaseModel):

    """RSIResponse class."""

    symbol: str
    interval: str
    time_period: int
    series_type: str
    last_refreshed: str
    data: List[RSIData]
    current_condition: MarketCondition
    analysis: str


class MACDData(BaseModel):

    """MACDData class."""

    timestamp: str
    macd: float
    macd_hist: float
    macd_signal: float


class MACDResponse(BaseModel):

    """MACDResponse class."""

    symbol: str
    interval: str
    series_type: str
    last_refreshed: str
    data: List[MACDData]
    current_condition: MarketCondition
    analysis: str


class StochData(BaseModel):

    """StochData class."""

    timestamp: str
    slowk: float
    slowd: float


class StochResponse(BaseModel):

    """StochResponse class."""

    symbol: str
    interval: str
    last_refreshed: str
    data: List[StochData]
    current_condition: MarketCondition
    analysis: str


class BollingerBandsData(BaseModel):

    """BollingerBandsData class."""

    timestamp: str
    real_upper_band: float
    real_middle_band: float
    real_lower_band: float


class BollingerBandsResponse(BaseModel):

    """BollingerBandsResponse class."""

    symbol: str
    interval: str
    time_period: int
    series_type: str
    last_refreshed: str
    data: List[BollingerBandsData]
    current_condition: MarketCondition
    analysis: str


class TechnicalAnalysisSummary(BaseModel):

    """TechnicalAnalysisSummary class."""

    symbol: str
    rsi_condition: Optional[MarketCondition] = None
    macd_condition: Optional[MarketCondition] = None
    stoch_condition: Optional[MarketCondition] = None
    bbands_condition: Optional[MarketCondition] = None
    overall_condition: MarketCondition
    confidence_score: float  # 0-1 scale
    recommendation: str


class IndicatorRequest(BaseModel):

    """IndicatorRequest class."""

    symbol: str
    interval: Optional[str] = "daily"
    time_period: Optional[int] = None
    series_type: Optional[str] = "close"
