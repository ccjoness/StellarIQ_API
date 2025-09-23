#!/usr/bin/env python3
"""
Simple verification script for push notification configuration
"""

import os

import requests
from dotenv import load_dotenv

API_URL = os.getenv("API_URL", "http://localhost:8000")


def check_environment():
    """Check environment configuration"""
    print("🔧 Environment Configuration Check")
    print("=" * 40)

    # Load environment variables
    load_dotenv()

    required_vars = {
        "EXPO_ACCESS_TOKEN": "Expo access token for push notifications",
        "EXPO_PROJECT_ID": "Expo project ID",
        "ENABLE_PUSH_NOTIFICATIONS": "Enable/disable push notifications",
    }

    optional_vars = {
        "SMTP_HOST": "Email server host",
        "SMTP_USERNAME": "Email username",
        "ENABLE_EMAIL_NOTIFICATIONS": "Enable/disable email notifications",
    }

    all_good = True

    print("📋 Required Configuration:")
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            if "TOKEN" in var and len(value) > 10:
                masked_value = value[:6] + "..." + value[-4:]
                print(f"   ✅ {var}: {masked_value}")
            else:
                print(f"   ✅ {var}: {value}")
        else:
            print(f"   ❌ {var}: Not set ({description})")
            all_good = False

    print("\n📋 Optional Configuration:")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            if "PASSWORD" in var or "USERNAME" in var:
                masked_value = (
                    value[:3] + "..." + value[-2:] if len(value) > 5 else "***"
                )
                print(f"   ✅ {var}: {masked_value}")
            else:
                print(f"   ✅ {var}: {value}")
        else:
            print(f"   ⚠️  {var}: Not set ({description})")

    return all_good


def check_api_health():
    """Check if API is running"""
    try:
        url = f"{API_URL}/health"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print("✅ API is running and healthy")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ API is not accessible: {e}")
        return False


def check_notification_endpoints():
    """Check notification endpoints"""
    print("\n🔔 Notification Endpoints Check")
    print("=" * 40)

    # Try to access notification endpoints (without auth)
    endpoints = [
        "/notifications/monitoring-status",
        "/notifications/device-tokens",
        "/notifications/history",
    ]

    for endpoint in endpoints:
        try:
            url = f"{API_URL}{endpoint}"
            response = requests.get(url, timeout=5)
            # We expect 401 (unauthorized) which means the endpoint exists
            if response.status_code == 401:
                print(f"   ✅ {endpoint}: Available (requires auth)")
            elif response.status_code == 404:
                print(f"   ❌ {endpoint}: Not found")
            else:
                print(
                    f"   ⚠️  {endpoint}: Unexpected response ({response.status_code})"
                )
        except requests.exceptions.RequestException as e:
            print(f"   ❌ {endpoint}: Error - {e}")


def main():
    """Main verification function"""
    print("🔍 StellarIQ Push Notification Configuration Verification")
    print("=" * 60)

    # Check environment
    env_ok = check_environment()

    print("\n🌐 API Health Check")
    print("=" * 40)
    api_ok = check_api_health()

    if api_ok:
        check_notification_endpoints()

    # Summary
    print("\n📊 Configuration Summary")
    print("=" * 40)

    if env_ok and api_ok:
        print("✅ Push notification system is properly configured!")
        print("\n📱 Next Steps:")
        print(
            "1. Get a real Expo access token from: https://expo.dev/accounts/[username]/settings/access-tokens"
        )
        print("2. Update EXPO_ACCESS_TOKEN in your .env file")
        print("3. Run the mobile app on a physical device")
        print("4. Test push notifications with: python test_push_notifications.py")

    elif env_ok and not api_ok:
        print("⚠️  Configuration looks good, but API is not running")
        print("   Start the API with: python main.py")

    elif not env_ok and api_ok:
        print("⚠️  API is running, but environment configuration needs attention")
        print("   Update your .env file with the missing variables")

    else:
        print("❌ Both configuration and API need attention")
        print("   1. Update your .env file")
        print("   2. Start the API server")

    print("\n📚 For detailed setup instructions, see: PUSH_NOTIFICATION_SETUP.md")


if __name__ == "__main__":
    main()
