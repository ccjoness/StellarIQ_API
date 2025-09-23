#!/usr/bin/env python3
"""
Test script for real push notifications
"""

import asyncio
import json
import os
from datetime import datetime

import httpx
import requests

API_URL = os.getenv("API_URL", "http://localhost:8000")

def get_auth_token():
    """Get authentication token"""
    login_data = {"email": "test2@example.com", "password": "testpassword123"}

    response = requests.post(f"{API_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json().get("access_token")
    return None


def register_test_device_token(token):
    """Register a test device token"""
    headers = {"Authorization": f"Bearer {token}"}

    # Use a real Expo push token format for testing
    # In production, this would come from the mobile app
    test_token = "ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]"

    print("📱 To get a real device token:")
    print("1. Run the StellarIQ mobile app on a physical device")
    print("2. Allow notifications when prompted")
    print("3. The app will automatically register the device token")
    print("4. Check the API logs or database for the real token")

    real_token = input(
        f"\n📝 Enter real Expo push token (or press Enter to use test token): "
    ).strip()
    if not real_token:
        real_token = test_token
        print(f"⚠️  Using test token: {real_token}")

    token_data = {
        "token": real_token,
        "device_type": "android",
        "device_name": "Test Device",
    }

    response = requests.post(
        f"{API_URL}/notifications/device-tokens", json=token_data, headers=headers
    )
    if response.status_code in [200, 201]:
        print("✅ Device token registered successfully")
        return real_token
    else:
        print(
            f"❌ Failed to register device token: {response.status_code} - {response.text}"
        )
        return None


async def test_expo_push_api_directly(device_token):
    """Test Expo Push API directly"""
    print("\n🔍 Testing Expo Push API directly...")

    expo_token = os.getenv("EXPO_ACCESS_TOKEN")
    if not expo_token:
        print("⚠️  No EXPO_ACCESS_TOKEN found in environment")
        print("   Push notifications may still work without it for development")

    message = {
        "to": device_token,
        "title": "StellarIQ Test",
        "body": "Direct API test notification",
        "data": {"test": True, "timestamp": datetime.now().isoformat()},
        "sound": "default",
        "priority": "high",
    }

    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate",
        "Content-Type": "application/json",
    }

    if expo_token:
        headers["Authorization"] = f"Bearer {expo_token}"
        print("🔑 Using Expo access token for authentication")
    else:
        print("⚠️  No access token - using anonymous API (limited)")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://exp.host/--/api/v2/push/send",
                json=[message],
                headers=headers,
                timeout=30.0,
            )

            print(f"📡 Response Status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print(f"✅ Push API Response: {json.dumps(result, indent=2)}")

                # Check for errors
                for data in result.get("data", []):
                    if data.get("status") == "error":
                        print(f"❌ Push Error: {data.get('message')}")
                        print(f"   Details: {data.get('details', {})}")
                        return False
                    elif data.get("status") == "ok":
                        print(f"✅ Push notification sent successfully!")
                        print(f"   Receipt ID: {data.get('id')}")
                        return True
            else:
                print(f"❌ Push API Error: {response.text}")
                return False

    except Exception as e:
        print(f"❌ Error testing Expo Push API: {e}")
        return False


def test_api_notification_endpoint(token, device_token):
    """Test the API notification endpoint"""
    print("\n🔔 Testing API notification endpoint...")

    headers = {"Authorization": f"Bearer {token}"}

    # Test market alert
    response = requests.post(
        f"{API_URL}/notifications/test-alert/AAPL", headers=headers
    )
    if response.status_code == 200:
        result = response.json()
        print(f"✅ API Test Alert: {result.get('message')}")
        return True
    else:
        print(f"❌ API Test Alert failed: {response.status_code} - {response.text}")
        return False


def check_notification_history(token):
    """Check notification history"""
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(
        f"{API_URL}/notifications/history?limit=5", headers=headers
    )
    if response.status_code == 200:
        notifications = response.json()
        print(f"\n📋 Recent Notifications ({len(notifications)}):")

        for i, notif in enumerate(notifications, 1):
            status_emoji = (
                "✅"
                if notif["status"] == "sent"
                else "❌"
                if notif["status"] == "failed"
                else "⏳"
            )
            print(f"   {i}. {status_emoji} {notif['title']} - {notif['status']}")
            print(f"      {notif['body']}")
            print(f"      {notif['created_at'][:19]}")
            if notif.get("error_message"):
                print(f"      Error: {notif['error_message']}")
            print()

        return notifications
    else:
        print(f"❌ Failed to get notification history: {response.status_code}")
        return []


def check_environment_config():
    """Check environment configuration"""
    print("🔧 Environment Configuration:")

    required_vars = [
        "EXPO_ACCESS_TOKEN",
        "EXPO_PROJECT_ID",
        "ENABLE_PUSH_NOTIFICATIONS",
    ]

    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive tokens
            if "TOKEN" in var and len(value) > 10:
                masked_value = value[:6] + "..." + value[-4:]
                print(f"   ✅ {var}: {masked_value}")
            else:
                print(f"   ✅ {var}: {value}")
        else:
            print(f"   ❌ {var}: Not set")


async def main():
    """Main test function"""
    print("🧪 StellarIQ Push Notification Testing")
    print("=" * 50)

    # Check environment
    check_environment_config()

    # Get auth token
    print("\n🔐 Getting authentication token...")
    auth_token = get_auth_token()
    if not auth_token:
        print("❌ Failed to get authentication token")
        return

    print("✅ Authentication successful")

    # Register device token
    print("\n📱 Registering device token...")
    device_token = register_test_device_token(auth_token)
    if not device_token:
        return

    # Test Expo Push API directly
    if device_token.startswith("ExponentPushToken[") and not device_token.endswith(
        "xxxxxxxxxxxxxxxxxxxxxx]"
    ):
        direct_success = await test_expo_push_api_directly(device_token)
        if direct_success:
            print("✅ Direct Expo Push API test successful!")
        else:
            print("❌ Direct Expo Push API test failed")
    else:
        print("⚠️  Skipping direct API test - using placeholder token")

    # Test API endpoint
    api_success = test_api_notification_endpoint(auth_token, device_token)

    # Check notification history
    notifications = check_notification_history(auth_token)

    # Summary
    print("\n🎯 Test Summary")
    print("=" * 50)

    if device_token.startswith("ExponentPushToken[") and not device_token.endswith(
        "xxxxxxxxxxxxxxxxxxxxxx]"
    ):
        print("✅ Real device token detected")
        print("📱 Check your device for push notifications!")
    else:
        print("⚠️  Test token used - no actual notifications will be received")

    print("\n💡 Next Steps:")
    print("1. Run the mobile app on a physical device")
    print("2. Allow notifications when prompted")
    print("3. Add stocks to watchlist with alerts enabled")
    print("4. Wait for real market condition changes")
    print("5. Monitor notification history in the API")

    print("\n🔧 Troubleshooting:")
    print("- Ensure EXPO_ACCESS_TOKEN is set correctly")
    print("- Verify device token format: ExponentPushToken[...]")
    print("- Check that notifications are enabled on the device")
    print("- Test on physical device, not simulator")


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv

    load_dotenv()

    asyncio.run(main())
