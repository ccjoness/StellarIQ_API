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
    alert_enabled: Optional[bool] = False
    alert_on_overbought: Optional[bool] = True
    alert_on_oversold: Optional[bool] = True
    alert_on_neutral: Optional[bool] = False


class FavoriteResponse(BaseModel):

    """FavoriteResponse class."""

    id: int
    symbol: str
    asset_type: AssetType
    name: Optional[str] = None
    created_at: datetime
    alert_enabled: bool
    alert_on_overbought: bool
    alert_on_oversold: bool
    alert_on_neutral: bool
    last_alert_state: Optional[str] = None
    last_alert_sent: Optional[datetime] = None

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
    alert_enabled: bool
    alert_on_overbought: bool
    alert_on_oversold: bool
    alert_on_neutral: bool
    last_alert_state: Optional[str] = None
    last_alert_sent: Optional[datetime] = None


class FavoritesListResponse(BaseModel):

    """FavoritesListResponse class."""

    favorites: List[FavoriteWithQuote]
    total_count: int


class FavoriteDelete(BaseModel):

    """FavoriteDelete class."""

    symbol: str
    asset_type: AssetType
