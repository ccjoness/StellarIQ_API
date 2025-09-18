"""Pydantic schemas for stock data models."""

from typing import List, Optional

from pydantic import BaseModel


class StockQuote(BaseModel):

    """StockQuote class."""

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

    """StockSearchResult class."""

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

    """StockSearchResponse class."""

    results: List[StockSearchResult]


class TimeSeriesData(BaseModel):

    """TimeSeriesData class."""

    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class StockDailyResponse(BaseModel):

    """StockDailyResponse class."""

    symbol: str
    last_refreshed: str
    time_zone: str
    data: List[TimeSeriesData]


class StockIntradayResponse(BaseModel):

    """StockIntradayResponse class."""

    symbol: str
    last_refreshed: str
    interval: str
    time_zone: str
    data: List[TimeSeriesData]


class StockHistoryRequest(BaseModel):

    """StockHistoryRequest class."""

    symbol: str
    interval: Optional[str] = "daily"  # daily, weekly, monthly, or intraday intervals
    outputsize: Optional[str] = "compact"  # compact or full


class StockQuoteRequest(BaseModel):

    """StockQuoteRequest class."""

    symbol: str


class StockSearchRequest(BaseModel):

    """StockSearchRequest class."""

    keywords: str


class StockOverview(BaseModel):
    """Stock overview for trending and popular lists."""

    symbol: str
    name: str
    current_price: float
    change_24h: Optional[float] = None
    change_percent_24h: Optional[float] = None
    volume_24h: Optional[int] = None
    market_cap: Optional[float] = None
    exchange: Optional[str] = None


class StockTrendingResponse(BaseModel):
    """Response for trending stocks."""

    trending: List[StockOverview]
    gainers: List[StockOverview]
    losers: List[StockOverview]


class StockPopularResponse(BaseModel):
    """Response for popular stocks."""

    popular_stocks: List[str]
    categories: dict
    description: str


# Stock categories organized by sector
STOCK_CATEGORIES = {
    "technology": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "NFLX"],
    "healthcare": ["JNJ", "PFE", "UNH", "ABBV", "TMO", "DHR", "BMY", "MRK"],
    "financial": ["JPM", "BAC", "WFC", "GS", "MS", "C", "AXP", "BLK"],
    "energy": ["XOM", "CVX", "COP", "EOG", "SLB", "PSX", "VLO", "MPC"],
    "consumer": ["PG", "KO", "PEP", "WMT", "HD", "MCD", "NKE", "SBUX"],
    "industrial": ["BA", "CAT", "GE", "MMM", "HON", "UPS", "LMT", "RTX"],
    "utilities": ["NEE", "DUK", "SO", "D", "AEP", "EXC", "XEL", "SRE"],
    "materials": ["LIN", "APD", "ECL", "SHW", "FCX", "NEM", "DOW", "DD"],
    "realestate": ["AMT", "PLD", "CCI", "EQIX", "PSA", "SPG", "O", "WELL"],
    "communication": ["VZ", "T", "TMUS", "CHTR", "CMCSA", "DIS", "NFLX", "GOOGL"],
}

# Popular stock symbols for reference
POPULAR_STOCKS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX",
    "JPM", "JNJ", "PG", "UNH", "HD", "V", "MA", "DIS", "PYPL", "ADBE",
    "CRM", "NFLX", "INTC", "CSCO", "PEP", "KO", "WMT", "MCD", "NKE",
    "BA", "CAT", "GE", "XOM", "CVX", "PFE", "MRK", "ABBV"
]
