from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

class MarketCondition(str, Enum):
    OVERSOLD = "oversold"
    OVERBOUGHT = "overbought"
    NEUTRAL = "neutral"

class RSIData(BaseModel):
    timestamp: str
    rsi: float

class RSIResponse(BaseModel):
    symbol: str
    interval: str
    time_period: int
    series_type: str
    last_refreshed: str
    data: List[RSIData]
    current_condition: MarketCondition
    analysis: str

class MACDData(BaseModel):
    timestamp: str
    macd: float
    macd_hist: float
    macd_signal: float

class MACDResponse(BaseModel):
    symbol: str
    interval: str
    series_type: str
    last_refreshed: str
    data: List[MACDData]
    current_condition: MarketCondition
    analysis: str

class StochData(BaseModel):
    timestamp: str
    slowk: float
    slowd: float

class StochResponse(BaseModel):
    symbol: str
    interval: str
    last_refreshed: str
    data: List[StochData]
    current_condition: MarketCondition
    analysis: str

class BollingerBandsData(BaseModel):
    timestamp: str
    real_upper_band: float
    real_middle_band: float
    real_lower_band: float

class BollingerBandsResponse(BaseModel):
    symbol: str
    interval: str
    time_period: int
    series_type: str
    last_refreshed: str
    data: List[BollingerBandsData]
    current_condition: MarketCondition
    analysis: str

class TechnicalAnalysisSummary(BaseModel):
    symbol: str
    rsi_condition: Optional[MarketCondition] = None
    macd_condition: Optional[MarketCondition] = None
    stoch_condition: Optional[MarketCondition] = None
    bbands_condition: Optional[MarketCondition] = None
    overall_condition: MarketCondition
    confidence_score: float  # 0-1 scale
    recommendation: str

class IndicatorRequest(BaseModel):
    symbol: str
    interval: Optional[str] = "daily"
    time_period: Optional[int] = None
    series_type: Optional[str] = "close"
