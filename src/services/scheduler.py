"""
Scheduler Service

Handles periodic appointment checks using APScheduler.
"""

import logging
import asyncio
import os
from collections import defaultdict
from typing import Optional
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from ..core.database import Database
from ..core.models import Subscription, UserPlan

_BERLIN = ZoneInfo("Europe/Berlin")
from .check_service import CheckService
from .subscription_service import SubscriptionService, _current_free_window_start
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

            # Compute time references once per scheduler run
            now_berlin = datetime.now(_BERLIN)
            in_free_window = _current_free_window_start(now_berlin) is not None
            today_10am_naive = (
                now_berlin.replace(hour=10, minute=0, second=0, microsecond=0)
                .astimezone(timezone.utc).replace(tzinfo=None)
            )
            today_midnight_naive = (
                now_berlin.replace(hour=0, minute=0, second=0, microsecond=0)
                .astimezone(timezone.utc).replace(tzinfo=None)
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
                        # Capture pre-check state before record_check updates these fields
                        was_available = sub.last_available
                        last_notified = sub.last_notified_at
                        became_available_at = sub.became_available_at

                        check = self.check_service.record_check(sub.id, result, checked_at)
                        if not check:
                            continue

                        if not (self.notification_service and sub.notify_telegram):
                            continue

                        now = checked_at
                        just_appeared = check.available and not was_available
                        just_gone = not check.available and was_available
                        is_premium = sub.user.plan in (UserPlan.PREMIUM, UserPlan.ADMIN)

                        if is_premium:
                            interval_min = sub.reminder_interval_minutes or 1440
                            reminder_due = (
                                check.available and was_available and (
                                    last_notified is None or
                                    (now - last_notified) >= timedelta(minutes=interval_min)
                                )
                            )
                            if just_appeared or reminder_due or just_gone:
                                try:
                                    if just_gone:
                                        sent = await self.notification_service.send_appointments_gone_notification(
                                            user=sub.user, subscription=sub, check=check,
                                        )
                                    else:
                                        sent = await self.notification_service.send_appointment_notification(
                                            user=sub.user, subscription=sub, check=check,
                                            appointments=check.appointments, is_reminder=reminder_due,
                                        )
                                    if sent:
                                        with self.db.get_session() as session:
                                            s = session.query(Subscription).filter_by(id=sub.id).first()
                                            if s:
                                                s.last_notified_at = now
                                                session.commit()
                                except Exception as notif_error:
                                    logger.error(f"Failed to send notification for sub {sub.id}: {notif_error}")
                        else:
                            # Free user: gate appeared by window; detect missed-it on just_gone
                            notify_appeared = just_appeared and in_free_window
                            reminder_due = (
                                check.available and was_available and
                                now >= today_10am_naive and
                                (last_notified is None or last_notified < today_10am_naive)
                            )
                            user_was_notified = (
                                last_notified is not None and
                                became_available_at is not None and
                                last_notified >= became_available_at
                            )
                            missed_it = (
                                just_gone and
                                became_available_at is not None and
                                not user_was_notified and
                                (sub.last_missed_notification_at is None or
                                 sub.last_missed_notification_at < today_midnight_naive)
                            )
                            send_gone_normal = just_gone and (user_was_notified or became_available_at is None)

                            if notify_appeared or reminder_due or send_gone_normal:
                                try:
                                    if send_gone_normal:
                                        sent = await self.notification_service.send_appointments_gone_notification(
                                            user=sub.user, subscription=sub, check=check,
                                        )
                                    else:
                                        sent = await self.notification_service.send_appointment_notification(
                                            user=sub.user, subscription=sub, check=check,
                                            appointments=check.appointments, is_reminder=reminder_due,
                                        )
                                    if sent:
                                        with self.db.get_session() as session:
                                            s = session.query(Subscription).filter_by(id=sub.id).first()
                                            if s:
                                                s.last_notified_at = now
                                                session.commit()
                                except Exception as notif_error:
                                    logger.error(f"Failed to send notification for sub {sub.id}: {notif_error}")

                            if missed_it:
                                try:
                                    sent = await self.notification_service.send_missed_opportunity_notification(
                                        user=sub.user,
                                        subscription=sub,
                                        check=check,
                                        became_available_at=became_available_at,
                                        gone_at=checked_at,
                                    )
                                    if sent:
                                        with self.db.get_session() as session:
                                            s = session.query(Subscription).filter_by(id=sub.id).first()
                                            if s:
                                                s.last_missed_notification_at = now
                                                session.commit()
                                except Exception as notif_error:
                                    logger.error(f"Failed to send missed-it notification for sub {sub.id}: {notif_error}")

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
