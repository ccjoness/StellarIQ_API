"""Business logic service for favorites operations."""

import logging
from typing import List

from fastapi import HTTPException, status
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.favorite import AssetType, Favorite
from app.schemas.favorite import FavoriteCreate, FavoriteWithQuote
from app.services.market_data import MarketDataService
from app.utils.data_parser import DataParser

logger = logging.getLogger(__name__)


class FavoritesService:

    """FavoritesService class."""

    def __init__(self, db: Session):
        self.db = db
        self.market_service = MarketDataService()

    def add_favorite(self, user_id: int, favorite_data: FavoriteCreate) -> Favorite:
        """Add a symbol to user's favorites."""
        # Check if already exists
        existing = (
            self.db.query(Favorite)
            .filter(
                and_(
                    Favorite.user_id == user_id,
                    Favorite.symbol == favorite_data.symbol.upper(),
                    Favorite.asset_type == favorite_data.asset_type,
                )
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{favorite_data.symbol} is already in your favorites",
            )

        # Create new favorite
        db_favorite = Favorite(
            user_id=user_id,
            symbol=favorite_data.symbol.upper(),
            asset_type=favorite_data.asset_type,
            name=favorite_data.name,
            # Market condition alerts
            alert_enabled=favorite_data.alert_enabled or False,
            alert_on_overbought=favorite_data.alert_on_overbought or True,
            alert_on_oversold=favorite_data.alert_on_oversold or True,
            alert_on_neutral=favorite_data.alert_on_neutral or False,
            # Price alerts
            price_alert_enabled=favorite_data.price_alert_enabled or False,
            alert_price_above=favorite_data.alert_price_above,
            alert_price_below=favorite_data.alert_price_below,
        )

        self.db.add(db_favorite)
        self.db.commit()
        self.db.refresh(db_favorite)
        return db_favorite

    def remove_favorite(self, user_id: int, symbol: str, asset_type: AssetType) -> bool:
        """Remove a symbol from user's favorites."""
        favorite = (
            self.db.query(Favorite)
            .filter(
                and_(
                    Favorite.user_id == user_id,
                    Favorite.symbol == symbol.upper(),
                    Favorite.asset_type == asset_type,
                )
            )
            .first()
        )

        if not favorite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{symbol} not found in your favorites",
            )

        self.db.delete(favorite)
        self.db.commit()
        return True

    def get_user_favorites(self, user_id: int) -> List[Favorite]:
        """Get all favorites for a user."""
        return self.db.query(Favorite).filter(Favorite.user_id == user_id).all()

    async def get_favorites_with_quotes(self, user_id: int) -> List[FavoriteWithQuote]:
        """Get user favorites with current market data."""
        favorites = self.get_user_favorites(user_id)
        favorites_with_quotes = []

        for favorite in favorites:
            favorite_with_quote = FavoriteWithQuote(
                id=favorite.id,
                symbol=favorite.symbol,
                asset_type=favorite.asset_type,
                name=favorite.name,
                created_at=favorite.created_at,
                # Market condition alerts
                alert_enabled=favorite.alert_enabled,
                alert_on_overbought=favorite.alert_on_overbought,
                alert_on_oversold=favorite.alert_on_oversold,
                alert_on_neutral=favorite.alert_on_neutral,
                last_alert_state=favorite.last_alert_state,
                last_alert_sent=favorite.last_alert_sent,
                # Price alerts
                price_alert_enabled=favorite.price_alert_enabled,
                alert_price_above=favorite.alert_price_above,
                alert_price_below=favorite.alert_price_below,
                last_price_alert_sent=favorite.last_price_alert_sent,
            )

            try:
                if favorite.asset_type == AssetType.STOCK:
                    # Get stock quote
                    quote_data = await self.market_service.get_stock_quote(
                        favorite.symbol
                    )
                    quote = DataParser.parse_stock_quote(quote_data)

                    favorite_with_quote.current_price = quote.price
                    favorite_with_quote.change = quote.change
                    favorite_with_quote.change_percent = quote.change_percent
                    favorite_with_quote.last_updated = quote.latest_trading_day

                elif favorite.asset_type == AssetType.CRYPTO:
                    # Get crypto exchange rate
                    rate_data = await self.market_service.get_crypto_exchange_rate(
                        favorite.symbol, "USD"
                    )
                    rate = DataParser.parse_crypto_exchange_rate(rate_data)

                    favorite_with_quote.current_price = rate.exchange_rate
                    favorite_with_quote.last_updated = rate.last_refreshed
                    # Note: Crypto exchange rate doesn't provide change data directly

            except Exception as e:
                logger.warning(f"Failed to get quote for {favorite.symbol}: {e}")
                # Continue without quote data

            favorites_with_quotes.append(favorite_with_quote)

        return favorites_with_quotes

    def is_favorite(self, user_id: int, symbol: str, asset_type: AssetType) -> bool:
        """Check if a symbol is in user's favorites."""
        favorite = (
            self.db.query(Favorite)
            .filter(
                and_(
                    Favorite.user_id == user_id,
                    Favorite.symbol == symbol.upper(),
                    Favorite.asset_type == asset_type,
                )
            )
            .first()
        )

        return favorite is not None

    def get_favorites_by_type(
        self, user_id: int, asset_type: AssetType
    ) -> List[Favorite]:
        """Get user favorites filtered by asset type."""
        return (
            self.db.query(Favorite)
            .filter(
                and_(Favorite.user_id == user_id, Favorite.asset_type == asset_type)
            )
            .all()
        )

    def get_favorite_count(self, user_id: int) -> int:
        """Get total count of user's favorites."""
        return self.db.query(Favorite).filter(Favorite.user_id == user_id).count()
