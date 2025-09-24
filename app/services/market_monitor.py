"""Background market monitoring service for watchlist alerts."""

import logging
from datetime import datetime, timedelta
from typing import List

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.favorite import Favorite
from app.schemas.analysis import MarketCondition
from app.schemas.notification import MarketAlertData
from app.services.market_analysis import MarketAnalysisService
from app.services.market_data import MarketDataService
from app.services.notification import NotificationService
from app.utils.data_parser import DataParser

logger = logging.getLogger(__name__)


class MarketMonitorService:
    """Service for monitoring market conditions and sending alerts."""

    def __init__(self):
        self.analysis_service = MarketAnalysisService()
        self.market_service = MarketDataService()
        self.notification_service = NotificationService()

    async def check_all_watchlists(self, db: Session) -> None:
        """Check all user watchlists for market condition changes."""
        try:
            logger.info("Starting watchlist market monitoring check")

            # Get all favorites with any type of alerts enabled
            favorites = (
                db.query(Favorite)
                .filter(
                    (Favorite.alert_enabled == True)
                    | (Favorite.price_alert_enabled == True)
                )
                .all()
            )

            logger.info(f"Found {len(favorites)} favorites with alerts enabled")

            for favorite in favorites:
                try:
                    # Check market condition alerts
                    if favorite.alert_enabled:
                        await self._check_favorite_alerts(favorite, db)

                    # Check price alerts
                    if favorite.price_alert_enabled:
                        await self._check_price_alerts(favorite, db)

                except Exception as e:
                    logger.error(
                        f"Error checking alerts for favorite {favorite.id}: {e}"
                    )

            logger.info("Completed watchlist market monitoring check")

        except Exception as e:
            logger.error(f"Error in watchlist monitoring: {e}")

    async def _check_favorite_alerts(self, favorite: Favorite, db: Session) -> None:
        """Check alerts for a specific favorite."""
        try:
            # Skip if we sent an alert recently (within last hour)
            if favorite.last_alert_sent:
                time_since_last_alert = datetime.utcnow() - favorite.last_alert_sent
                if time_since_last_alert < timedelta(hours=1):
                    logger.debug(f"Skipping {favorite.symbol} - alert sent recently")
                    return

            # Get market analysis
            analysis = await self.analysis_service.analyze_symbol(
                symbol=favorite.symbol,
                asset_type=favorite.asset_type.value,
            )

            if not analysis:
                logger.warning(f"No analysis available for {favorite.symbol}")
                return

            current_condition = analysis.overall_condition.value
            previous_condition = favorite.last_alert_state

            # Check if condition changed and if we should alert
            should_alert = self._should_send_alert(
                current_condition, previous_condition, favorite
            )

            if should_alert:
                logger.info(
                    f"Sending alert for {favorite.symbol}: "
                    f"{previous_condition} -> {current_condition}"
                )

                # Create alert data
                alert_data = MarketAlertData(
                    symbol=favorite.symbol,
                    market_condition=current_condition,
                    confidence_score=analysis.confidence_score,
                    current_price=analysis.current_price,
                    previous_condition=previous_condition,
                )

                # Send notification
                success = await self.notification_service.send_market_alert(
                    user_id=favorite.user_id,
                    favorite_id=favorite.id,
                    alert_data=alert_data,
                    db=db,
                )

                if success:
                    # Update favorite with new alert state
                    favorite.last_alert_state = current_condition
                    favorite.last_alert_sent = datetime.utcnow()
                    db.commit()
                    logger.info(f"Alert sent successfully for {favorite.symbol}")
                else:
                    logger.error(f"Failed to send alert for {favorite.symbol}")
            else:
                # Update state even if no alert sent
                if current_condition != previous_condition:
                    favorite.last_alert_state = current_condition
                    db.commit()
                    logger.debug(
                        f"Updated state for {favorite.symbol}: "
                        f"{previous_condition} -> {current_condition} (no alert)"
                    )

        except Exception as e:
            logger.error(f"Error checking alerts for {favorite.symbol}: {e}")

    def _should_send_alert(
        self, current_condition: str, previous_condition: str, favorite: Favorite
    ) -> bool:
        """Determine if an alert should be sent based on conditions and preferences."""
        # No alert if condition hasn't changed
        if current_condition == previous_condition:
            return False

        # Check user preferences for this condition
        if current_condition == MarketCondition.OVERBOUGHT.value:
            return favorite.alert_on_overbought
        elif current_condition == MarketCondition.OVERSOLD.value:
            return favorite.alert_on_oversold
        elif current_condition == MarketCondition.NEUTRAL.value:
            return favorite.alert_on_neutral

        return False

    async def check_user_watchlist(self, user_id: int, db: Session) -> None:
        """Check watchlist for a specific user."""
        try:
            logger.info(f"Checking watchlist for user {user_id}")

            favorites = (
                db.query(Favorite)
                .filter(Favorite.user_id == user_id, Favorite.alert_enabled == True)
                .all()
            )

            logger.info(
                f"Found {len(favorites)} favorites with alerts for user {user_id}"
            )

            for favorite in favorites:
                try:
                    await self._check_favorite_alerts(favorite, db)
                except Exception as e:
                    logger.error(
                        f"Error checking alerts for favorite {favorite.id}: {e}"
                    )

        except Exception as e:
            logger.error(f"Error checking watchlist for user {user_id}: {e}")

    async def _check_price_alerts(self, favorite: Favorite, db: Session) -> None:
        """Check price alerts for a specific favorite."""
        try:
            # Skip if no price thresholds are set
            if not favorite.alert_price_above and not favorite.alert_price_below:
                return

            # Get current price
            current_price = await self._get_current_price(favorite)
            if current_price is None:
                logger.warning(f"Could not get current price for {favorite.symbol}")
                return

            # Check if we should send price alerts (avoid spam)
            if self._should_send_price_alert(favorite):
                alert_triggered = False
                alert_message = ""

                # Check price above threshold
                if (
                    favorite.alert_price_above
                    and current_price >= favorite.alert_price_above
                ):
                    alert_triggered = True
                    alert_message = f"Price Alert: {favorite.symbol} has reached ${current_price:.2f}, above your alert threshold of ${favorite.alert_price_above:.2f}"

                # Check price below threshold
                elif (
                    favorite.alert_price_below
                    and current_price <= favorite.alert_price_below
                ):
                    alert_triggered = True
                    alert_message = f"Price Alert: {favorite.symbol} has dropped to ${current_price:.2f}, below your alert threshold of ${favorite.alert_price_below:.2f}"

                if alert_triggered:
                    logger.info(
                        f"Sending price alert for {favorite.symbol}: ${current_price:.2f}"
                    )

                    # Send price alert notification
                    success = await self._send_price_alert(
                        favorite, current_price, alert_message, db
                    )

                    if success:
                        # Update last price alert sent timestamp
                        favorite.last_price_alert_sent = datetime.now()
                        db.commit()

        except Exception as e:
            logger.error(f"Error checking price alerts for {favorite.symbol}: {e}")

    async def _get_current_price(self, favorite: Favorite) -> float:
        """Get current price for a favorite asset."""
        try:
            if favorite.asset_type.value == "stock":
                quote_data = await self.market_service.get_stock_quote(favorite.symbol)
                quote = DataParser.parse_stock_quote(quote_data)
                return quote.price
            elif favorite.asset_type.value == "crypto":
                rate_data = await self.market_service.get_crypto_exchange_rate(
                    favorite.symbol, "USD"
                )
                rate = DataParser.parse_crypto_exchange_rate(rate_data)
                return rate.exchange_rate
        except Exception as e:
            logger.error(f"Error getting current price for {favorite.symbol}: {e}")
            return None

    def _should_send_price_alert(self, favorite: Favorite) -> bool:
        """Check if we should send a price alert (to avoid spam)."""
        if not favorite.last_price_alert_sent:
            return True

        # Only send price alerts once per hour to avoid spam
        time_since_last_alert = datetime.now() - favorite.last_price_alert_sent
        return time_since_last_alert.total_seconds() > 3600  # 1 hour

    async def _send_price_alert(
        self, favorite: Favorite, current_price: float, message: str, db: Session
    ) -> bool:
        """Send a price alert notification."""
        try:
            from app.models.notification import (
                Notification,
                NotificationChannel,
                NotificationStatus,
                NotificationType,
            )

            # Create notification record
            notification = Notification(
                user_id=favorite.user_id,
                favorite_id=favorite.id,
                title=f"{favorite.symbol} Price Alert",
                body=message,
                notification_type=NotificationType.PRICE_ALERT,
                channel=NotificationChannel.PUSH,
                symbol=favorite.symbol,
                status=NotificationStatus.PENDING,
            )
            db.add(notification)
            db.commit()

            # Send notification using the notification service
            # For now, we'll create a simple alert data structure
            alert_data = {
                "symbol": favorite.symbol,
                "current_price": current_price,
                "alert_type": "price_alert",
                "message": message,
            }

            # Send push notification if user has push notifications enabled
            user = favorite.user
            if user and user.push_notifications:
                # Use the existing notification service infrastructure
                success = await self.notification_service._send_push_notification(
                    favorite.user_id, favorite.id, alert_data, db
                )

                # Update notification status
                notification.status = (
                    NotificationStatus.SENT if success else NotificationStatus.FAILED
                )
                db.commit()

                return success

            return True

        except Exception as e:
            logger.error(f"Error sending price alert for {favorite.symbol}: {e}")
            return False

    async def force_check_symbol(self, user_id: int, symbol: str, db: Session) -> bool:
        """Force check a specific symbol for a user (for testing)."""
        try:
            favorite = (
                db.query(Favorite)
                .filter(
                    Favorite.user_id == user_id,
                    Favorite.symbol == symbol,
                    Favorite.alert_enabled == True,
                )
                .first()
            )

            if not favorite:
                logger.warning(
                    f"No enabled favorite found for user {user_id}, symbol {symbol}"
                )
                return False

            # Temporarily reset last alert time to force check
            original_last_alert = favorite.last_alert_sent
            favorite.last_alert_sent = None
            db.commit()

            try:
                await self._check_favorite_alerts(favorite, db)
                return True
            finally:
                # Restore original time if no new alert was sent
                if favorite.last_alert_sent is None:
                    favorite.last_alert_sent = original_last_alert
                    db.commit()

        except Exception as e:
            logger.error(
                f"Error force checking symbol {symbol} for user {user_id}: {e}"
            )
            return False

    def get_monitoring_stats(self, db: Session) -> dict:
        """Get statistics about monitoring status."""
        try:
            total_favorites = db.query(Favorite).count()
            enabled_alerts = (
                db.query(Favorite).filter(Favorite.alert_enabled == True).count()
            )

            recent_alerts = (
                db.query(Favorite)
                .filter(
                    Favorite.last_alert_sent >= datetime.utcnow() - timedelta(hours=24)
                )
                .count()
            )

            return {
                "total_favorites": total_favorites,
                "enabled_alerts": enabled_alerts,
                "recent_alerts_24h": recent_alerts,
                "last_check": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting monitoring stats: {e}")
            return {
                "error": str(e),
                "last_check": datetime.utcnow().isoformat(),
            }
