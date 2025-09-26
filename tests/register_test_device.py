#!/usr/bin/env python3
"""
Script to register a test device token for push notification testing.

This script manually adds a test device token to a user's account
so you can test push notifications without needing the mobile app.
"""

import os
import sys
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pathlib

# Add the parent directory to the Python path
parent_path = pathlib.Path(__file__).parent.parent.resolve()
sys.path.append(str(parent_path))

from app.models.device_token import DeviceToken, DeviceType
from app.models.user import User
from config import settings

# Database setup
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def register_test_device_token(user_id: int, device_type: str = "ios"):
    """Register a test device token for a user."""
    session = SessionLocal()
    try:
        # Check if user exists
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            print(f"❌ User with ID {user_id} not found.")
            return False

        print(f"👤 Found user: {user.username} ({user.email})")

        # Generate a test Expo push token
        # Note: This is a valid format but won't actually receive notifications
        # For real testing, you'd need a token from an actual device
        test_token = f"ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx-test-{user_id}]"

        # Check if this user already has a device token
        existing_token = (
            session.query(DeviceToken)
            .filter(DeviceToken.user_id == user_id, DeviceToken.is_active == True)
            .first()
        )

        if existing_token:
            print(
                f"⚠️  User already has an active device token: {existing_token.token[:30]}..."
            )
            choice = input("Replace existing token? (y/n): ").lower().strip()
            if choice != "y":
                print("Cancelled.")
                return False

            # Deactivate existing token
            existing_token.is_active = False
            print("🔄 Deactivated existing token")

        # Create new device token
        device_token = DeviceToken(
            user_id=user_id,
            token=test_token,
            device_type=DeviceType.IOS
            if device_type.lower() == "ios"
            else DeviceType.ANDROID,
            device_id=f"test-device-{user_id}",
            device_name=f"Test {device_type.upper()} Device",
            is_active=True,
            last_used_at=datetime.now(),
        )

        session.add(device_token)
        session.commit()

        print(f"✅ Successfully registered test device token for {user.username}")
        print(f"📱 Device Type: {device_type.upper()}")
        print(f"🔑 Token: {test_token[:30]}...")
        print(f"📅 Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return True

    except Exception as e:
        print(f"❌ Error registering device token: {e}")
        session.rollback()
        return False
    finally:
        session.close()


def list_users():
    """List all users for selection."""
    session = SessionLocal()
    try:
        users = session.query(User).all()

        if not users:
            print("No users found in the database.")
            return

        print("\n📋 Available Users:")
        print("=" * 60)

        for user in users:
            device_count = (
                session.query(DeviceToken)
                .filter(DeviceToken.user_id == user.id, DeviceToken.is_active == True)
                .count()
            )

            print(f"ID: {user.id} | {user.username} | {user.email}")
            print(
                f"Push Notifications: {'✅ Enabled' if user.push_notifications else '❌ Disabled'}"
            )
            print(f"Active Devices: {device_count}")
            print("-" * 40)

    finally:
        session.close()


def main():
    """Main function."""
    print("🔧 StellarIQ Test Device Token Registration")
    print("=" * 50)

    # List available users
    list_users()

    # Get user input
    try:
        user_id = int(input("\n👤 Enter User ID to register test device: ").strip())
        device_type = (
            input("📱 Enter device type (ios/android) [default: ios]: ").strip() or "ios"
        )

        if device_type.lower() not in ["ios", "android"]:
            print("❌ Invalid device type. Use 'ios' or 'android'.")
            return

        # Register the test device
        success = register_test_device_token(user_id, device_type)

        if success:
            print("\n🎉 Test device registered successfully!")
            print("\n🚀 You can now test push notifications with:")
            print(
                f'   python quick_push_test.py --user-id {user_id} --custom "Test" "Hello World!"'
            )
            print(
                f"   python quick_push_test.py --user-id {user_id} --market-alert AAPL"
            )

    except ValueError:
        print("❌ Invalid user ID. Please enter a number.")
    except KeyboardInterrupt:
        print("\n👋 Cancelled by user.")


if __name__ == "__main__":
    main()
