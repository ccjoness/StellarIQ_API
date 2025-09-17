from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from sqlalchemy.orm import Session

from app.services.market_data import MarketDataService
from app.services.crypto_portfolio import CryptoPortfolioService
from app.schemas.crypto import (
    CryptoExchangeRate,
    CryptoDailyResponse,
    CryptoQuote,
    CryptoSearchResponse,
    CryptoSearchResult,
    CryptoOverview,
    CryptoTrendingResponse,
    CryptoPortfolioCreate,
    CryptoPortfolioUpdate,
    CryptoPortfolioResponse,
    POPULAR_CRYPTOS,
    CRYPTO_CATEGORIES
)
from app.utils.data_parser import DataParser
from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.models.user import User
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/crypto", tags=["Cryptocurrency"])

@router.get("/popular")
async def get_popular_cryptos(
    current_user: User = Depends(get_current_active_user)
):
    """Get list of popular cryptocurrency symbols."""
    return {
        "popular_cryptos": POPULAR_CRYPTOS,
        "categories": CRYPTO_CATEGORIES,
        "description": "List of popular cryptocurrency symbols supported by the API"
    }

@router.get("/categories")
async def get_crypto_categories(
    current_user: User = Depends(get_current_active_user)
):
    """Get cryptocurrency categories."""
    return {
        "categories": CRYPTO_CATEGORIES,
        "description": "Cryptocurrency symbols organized by categories"
    }

@router.get("/rate/{from_currency}")
async def get_crypto_exchange_rate(
    from_currency: str,
    to_currency: Optional[str] = Query("USD", description="Target currency (default: USD)"),
    current_user: User = Depends(get_current_active_user)
):
    """Get cryptocurrency exchange rate."""
    try:
        market_service = MarketDataService()
        data = await market_service.get_crypto_exchange_rate(
            from_currency.upper(), 
            to_currency.upper()
        )
        
        rate = DataParser.parse_crypto_exchange_rate(data)
        return rate
        
    except Exception as e:
        logger.error(f"Error getting crypto rate for {from_currency}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get crypto exchange rate: {str(e)}"
        )

@router.get("/daily/{symbol}", response_model=CryptoDailyResponse)
async def get_crypto_daily(
    symbol: str,
    market: Optional[str] = Query("USD", description="Market currency (default: USD)"),
    current_user: User = Depends(get_current_active_user)
):
    """Get daily cryptocurrency data."""
    try:
        market_service = MarketDataService()
        data = await market_service.get_crypto_daily(symbol.upper(), market.upper())
        
        metadata = DataParser.get_crypto_metadata(data)
        time_series_data = DataParser.parse_crypto_daily_data(data)
        
        return CryptoDailyResponse(
            symbol=metadata["symbol"],
            market=metadata["market"],
            last_refreshed=metadata["last_refreshed"],
            time_zone=metadata["time_zone"],
            data=time_series_data
        )
        
    except Exception as e:
        logger.error(f"Error getting crypto daily data for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get crypto daily data: {str(e)}"
        )

@router.get("/rates/multiple")
async def get_multiple_crypto_rates(
    symbols: str = Query(..., description="Comma-separated list of crypto symbols (e.g., BTC,ETH,ADA)"),
    to_currency: Optional[str] = Query("USD", description="Target currency (default: USD)"),
    current_user: User = Depends(get_current_active_user)
):
    """Get exchange rates for multiple cryptocurrencies."""
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(",")]
        if len(symbol_list) > 10:  # Limit to prevent abuse
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 10 symbols allowed per request"
            )
        
        market_service = MarketDataService()
        rates = {}
        
        for symbol in symbol_list:
            try:
                data = await market_service.get_crypto_exchange_rate(symbol, to_currency.upper())
                rate = DataParser.parse_crypto_exchange_rate(data)
                rates[symbol] = rate
            except Exception as e:
                logger.warning(f"Failed to get rate for {symbol}: {e}")
                rates[symbol] = {"error": str(e)}
        
        return {
            "rates": rates,
            "to_currency": to_currency.upper(),
            "timestamp": "now"
        }

    except Exception as e:
        logger.error(f"Error getting multiple crypto rates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get crypto rates: {str(e)}"
        )

