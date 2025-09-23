"""Device token model for push notifications."""

import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class DeviceType(enum.Enum):
    """Device type enumeration."""

    IOS = "ios"
    ANDROID = "android"
    WEB = "web"


class DeviceToken(Base):
    """Device token model for push notifications."""

    __tablename__ = "device_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String, nullable=False, index=True)
    device_type = Column(Enum(DeviceType), nullable=False)
    device_id = Column(String, nullable=True)  # Unique device identifier
    device_name = Column(String, nullable=True)  # User-friendly device name
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="device_tokens")

    # Ensure unique token per user
    __table_args__ = ({"schema": None},)
