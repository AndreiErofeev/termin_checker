"""
Subscription Service

Handles subscription management operations.
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.orm import joinedload

from ..core.database import Database
from ..core.models import Subscription, Service, User, UserPlan

logger = logging.getLogger(__name__)

BERLIN = ZoneInfo("Europe/Berlin")
_UTC = ZoneInfo("UTC")

# (start_hour, start_min, end_hour, end_min) in Berlin time
FREE_WINDOWS = [
    (7, 30, 8, 0),
    (9, 30, 10, 0),
    (12, 30, 13, 0),
    (15, 30, 16, 0),
]


def _current_free_window_start(now_berlin: datetime) -> datetime | None:
    """Return the start datetime of the current free window in Berlin time, or None if not in a window."""
    for (sh, sm, eh, em) in FREE_WINDOWS:
        window_start = now_berlin.replace(hour=sh, minute=sm, second=0, microsecond=0)
        window_end = now_berlin.replace(hour=eh, minute=em, second=0, microsecond=0)
        if window_start <= now_berlin < window_end:
            return window_start
    return None


class SubscriptionService:
    """Service for managing subscriptions"""

    def __init__(self, db: Database):
        """
        Initialize subscription service

        Args:
            db: Database instance
        """
        self.db = db

    def create_subscription(
        self,
        user_id: int,
        service_id: int,
        interval_hours: int = 1,
        quantity: int = 1,
        notify_telegram: bool = True
    ) -> Optional[Subscription]:
        """
        Create a new subscription

        Args:
            user_id: User ID
            service_id: Service ID
            interval_hours: Check interval in hours
            quantity: Number of people
            notify_telegram: Whether to send Telegram notifications

        Returns:
            Subscription object or None if error
        """
        try:
            with self.db.get_session() as session:
                # Check if subscription already exists
                existing = session.query(Subscription).filter(
                    Subscription.user_id == user_id,
                    Subscription.service_id == service_id
                ).first()

                if existing:
                    # Reactivate if inactive
                    if not existing.active:
                        existing.active = True
                        existing.interval_hours = interval_hours
                        existing.quantity = quantity
                        existing.notify_telegram = notify_telegram
                        session.commit()
                        logger.info(f"Reactivated subscription {existing.id}")
                    else:
                        logger.warning(f"Subscription already exists for user {user_id}, service {service_id}")

                    # Re-fetch with eager loading of service relationship
                    existing = session.query(Subscription).options(
                        joinedload(Subscription.service)
                    ).filter(Subscription.id == existing.id).first()
                    return existing

                # Create new subscription
                subscription = Subscription(
                    user_id=user_id,
                    service_id=service_id,
                    interval_hours=interval_hours,
                    quantity=quantity,
                    notify_telegram=notify_telegram,
                    active=True
                )

                session.add(subscription)
                session.commit()

                # Re-fetch with eager loading of service relationship
                subscription = session.query(Subscription).options(
                    joinedload(Subscription.service)
                ).filter(Subscription.id == subscription.id).first()

                logger.info(f"Created subscription {subscription.id} for user {user_id}")
                return subscription

        except Exception as e:
            logger.error(f"Error creating subscription: {e}", exc_info=True)
            return None

    def get_user_subscriptions(self, user_id: int, active_only: bool = True) -> List[Subscription]:
        """
        Get all subscriptions for a user

        Args:
            user_id: User ID
            active_only: Only return active subscriptions

        Returns:
            List of Subscription objects
        """
        with self.db.get_session() as session:
            query = session.query(Subscription).options(
                joinedload(Subscription.service)
            ).filter(Subscription.user_id == user_id)

            if active_only:
                query = query.filter(Subscription.active == True)

            subscriptions = query.all()
            return subscriptions

    def get_subscription(self, subscription_id: int) -> Optional[Subscription]:
        """
        Get a subscription by ID

        Args:
            subscription_id: Subscription ID

        Returns:
            Subscription object or None
        """
        with self.db.get_session() as session:
            subscription = session.query(Subscription).options(
                joinedload(Subscription.service),
                joinedload(Subscription.user)
            ).filter(
                Subscription.id == subscription_id
            ).first()

            return subscription

    def update_subscription(
        self,
        subscription_id: int,
        **kwargs
    ) -> Optional[Subscription]:
        """
        Update a subscription

        Args:
            subscription_id: Subscription ID
            **kwargs: Fields to update

        Returns:
            Updated Subscription object or None
        """
        try:
            with self.db.get_session() as session:
                subscription = session.query(Subscription).filter(
                    Subscription.id == subscription_id
                ).first()

                if not subscription:
                    logger.warning(f"Subscription {subscription_id} not found")
                    return None

                for key, value in kwargs.items():
                    if hasattr(subscription, key):
                        setattr(subscription, key, value)

                session.commit()

                # Re-fetch with eager loading
                subscription = session.query(Subscription).options(
                    joinedload(Subscription.service),
                    joinedload(Subscription.user)
                ).filter(Subscription.id == subscription_id).first()

                logger.info(f"Updated subscription {subscription_id}")
                return subscription

        except Exception as e:
            logger.error(f"Error updating subscription {subscription_id}: {e}")
            return None

    def delete_subscription(self, subscription_id: int) -> bool:
        """
        Delete (deactivate) a subscription

        Args:
            subscription_id: Subscription ID

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db.get_session() as session:
                subscription = session.query(Subscription).filter(
                    Subscription.id == subscription_id
                ).first()

                if not subscription:
                    return False

                subscription.active = False
                session.commit()

                logger.info(f"Deactivated subscription {subscription_id}")
                return True

        except Exception as e:
            logger.error(f"Error deleting subscription {subscription_id}: {e}")
            return False

    def get_all_active_subscriptions(self) -> List[Subscription]:
        """
        Get all active subscriptions across all users

        Returns:
            List of active Subscription objects
        """
        with self.db.get_session() as session:
            subscriptions = session.query(Subscription).options(
                joinedload(Subscription.service),
                joinedload(Subscription.user)
            ).filter(
                Subscription.active == True
            ).all()

            return subscriptions

    def get_subscriptions_due_for_check(self) -> List[Subscription]:
        """
        Get subscriptions due for checking (every 15 minutes, all plans).
        Notification gating for free users happens in the scheduler.
        Premium subscriptions are returned first.

        Returns:
            List of Subscription objects due for checking (premium first)
        """
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)

        with self.db.get_session() as session:
            subscriptions = session.query(Subscription).options(
                joinedload(Subscription.service),
                joinedload(Subscription.user)
            ).filter(
                Subscription.active == True
            ).all()

            premium_due = []
            free_due = []

            for sub in subscriptions:
                if sub.last_checked_at is not None and now_utc - sub.last_checked_at < timedelta(minutes=15):
                    continue
                if sub.user.plan in (UserPlan.PREMIUM, UserPlan.ADMIN):
                    premium_due.append(sub)
                else:
                    free_due.append(sub)

            return premium_due + free_due