@router.get("/intraday/{symbol}")
async def get_crypto_intraday(
    symbol: str,
    market: Optional[str] = Query("USD", description="Market currency (default: USD)"),
    interval: Optional[str] = Query("5min", description="Time interval (1min, 5min, 15min, 30min, 60min)"),
    current_user: User = Depends(get_current_active_user)
):
    """Get intraday cryptocurrency data."""
    try:
        # Validate interval
        valid_intervals = ["1min", "5min", "15min", "30min", "60min"]
        if interval not in valid_intervals:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid interval. Must be one of: {', '.join(valid_intervals)}"
            )

        market_service = MarketDataService()
        data = await market_service.get_crypto_intraday(symbol.upper(), market.upper(), interval)

        metadata = DataParser.get_crypto_metadata(data)
        time_series_data = DataParser.parse_crypto_intraday_data(data, interval)

        return {
            "symbol": metadata["symbol"],
            "market": metadata["market"],
            "interval": interval,
            "last_refreshed": metadata["last_refreshed"],
            "time_zone": metadata["time_zone"],
            "data": time_series_data
        }

    except Exception as e:
        logger.error(f"Error getting crypto intraday data for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get crypto intraday data: {str(e)}"
        )

@router.get("/weekly/{symbol}")
async def get_crypto_weekly(
    symbol: str,
    market: Optional[str] = Query("USD", description="Market currency (default: USD)"),
    current_user: User = Depends(get_current_active_user)
):
    """Get weekly cryptocurrency data."""
    try:
        market_service = MarketDataService()
        data = await market_service.get_crypto_weekly(symbol.upper(), market.upper())

        metadata = DataParser.get_crypto_metadata(data)
        time_series_data = DataParser.parse_crypto_daily_data(data)  # Same format as daily

        return {
            "symbol": metadata["symbol"],
            "market": metadata["market"],
            "timeframe": "weekly",
            "last_refreshed": metadata["last_refreshed"],
            "time_zone": metadata["time_zone"],
            "data": time_series_data
        }

    except Exception as e:
        logger.error(f"Error getting crypto weekly data for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get crypto weekly data: {str(e)}"
        )

@router.get("/monthly/{symbol}")
async def get_crypto_monthly(
    symbol: str,
    market: Optional[str] = Query("USD", description="Market currency (default: USD)"),
    current_user: User = Depends(get_current_active_user)
):
    """Get monthly cryptocurrency data."""
    try:
        market_service = MarketDataService()
        data = await market_service.get_crypto_monthly(symbol.upper(), market.upper())

        metadata = DataParser.get_crypto_metadata(data)
        time_series_data = DataParser.parse_crypto_daily_data(data)  # Same format as daily

        return {
            "symbol": metadata["symbol"],
            "market": metadata["market"],
            "timeframe": "monthly",
            "last_refreshed": metadata["last_refreshed"],
            "time_zone": metadata["time_zone"],
            "data": time_series_data
        }

    except Exception as e:
        logger.error(f"Error getting crypto monthly data for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get crypto monthly data: {str(e)}"
        )

@router.get("/quote/{symbol}")
async def get_crypto_quote(
    symbol: str,
    to_currency: Optional[str] = Query("USD", description="Target currency (default: USD)"),
    current_user: User = Depends(get_current_active_user)
):
    """Get real-time cryptocurrency quote."""
    try:
        market_service = MarketDataService()
        data = await market_service.get_crypto_exchange_rate(symbol.upper(), to_currency.upper())

        quote_data = DataParser.parse_crypto_quote(data)

        return CryptoQuote(
            symbol=quote_data["symbol"],
            name=quote_data["name"],
            price=quote_data["price"],
            last_updated=quote_data["last_updated"]
        )

    except Exception as e:
        logger.error(f"Error getting crypto quote for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get crypto quote: {str(e)}"
        )

