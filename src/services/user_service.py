"""
User Service

Handles user management operations.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from ..core.database import Database
from ..core.models import User, UserPlan

logger = logging.getLogger(__name__)


class UserService:
    """Service for user management"""

    def __init__(self, db: Database):
        """
        Initialize user service

        Args:
            db: Database instance
        """
        self.db = db

    def create_or_update_user(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        **kwargs
    ) -> User:
        """
        Create new user or update existing user

        Args:
            telegram_id: Telegram user ID
            username: Telegram username
            first_name: User's first name
            last_name: User's last name
            **kwargs: Additional user attributes

        Returns:
            User object
        """
        with self.db.get_session() as session:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()

            if user:
                # Update existing user
                user.username = username or user.username
                user.first_name = first_name or user.first_name
                user.last_name = last_name or user.last_name
                user.last_active = datetime.now()

                for key, value in kwargs.items():
                    if hasattr(user, key):
                        setattr(user, key, value)

                logger.info(f"Updated user {telegram_id}")
            else:
                # Create new user
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    plan=kwargs.get('plan', UserPlan.FREE),
                    active=True
                )
                session.add(user)
                logger.info(f"Created new user {telegram_id}")

            session.commit()
            session.refresh(user)
            return user

    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """
        Get user by Telegram ID

        Args:
            telegram_id: Telegram user ID

        Returns:
            User object or None
        """
        with self.db.get_session() as session:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if user:
                session.refresh(user)
            return user

    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get statistics for a user

        Args:
            user_id: User ID

        Returns:
            Dictionary with user statistics
        """
        with self.db.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()

            if not user:
                return {}

            total_subscriptions = len(user.subscriptions)
            active_subscriptions = sum(1 for s in user.subscriptions if s.active)

            total_checks = sum(len(s.checks) for s in user.subscriptions)

            return {
                'telegram_id': user.telegram_id,
                'username': user.username,
                'plan': user.plan.value,
                'total_subscriptions': total_subscriptions,
                'active_subscriptions': active_subscriptions,
                'total_checks': total_checks,
                'created_at': user.created_at.isoformat(),
                'last_active': user.last_active.isoformat() if user.last_active else None
            }

    def update_plan(self, telegram_id: int, plan: UserPlan) -> bool:
        """
        Update user's subscription plan

        Args:
            telegram_id: Telegram user ID
            plan: New plan

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db.get_session() as session:
                user = session.query(User).filter(User.telegram_id == telegram_id).first()

                if not user:
                    return False

                user.plan = plan
                session.commit()

                logger.info(f"Updated plan for user {telegram_id} to {plan.value}")
                return True

        except Exception as e:
            logger.error(f"Error updating plan for user {telegram_id}: {e}")
            return False

    def deactivate_user(self, telegram_id: int) -> bool:
        """
        Deactivate a user

        Args:
            telegram_id: Telegram user ID

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db.get_session() as session:
                user = session.query(User).filter(User.telegram_id == telegram_id).first()

                if not user:
                    return False

                user.active = False
                session.commit()

                logger.info(f"Deactivated user {telegram_id}")
                return True

        except Exception as e:
            logger.error(f"Error deactivating user {telegram_id}: {e}")
            return False
