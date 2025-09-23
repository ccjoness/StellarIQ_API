"""Notification management endpoints."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.device_token import DeviceToken
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import (
    DeviceTokenCreate,
    DeviceTokenResponse,
    NotificationResponse,
    NotificationSummary,
)
from app.services.market_monitor import MarketMonitorService
from app.services.notification import NotificationService
from app.services.scheduler import scheduler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("/device-tokens", response_model=DeviceTokenResponse)
async def register_device_token(
    token_data: DeviceTokenCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Register a device token for push notifications."""
    try:
        notification_service = NotificationService()
        device_token = await notification_service.register_device_token(
            user_id=current_user.id,
            token_data=token_data.dict(),
            db=db,
        )
        return device_token

    except Exception as e:
        logger.error(f"Failed to register device token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register device token",
        )


@router.get("/device-tokens", response_model=List[DeviceTokenResponse])
async def get_device_tokens(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all device tokens for the current user."""
    try:
        device_tokens = (
            db.query(DeviceToken).filter(DeviceToken.user_id == current_user.id).all()
        )
        return device_tokens

    except Exception as e:
        logger.error(f"Failed to get device tokens: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get device tokens",
        )


@router.delete("/device-tokens/{token_id}")
async def delete_device_token(
    token_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a device token."""
    try:
        device_token = (
            db.query(DeviceToken)
            .filter(
                DeviceToken.id == token_id,
                DeviceToken.user_id == current_user.id,
            )
            .first()
        )

        if not device_token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device token not found",
            )

        db.delete(device_token)
        db.commit()

        return {"message": "Device token deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete device token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete device token",
        )


@router.get("/history", response_model=List[NotificationResponse])
async def get_notification_history(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get notification history for the current user."""
    try:
        notification_service = NotificationService()
        notifications = await notification_service.get_notification_history(
            user_id=current_user.id,
            limit=limit,
            offset=offset,
            db=db,
        )
        return notifications

    except Exception as e:
        logger.error(f"Failed to get notification history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notification history",
        )


@router.get("/summary", response_model=NotificationSummary)
async def get_notification_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get notification summary for the current user."""
    try:
        # Get total notifications
        total_notifications = (
            db.query(Notification)
            .filter(Notification.user_id == current_user.id)
            .count()
        )

        # Get unread notifications
        unread_notifications = (
            db.query(Notification)
            .filter(
                Notification.user_id == current_user.id,
                Notification.read_at.is_(None),
            )
            .count()
        )

        # Get recent notifications (last 10)
        recent_notifications = (
            db.query(Notification)
            .filter(Notification.user_id == current_user.id)
            .order_by(Notification.created_at.desc())
            .limit(10)
            .all()
        )

        return NotificationSummary(
            total_notifications=total_notifications,
            unread_notifications=unread_notifications,
            recent_notifications=recent_notifications,
        )

    except Exception as e:
        logger.error(f"Failed to get notification summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notification summary",
        )


@router.post("/mark-read/{notification_id}")
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a notification as read."""
    try:
        notification = (
            db.query(Notification)
            .filter(
                Notification.id == notification_id,
                Notification.user_id == current_user.id,
            )
            .first()
        )

        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found",
            )

        if not notification.read_at:
            from datetime import datetime

            notification.read_at = datetime.utcnow()
            db.commit()

        return {"message": "Notification marked as read"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark notification as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read",
        )


@router.post("/test-alert/{symbol}")
async def test_market_alert(
    symbol: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Test market alert for a specific symbol (for development/testing)."""
    try:
        market_monitor = MarketMonitorService()
        success = await market_monitor.force_check_symbol(
            user_id=current_user.id,
            symbol=symbol.upper(),
            db=db,
        )

        if success:
            return {"message": f"Test alert triggered for {symbol}"}
        else:
            return {"message": f"No alert conditions met for {symbol}"}

    except Exception as e:
        logger.error(f"Failed to test market alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test market alert",
        )


@router.get("/monitoring-status")
async def get_monitoring_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get monitoring system status."""
    try:
        # Get scheduler status
        scheduler_status = scheduler.get_job_status()

        # Get monitoring stats
        market_monitor = MarketMonitorService()
        monitoring_stats = market_monitor.get_monitoring_stats(db)

        return {
            "scheduler": scheduler_status,
            "monitoring": monitoring_stats,
        }

    except Exception as e:
        logger.error(f"Failed to get monitoring status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get monitoring status",
        )


@router.post("/trigger-monitoring")
async def trigger_monitoring(
    current_user: User = Depends(get_current_user),
):
    """Manually trigger market monitoring (for testing)."""
    try:
        success = await scheduler.trigger_market_monitoring()

        if success:
            return {"message": "Market monitoring triggered successfully"}
        else:
            return {"message": "Failed to trigger market monitoring"}

    except Exception as e:
        logger.error(f"Failed to trigger monitoring: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger monitoring",
        )
