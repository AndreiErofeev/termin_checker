"""
Appointment Check Service

This service handles running appointment checks for subscriptions
and storing results in the database.
"""

import logging
from datetime import datetime
from typing import Optional
from pathlib import Path

from sqlalchemy.orm import joinedload

from ..core.appointment_checker import AppointmentChecker, CheckResult as CheckerResult
from ..core.database import Database
from ..core.models import Check, Appointment, Subscription, CheckStatus

logger = logging.getLogger(__name__)


class CheckService:
    """Service for managing appointment checks"""

    def __init__(self, db: Database):
        """
        Initialize check service

        Args:
            db: Database instance
        """
        self.db = db
        self.checker = None

    async def run_subscription_check(self, subscription_id: int) -> Optional[Check]:
        """
        Run an appointment check for a subscription

        Args:
            subscription_id: ID of the subscription to check

        Returns:
            Check object with results, or None if error
        """
        try:
            # Load subscription with relationships
            with self.db.get_session() as session:
                subscription = session.query(Subscription).options(
                    joinedload(Subscription.service),
                    joinedload(Subscription.user)
                ).filter(
                    Subscription.id == subscription_id,
                    Subscription.active == True
                ).first()

                if not subscription:
                    logger.warning(f"Subscription {subscription_id} not found or inactive")
                    return None

                # Get service details
                service = subscription.service
                user = subscription.user

                logger.info(
                    f"Running check for user {user.telegram_id} - "
                    f"{service.category} / {service.service_name}"
                )

                # Initialize checker if needed
                if not self.checker:
                    self.checker = AppointmentChecker()

                # Run the check
                result: CheckerResult = await self.checker.check_appointments(
                    category=service.category,
                    service=service.service_name,
                    quantity=subscription.quantity
                )

                # Create Check record
                check = Check(
                    subscription_id=subscription.id,
                    status=CheckStatus(result.status),
                    available=result.available,
                    appointment_count=len(result.appointments),
                    screenshot_path=result.screenshot_path,
                    error_message=result.error_message,
                    checked_at=datetime.fromisoformat(result.checked_at) if result.checked_at else datetime.now()
                )

                session.add(check)
                session.flush()  # Get check.id

                # Create Appointment records if found
                if result.appointments:
                    for apt_slot in result.appointments:
                        appointment = Appointment(
                            check_id=check.id,
                            appointment_date=apt_slot.date or "",
                            appointment_time=apt_slot.time or "",
                            location=apt_slot.location or "",
                            raw_text=apt_slot.raw_text
                        )
                        session.add(appointment)

                # Update subscription last_checked
                subscription.last_checked_at = check.checked_at

                # Update service statistics
                service.total_checks += 1
                if result.available:
                    service.last_appointments_at = check.checked_at

                session.commit()

                # Re-fetch check with appointments loaded
                check = session.query(Check).options(
                    joinedload(Check.appointments)
                ).filter(Check.id == check.id).first()

                logger.info(
                    f"Check completed: {check.status.value}, "
                    f"Appointments: {check.appointment_count}"
                )

                return check

        except Exception as e:
            logger.error(f"Error running check for subscription {subscription_id}: {e}", exc_info=True)

            # Try to save error state
            try:
                with self.db.get_session() as session:
                    check = Check(
                        subscription_id=subscription_id,
                        status=CheckStatus.ERROR,
                        available=False,
                        appointment_count=0,
                        error_message=str(e),
                        checked_at=datetime.now()
                    )
                    session.add(check)
                    session.commit()
                    return check
            except:
                pass

            return None

    async def cleanup(self):
        """Clean up resources"""
        if self.checker:
            await self.checker.cleanup()
