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


class TrendingStock(BaseModel):

    """TrendingStock class."""

    ticker: str
    name: Optional[str] = None
    price: float
    change_amount: float
    change_percentage: float
    volume_humanized: str
    volume: int


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
    metadata: str
    last_updated: str
    trending: List[TrendingStock]
    gainers: List[TrendingStock]
    losers: List[TrendingStock]


class StockPopularResponse(BaseModel):
    """Response for popular stocks."""

    popular_stocks: List[str]
    categories: dict
    description: str

class StockCompanyInfo(BaseModel):
    """Company information for a stock."""

    symbol: str
    asset_type: str
    name: str
    description: str
    cik: str
    exchange: str
    currency: str
    country: str
    sector: str
    industry: str
    address: str
    official_site: str
    fiscal_year_end: str
    latest_quarter: str
    market_capitalization: str
    ebitda: str
    pe_ratio: str
    peg_ratio: str
    book_value: str
    dividend_per_share: str
    dividend_yield: str
    eps: str
    revenue_per_share_ttm: str
    profit_margin: str
    operating_margin_ttm: str
    return_on_assets_ttm: str
    return_on_equity_ttm: str
    revenue_ttm: str
    gross_profit_ttm: str
    diluted_epsttm: str
    quarterly_earnings_growth_yoy: str
    quarterly_revenue_growth_yoy: str
    analyst_target_price: str
    analyst_rating_strong_buy: str
    analyst_rating_buy: str
    analyst_rating_hold: str
    analyst_rating_sell: str
    analyst_rating_strong_sell: str
    trailing_pe: str
    forward_pe: str
    price_to_sales_ratio_ttm: str
    price_to_book_ratio: str
    evto_revenue: str
    evto_ebitda: str
    beta: str
    week_high_52: str
    week_low_52: str
    day_moving_average_50: str
    day_moving_average_200: str
    shares_outstanding: str
    shares_float: str
    percent_insiders: str
    percent_institutions: str
    dividend_date: str
    ex_dividend_date: str



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
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "TSLA",
    "META",
    "NVDA",
    "NFLX",
    "JPM",
    "JNJ",
    "PG",
    "UNH",
    "HD",
    "V",
    "MA",
    "DIS",
    "PYPL",
    "ADBE",
    "CRM",
    "NFLX",
    "INTC",
    "CSCO",
    "PEP",
    "KO",
    "WMT",
    "MCD",
    "NKE",
    "BA",
    "CAT",
    "GE",
    "XOM",
    "CVX",
    "PFE",
    "MRK",
    "ABBV",
]
