from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class StockQuote(BaseModel):
    symbol: str
    open: float
    high: float
    low: float
    price: float
    volume: int
    latest_trading_day: str
    previous_close: float
    change: float
    change_percent: str


class StockSearchResult(BaseModel):
    symbol: str
    name: str
    type: str
    region: str
    market_open: str
    market_close: str
    timezone: str
    currency: str
    match_score: float


class StockSearchResponse(BaseModel):
    results: List[StockSearchResult]


class TimeSeriesData(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class StockDailyResponse(BaseModel):
    symbol: str
    last_refreshed: str
    time_zone: str
    data: List[TimeSeriesData]


class StockIntradayResponse(BaseModel):
    symbol: str
    last_refreshed: str
    interval: str
    time_zone: str
    data: List[TimeSeriesData]


class StockHistoryRequest(BaseModel):
    symbol: str
    interval: Optional[str] = "daily"  # daily, weekly, monthly, or intraday intervals
    outputsize: Optional[str] = "compact"  # compact or full


class StockQuoteRequest(BaseModel):
    symbol: str


class StockSearchRequest(BaseModel):
    keywords: str
