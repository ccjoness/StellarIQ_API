"""User model for authentication and user management."""

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    """User model for authentication and user management."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Refresh token fields
    refresh_token = Column(Text, nullable=True)
    refresh_token_expires_at = Column(DateTime(timezone=True), nullable=True)

    # Password reset fields
    password_reset_token = Column(Text, nullable=True)
    password_reset_expires_at = Column(DateTime(timezone=True), nullable=True)

    # Educational disclaimer agreement
    agreed_to_disclaimer = Column(Boolean, default=False, nullable=False)
    disclaimer_agreed_at = Column(DateTime(timezone=True), nullable=True)

    # Profile fields
    full_name = Column(String, nullable=True)
    timezone = Column(String, default="UTC", nullable=False)
    preferred_currency = Column(String, default="USD", nullable=False)
    email_notifications = Column(Boolean, default=True, nullable=False)
    push_notifications = Column(Boolean, default=True, nullable=False)

    # Relationships
    favorites = relationship(
        "Favorite", back_populates="user", cascade="all, delete-orphan"
    )
    device_tokens = relationship(
        "DeviceToken", back_populates="user", cascade="all, delete-orphan"
    )
    notifications = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )
