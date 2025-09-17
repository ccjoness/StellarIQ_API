# Crypto API Documentation

## Overview

The StellarIQ Crypto API provides comprehensive cryptocurrency data and portfolio management functionality. All endpoints require authentication via Bearer token.

## Base URL
```
http://localhost:8000/crypto
```

## Authentication
All endpoints require a valid JWT token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### 1. Popular Cryptocurrencies
**GET** `/popular`

Get list of popular cryptocurrency symbols with categories.

**Response:**
```json
{
  "popular_cryptos": ["BTC", "ETH", "BNB", ...],
  "categories": {
    "major": ["BTC", "ETH", "BNB", "XRP", "ADA", "SOL", "DOT", "AVAX"],
    "defi": ["UNI", "LINK", "AAVE", "COMP", "MKR", "SNX", "CRV", "YFI"],
    "gaming": ["SAND", "MANA", "ENJ", "AXS", "GALA", "ILV"],
    "layer1": ["BTC", "ETH", "ADA", "SOL", "DOT", "AVAX", "NEAR", "ATOM"],
    "meme": ["DOGE", "SHIB", "FLOKI", "PEPE"],
    "privacy": ["XMR", "ZEC", "DASH", "ZCASH"]
  },
  "description": "List of popular cryptocurrency symbols supported by the API"
}
```

### 2. Crypto Categories
**GET** `/categories`

Get cryptocurrency symbols organized by categories.

### 3. Exchange Rate
**GET** `/rate/{from_currency}?to_currency=USD`

Get cryptocurrency exchange rate.

**Parameters:**
- `from_currency` (path): Source cryptocurrency symbol (e.g., BTC)
- `to_currency` (query, optional): Target currency (default: USD)

**Response:**
```json
{
  "from_currency_code": "BTC",
  "from_currency_name": "Bitcoin",
  "to_currency_code": "USD",
  "to_currency_name": "United States Dollar",
  "exchange_rate": 116524.25,
  "last_refreshed": "2025-09-17 03:45:30",
  "time_zone": "UTC",
  "bid_price": 116520.00,
  "ask_price": 116528.50
}
```

### 4. Multiple Exchange Rates
**GET** `/rates/multiple?symbols=BTC,ETH,ADA&to_currency=USD`

Get exchange rates for multiple cryptocurrencies.

**Parameters:**
- `symbols` (query): Comma-separated list of crypto symbols (max 10)
- `to_currency` (query, optional): Target currency (default: USD)

### 5. Real-time Quote
**GET** `/quote/{symbol}?to_currency=USD`

Get real-time cryptocurrency quote.

**Response:**
```json
{
  "symbol": "BTC",
  "name": "Bitcoin",
  "price": 116524.25,
  "change_24h": null,
  "change_percent_24h": null,
  "volume_24h": null,
  "market_cap": null,
  "last_updated": "2025-09-17 03:45:30"
}
```

### 6. Daily Data
**GET** `/daily/{symbol}?market=USD`

Get daily cryptocurrency historical data.

**Parameters:**
- `symbol` (path): Cryptocurrency symbol
- `market` (query, optional): Market currency (default: USD)

### 7. Intraday Data
**GET** `/intraday/{symbol}?market=USD&interval=5min`

Get intraday cryptocurrency data.

**Parameters:**
- `symbol` (path): Cryptocurrency symbol
- `market` (query, optional): Market currency (default: USD)
- `interval` (query, optional): Time interval (1min, 5min, 15min, 30min, 60min)

### 8. Weekly Data
**GET** `/weekly/{symbol}?market=USD`

Get weekly cryptocurrency historical data.

### 9. Monthly Data
**GET** `/monthly/{symbol}?market=USD`

Get monthly cryptocurrency historical data.

### 10. Search
**GET** `/search?query=BTC`

Search for cryptocurrencies.

**Parameters:**
- `query` (query): Search query

**Response:**
```json
{
  "results": [
    {
      "symbol": "BTC",
      "name": "BTC Cryptocurrency",
      "market_type": "crypto",
      "exchange": null
    }
  ],
  "total_count": 1
}
```

### 11. Trending
**GET** `/trending`

Get trending cryptocurrencies.

**Response:**
```json
{
  "trending": [...],
  "gainers": [...],
  "losers": [...]
}
```

## Portfolio Management

### 12. Get Portfolio
**GET** `/portfolio`

Get user's crypto portfolio with current prices and profit/loss calculations.

**Response:**
```json
{
  "portfolio": [
    {
      "symbol": "BTC",
      "name": "BTC",
      "amount": 0.5,
      "average_buy_price": 50000.0,
      "current_price": 116524.25,
      "total_value": 58262.125,
      "profit_loss": 33262.125,
      "profit_loss_percentage": 133.0485
    }
  ],
  "total_value": 58262.125,
  "total_profit_loss": 33262.125,
  "total_profit_loss_percentage": 133.0485
}
```

### 13. Add to Portfolio
**POST** `/portfolio`

Add cryptocurrency to user's portfolio.

**Request Body:**
```json
{
  "symbol": "BTC",
  "amount": 0.5,
  "average_buy_price": 50000.0
}
```

### 14. Update Portfolio Item
**PUT** `/portfolio/{symbol}`

Update cryptocurrency in user's portfolio.

**Request Body:**
```json
{
  "amount": 1.0,
  "average_buy_price": 55000.0
}
```

### 15. Remove from Portfolio
**DELETE** `/portfolio/{symbol}`

Remove cryptocurrency from user's portfolio.

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `401`: Unauthorized (invalid/missing token)
- `404`: Not Found
- `500`: Internal Server Error

Error responses include a detail message:
```json
{
  "detail": "Error description"
}
```

## Rate Limiting

The API implements rate limiting based on the Alpha Vantage API limits:
- Free tier: 5 calls per minute
- Premium tier: 75 calls per minute

## Caching

All market data is cached to improve performance and reduce API calls:
- Exchange rates: 30 seconds
- Daily/weekly/monthly data: 5 minutes
- Search results: 5 minutes

## Data Sources

- **Alpha Vantage API**: Primary data source for real-time and historical cryptocurrency data
- **Internal Database**: Portfolio management and user data
