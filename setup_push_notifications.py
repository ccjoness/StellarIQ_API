#!/usr/bin/env python3
"""
Setup script for configuring real push notifications in StellarIQ
"""

import os
import subprocess
import sys
from pathlib import Path


def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_step(step_num, title):
    """Print a formatted step"""
    print(f"\n📋 Step {step_num}: {title}")
    print("-" * 40)


def check_expo_cli():
    """Check if Expo CLI is installed"""
    try:
        result = subprocess.run(
            ["npx", "expo", "--version"], capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"✅ Expo CLI found: {result.stdout.strip()}")
            return True
        else:
            print("❌ Expo CLI not found")
            return False
    except FileNotFoundError:
        print("❌ Node.js/npm not found")
        return False


def get_expo_project_info():
    """Get Expo project information"""
    mobile_dir = Path("../StellarIQ_Mobile")
    if not mobile_dir.exists():
        print("❌ StellarIQ_Mobile directory not found")
        return None

    app_json_path = mobile_dir / "app.json"
    if not app_json_path.exists():
        print("❌ app.json not found in mobile project")
        return None

    try:
        import json

        with open(app_json_path, "r") as f:
            app_config = json.load(f)

        expo_config = app_config.get("expo", {})
        project_id = expo_config.get("extra", {}).get("eas", {}).get("projectId")
        slug = expo_config.get("slug")

        print(f"📱 Project Slug: {slug}")
        print(f"🆔 Project ID: {project_id}")

        return {"slug": slug, "project_id": project_id, "config": expo_config}
    except Exception as e:
        print(f"❌ Error reading app.json: {e}")
        return None


def setup_expo_account():
    """Guide user through Expo account setup"""
    print("🔐 Expo Account Setup")
    print(
        "\n1. If you don't have an Expo account, create one at: https://expo.dev/signup"
    )
    print("2. Login to your Expo account:")

    try:
        result = subprocess.run(["npx", "expo", "login"], cwd="../StellarIQ_Mobile")
        if result.returncode == 0:
            print("✅ Successfully logged in to Expo")
            return True
        else:
            print("❌ Failed to login to Expo")
            return False
    except Exception as e:
        print(f"❌ Error during Expo login: {e}")
        return False


def get_expo_access_token():
    """Guide user to get Expo access token"""
    print("🔑 Getting Expo Access Token")
    print(
        "\n1. Go to: https://expo.dev/accounts/[your-username]/settings/access-tokens"
    )
    print("2. Click 'Create Token'")
    print("3. Give it a name like 'StellarIQ Push Notifications'")
    print("4. Copy the generated token")

    token = input("\n📝 Paste your Expo access token here: ").strip()
    if token:
        print("✅ Access token received")
        return token
    else:
        print("❌ No token provided")
        return None


def update_env_file(expo_token, project_id):
    """Update the .env file with Expo configuration"""
    env_path = Path(".env")

    try:
        # Read current .env file
        env_content = ""
        if env_path.exists():
            with open(env_path, "r") as f:
                env_content = f.read()

        # Update or add Expo configuration
        lines = env_content.split("\n")
        updated_lines = []
        token_updated = False
        project_updated = False

        for line in lines:
            if line.startswith("EXPO_ACCESS_TOKEN="):
                updated_lines.append(f"EXPO_ACCESS_TOKEN={expo_token}")
                token_updated = True
            elif line.startswith("EXPO_PROJECT_ID="):
                updated_lines.append(f"EXPO_PROJECT_ID={project_id}")
                project_updated = True
            else:
                updated_lines.append(line)

        # Add missing configuration
        if not token_updated:
            updated_lines.append(f"EXPO_ACCESS_TOKEN={expo_token}")
        if not project_updated:
            updated_lines.append(f"EXPO_PROJECT_ID={project_id}")

        # Write back to file
        with open(env_path, "w") as f:
            f.write("\n".join(updated_lines))

        print("✅ .env file updated with Expo configuration")
        return True

    except Exception as e:
        print(f"❌ Error updating .env file: {e}")
        return False


