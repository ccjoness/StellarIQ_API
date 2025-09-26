#!/usr/bin/env python3
"""
Test script for push notifications in StellarIQ API.

This script allows you to test push notifications to specific users by:
1. Listing all users and their device tokens
2. Sending test notifications to selected users
3. Testing different notification types (market alerts, general notifications)
4. Verifying notification delivery status

Usage:
    python test_push_notifications.py
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import List, Optional

import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

from app.core.database import Base
from app.models.device_token import DeviceToken, DeviceType
from app.models.notification import Notification, NotificationChannel, NotificationStatus, NotificationType
from app.models.user import User
from app.schemas.notification import MarketAlertData
from app.services.notification import NotificationService
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database setup
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class PushNotificationTester:
    """Test class for push notifications."""

    def __init__(self):
        self.notification_service = NotificationService()
        self.session = SessionLocal()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def list_users_with_tokens(self) -> List[dict]:
        """List all users with their device tokens."""
        users = self.session.query(User).all()
        user_data = []

        for user in users:
            device_tokens = (
                self.session.query(DeviceToken)
                .filter(DeviceToken.user_id == user.id, DeviceToken.is_active == True)
                .all()
            )

            user_info = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "push_notifications_enabled": user.push_notifications,
                "device_tokens": [
                    {
                        "id": token.id,
                        "token": token.token[:20] + "..." if len(token.token) > 20 else token.token,
                        "device_type": token.device_type.value,
                        "device_name": token.device_name,
                        "last_used": token.last_used_at.isoformat() if token.last_used_at else None,
                        "created_at": token.created_at.isoformat()
                    }
                    for token in device_tokens
                ]
            }
            user_data.append(user_info)

        return user_data

    def display_users(self):
        """Display all users with their device tokens in a formatted way."""
        users = self.list_users_with_tokens()

        if not users:
            print("No users found in the database.")
            return

        print("\n" + "="*80)
        print("USERS WITH DEVICE TOKENS")
        print("="*80)

        for user in users:
            print(f"\nUser ID: {user['id']}")
            print(f"Username: {user['username']}")
            print(f"Email: {user['email']}")
            print(f"Push Notifications: {'Enabled' if user['push_notifications_enabled'] else 'Disabled'}")

            if user['device_tokens']:
                print(f"Device Tokens ({len(user['device_tokens'])}):")
                for i, token in enumerate(user['device_tokens'], 1):
                    print(f"  {i}. Type: {token['device_type']}")
                    print(f"     Token: {token['token']}")
                    print(f"     Device: {token['device_name'] or 'Unknown'}")
                    print(f"     Created: {token['created_at']}")
                    if token['last_used']:
                        print(f"     Last Used: {token['last_used']}")
            else:
                print("No active device tokens")

            print("-" * 40)

    async def send_test_market_alert(self, user_id: int, symbol: str = "AAPL") -> bool:
        """Send a test market alert notification to a specific user."""
        try:
            # Create test market alert data
            alert_data = MarketAlertData(
                symbol=symbol,
                market_condition="overbought",
                confidence_score=0.85,
                current_price=150.25,
                previous_condition="neutral"
            )

            # Send the notification
            success = await self.notification_service.send_market_alert(
                user_id=user_id,
                favorite_id=1,  # Mock favorite ID
                alert_data=alert_data,
                db=self.session
            )

            if success:
                logger.info(f"Test market alert sent successfully to user {user_id}")
            else:
                logger.error(f"Failed to send test market alert to user {user_id}")

            return success

        except Exception as e:
            logger.error(f"Error sending test market alert: {e}")
            return False

    async def send_custom_notification(
        self,
        user_id: int,
        title: str,
        body: str,
        notification_type: NotificationType = NotificationType.MARKET_ALERT
    ) -> bool:
        """Send a custom notification to a specific user."""
        try:
            # Get user's device tokens
            device_tokens = (
                self.session.query(DeviceToken)
                .filter(DeviceToken.user_id == user_id, DeviceToken.is_active == True)
                .all()
            )

            if not device_tokens:
                logger.warning(f"No active device tokens found for user {user_id}")
                return False

            # Create notification record
            notification = Notification(
                user_id=user_id,
                title=title,
                body=body,
                notification_type=notification_type,
                channel=NotificationChannel.PUSH,
                status=NotificationStatus.PENDING,
            )
            self.session.add(notification)
            self.session.commit()

            # Prepare messages for Expo
            messages = []
            for token in device_tokens:
                messages.append({
                    "to": token.token,
                    "title": title,
                    "body": body,
                    "data": {
                        "type": "custom_test",
                        "timestamp": datetime.now().isoformat()
                    },
                    "sound": "default",
                    "priority": "high",
                })

            # Send to Expo Push API
            success = await self._send_expo_notifications(messages)

            # Update notification status
            notification.status = (
                NotificationStatus.SENT if success else NotificationStatus.FAILED
            )
            if success:
                notification.sent_at = datetime.now()

            self.session.commit()

            if success:
                logger.info(f"Custom notification sent successfully to user {user_id}")
            else:
                logger.error(f"Failed to send custom notification to user {user_id}")

            return success

        except Exception as e:
            logger.error(f"Error sending custom notification: {e}")
            return False

    async def _send_expo_notifications(self, messages: List[dict]) -> bool:
        """Send notifications via Expo Push API."""
        try:
            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate",
                "Content-Type": "application/json",
            }

            # Add authorization header if access token is available
            expo_access_token = os.getenv("EXPO_ACCESS_TOKEN")
            if expo_access_token:
                headers["Authorization"] = f"Bearer {expo_access_token}"

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://exp.host/--/api/v2/push/send",
                    json=messages,
                    headers=headers,
                )

                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Expo API Response: {json.dumps(result, indent=2)}")

                    # Check for any errors in the response
                    for data in result.get("data", []):
                        if data.get("status") == "error":
                            logger.error(f"Expo push error: {data.get('message')}")
                            return False
                    return True
                else:
                    logger.error(f"Expo push API error: {response.status_code} - {response.text}")
                    return False

        except Exception as e:
            logger.error(f"Failed to send Expo push notifications: {e}")
            return False

    def get_notification_history(self, user_id: Optional[int] = None, limit: int = 10) -> List[dict]:
        """Get recent notification history."""
        query = self.session.query(Notification)

        if user_id:
            query = query.filter(Notification.user_id == user_id)

        notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()

        return [
            {
                "id": notif.id,
                "user_id": notif.user_id,
                "title": notif.title,
                "body": notif.body,
                "type": notif.notification_type.value,
                "channel": notif.channel.value,
                "status": notif.status.value,
                "created_at": notif.created_at.isoformat(),
                "sent_at": notif.sent_at.isoformat() if notif.sent_at else None,
                "symbol": notif.symbol,
                "market_condition": notif.market_condition
            }
            for notif in notifications
        ]


def print_menu():
    """Print the main menu."""
    print("\n" + "="*60)
    print("STELLARIQ PUSH NOTIFICATION TESTER")
    print("="*60)
    print("1. List all users with device tokens")
    print("2. Send test market alert to user")
    print("3. Send custom notification to user")
    print("4. View notification history")
    print("5. Test Expo API connection")
    print("6. Exit")
    print("-" * 60)


async def test_expo_connection():
    """Test connection to Expo Push API."""
    try:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        expo_access_token = os.getenv("EXPO_ACCESS_TOKEN")
        if expo_access_token:
            headers["Authorization"] = f"Bearer {expo_access_token}"
            print("✓ Expo access token found")
        else:
            print("⚠ No Expo access token found (EXPO_ACCESS_TOKEN env var)")

        # Test with a dummy message to check API connectivity
        test_message = [{
            "to": "ExponentPushToken[test]",
            "title": "Test",
            "body": "Connection test"
        }]

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://exp.host/--/api/v2/push/send",
                json=test_message,
                headers=headers,
            )

            print(f"Expo API Status: {response.status_code}")
            if response.status_code == 200:
                print("✓ Expo API is accessible")
                result = response.json()
                print(f"Response: {json.dumps(result, indent=2)}")
            else:
                print(f"✗ Expo API error: {response.text}")

    except Exception as e:
        print(f"✗ Failed to connect to Expo API: {e}")


async def main():
    """Main function to run the notification tester."""
    print("Initializing StellarIQ Push Notification Tester...")

    # Check environment variables
    required_env_vars = ["DATABASE_URL"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]

    if missing_vars:
        print(f"Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables and try again.")
        return

    try:
        with PushNotificationTester() as tester:
            while True:
                print_menu()
                choice = input("Enter your choice (1-6): ").strip()

                if choice == "1":
                    tester.display_users()

                elif choice == "2":
                    user_id = input("Enter user ID: ").strip()
                    symbol = input("Enter symbol (default: AAPL): ").strip() or "AAPL"

                    try:
                        user_id = int(user_id)
                        print(f"Sending test market alert for {symbol} to user {user_id}...")
                        success = await tester.send_test_market_alert(user_id, symbol)
                        if success:
                            print("✓ Test market alert sent successfully!")
                        else:
                            print("✗ Failed to send test market alert")
                    except ValueError:
                        print("Invalid user ID. Please enter a number.")

                elif choice == "3":
                    user_id = input("Enter user ID: ").strip()
                    title = input("Enter notification title: ").strip()
                    body = input("Enter notification body: ").strip()

                    try:
                        user_id = int(user_id)
                        if title and body:
                            print(f"Sending custom notification to user {user_id}...")
                            success = await tester.send_custom_notification(user_id, title, body)
                            if success:
                                print("✓ Custom notification sent successfully!")
                            else:
                                print("✗ Failed to send custom notification")
                        else:
                            print("Title and body are required.")
                    except ValueError:
                        print("Invalid user ID. Please enter a number.")

                elif choice == "4":
                    user_id_input = input("Enter user ID (or press Enter for all users): ").strip()
                    limit_input = input("Enter limit (default: 10): ").strip()

                    user_id = None
                    if user_id_input:
                        try:
                            user_id = int(user_id_input)
                        except ValueError:
                            print("Invalid user ID. Showing all users.")

                    limit = 10
                    if limit_input:
                        try:
                            limit = int(limit_input)
                        except ValueError:
                            print("Invalid limit. Using default (10).")

                    history = tester.get_notification_history(user_id, limit)

                    if history:
                        print(f"\nRecent Notifications ({len(history)}):")
                        print("-" * 80)
                        for notif in history:
                            print(f"ID: {notif['id']} | User: {notif['user_id']} | Status: {notif['status']}")
                            print(f"Title: {notif['title']}")
                            print(f"Body: {notif['body']}")
                            print(f"Type: {notif['type']} | Channel: {notif['channel']}")
                            print(f"Created: {notif['created_at']}")
                            if notif['sent_at']:
                                print(f"Sent: {notif['sent_at']}")
                            print("-" * 40)
                    else:
                        print("No notifications found.")

                elif choice == "5":
                    print("Testing Expo API connection...")
                    await test_expo_connection()

                elif choice == "6":
                    print("Goodbye!")
                    break

                else:
                    print("Invalid choice. Please try again.")

                input("\nPress Enter to continue...")

    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main())
