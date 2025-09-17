"""Pydantic schemas for crypto data models."""

from typing import List, Optional

from pydantic import BaseModel, Field


class CryptoExchangeRate(BaseModel):

    """CryptoExchangeRate class."""

    from_currency_code: str
    from_currency_name: str
    to_currency_code: str
    to_currency_name: str
    exchange_rate: float
    last_refreshed: str
    time_zone: str
    bid_price: Optional[float] = None
    ask_price: Optional[float] = None


class CryptoTimeSeriesData(BaseModel):

    """CryptoTimeSeriesData class."""

    timestamp: str
    open_usd: float
    high_usd: float
    low_usd: float
    close_usd: float
    volume: float
    market_cap_usd: float


class CryptoDailyResponse(BaseModel):

    """CryptoDailyResponse class."""

    symbol: str
    market: str
    last_refreshed: str
    time_zone: str
    data: List[CryptoTimeSeriesData]


class CryptoRateRequest(BaseModel):

    """CryptoRateRequest class."""

    from_currency: str
    to_currency: Optional[str] = "USD"


class CryptoDailyRequest(BaseModel):

    """CryptoDailyRequest class."""

    symbol: str
    market: Optional[str] = "USD"


class CryptoQuote(BaseModel):
    """Real-time crypto quote data"""

    symbol: str
    name: str
    price: float
    change_24h: Optional[float] = None
    change_percent_24h: Optional[float] = None
    volume_24h: Optional[float] = None
    market_cap: Optional[float] = None
    last_updated: str


class CryptoSearchResult(BaseModel):
    """Crypto search result"""

    symbol: str
    name: str
    market_type: str = "crypto"
    exchange: Optional[str] = None


class CryptoSearchResponse(BaseModel):
    """Crypto search response"""

    results: List[CryptoSearchResult]
    total_count: int


class CryptoOverview(BaseModel):
    """Crypto market overview"""

    symbol: str
    name: str
    current_price: float
    market_cap: Optional[float] = None
    market_cap_rank: Optional[int] = None
    volume_24h: Optional[float] = None
    price_change_24h: Optional[float] = None
    price_change_percentage_24h: Optional[float] = None
    circulating_supply: Optional[float] = None
    total_supply: Optional[float] = None
    max_supply: Optional[float] = None
    last_updated: str


class CryptoTrendingResponse(BaseModel):
    """Trending cryptocurrencies response"""

    trending: List[CryptoOverview]
    gainers: List[CryptoOverview]
    losers: List[CryptoOverview]


class CryptoPortfolioItem(BaseModel):
    """Crypto portfolio item"""

    symbol: str
    name: str
    amount: float = Field(..., gt=0, description="Amount of crypto owned")
    average_buy_price: Optional[float] = Field(
        None, gt=0, description="Average purchase price"
    )
    current_price: Optional[float] = None
    total_value: Optional[float] = None
    profit_loss: Optional[float] = None
    profit_loss_percentage: Optional[float] = None


class CryptoPortfolioCreate(BaseModel):
    """Create crypto portfolio item"""

    symbol: str = Field(..., min_length=1, max_length=10)
    amount: float = Field(..., gt=0)
    average_buy_price: Optional[float] = Field(None, gt=0)


class CryptoPortfolioUpdate(BaseModel):
    """Update crypto portfolio item"""

    amount: Optional[float] = Field(None, gt=0)
    average_buy_price: Optional[float] = Field(None, gt=0)


class CryptoPortfolioResponse(BaseModel):
    """Crypto portfolio response"""

    portfolio: List[CryptoPortfolioItem]
    total_value: float
    total_profit_loss: float
    total_profit_loss_percentage: float


# Common cryptocurrency symbols for reference
POPULAR_CRYPTOS = [
    "BTC",
    "ETH",
    "BNB",
    "XRP",
    "ADA",
    "SOL",
    "DOGE",
    "DOT",
    "AVAX",
    "SHIB",
    "MATIC",
    "LTC",
    "UNI",
    "LINK",
    "ATOM",
    "XLM",
    "BCH",
    "ALGO",
    "VET",
    "ICP",
    "NEAR",
    "FTM",
    "SAND",
    "MANA",
    "CRO",
    "LRC",
    "ENJ",
    "BAT",
    "ZEC",
    "DASH",
]

# Crypto categories for better organization
CRYPTO_CATEGORIES = {
    "major": ["BTC", "ETH", "BNB", "XRP", "ADA", "SOL", "DOT", "AVAX"],
    "defi": ["UNI", "LINK", "AAVE", "COMP", "MKR", "SNX", "CRV", "YFI"],
    "gaming": ["SAND", "MANA", "ENJ", "AXS", "GALA", "ILV"],
    "layer1": ["BTC", "ETH", "ADA", "SOL", "DOT", "AVAX", "NEAR", "ATOM"],
    "meme": ["DOGE", "SHIB", "FLOKI", "PEPE"],
    "privacy": ["XMR", "ZEC", "DASH", "ZCASH"],
}
