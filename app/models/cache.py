"""Cache model for storing API responses."""

from sqlalchemy import Column, DateTime, Index, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class CacheEntry(Base):
    """Cache entry model for storing API responses."""

    __tablename__ = "cache_entries"

    id = Column(Integer, primary_key=True, index=True)
    cache_key = Column(String, unique=True, index=True, nullable=False)
    data = Column(Text, nullable=False)  # JSON data stored as text
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Index for efficient cleanup of expired entries
    __table_args__ = (Index("idx_cache_expires_at", "expires_at"),)
