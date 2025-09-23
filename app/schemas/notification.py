"""Pydantic schemas for notification data models."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.models.device_token import DeviceType
from app.models.notification import (
    NotificationChannel,
    NotificationStatus,
    NotificationType,
)


class DeviceTokenCreate(BaseModel):
    """DeviceTokenCreate schema."""

    token: str
    device_type: DeviceType
    device_id: Optional[str] = None
    device_name: Optional[str] = None


class DeviceTokenResponse(BaseModel):
    """DeviceTokenResponse schema."""

    id: int
    token: str
    device_type: DeviceType
    device_id: Optional[str] = None
    device_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None

    class Config:
        """Config class."""

        from_attributes = True


class NotificationCreate(BaseModel):
    """NotificationCreate schema."""

    title: str
    body: str
    notification_type: NotificationType
    channel: NotificationChannel
    symbol: Optional[str] = None
    market_condition: Optional[str] = None
    confidence_score: Optional[str] = None


class NotificationResponse(BaseModel):
    """NotificationResponse schema."""

    id: int
    title: str
    body: str
    notification_type: NotificationType
    channel: NotificationChannel
    symbol: Optional[str] = None
    market_condition: Optional[str] = None
    confidence_score: Optional[str] = None
    status: NotificationStatus
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        """Config class."""

        from_attributes = True


class NotificationPreferencesUpdate(BaseModel):
    """NotificationPreferencesUpdate schema."""

    alert_enabled: Optional[bool] = None
    alert_on_overbought: Optional[bool] = None
    alert_on_oversold: Optional[bool] = None
    alert_on_neutral: Optional[bool] = None


class MarketAlertData(BaseModel):
    """MarketAlertData schema for market condition notifications."""

    symbol: str
    market_condition: str  # 'overbought', 'oversold', 'neutral'
    confidence_score: float
    current_price: Optional[float] = None
    previous_condition: Optional[str] = None


class NotificationSummary(BaseModel):
    """NotificationSummary schema."""

    total_notifications: int
    unread_notifications: int
    recent_notifications: List[NotificationResponse]