@router.get("/search")
async def search_crypto(
    query: str = Query(..., description="Search query for cryptocurrency"),
    current_user: User = Depends(get_current_active_user)
):
    """Search for cryptocurrencies."""
    try:
        query_upper = query.upper()

        # Simple search in popular cryptos and categories
        results = []

        # Search in popular cryptos
        for symbol in POPULAR_CRYPTOS:
            if query_upper in symbol:
                results.append(CryptoSearchResult(
                    symbol=symbol,
                    name=f"{symbol} Cryptocurrency",
                    market_type="crypto"
                ))

        # Search in categories
        for category, symbols in CRYPTO_CATEGORIES.items():
            if query_upper in category.upper():
                for symbol in symbols:
                    if symbol not in [r.symbol for r in results]:
                        results.append(CryptoSearchResult(
                            symbol=symbol,
                            name=f"{symbol} Cryptocurrency",
                            market_type="crypto"
                        ))

        return CryptoSearchResponse(
            results=results[:20],  # Limit to 20 results
            total_count=len(results)
        )

    except Exception as e:
        logger.error(f"Error searching crypto: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search crypto: {str(e)}"
        )

@router.get("/trending")
async def get_trending_crypto(
    current_user: User = Depends(get_current_active_user)
):
    """Get trending cryptocurrencies (mock data for now)."""
    try:
        # For now, return popular cryptos as trending
        # In a real implementation, this would fetch from a trending API
        trending_symbols = POPULAR_CRYPTOS[:10]

        market_service = MarketDataService()
        trending_data = []

        for symbol in trending_symbols:
            try:
                data = await market_service.get_crypto_exchange_rate(symbol, "USD")
                rate = DataParser.parse_crypto_exchange_rate(data)

                overview = CryptoOverview(
                    symbol=symbol,
                    name=rate.from_currency_name,
                    current_price=rate.exchange_rate,
                    last_updated=rate.last_refreshed
                )
                trending_data.append(overview)
            except Exception as e:
                logger.warning(f"Failed to get data for trending crypto {symbol}: {e}")
                continue

        return CryptoTrendingResponse(
            trending=trending_data,
            gainers=trending_data[:5],  # Mock data
            losers=trending_data[5:10]  # Mock data
        )

    except Exception as e:
        logger.error(f"Error getting trending crypto: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trending crypto: {str(e)}"
        )

# Portfolio endpoints
@router.get("/portfolio", response_model=CryptoPortfolioResponse)
async def get_crypto_portfolio(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's crypto portfolio."""
    try:
        portfolio_service = CryptoPortfolioService(db)
        portfolio = await portfolio_service.get_user_portfolio(current_user.id)
        return portfolio

    except Exception as e:
        logger.error(f"Error getting crypto portfolio for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get crypto portfolio: {str(e)}"
        )

@router.post("/portfolio")
async def add_crypto_to_portfolio(
    portfolio_item: CryptoPortfolioCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add cryptocurrency to user's portfolio."""
    try:
        portfolio_service = CryptoPortfolioService(db)
        item = portfolio_service.add_portfolio_item(current_user.id, portfolio_item)

        return {
            "message": f"Successfully added {portfolio_item.symbol} to portfolio",
            "item": {
                "id": item.id,
                "symbol": item.symbol,
                "amount": item.amount,
                "average_buy_price": item.average_buy_price
            }
        }

    except Exception as e:
        logger.error(f"Error adding crypto to portfolio for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add crypto to portfolio: {str(e)}"
        )

@router.put("/portfolio/{symbol}")
async def update_crypto_in_portfolio(
    symbol: str,
    update_data: CryptoPortfolioUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update cryptocurrency in user's portfolio."""
    try:
        portfolio_service = CryptoPortfolioService(db)
        item = portfolio_service.update_portfolio_item(current_user.id, symbol, update_data)

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Crypto {symbol} not found in portfolio"
            )

        return {
            "message": f"Successfully updated {symbol} in portfolio",
            "item": {
                "id": item.id,
                "symbol": item.symbol,
                "amount": item.amount,
                "average_buy_price": item.average_buy_price
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating crypto in portfolio for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update crypto in portfolio: {str(e)}"
        )

@router.delete("/portfolio/{symbol}")
async def remove_crypto_from_portfolio(
    symbol: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove cryptocurrency from user's portfolio."""
    try:
        portfolio_service = CryptoPortfolioService(db)
        success = portfolio_service.remove_portfolio_item(current_user.id, symbol)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Crypto {symbol} not found in portfolio"
            )

        return {
            "message": f"Successfully removed {symbol} from portfolio"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing crypto from portfolio for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove crypto from portfolio: {str(e)}"
        )
