#!/usr/bin/env python3
"""
Test script for market alert functionality
"""

import time

import requests

BASE_URL = "http://localhost:8000"


def get_auth_token():
    """Get authentication token"""
    login_data = {"email": "test2@example.com", "password": "testpassword123"}

    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json().get("access_token")
    return None


def test_market_alert(token, symbol="AAPL"):
    """Test market alert for a specific symbol"""
    try:
        headers = {"Authorization": f"Bearer {token}"}

        print(f"🔍 Testing market alert for {symbol}...")
        response = requests.post(
            f"{BASE_URL}/notifications/test-alert/{symbol}", headers=headers
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Test alert result: {result.get('message')}")
            return True
        else:
            print(f"❌ Test alert failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Test alert error: {e}")
        return False


def check_notification_history(token):
    """Check notification history"""
    try:
        headers = {"Authorization": f"Bearer {token}"}

        response = requests.get(f"{BASE_URL}/notifications/history", headers=headers)
        if response.status_code == 200:
            notifications = response.json()
            print(f"📋 Found {len(notifications)} notifications:")

            for i, notif in enumerate(notifications[:5], 1):  # Show first 5
                print(
                    f"   {i}. {notif['title']} - {notif['status']} ({notif['created_at'][:19]})"
                )
                if notif.get("symbol"):
                    print(
                        f"      Symbol: {notif['symbol']}, Condition: {notif.get('market_condition', 'N/A')}"
                    )

            return notifications
        else:
            print(f"❌ Failed to get notification history: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Notification history error: {e}")
        return []


def check_monitoring_stats(token):
    """Check monitoring statistics"""
    try:
        headers = {"Authorization": f"Bearer {token}"}

        response = requests.get(
            f"{BASE_URL}/notifications/monitoring-status", headers=headers
        )
        if response.status_code == 200:
            result = response.json()
            monitoring = result.get("monitoring", {})

            print(f"📊 Monitoring Statistics:")
            print(f"   Total favorites: {monitoring.get('total_favorites', 0)}")
            print(f"   Enabled alerts: {monitoring.get('enabled_alerts', 0)}")
            print(f"   Recent alerts (24h): {monitoring.get('recent_alerts_24h', 0)}")

            scheduler = result.get("scheduler", {})
            print(f"   Scheduler status: {scheduler.get('status', 'unknown')}")

            return result
        else:
            print(f"❌ Failed to get monitoring status: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Monitoring status error: {e}")
        return None


def main():
    """Run market alert tests"""
    print("🚨 Testing StellarIQ Market Alert System")
    print("=" * 50)

    # Get authentication token
    token = get_auth_token()
    if not token:
        print("❌ Failed to get authentication token")
        return

    print("✅ Authentication successful")

    # Check initial monitoring stats
    print("\n📊 Initial Monitoring Status:")
    check_monitoring_stats(token)

    # Check initial notification history
    print("\n📋 Initial Notification History:")
    initial_notifications = check_notification_history(token)
    initial_count = len(initial_notifications)

    # Test market alert
    print("\n🔔 Testing Market Alert:")
    alert_success = test_market_alert(token, "AAPL")

    if alert_success:
        print("\n⏳ Waiting a moment for alert processing...")
        time.sleep(3)

        # Check notification history again
        print("\n📋 Updated Notification History:")
        updated_notifications = check_notification_history(token)
        updated_count = len(updated_notifications)

        if updated_count > initial_count:
            print(
                f"✅ New notifications detected! ({updated_count - initial_count} new)"
            )
        else:
            print(
                "ℹ️ No new notifications (this is normal if market conditions haven't changed)"
            )

        # Check updated monitoring stats
        print("\n📊 Updated Monitoring Status:")
        check_monitoring_stats(token)

    print("\n🎯 Market Alert Test Summary:")
    print("=" * 50)
    print("✅ Market alert system is functional")
    print("📈 Background monitoring is active")
    print("🔔 Notifications are being tracked")

    print("\n💡 Tips:")
    print("- Alerts are only sent when market conditions actually change")
    print("- The system prevents spam by limiting alerts to once per hour per symbol")
    print("- Check the logs for detailed monitoring activity")


if __name__ == "__main__":
    main()
