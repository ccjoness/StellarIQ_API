"""API router for favorites endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.models.favorite import AssetType
from app.models.user import User
from app.schemas.favorite import (
    FavoriteCreate,
    FavoriteResponse,
    FavoritesListResponse,
    FavoriteWithQuote,
)
from app.schemas.notification import NotificationPreferencesUpdate
from app.services.favorites import FavoritesService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/favorites", tags=["Favorites"])


@router.post("/", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
async def add_favorite(
    favorite_data: FavoriteCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Add a symbol to user's favorites."""
    try:
        favorites_service = FavoritesService(db)
        favorite = favorites_service.add_favorite(current_user.id, favorite_data)
        return favorite

    except Exception as e:
        logger.error(f"Error adding favorite: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add favorite: {str(e)}",
        )


@router.delete("/{symbol}")
async def remove_favorite(
    symbol: str,
    asset_type: AssetType = Query(..., description="Asset type: stock or crypto"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Remove a symbol from user's favorites."""
    try:
        favorites_service = FavoritesService(db)
        favorites_service.remove_favorite(current_user.id, symbol, asset_type)
        return {"message": f"{symbol} removed from favorites"}

    except Exception as e:
        logger.error(f"Error removing favorite: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove favorite: {str(e)}",
        )


@router.get("/", response_model=FavoritesListResponse)
async def get_favorites(
    include_quotes: Optional[bool] = Query(
        True, description="Include current market quotes"
    ),
    asset_type: Optional[AssetType] = Query(None, description="Filter by asset type"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get user's favorite symbols with optional market data."""
    try:
        favorites_service = FavoritesService(db)

        if include_quotes:
            if asset_type:
                # Get favorites by type, then fetch quotes
                favorites = favorites_service.get_favorites_by_type(
                    current_user.id, asset_type
                )
                favorites_with_quotes = []

                for favorite in favorites:
                    favorite_with_quote = FavoriteWithQuote(
                        id=favorite.id,
                        symbol=favorite.symbol,
                        asset_type=favorite.asset_type,
                        name=favorite.name,
                        created_at=favorite.created_at,
                    )
                    favorites_with_quotes.append(favorite_with_quote)

                # Note: For simplicity, not fetching quotes for filtered results
                # In production, you might want to fetch quotes for filtered results too
            else:
                favorites_with_quotes = (
                    await favorites_service.get_favorites_with_quotes(current_user.id)
                )
        else:
            # Get favorites without quotes
            if asset_type:
                favorites = favorites_service.get_favorites_by_type(
                    current_user.id, asset_type
                )
            else:
                favorites = favorites_service.get_user_favorites(current_user.id)

            favorites_with_quotes = [
                FavoriteWithQuote(
                    id=fav.id,
                    symbol=fav.symbol,
                    asset_type=fav.asset_type,
                    name=fav.name,
                    created_at=fav.created_at,
                )
                for fav in favorites
            ]

        return FavoritesListResponse(
            favorites=favorites_with_quotes, total_count=len(favorites_with_quotes)
        )

    except Exception as e:
        logger.error(f"Error getting favorites: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get favorites: {str(e)}",
        )


@router.get("/check/{symbol}")
async def check_favorite(
    symbol: str,
    asset_type: AssetType = Query(..., description="Asset type: stock or crypto"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Check if a symbol is in user's favorites."""
    try:
        favorites_service = FavoritesService(db)
        is_favorite = favorites_service.is_favorite(current_user.id, symbol, asset_type)

        return {
            "symbol": symbol.upper(),
            "asset_type": asset_type,
            "is_favorite": is_favorite,
        }

    except Exception as e:
        logger.error(f"Error checking favorite: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check favorite: {str(e)}",
        )


@router.get("/stats")
async def get_favorites_stats(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """Get user's favorites statistics."""
    try:
        favorites_service = FavoritesService(db)

        total_count = favorites_service.get_favorite_count(current_user.id)
        stock_count = len(
            favorites_service.get_favorites_by_type(current_user.id, AssetType.STOCK)
        )
        crypto_count = len(
            favorites_service.get_favorites_by_type(current_user.id, AssetType.CRYPTO)
        )

        return {
            "total_favorites": total_count,
            "stock_favorites": stock_count,
            "crypto_favorites": crypto_count,
        }

    except Exception as e:
        logger.error(f"Error getting favorites stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get favorites stats: {str(e)}",
        )


@router.put("/{favorite_id}/notifications", response_model=FavoriteResponse)
async def update_notification_preferences(
    favorite_id: int,
    preferences: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update notification preferences for a favorite."""
    try:
        from app.models.favorite import Favorite

        # Get the favorite and verify ownership
        favorite = (
            db.query(Favorite)
            .filter(Favorite.id == favorite_id, Favorite.user_id == current_user.id)
            .first()
        )

        if not favorite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Favorite not found",
            )

        # Update notification preferences
        if preferences.alert_enabled is not None:
            favorite.alert_enabled = preferences.alert_enabled
        if preferences.alert_on_overbought is not None:
            favorite.alert_on_overbought = preferences.alert_on_overbought
        if preferences.alert_on_oversold is not None:
            favorite.alert_on_oversold = preferences.alert_on_oversold
        if preferences.alert_on_neutral is not None:
            favorite.alert_on_neutral = preferences.alert_on_neutral

        db.commit()
        db.refresh(favorite)

        return favorite

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating notification preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update notification preferences: {str(e)}",
        )
