#!/usr/bin/env python3
"""
Email Alert Testing Script for StellarIQ

This script allows you to test sending email alerts to users.
It supports both market condition alerts and price alerts.
"""

import sys
import asyncio
import argparse
from datetime import datetime
from typing import Optional

# Add the app directory to the path
sys.path.append('.')

from app.core.database import SessionLocal
from app.models.user import User
from app.models.favorite import Favorite
from app.services.email import EmailService
from app.services.notification import NotificationService
from app.schemas.notification import MarketAlertData
from app.schemas.analysis import MarketCondition


class EmailAlertTester:
    """Test email alert functionality."""
    
    def __init__(self):
        self.email_service = EmailService()
        self.notification_service = NotificationService()
        self.db = SessionLocal()
    
    def list_users(self):
        """List all users in the database."""
        users = self.db.query(User).all()
        
        if not users:
            print("❌ No users found in the database.")
            return []
        
        print("\n👥 Available Users:")
        print("-" * 60)
        for i, user in enumerate(users, 1):
            status = "✅ Active" if user.is_active else "❌ Inactive"
            email_pref = "📧 On" if user.email_notifications else "📧 Off"
            print(f"{i:2d}. {user.email:30s} | {status} | {email_pref}")
        print("-" * 60)
        
        return users
    
    def list_user_favorites(self, user_id: int):
        """List favorites for a specific user."""
        favorites = self.db.query(Favorite).filter(Favorite.user_id == user_id).all()
        
        if not favorites:
            print(f"❌ No favorites found for user ID {user_id}.")
            return []
        
        print(f"\n📊 Favorites for User ID {user_id}:")
        print("-" * 80)
        for i, fav in enumerate(favorites, 1):
            alerts = []
            if fav.alert_enabled:
                alerts.append("Market")
            if fav.price_alert_enabled:
                price_alerts = []
                if fav.alert_price_above:
                    price_alerts.append(f">${fav.alert_price_above}")
                if fav.alert_price_below:
                    price_alerts.append(f"${fav.alert_price_below}")
                if price_alerts:
                    alerts.append(f"Price({'/'.join(price_alerts)})")
            
            alert_status = f"🔔 {', '.join(alerts)}" if alerts else "🔕 None"
            print(f"{i:2d}. {fav.symbol:8s} | {fav.asset_type.value:6s} | {alert_status}")
        print("-" * 80)
        
        return favorites
    
    def send_test_market_alert(self, user_email: str, symbol: str = "AAPL", 
                              condition: str = "overbought", confidence: float = 0.85):
        """Send a test market condition alert."""
        try:
            # Create mock alert data
            alert_data = MarketAlertData(
                symbol=symbol,
                market_condition=MarketCondition(condition),
                confidence_score=confidence,
                current_price=150.25,
                previous_condition=MarketCondition.NEUTRAL,
                timestamp=datetime.now()
            )
            
            title = f"{symbol} Market Alert"
            body = f"{symbol} is showing {condition} signals with {confidence:.1%} confidence."
            
            print(f"\n📧 Sending market alert email...")
            print(f"   To: {user_email}")
            print(f"   Symbol: {symbol}")
            print(f"   Condition: {condition}")
            print(f"   Confidence: {confidence:.1%}")
            
            success = self.email_service.send_market_alert_email(
                user_email, title, body, alert_data
            )
            
            if success:
                print("✅ Market alert email sent successfully!")
            else:
                print("❌ Failed to send market alert email.")
            
            return success
            
        except Exception as e:
            print(f"❌ Error sending market alert: {e}")
            return False
    
    def send_test_price_alert(self, user_email: str, symbol: str = "AAPL", 
                             current_price: float = 195.50, threshold: float = 195.00,
                             alert_type: str = "above"):
        """Send a test price alert."""
        try:
            title = f"{symbol} Price Alert"
            
            if alert_type == "above":
                body = f"Price Alert: {symbol} has reached ${current_price:.2f}, above your alert threshold of ${threshold:.2f}"
            else:
                body = f"Price Alert: {symbol} has dropped to ${current_price:.2f}, below your alert threshold of ${threshold:.2f}"
            
            print(f"\n📧 Sending price alert email...")
            print(f"   To: {user_email}")
            print(f"   Symbol: {symbol}")
            print(f"   Current Price: ${current_price:.2f}")
            print(f"   Threshold: ${threshold:.2f}")
            print(f"   Alert Type: {alert_type}")

            # Use the dedicated price alert email method
            success = self.email_service.send_price_alert_email(
                user_email, symbol, current_price, threshold, alert_type
            )
            
            if success:
                print("✅ Price alert email sent successfully!")
            else:
                print("❌ Failed to send price alert email.")
                print("💡 Note: SMTP may not be configured. Check logs for details.")
            
            return success
            
        except Exception as e:
            print(f"❌ Error sending price alert: {e}")
            return False
    
    def send_test_password_reset(self, user_email: str):
        """Send a test password reset email."""
        try:
            print(f"\n📧 Sending password reset email...")
            print(f"   To: {user_email}")
            
            success = self.email_service.send_password_reset_email(
                user_email, "test-reset-token-12345"
            )
            
            if success:
                print("✅ Password reset email sent successfully!")
            else:
                print("❌ Failed to send password reset email.")
            
            return success
            
        except Exception as e:
            print(f"❌ Error sending password reset email: {e}")
            return False
    
    def interactive_mode(self):
        """Run in interactive mode."""
        print("🚀 StellarIQ Email Alert Tester")
        print("=" * 50)
        
        while True:
            print("\n📋 Available Actions:")
            print("1. List all users")
            print("2. List user favorites")
            print("3. Send test market alert")
            print("4. Send test price alert")
            print("5. Send test password reset")
            print("6. Exit")
            
            try:
                choice = input("\nSelect an action (1-6): ").strip()
                
                if choice == "1":
                    self.list_users()
                
                elif choice == "2":
                    users = self.list_users()
                    if users:
                        try:
                            user_num = int(input("Enter user number: ")) - 1
                            if 0 <= user_num < len(users):
                                self.list_user_favorites(users[user_num].id)
                            else:
                                print("❌ Invalid user number.")
                        except ValueError:
                            print("❌ Please enter a valid number.")
                
                elif choice == "3":
                    email = input("Enter user email: ").strip()
                    symbol = input("Enter symbol (default: AAPL): ").strip() or "AAPL"
                    condition = input("Enter condition (overbought/oversold/neutral, default: overbought): ").strip() or "overbought"
                    try:
                        confidence = float(input("Enter confidence (0.0-1.0, default: 0.85): ").strip() or "0.85")
                        self.send_test_market_alert(email, symbol, condition, confidence)
                    except ValueError:
                        print("❌ Invalid confidence value.")
                
                elif choice == "4":
                    email = input("Enter user email: ").strip()
                    symbol = input("Enter symbol (default: AAPL): ").strip() or "AAPL"
                    try:
                        current_price = float(input("Enter current price (default: 195.50): ").strip() or "195.50")
                        threshold = float(input("Enter threshold price (default: 195.00): ").strip() or "195.00")
                        alert_type = input("Enter alert type (above/below, default: above): ").strip() or "above"
                        self.send_test_price_alert(email, symbol, current_price, threshold, alert_type)
                    except ValueError:
                        print("❌ Invalid price value.")
                
                elif choice == "5":
                    email = input("Enter user email: ").strip()
                    self.send_test_password_reset(email)
                
                elif choice == "6":
                    print("👋 Goodbye!")
                    break
                
                else:
                    print("❌ Invalid choice. Please select 1-6.")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
    
    def close(self):
        """Clean up resources."""
        self.db.close()


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test email alerts for StellarIQ")
    parser.add_argument("--email", help="User email to send test to")
    parser.add_argument("--type", choices=["market", "price", "reset"], 
                       help="Type of alert to send")
    parser.add_argument("--symbol", default="AAPL", help="Stock symbol")
    parser.add_argument("--condition", default="overbought", 
                       choices=["overbought", "oversold", "neutral"],
                       help="Market condition for market alerts")
    parser.add_argument("--confidence", type=float, default=0.85,
                       help="Confidence score for market alerts")
    parser.add_argument("--current-price", type=float, default=195.50,
                       help="Current price for price alerts")
    parser.add_argument("--threshold", type=float, default=195.00,
                       help="Threshold price for price alerts")
    parser.add_argument("--alert-type", choices=["above", "below"], default="above",
                       help="Price alert type")
    
    args = parser.parse_args()
    
    tester = EmailAlertTester()
    
    try:
        if args.email and args.type:
            # Command line mode
            if args.type == "market":
                tester.send_test_market_alert(args.email, args.symbol, 
                                            args.condition, args.confidence)
            elif args.type == "price":
                tester.send_test_price_alert(args.email, args.symbol,
                                           args.current_price, args.threshold,
                                           args.alert_type)
            elif args.type == "reset":
                tester.send_test_password_reset(args.email)
        else:
            # Interactive mode
            tester.interactive_mode()
    
    finally:
        tester.close()


if __name__ == "__main__":
    main()
