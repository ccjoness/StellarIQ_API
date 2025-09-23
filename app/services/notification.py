"""Notification service for sending push notifications and emails."""

import json
import logging
import os
from datetime import datetime
from typing import List, Optional

import httpx
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.device_token import DeviceToken
from app.models.notification import (
    Notification,
    NotificationChannel,
    NotificationStatus,
    NotificationType,
)
from app.models.user import User
from app.schemas.notification import MarketAlertData, NotificationCreate
from app.services.email import EmailService

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications via various channels."""

    def __init__(self):
        self.email_service = EmailService()
        self.expo_access_token = os.getenv("EXPO_ACCESS_TOKEN")
        self.expo_project_id = os.getenv("EXPO_PROJECT_ID")
        self.enable_push_notifications = (
            os.getenv("ENABLE_PUSH_NOTIFICATIONS", "true").lower() == "true"
        )
        self.enable_email_notifications = (
            os.getenv("ENABLE_EMAIL_NOTIFICATIONS", "true").lower() == "true"
        )

    async def send_market_alert(
        self,
        user_id: int,
        favorite_id: int,
        alert_data: MarketAlertData,
        db: Session,
    ) -> bool:
        """Send market alert notification to user via all enabled channels."""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.error(f"User {user_id} not found")
                return False

            success = True

            # Send push notification if enabled
            if user.push_notifications and self.enable_push_notifications:
                push_success = await self._send_push_notification(
                    user_id, favorite_id, alert_data, db
                )
                success = success and push_success

            # Send email notification if enabled
            if user.email_notifications:
                email_success = await self._send_email_notification(
                    user, favorite_id, alert_data, db
                )
                success = success and email_success

            return success

        except Exception as e:
            logger.error(f"Failed to send market alert for user {user_id}: {e}")
            return False

    async def _send_push_notification(
        self,
        user_id: int,
        favorite_id: int,
        alert_data: MarketAlertData,
        db: Session,
    ) -> bool:
        """Send push notification via Expo."""
        try:
            # Get active device tokens for user
            device_tokens = (
                db.query(DeviceToken)
                .filter(DeviceToken.user_id == user_id, DeviceToken.is_active == True)
                .all()
            )

            if not device_tokens:
                logger.warning(f"No active device tokens found for user {user_id}")
                return True  # Not an error, just no devices to notify

            # Create notification record
            title = f"{alert_data.symbol} Market Alert"
            body = self._format_alert_message(alert_data)

            notification = Notification(
                user_id=user_id,
                favorite_id=favorite_id,
                title=title,
                body=body,
                notification_type=NotificationType.MARKET_ALERT,
                channel=NotificationChannel.PUSH,
                symbol=alert_data.symbol,
                market_condition=alert_data.market_condition,
                confidence_score=str(alert_data.confidence_score),
                status=NotificationStatus.PENDING,
            )
            db.add(notification)
            db.commit()

            # Send to Expo Push API
            success = await self._send_expo_push_notifications(
                device_tokens, title, body, alert_data
            )

            # Update notification status
            notification.status = (
                NotificationStatus.SENT if success else NotificationStatus.FAILED
            )
            notification.sent_at = datetime.utcnow() if success else None
            if not success:
                notification.error_message = "Failed to send push notification"
            db.commit()

            return success

        except Exception as e:
            logger.error(f"Failed to send push notification: {e}")
            return False

    async def _send_email_notification(
        self,
        user: User,
        favorite_id: int,
        alert_data: MarketAlertData,
        db: Session,
    ) -> bool:
        """Send email notification."""
        try:
            # Create notification record
            title = f"{alert_data.symbol} Market Alert"
            body = self._format_alert_message(alert_data, include_details=True)

            notification = Notification(
                user_id=user.id,
                favorite_id=favorite_id,
                title=title,
                body=body,
                notification_type=NotificationType.MARKET_ALERT,
                channel=NotificationChannel.EMAIL,
                symbol=alert_data.symbol,
                market_condition=alert_data.market_condition,
                confidence_score=str(alert_data.confidence_score),
                status=NotificationStatus.PENDING,
            )
            db.add(notification)
            db.commit()

            # Send email
            success = self.email_service.send_market_alert_email(
                user.email, title, body, alert_data
            )

            # Update notification status
            notification.status = (
                NotificationStatus.SENT if success else NotificationStatus.FAILED
            )
            notification.sent_at = datetime.utcnow() if success else None
            if not success:
                notification.error_message = "Failed to send email notification"
            db.commit()

            return success

        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False

    async def _send_expo_push_notifications(
        self,
        device_tokens: List[DeviceToken],
        title: str,
        body: str,
        alert_data: MarketAlertData,
    ) -> bool:
        """Send push notifications via Expo Push API."""
        try:
            # Prepare messages for Expo
            messages = []
            for token in device_tokens:
                messages.append(
                    {
                        "to": token.token,
                        "title": title,
                        "body": body,
                        "data": {
                            "symbol": alert_data.symbol,
                            "market_condition": alert_data.market_condition,
                            "confidence_score": alert_data.confidence_score,
                            "type": "market_alert",
                        },
                        "sound": "default",
                        "priority": "high",
                    }
                )

            # Send to Expo Push API
            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate",
                "Content-Type": "application/json",
            }

            # Add authorization header if access token is available
            if self.expo_access_token:
                headers["Authorization"] = f"Bearer {self.expo_access_token}"

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://exp.host/--/api/v2/push/send",
                    json=messages,
                    headers=headers,
                )

                if response.status_code == 200:
                    result = response.json()
                    # Check for any errors in the response
                    for data in result.get("data", []):
                        if data.get("status") == "error":
                            logger.error(f"Expo push error: {data.get('message')}")
                            return False
                    return True
                else:
                    logger.error(
                        f"Expo push API error: {response.status_code} - {response.text}"
                    )
                    return False

        except Exception as e:
            logger.error(f"Failed to send Expo push notifications: {e}")
            return False

    def _format_alert_message(
        self, alert_data: MarketAlertData, include_details: bool = False
    ) -> str:
        """Format alert message for notifications."""
        condition_text = {
            "overbought": "is showing overbought signals",
            "oversold": "is showing oversold signals",
            "neutral": "has returned to neutral conditions",
        }.get(
            alert_data.market_condition,
            f"condition changed to {alert_data.market_condition}",
        )

        message = f"{alert_data.symbol} {condition_text}"

        if include_details:
            message += f" (Confidence: {alert_data.confidence_score:.1%})"
            if alert_data.current_price:
                message += f" at ${alert_data.current_price:.2f}"

        return message

    async def register_device_token(
        self,
        user_id: int,
        token_data: dict,
        db: Session,
    ) -> DeviceToken:
        """Register or update device token for push notifications."""
        try:
            # Check if token already exists
            existing_token = (
                db.query(DeviceToken)
                .filter(
                    DeviceToken.user_id == user_id,
                    DeviceToken.token == token_data["token"],
                )
                .first()
            )

            if existing_token:
                # Update existing token
                existing_token.is_active = True
                existing_token.last_used_at = datetime.utcnow()
                existing_token.device_name = token_data.get(
                    "device_name", existing_token.device_name
                )
                db.commit()
                return existing_token
            else:
                # Create new token
                device_token = DeviceToken(
                    user_id=user_id,
                    token=token_data["token"],
                    device_type=token_data["device_type"],
                    device_id=token_data.get("device_id"),
                    device_name=token_data.get("device_name"),
                    is_active=True,
                    last_used_at=datetime.utcnow(),
                )
                db.add(device_token)
                db.commit()
                return device_token

        except Exception as e:
            logger.error(f"Failed to register device token: {e}")
            raise

    async def get_notification_history(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        db: Session = None,
    ) -> List[Notification]:
        """Get notification history for user."""
        try:
            notifications = (
                db.query(Notification)
                .filter(Notification.user_id == user_id)
                .order_by(Notification.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            return notifications

        except Exception as e:
            logger.error(f"Failed to get notification history: {e}")
            return []
