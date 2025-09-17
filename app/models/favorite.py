from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class AssetType(enum.Enum):
    STOCK = "stock"
    CRYPTO = "crypto"

class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String, nullable=False, index=True)
    asset_type = Column(Enum(AssetType), nullable=False)
    name = Column(String, nullable=True)  # Company/crypto name
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="favorites")

    # Ensure unique favorite per user per symbol
    __table_args__ = (
        {"schema": None},
    )
