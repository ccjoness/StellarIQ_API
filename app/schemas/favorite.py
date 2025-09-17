from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.models.favorite import AssetType


class FavoriteCreate(BaseModel):
    symbol: str
    asset_type: AssetType
    name: Optional[str] = None


class FavoriteResponse(BaseModel):
    id: int
    symbol: str
    asset_type: AssetType
    name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FavoriteWithQuote(BaseModel):
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
    favorites: List[FavoriteWithQuote]
    total_count: int


class FavoriteDelete(BaseModel):
    symbol: str
    asset_type: AssetType
