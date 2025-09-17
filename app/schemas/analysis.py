from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from app.schemas.indicators import MarketCondition


class AnalysisThresholds(BaseModel):
    rsi_overbought: float = 70.0
    rsi_oversold: float = 30.0
    stoch_overbought: float = 80.0
    stoch_oversold: float = 20.0
    # MACD and Bollinger Bands use signal crossovers, not fixed thresholds


class IndicatorSignal(BaseModel):
    indicator: str
    condition: MarketCondition
    value: float
    signal_strength: float  # 0-1 scale
    description: str


class MarketAnalysisResult(BaseModel):
    symbol: str
    asset_type: str
    analysis_timestamp: datetime
    current_price: Optional[float] = None
    signals: List[IndicatorSignal]
    overall_condition: MarketCondition
    confidence_score: float  # 0-1 scale
    recommendation: str
    risk_level: str  # "low", "medium", "high"
    thresholds_used: AnalysisThresholds


class BulkAnalysisRequest(BaseModel):
    symbols: List[str]
    asset_type: str = "stock"  # "stock" or "crypto"
    thresholds: Optional[AnalysisThresholds] = None


class BulkAnalysisResponse(BaseModel):
    results: List[MarketAnalysisResult]
    summary: Dict[str, int]  # Count of overbought, oversold, neutral
    analysis_timestamp: datetime


class WatchlistAnalysis(BaseModel):
    user_id: int
    total_favorites: int
    overbought_count: int
    oversold_count: int
    neutral_count: int
    top_opportunities: List[MarketAnalysisResult]  # Top oversold stocks
    top_risks: List[MarketAnalysisResult]  # Top overbought stocks


class MarketScreenerRequest(BaseModel):
    condition: MarketCondition
    min_confidence: Optional[float] = 0.6
    asset_type: Optional[str] = "stock"
    limit: Optional[int] = 20


class ScreenerResult(BaseModel):
    symbol: str
    name: Optional[str] = None
    condition: MarketCondition
    confidence_score: float
    current_price: Optional[float] = None
    change_percent: Optional[str] = None
    key_signals: List[str]
