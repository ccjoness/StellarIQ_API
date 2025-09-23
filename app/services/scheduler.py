"""Background task scheduler for market monitoring."""

import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.database import SessionLocal
from app.services.market_monitor import MarketMonitorService

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Background task scheduler for market monitoring and notifications."""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.market_monitor = MarketMonitorService()
        self._is_running = False

    def start(self):
        """Start the background scheduler."""
        if self._is_running:
            logger.warning("Scheduler is already running")
            return

        try:
            # Add market monitoring job - run every 5 minutes during market hours
            self.scheduler.add_job(
                func=self._run_market_monitoring,
                trigger=IntervalTrigger(minutes=5),
                id="market_monitoring",
                name="Market Monitoring",
                replace_existing=True,
                max_instances=1,  # Prevent overlapping runs
            )

            # Add cleanup job - run daily at 2 AM
            self.scheduler.add_job(
                func=self._cleanup_old_notifications,
                trigger="cron",
                hour=2,
                minute=0,
                id="notification_cleanup",
                name="Notification Cleanup",
                replace_existing=True,
            )

            # Add health check job - run every hour
            self.scheduler.add_job(
                func=self._health_check,
                trigger=IntervalTrigger(hours=1),
                id="health_check",
                name="Health Check",
                replace_existing=True,
            )

            self.scheduler.start()
            self._is_running = True
            logger.info("Background scheduler started successfully")

        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            raise

    def stop(self):
        """Stop the background scheduler."""
        if not self._is_running:
            logger.warning("Scheduler is not running")
            return

        try:
            self.scheduler.shutdown(wait=True)
            self._is_running = False
            logger.info("Background scheduler stopped successfully")

        except Exception as e:
            logger.error(f"Failed to stop scheduler: {e}")

    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._is_running and self.scheduler.running

    async def _run_market_monitoring(self):
        """Run market monitoring task."""
        try:
            logger.info("Starting scheduled market monitoring task")
            start_time = datetime.utcnow()

            # Create database session
            db = SessionLocal()
            try:
                await self.market_monitor.check_all_watchlists(db)
            finally:
                db.close()

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            logger.info(f"Market monitoring task completed in {duration:.2f} seconds")

        except Exception as e:
            logger.error(f"Error in scheduled market monitoring: {e}")

    async def _cleanup_old_notifications(self):
        """Clean up old notifications and device tokens."""
        try:
            logger.info("Starting notification cleanup task")

            from datetime import timedelta

            from app.models.device_token import DeviceToken
            from app.models.notification import Notification

            db = SessionLocal()
            try:
                # Delete notifications older than 30 days
                cutoff_date = datetime.utcnow() - timedelta(days=30)
                old_notifications = (
                    db.query(Notification)
                    .filter(Notification.created_at < cutoff_date)
                    .count()
                )

                if old_notifications > 0:
                    db.query(Notification).filter(
                        Notification.created_at < cutoff_date
                    ).delete()
                    logger.info(f"Deleted {old_notifications} old notifications")

                # Mark device tokens as inactive if not used in 60 days
                inactive_cutoff = datetime.utcnow() - timedelta(days=60)
                inactive_tokens = (
                    db.query(DeviceToken)
                    .filter(
                        DeviceToken.last_used_at < inactive_cutoff,
                        DeviceToken.is_active == True,
                    )
                    .count()
                )

                if inactive_tokens > 0:
                    db.query(DeviceToken).filter(
                        DeviceToken.last_used_at < inactive_cutoff,
                        DeviceToken.is_active == True,
                    ).update({"is_active": False})
                    logger.info(f"Marked {inactive_tokens} device tokens as inactive")

                db.commit()

            finally:
                db.close()

            logger.info("Notification cleanup task completed")

        except Exception as e:
            logger.error(f"Error in notification cleanup: {e}")

    async def _health_check(self):
        """Perform health check and log system status."""
        try:
            logger.info("Performing health check")

            db = SessionLocal()
            try:
                stats = self.market_monitor.get_monitoring_stats(db)
                logger.info(f"Monitoring stats: {stats}")
            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error in health check: {e}")

    def get_job_status(self) -> dict:
        """Get status of all scheduled jobs."""
        try:
            jobs = []
            for job in self.scheduler.get_jobs():
                jobs.append(
                    {
                        "id": job.id,
                        "name": job.name,
                        "next_run": job.next_run_time.isoformat()
                        if job.next_run_time
                        else None,
                        "trigger": str(job.trigger),
                    }
                )

            return {
                "scheduler_running": self.is_running(),
                "jobs": jobs,
                "status": "healthy" if self.is_running() else "stopped",
            }

        except Exception as e:
            logger.error(f"Error getting job status: {e}")
            return {
                "scheduler_running": False,
                "jobs": [],
                "status": "error",
                "error": str(e),
            }

    async def trigger_market_monitoring(self):
        """Manually trigger market monitoring (for testing)."""
        try:
            logger.info("Manually triggering market monitoring")
            await self._run_market_monitoring()
            return True
        except Exception as e:
            logger.error(f"Error manually triggering market monitoring: {e}")
            return False


# Global scheduler instance
scheduler = TaskScheduler()
