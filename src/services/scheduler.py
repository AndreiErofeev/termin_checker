"""
Scheduler Service

Handles periodic appointment checks using APScheduler.
"""

import logging
import asyncio
from typing import Optional
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from ..core.database import Database
from .check_service import CheckService
from .subscription_service import SubscriptionService

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for scheduling periodic appointment checks"""

    def __init__(self, db: Database):
        """
        Initialize scheduler service

        Args:
            db: Database instance
        """
        self.db = db
        self.check_service = CheckService(db)
        self.subscription_service = SubscriptionService(db)
        self.scheduler = AsyncIOScheduler()
        self.running = False

    def start(self):
        """Start the scheduler"""
        if self.running:
            logger.warning("Scheduler already running")
            return

        logger.info("Starting scheduler...")

        # Add main check job - runs every 5 minutes
        self.scheduler.add_job(
            self._check_all_due_subscriptions,
            trigger=IntervalTrigger(minutes=5),
            id='check_subscriptions',
            name='Check due subscriptions',
            replace_existing=True
        )

        self.scheduler.start()
        self.running = True

        logger.info("Scheduler started successfully")

    def stop(self):
        """Stop the scheduler"""
        if not self.running:
            return

        logger.info("Stopping scheduler...")
        self.scheduler.shutdown()
        self.running = False
        logger.info("Scheduler stopped")

    async def _check_all_due_subscriptions(self):
        """Check all subscriptions that are due for checking"""
        try:
            logger.info("Running scheduled check for due subscriptions...")

            # Get subscriptions due for checking
            due_subscriptions = self.subscription_service.get_subscriptions_due_for_check()

            if not due_subscriptions:
                logger.info("No subscriptions due for checking")
                return

            logger.info(f"Found {len(due_subscriptions)} subscription(s) due for checking")

            # Run checks for each subscription
            for subscription in due_subscriptions:
                try:
                    logger.info(f"Checking subscription {subscription.id}...")

                    check = await self.check_service.run_subscription_check(subscription.id)

                    if check and check.available:
                        logger.info(
                            f"✅ Found {check.appointment_count} appointment(s) "
                            f"for subscription {subscription.id}"
                        )
                        # Notification will be handled by notification service
                    else:
                        logger.info(f"No appointments found for subscription {subscription.id}")

                except Exception as e:
                    logger.error(
                        f"Error checking subscription {subscription.id}: {e}",
                        exc_info=True
                    )

                # Small delay between checks to avoid rate limiting
                await asyncio.sleep(2)

            logger.info("Scheduled check completed")

        except Exception as e:
            logger.error(f"Error in scheduled check: {e}", exc_info=True)

    async def check_subscription_now(self, subscription_id: int) -> Optional[object]:
        """
        Manually trigger a check for a specific subscription

        Args:
            subscription_id: Subscription ID

        Returns:
            Check object or None
        """
        try:
            logger.info(f"Manual check triggered for subscription {subscription_id}")
            check = await self.check_service.run_subscription_check(subscription_id)
            return check

        except Exception as e:
            logger.error(f"Error in manual check for subscription {subscription_id}: {e}")
            return None

    def get_status(self) -> dict:
        """
        Get scheduler status

        Returns:
            Dictionary with scheduler status information
        """
        jobs = self.scheduler.get_jobs()

        return {
            'running': self.running,
            'jobs': [
                {
                    'id': job.id,
                    'name': job.name,
                    'next_run': job.next_run_time.isoformat() if job.next_run_time else None
                }
                for job in jobs
            ]
        }


async def run_scheduler_standalone():
    """Run scheduler as standalone service"""
    from ..core.database import init_database

    logger.info("Initializing standalone scheduler...")

    # Initialize database
    db = init_database()

    # Create scheduler
    scheduler = SchedulerService(db)

    # Start scheduler
    scheduler.start()

    logger.info("Scheduler is running. Press Ctrl+C to stop.")

    try:
        # Keep running
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Received interrupt signal")

    finally:
        scheduler.stop()
        await scheduler.check_service.cleanup()
        logger.info("Scheduler stopped")


if __name__ == '__main__':
    # Run scheduler as standalone process
    asyncio.run(run_scheduler_standalone())
