#!/usr/bin/env python3
"""
Quick push notification test script for StellarIQ API.

This is a simplified script for quickly testing push notifications.
Usage examples:
    python quick_push_test.py --list-users
    python quick_push_test.py --user-id 1 --market-alert AAPL
    python quick_push_test.py --user-id 1 --custom "Test Title" "Test Message"
    python quick_push_test.py --test-expo
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime

import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pathlib

# Add the app directory to the Python path
app_path = pathlib.Path(__file__).parent.parent.resolve() / "app"
sys.path.append(str(app_path))

from app.models.device_token import DeviceToken
from app.models.user import User
from app.schemas.notification import MarketAlertData
from app.services.notification import NotificationService
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Database setup
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


async def list_users():
    """List all users with their device tokens."""
    session = SessionLocal()
    try:
        users = session.query(User).all()

        if not users:
            print("No users found in the database.")
            return

        print("\nUsers with Device Tokens:")
        print("=" * 60)

        for user in users:
            device_tokens = (
                session.query(DeviceToken)
                .filter(DeviceToken.user_id == user.id, DeviceToken.is_active == True)
                .all()
            )

            print(f"ID: {user.id} | Username: {user.username} | Email: {user.email}")
            print(f"Push Notifications: {'Enabled' if user.push_notifications else 'Disabled'}")
            print(f"Active Device Tokens: {len(device_tokens)}")

            for i, token in enumerate(device_tokens, 1):
                token_preview = token.token[:20] + "..." if len(token.token) > 20 else token.token
                print(f"  {i}. {token.device_type.value} - {token_preview}")

            print("-" * 40)

    finally:
        session.close()


async def send_market_alert(user_id: int, symbol: str):
    """Send a test market alert to a specific user."""
    session = SessionLocal()
    try:
        # Check if user exists
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            print(f"User with ID {user_id} not found.")
            return False

        print(f"Sending market alert for {symbol} to user {user.username} (ID: {user_id})")

        # Create test market alert data
        alert_data = MarketAlertData(
            symbol=symbol,
            market_condition="overbought",
            confidence_score=0.85,
            current_price=150.25,
            previous_condition="neutral"
        )

        # Send the notification (use None for favorite_id to avoid FK constraint)
        notification_service = NotificationService()
        success = await notification_service.send_market_alert(
            user_id=user_id,
            favorite_id=None,  # No favorite ID to avoid FK constraint
            alert_data=alert_data,
            db=session
        )

        if success:
            print("✓ Market alert sent successfully!")
        else:
            print("✗ Failed to send market alert")

        return success

    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        session.close()


async def send_custom_notification(user_id: int, title: str, body: str):
    """Send a custom notification to a specific user."""
    session = SessionLocal()
    try:
        # Check if user exists
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            print(f"User with ID {user_id} not found.")
            return False

        print(f"Sending custom notification to user {user.username} (ID: {user_id})")
        print(f"Title: {title}")
        print(f"Body: {body}")

        # Get user's device tokens
        device_tokens = (
            session.query(DeviceToken)
            .filter(DeviceToken.user_id == user_id, DeviceToken.is_active == True)
            .all()
        )

        if not device_tokens:
            print(f"No active device tokens found for user {user_id}")
            return False

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
        success = await send_expo_notifications(messages)

        if success:
            print("✓ Custom notification sent successfully!")
        else:
            print("✗ Failed to send custom notification")

        return success

    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        session.close()


async def send_expo_notifications(messages):
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
                print(f"Expo API Response: {json.dumps(result, indent=2)}")

                # Check for any errors in the response
                for data in result.get("data", []):
                    if data.get("status") == "error":
                        print(f"Expo push error: {data.get('message')}")
                        return False
                return True
            else:
                print(f"Expo push API error: {response.status_code} - {response.text}")
                return False

    except Exception as e:
        print(f"Failed to send Expo push notifications: {e}")
        return False


async def test_expo_connection():
    """Test connection to Expo Push API."""
    print("Testing Expo Push API connection...")

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
                print("✓ Expo API is accessible and responding correctly")
                result = response.json()

                # Check if we got the expected "DeviceNotRegistered" error for our test token
                if (result.get("data") and
                    len(result["data"]) > 0 and
                    result["data"][0].get("details", {}).get("error") == "DeviceNotRegistered"):
                    print("✓ API correctly identified test token as invalid (this is expected)")
                    print("✓ Connection test SUCCESSFUL - ready to send real notifications!")
                else:
                    print("Response details:")
                    print(f"{json.dumps(result, indent=2)}")
            else:
                print(f"✗ Expo API error: {response.text}")

    except Exception as e:
        print(f"✗ Failed to connect to Expo API: {e}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Quick push notification tester for StellarIQ")

    # Add arguments
    parser.add_argument("--list-users", action="store_true", help="List all users with device tokens")
    parser.add_argument("--user-id", type=int, help="Target user ID for notifications")
    parser.add_argument("--market-alert", type=str, help="Send market alert for specified symbol")
    parser.add_argument("--custom", nargs=2, metavar=("TITLE", "BODY"), help="Send custom notification with title and body")
    parser.add_argument("--test-expo", action="store_true", help="Test Expo API connection")

    args = parser.parse_args()

    # Check if no arguments provided
    if not any(vars(args).values()):
        parser.print_help()
        return

    async def run_commands():
        if args.list_users:
            await list_users()

        if args.test_expo:
            await test_expo_connection()

        if args.user_id:
            if args.market_alert:
                await send_market_alert(args.user_id, args.market_alert)
            elif args.custom:
                title, body = args.custom
                await send_custom_notification(args.user_id, title, body)
            else:
                print("When using --user-id, you must specify either --market-alert or --custom")

    # Run the async commands
    asyncio.run(run_commands())


if __name__ == "__main__":
    main()
