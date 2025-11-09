"""
Notification Service

Handles sending notifications to users via Telegram.
"""

import logging
from typing import Optional, List
from datetime import datetime

from telegram import Bot
from telegram.error import TelegramError

from ..core.database import Database
from ..core.models import Notification, Check, Appointment, User

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications"""

    def __init__(self, db: Database, bot_token: str):
        """
        Initialize notification service

        Args:
            db: Database instance
            bot_token: Telegram bot token
        """
        self.db = db
        self.bot = Bot(token=bot_token)

    async def send_appointment_notification(
        self,
        user: User,
        check: Check,
        appointments: List[Appointment]
    ) -> bool:
        """
        Send appointment availability notification to user

        Args:
            user: User object
            check: Check object
            appointments: List of Appointment objects

        Returns:
            True if notification sent successfully, False otherwise
        """
        try:
            service = check.subscription.service

            # Format message
            message = (
                f"🎉 *Appointments Available!*\n\n"
                f"*Service:* {service.service_name}\n"
                f"*Category:* {service.category}\n\n"
                f"*Found {len(appointments)} appointment(s):*\n\n"
            )

            # Add appointment slots (limit to 15 to avoid message too long)
            for idx, apt in enumerate(appointments[:15], 1):
                message += f"{idx}. 📅 {apt.appointment_date} at {apt.appointment_time}\n"

            if len(appointments) > 15:
                message += f"\n... and {len(appointments) - 15} more appointments\n"

            message += (
                f"\n🔗 Book now: {service.base_url}\n\n"
                f"_Checked at {check.checked_at.strftime('%Y-%m-%d %H:%M')}_"
            )

            # Send message
            await self.bot.send_message(
                chat_id=user.telegram_id,
                text=message,
                parse_mode='Markdown'
            )

            # Save notification record
            with self.db.get_session() as session:
                notification = Notification(
                    user_id=user.id,
                    check_id=check.id,
                    message=message,
                    sent_at=datetime.now(),
                    success=True
                )
                session.add(notification)
                session.commit()

            logger.info(f"Sent notification to user {user.telegram_id} for check {check.id}")
            return True

        except TelegramError as e:
            logger.error(f"Telegram error sending notification to user {user.telegram_id}: {e}")

            # Save failed notification
            try:
                with self.db.get_session() as session:
                    notification = Notification(
                        user_id=user.id,
                        check_id=check.id,
                        message=message if 'message' in locals() else "Error formatting message",
                        sent_at=datetime.now(),
                        success=False,
                        error_message=str(e)
                    )
                    session.add(notification)
                    session.commit()
            except:
                pass

            return False

        except Exception as e:
            logger.error(f"Error sending notification to user {user.telegram_id}: {e}", exc_info=True)
            return False

    async def send_error_notification(
        self,
        user: User,
        check: Check,
        error_message: str
    ) -> bool:
        """
        Send error notification to user

        Args:
            user: User object
            check: Check object
            error_message: Error message

        Returns:
            True if notification sent successfully, False otherwise
        """
        try:
            service = check.subscription.service

            message = (
                f"⚠️ *Check Failed*\n\n"
                f"*Service:* {service.service_name}\n"
                f"*Error:* {error_message}\n\n"
                f"_We'll try again at the next scheduled check._"
            )

            await self.bot.send_message(
                chat_id=user.telegram_id,
                text=message,
                parse_mode='Markdown'
            )

            # Save notification record
            with self.db.get_session() as session:
                notification = Notification(
                    user_id=user.id,
                    check_id=check.id,
                    message=message,
                    sent_at=datetime.now(),
                    success=True
                )
                session.add(notification)
                session.commit()

            logger.info(f"Sent error notification to user {user.telegram_id}")
            return True

        except Exception as e:
            logger.error(f"Error sending error notification: {e}")
            return False

    async def send_admin_alert(self, message: str, admin_chat_id: Optional[int] = None) -> bool:
        """
        Send alert to admin

        Args:
            message: Alert message
            admin_chat_id: Admin chat ID (optional, from env if not provided)

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            if not admin_chat_id:
                import os
                admin_chat_id = os.getenv('ADMIN_TELEGRAM_ID')

            if not admin_chat_id:
                logger.warning("No admin chat ID configured")
                return False

            await self.bot.send_message(
                chat_id=admin_chat_id,
                text=f"🔔 *Admin Alert*\n\n{message}",
                parse_mode='Markdown'
            )

            logger.info("Sent admin alert")
            return True

        except Exception as e:
            logger.error(f"Error sending admin alert: {e}")
            return False

    async def send_custom_message(
        self,
        telegram_id: int,
        message: str,
        parse_mode: str = 'Markdown'
    ) -> bool:
        """
        Send custom message to user

        Args:
            telegram_id: User's Telegram ID
            message: Message text
            parse_mode: Parse mode (Markdown or HTML)

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            await self.bot.send_message(
                chat_id=telegram_id,
                text=message,
                parse_mode=parse_mode
            )

            logger.info(f"Sent custom message to user {telegram_id}")
            return True

        except Exception as e:
            logger.error(f"Error sending custom message to user {telegram_id}: {e}")
            return False
