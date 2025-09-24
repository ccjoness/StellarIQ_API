"""Favorite model for user's favorite assets."""

import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class AssetType(enum.Enum):
    """Asset type enumeration."""

    STOCK = "stock"
    CRYPTO = "crypto"


class Favorite(Base):
    """Favorite asset model."""

    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String, nullable=False, index=True)
    asset_type = Column(Enum(AssetType), nullable=False)
    name = Column(String, nullable=True)  # Company/crypto name
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Market condition notification preferences
    alert_enabled = Column(Boolean, default=False, nullable=False)
    alert_on_overbought = Column(Boolean, default=True, nullable=False)
    alert_on_oversold = Column(Boolean, default=True, nullable=False)
    alert_on_neutral = Column(Boolean, default=False, nullable=False)

    # Price alert preferences
    price_alert_enabled = Column(Boolean, default=False, nullable=False)
    alert_price_above = Column(
        Float, nullable=True
    )  # Alert when price goes above this value
    alert_price_below = Column(
        Float, nullable=True
    )  # Alert when price goes below this value

    # Last alert tracking to prevent spam
    last_alert_state = Column(
        String, nullable=True
    )  # 'overbought', 'oversold', 'neutral'
    last_alert_sent = Column(DateTime(timezone=True), nullable=True)
    last_price_alert_sent = Column(
        DateTime(timezone=True), nullable=True
    )  # Track last price alert

    # Relationships
    user = relationship("User", back_populates="favorites")

    # Ensure unique favorite per user per symbol
    __table_args__ = ({"schema": None},)
