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
from ..core.models import Check, Appointment, Subscription, CheckStatus, Service

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

    def _get_checker(self, base_url: str) -> "AppointmentChecker":
        """Return (or initialize) the shared AppointmentChecker instance."""
        if not self.checker:
            self.checker = AppointmentChecker(config={'base_url': base_url, 'headless': True})
        else:
            self.checker.config['base_url'] = base_url
        return self.checker

    async def scrape_service(self, service_id: int, quantity: int) -> Optional[CheckerResult]:
        """Run one Playwright check for a service. Updates service.total_checks in DB."""
        with self.db.get_session() as session:
            service = session.query(Service).filter_by(id=service_id).first()
            if not service:
                logger.warning(f"Service {service_id} not found")
                return None
            category = service.category
            service_name = service.service_name
            base_url = service.base_url

        try:
            checker = self._get_checker(base_url)
            result: CheckerResult = await checker.check_appointments(
                category=category,
                service=service_name,
                quantity=quantity,
            )
        except Exception as e:
            logger.error(f"Error scraping service {service_id}: {e}", exc_info=True)
            return None

        try:
            with self.db.get_session() as session:
                service = session.query(Service).filter_by(id=service_id).first()
                if service:
                    service.total_checks += 1
                    if result.available:
                        service.last_appointments_at = datetime.now()
                    session.commit()
        except Exception as e:
            logger.warning(f"Failed to update service stats for {service_id}: {e}")

        logger.info(f"Scraped service {service_id}: {result.status}, available={result.available}")
        return result

    def record_check(self, subscription_id: int, result: CheckerResult, checked_at: datetime) -> Optional[Check]:
        """Save a Check record for a subscription from a pre-scraped result."""
        try:
            with self.db.get_session() as session:
                subscription = session.query(Subscription).filter(
                    Subscription.id == subscription_id,
                    Subscription.active == True,
                ).first()
                if not subscription:
                    logger.warning(f"Subscription {subscription_id} not found or inactive")
                    return None

                check = Check(
                    subscription_id=subscription_id,
                    status=CheckStatus(result.status),
                    available=result.available,
                    appointment_count=len(result.appointments),
                    screenshot_path=result.screenshot_path,
                    error_message=result.error_message,
                    checked_at=checked_at,
                )
                session.add(check)
                session.flush()

                if result.appointments:
                    for apt_slot in result.appointments:
                        session.add(Appointment(
                            check_id=check.id,
                            appointment_date=apt_slot.date or "",
                            appointment_time=apt_slot.time or "",
                            location=apt_slot.location or "",
                            raw_text=apt_slot.raw_text,
                        ))

                subscription.last_checked_at = checked_at
                session.commit()

                check = session.query(Check).options(
                    joinedload(Check.appointments),
                ).filter(Check.id == check.id).first()

                return check
        except Exception as e:
            logger.error(f"Error recording check for subscription {subscription_id}: {e}", exc_info=True)
            return None

    async def run_subscription_check(self, subscription_id: int) -> Optional[Check]:
        """Run a check for a single subscription. Used for manual checks from the bot."""
        with self.db.get_session() as session:
            subscription = session.query(Subscription).options(
                joinedload(Subscription.service),
            ).filter(
                Subscription.id == subscription_id,
                Subscription.active == True,
            ).first()
            if not subscription:
                logger.warning(f"Subscription {subscription_id} not found or inactive")
                return None
            service_id = subscription.service_id
            quantity = subscription.quantity

        checked_at = datetime.now()
        result = await self.scrape_service(service_id, quantity)

        if result is None:
            try:
                with self.db.get_session() as session:
                    check = Check(
                        subscription_id=subscription_id,
                        status=CheckStatus.ERROR,
                        available=False,
                        appointment_count=0,
                        error_message="Scrape failed",
                        checked_at=checked_at,
                    )
                    session.add(check)
                    session.commit()
                    return check
            except Exception:
                return None

        return self.record_check(subscription_id, result, checked_at)

    async def cleanup(self):
        """Clean up resources"""
        if self.checker:
            await self.checker.cleanup()
