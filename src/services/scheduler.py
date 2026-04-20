"""
Scheduler Service

Handles periodic appointment checks using APScheduler.
"""

import logging
import asyncio
import os
from collections import defaultdict
from typing import Optional
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from ..core.database import Database
from .check_service import CheckService
from .subscription_service import SubscriptionService
from .notification_service import NotificationService

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for scheduling periodic appointment checks"""

    def __init__(self, db: Database, bot_token: Optional[str] = None):
        """
        Initialize scheduler service

        Args:
            db: Database instance
            bot_token: Telegram bot token (optional, reads from env if not provided)
        """
        self.db = db
        self.check_service = CheckService(db)
        self.subscription_service = SubscriptionService(db)

        # Initialize notification service if bot token available
        bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.notification_service = NotificationService(db, bot_token) if bot_token else None

        self.scheduler = AsyncIOScheduler()
        self.running = False

    def start(self):
        """Start the scheduler"""
        if self.running:
            logger.warning("Scheduler already running")
            return

        logger.info("Starting scheduler...")

        # Poll every 5 minutes; due-check logic inside decides which subs actually run.
        # Polling hourly caused subs to be checked every ~2h because Playwright takes
        # seconds, pushing last_checked_at past the fire time so the next fire misses them.
        self.scheduler.add_job(
            self._check_all_due_subscriptions,
            trigger=IntervalTrigger(minutes=5),
            id='check_subscriptions',
            name='Check due subscriptions',
            replace_existing=True,
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
        """Check all due subscriptions, scraping each unique service only once."""
        try:
            due_subscriptions = self.subscription_service.get_subscriptions_due_for_check()
            if not due_subscriptions:
                logger.info("No subscriptions due for checking")
                return

            # Group by (service_id, quantity) — same service with different qty needs separate scrapes
            groups: dict = defaultdict(list)
            for sub in due_subscriptions:
                groups[(sub.service_id, sub.quantity)].append(sub)

            logger.info(
                f"Found {len(due_subscriptions)} due subscription(s) "
                f"across {len(groups)} unique service/quantity group(s)"
            )

            for (service_id, quantity), subs in groups.items():
                checked_at = datetime.now()
                logger.info(
                    f"Scraping service {service_id} qty={quantity} "
                    f"for {len(subs)} subscriber(s)..."
                )

                result = await self.check_service.scrape_service(service_id, quantity)

                if result is None:
                    logger.error(
                        f"Scrape failed for service {service_id} qty={quantity}, "
                        f"skipping {len(subs)} subscription(s)"
                    )
                    await asyncio.sleep(2)
                    continue

                for sub in subs:
                    try:
                        check = self.check_service.record_check(sub.id, result, checked_at)
                        if check and check.available and self.notification_service:
                            if sub.notify_telegram and sub.notify_on_found:
                                try:
                                    await self.notification_service.send_appointment_notification(
                                        user=sub.user,
                                        check=check,
                                        appointments=check.appointments,
                                    )
                                except Exception as notif_error:
                                    logger.error(
                                        f"Failed to send notification for sub {sub.id}: {notif_error}"
                                    )
                    except Exception as e:
                        logger.error(
                            f"Error processing subscription {sub.id}: {e}", exc_info=True
                        )

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
