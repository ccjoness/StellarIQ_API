"""Notification models for tracking notification history."""

import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class NotificationType(enum.Enum):
    """Notification type enumeration."""

    MARKET_ALERT = "market_alert"
    PRICE_ALERT = "price_alert"
    SYSTEM = "system"


class NotificationStatus(enum.Enum):
    """Notification status enumeration."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    READ = "read"


class NotificationChannel(enum.Enum):
    """Notification channel enumeration."""

    PUSH = "push"
    EMAIL = "email"
    SMS = "sms"


class Notification(Base):
    """Notification history model."""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    favorite_id = Column(Integer, ForeignKey("favorites.id"), nullable=True)

    # Notification content
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    notification_type = Column(Enum(NotificationType), nullable=False)
    channel = Column(Enum(NotificationChannel), nullable=False)

    # Market alert specific data
    symbol = Column(String, nullable=True, index=True)
    market_condition = Column(
        String, nullable=True
    )  # 'overbought', 'oversold', 'neutral'
    confidence_score = Column(String, nullable=True)  # Store as string for flexibility

    # Status tracking
    status = Column(
        Enum(NotificationStatus), default=NotificationStatus.PENDING, nullable=False
    )
    sent_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="notifications")
    favorite = relationship("Favorite")

    # Index for efficient queries
    __table_args__ = ({"schema": None},)
