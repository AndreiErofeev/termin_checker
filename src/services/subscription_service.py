"""
Subscription Service

Handles subscription management operations.
"""

import logging
from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import joinedload

from ..core.database import Database
from ..core.models import Subscription, Service, User

logger = logging.getLogger(__name__)


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
        Get subscriptions that are due for checking based on interval

        Returns:
            List of Subscription objects due for checking
        """
        from datetime import timedelta

        with self.db.get_session() as session:
            now = datetime.now()

            subscriptions = session.query(Subscription).options(
                joinedload(Subscription.service),
                joinedload(Subscription.user)
            ).filter(
                Subscription.active == True
            ).all()

            due_subscriptions = []

            for sub in subscriptions:
                if sub.last_checked_at is None:
                    # Never checked, due immediately
                    due_subscriptions.append(sub)
                else:
                    # Check if enough time has passed
                    time_since_check = now - sub.last_checked_at
                    if time_since_check >= timedelta(hours=sub.interval_hours):
                        due_subscriptions.append(sub)

            return due_subscriptions