def setup_firebase_credentials():
    """Guide user through Firebase setup for Android push notifications"""
    print("🔥 Firebase Setup (for Android)")
    print("\n1. Go to: https://console.firebase.google.com/")
    print("2. Create a new project or select existing one")
    print("3. Add an Android app with package name: com.stellariq.app")
    print("4. Download google-services.json")
    print("5. Place it in: StellarIQ_Mobile/android/app/google-services.json")

    firebase_path = Path("../StellarIQ_Mobile/android/app/google-services.json")
    if firebase_path.exists():
        print("✅ google-services.json found")
        return True
    else:
        print(
            "⚠️  google-services.json not found - Android push notifications may not work"
        )
        return False


def setup_apns_credentials():
    """Guide user through APNs setup for iOS push notifications"""
    print("🍎 Apple Push Notification Service (APNs) Setup")
    print("\n1. Go to: https://developer.apple.com/account/resources/certificates/list")
    print("2. Create a new certificate for 'Apple Push Notification service SSL'")
    print("3. Download the certificate and convert to .p8 format")
    print(
        "4. Upload to Expo: https://expo.dev/accounts/[your-username]/projects/stellariq/credentials"
    )

    print(
        "⚠️  iOS push notifications require Apple Developer Program membership ($99/year)"
    )
    return True


def test_push_notifications():
    """Test push notification setup"""
    print("🧪 Testing Push Notifications")
    print("\n1. Start the StellarIQ API server")
    print("2. Run the mobile app on a physical device")
    print("3. Register for notifications in the app")
    print("4. Add a stock to your watchlist with alerts enabled")
    print("5. Use the test alert endpoint to verify notifications work")

    test_choice = input(
        "\nWould you like to run the notification test script? (y/n): "
    ).lower()
    if test_choice == "y":
        try:
            subprocess.run([sys.executable, "test_notifications.py"])
        except Exception as e:
            print(f"❌ Error running test script: {e}")


def main():
    """Main setup function"""
    print_header("StellarIQ Push Notification Setup")

    print("🚀 This script will help you configure real push notifications for StellarIQ")
    print("📱 You'll need an Expo account and optionally Firebase/APNs credentials")

    # Step 1: Check prerequisites
    print_step(1, "Checking Prerequisites")
    if not check_expo_cli():
        print("\n❌ Please install Node.js and Expo CLI first:")
        print("   npm install -g @expo/cli")
        return

    # Step 2: Get project info
    print_step(2, "Getting Project Information")
    project_info = get_expo_project_info()
    if not project_info:
        return

    # Step 3: Expo account setup
    print_step(3, "Expo Account Setup")
    if not setup_expo_account():
        print("⚠️  Continuing without Expo login - you may need to login later")

    # Step 4: Get access token
    print_step(4, "Getting Expo Access Token")
    expo_token = get_expo_access_token()
    if not expo_token:
        print("❌ Access token is required for push notifications")
        return

    # Step 5: Update environment
    print_step(5, "Updating Environment Configuration")
    if not update_env_file(expo_token, project_info["project_id"]):
        return

    # Step 6: Platform-specific setup
    print_step(6, "Platform-Specific Setup")
    setup_firebase_credentials()
    setup_apns_credentials()

    # Step 7: Test setup
    print_step(7, "Testing Configuration")
    test_push_notifications()

    # Final instructions
    print_header("Setup Complete!")
    print("✅ Push notification configuration is ready!")
    print("\n📋 Next Steps:")
    print("1. Restart your API server to load new environment variables")
    print("2. Build and test your mobile app on a physical device")
    print("3. Register for notifications in the app")
    print("4. Test with real market alerts")

    print("\n💡 Important Notes:")
    print("- Push notifications only work on physical devices, not simulators")
    print("- iOS requires Apple Developer Program for production")
    print("- Android requires Firebase configuration")
    print("- Test thoroughly before deploying to production")


if __name__ == "__main__":
    main()
