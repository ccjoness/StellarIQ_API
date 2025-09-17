"""Pydantic schemas for favorite data models."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.models.favorite import AssetType


class FavoriteCreate(BaseModel):

    """FavoriteCreate class."""

    symbol: str
    asset_type: AssetType
    name: Optional[str] = None


class FavoriteResponse(BaseModel):

    """FavoriteResponse class."""

    id: int
    symbol: str
    asset_type: AssetType
    name: Optional[str] = None
    created_at: datetime

    class Config:
        """Config class."""

        from_attributes = True


class FavoriteWithQuote(BaseModel):

    """FavoriteWithQuote class."""

    id: int
    symbol: str
    asset_type: AssetType
    name: Optional[str] = None
    created_at: datetime
    current_price: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[str] = None
    last_updated: Optional[str] = None


class FavoritesListResponse(BaseModel):

    """FavoritesListResponse class."""

    favorites: List[FavoriteWithQuote]
    total_count: int


class FavoriteDelete(BaseModel):

    """FavoriteDelete class."""

    symbol: str
    asset_type: AssetType
