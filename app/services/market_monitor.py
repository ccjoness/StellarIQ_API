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
from app.services.notification import NotificationService

logger = logging.getLogger(__name__)


class MarketMonitorService:
    """Service for monitoring market conditions and sending alerts."""

    def __init__(self):
        self.analysis_service = MarketAnalysisService()
        self.notification_service = NotificationService()

    async def check_all_watchlists(self, db: Session) -> None:
        """Check all user watchlists for market condition changes."""
        try:
            logger.info("Starting watchlist market monitoring check")

            # Get all favorites with alerts enabled
            favorites = db.query(Favorite).filter(Favorite.alert_enabled == True).all()

            logger.info(f"Found {len(favorites)} favorites with alerts enabled")

            for favorite in favorites:
                try:
                    await self._check_favorite_alerts(favorite, db)
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
