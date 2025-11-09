"""
Düsseldorf Appointment Checker - Refactored Core Module

This module provides functionality to check appointment availability
on the Düsseldorf city appointment booking website.
"""

import asyncio
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from playwright.async_api import async_playwright, expect, Page, Browser, TimeoutError as PlaywrightTimeout


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class AppointmentSlot:
    """Represents a single appointment slot"""
    date: Optional[str] = None
    time: Optional[str] = None
    location: Optional[str] = None
    raw_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CheckResult:
    """Result of an appointment check"""
    status: str  # success, error, no_appointments, appointments_found
    available: bool
    appointments: List[AppointmentSlot]
    screenshot_path: Optional[str] = None
    error_message: Optional[str] = None
    checked_at: str = ""
    service_name: str = ""
    category_name: str = ""

    def __post_init__(self):
        if not self.checked_at:
            self.checked_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'appointments': [apt.to_dict() for apt in self.appointments]
        }


class AppointmentChecker:
    """Main class for checking appointment availability"""

    # Detection patterns for "no appointments" messages
    NO_APPOINTMENT_PATTERNS = [
        "Zurzeit sind keine Termine frei",
        "Zurzeit sind keine Termine verfügbar",
        "Leider sind derzeit keine Termine verfügbar",
        "Es sind zurzeit keine Termine verfügbar",
        "Aktuell sind keine Termine buchbar",
        "Keine Zeiten verfügbar",
        "keine freien Termine"
    ]

    # Default configuration
    DEFAULT_CONFIG = {
        'base_url': 'https://termine.duesseldorf.de/select2?md=3',
        'headless': False,
        'slow_mo': 300,
        'timeout': 30000,
        'screenshot_dir': 'screenshots',
        'debug': True
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the appointment checker

        Args:
            config: Configuration dictionary (optional)
        """
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        self.screenshot_dir = Path(self.config['screenshot_dir'])
        self.screenshot_dir.mkdir(exist_ok=True)

    async def check_appointments(
        self,
        category: str,
        service: str,
        quantity: int = 1
    ) -> CheckResult:
        """
        Check appointment availability for a specific service

        Args:
            category: The service category to expand
            service: The specific service to select
            quantity: Number of appointments needed (default: 1)

        Returns:
            CheckResult object with status and appointment details
        """
        logger.info(f"Starting appointment check for: {service}")

        browser: Optional[Browser] = None

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=self.config['headless'],
                    slow_mo=self.config['slow_mo']
                )

                page = await browser.new_page()
                page.set_default_timeout(self.config['timeout'])

                # Navigate through the booking process
                await self._navigate_to_service(page, category, service, quantity)

                # Wait for final page to load
                await page.wait_for_load_state("networkidle", timeout=15000)

                # Detect and extract appointments
                result = await self._detect_and_extract_appointments(page, service, category)

                # Take screenshot
                screenshot_path = await self._save_screenshot(page, result.status)
                result.screenshot_path = screenshot_path

                logger.info(f"Check completed. Status: {result.status}, Available: {result.available}")

                return result

        except PlaywrightTimeout as e:
            logger.error(f"Timeout error: {e}")
            screenshot_path = await self._save_error_screenshot(page, "timeout") if page else None
            return CheckResult(
                status="error",
                available=False,
                appointments=[],
                error_message=f"Timeout: {str(e)}",
                screenshot_path=screenshot_path,
                service_name=service,
                category_name=category
            )

        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            screenshot_path = await self._save_error_screenshot(page, "error") if page else None
            return CheckResult(
                status="error",
                available=False,
                appointments=[],
                error_message=str(e),
                screenshot_path=screenshot_path,
                service_name=service,
                category_name=category
            )

        finally:
            if browser:
                await browser.close()
                logger.debug("Browser closed")

    async def _navigate_to_service(
        self,
        page: Page,
        category: str,
        service: str,
        quantity: int
    ) -> None:
        """Navigate through the booking form to the appointments page"""

        # Step 1: Load initial page
        logger.info("Step 1: Loading initial page")
        await page.goto(self.config['base_url'])

        # Step 1.1: Handle cookie consent
        logger.info("Step 1.1: Handling cookie consent")
        await self._handle_cookie_consent(page)

        # Step 2: Expand category
        logger.info(f"Step 2: Expanding category: {category}")
        try:
            category_element = page.get_by_text(category, exact=True)
            await category_element.click(timeout=10000)
            await page.wait_for_timeout(500)  # Wait for accordion animation
        except Exception as e:
            logger.error(f"Failed to expand category: {e}")
            raise

        # Step 3: Select service
        logger.info(f"Step 3: Selecting service: {service}")
        try:
            row = page.locator("li").filter(has_text=service).first
            await row.click()
            await page.wait_for_timeout(300)
        except Exception as e:
            logger.error(f"Failed to select service: {e}")
            raise

        # Step 3.1: Set quantity
        logger.info(f"Step 3.1: Setting quantity to {quantity}")
        await self._set_quantity(row, quantity)

        # Step 4: Click first "Weiter" button
        logger.info("Step 4: Clicking first 'Weiter' button")
        try:
            weiter = page.get_by_role("button", name="Weiter")
            await expect(weiter).to_be_enabled(timeout=10000)
            await weiter.click()
            await page.wait_for_load_state("domcontentloaded")
        except Exception as e:
            logger.error(f"Failed to click first Weiter: {e}")
            raise

        # Step 5: Handle optional confirmation popup
        logger.info("Step 5: Checking for confirmation popup")
        await self._handle_popup(page)

        # Step 6: Click second "Weiter" button
        logger.info("Step 6: Clicking second 'Weiter' button")
        try:
            weiter2 = page.get_by_role("button", name="Weiter")
            await weiter2.click(timeout=10000)
            await page.wait_for_load_state("domcontentloaded")
        except Exception as e:
            logger.error(f"Failed to click second Weiter: {e}")
            raise

    async def _handle_cookie_consent(self, page: Page) -> None:
        """Handle cookie consent banner if present"""
        cookie_buttons = [
            "Akzeptieren",
            "Alle akzeptieren",
            "Zustimmen",
            "OK"
        ]

        for button_text in cookie_buttons:
            try:
                accept_button = page.get_by_role("button", name=button_text)
                await accept_button.click(timeout=3000)
                logger.info(f"Cookie consent accepted via '{button_text}'")
                await page.wait_for_timeout(500)
                return
            except:
                continue

        logger.info("No cookie banner found or already accepted")

    async def _set_quantity(self, row_locator, quantity: int) -> None:
        """Set the quantity input field"""
        try:
            spin = row_locator.locator("input[type=number]")
            await expect(spin).to_be_visible(timeout=10000)

            # Clear and set value
            await spin.fill("")
            await spin.type(str(quantity))
            await spin.press("Tab")  # Trigger change event

            logger.debug(f"Quantity set to {quantity}")
        except Exception as e:
            logger.error(f"Failed to set quantity: {e}")
            raise

    async def _handle_popup(self, page: Page) -> None:
        """Handle optional confirmation popup"""
        popup_buttons = [
            "button:has-text('OK')",
            "button:has-text('Fortfahren')",
            "button:has-text('Bestätigen')"
        ]

        for selector in popup_buttons:
            try:
                popup = page.locator(selector)
                count = await popup.count()
                if count > 0:
                    await popup.first.click()
                    logger.info(f"Popup handled: {selector}")
                    await page.wait_for_timeout(500)
                    return
            except:
                continue

        logger.debug("No popup found")

    async def _detect_and_extract_appointments(
        self,
        page: Page,
        service: str,
        category: str
    ) -> CheckResult:
        """
        Detect if appointments are available and extract details

        Args:
            page: Playwright page object
            service: Service name for metadata
            category: Category name for metadata

        Returns:
            CheckResult with detection and extraction results
        """
        # Get page content
        html = await page.content()

        # Check for "no appointments" patterns
        for pattern in self.NO_APPOINTMENT_PATTERNS:
            if pattern.lower() in html.lower():
                logger.info(f"No appointments detected (pattern: {pattern})")
                return CheckResult(
                    status="no_appointments",
                    available=False,
                    appointments=[],
                    service_name=service,
                    category_name=category
                )

        # If no "no appointments" message, try to extract appointments
        logger.info("No 'no appointments' message found, attempting to extract slots")
        appointments = await self._extract_appointment_slots(page)

        if appointments:
            logger.info(f"Found {len(appointments)} appointment slots")
            return CheckResult(
                status="appointments_found",
                available=True,
                appointments=appointments,
                service_name=service,
                category_name=category
            )
        else:
            logger.warning("Could not determine appointment status conclusively")
            return CheckResult(
                status="unknown",
                available=False,
                appointments=[],
                error_message="Could not detect appointments or confirm unavailability",
                service_name=service,
                category_name=category
            )

    async def _extract_appointment_slots(self, page: Page) -> List[AppointmentSlot]:
        """
        Extract available appointment slots from the page

        The Düsseldorf website uses an accordion structure where:
        - Each date is in an <h3> tag (e.g., "Dienstag, 18.11.2025")
        - Below each h3 is a div containing a table with time slot buttons
        - Time slots are in <button> or <td> elements containing time strings

        Args:
            page: Playwright page object

        Returns:
            List of AppointmentSlot objects with dates and times
        """
        appointments = []

        try:
            # Find all date headers (accordion h3 elements)
            date_headers = page.locator("h3.ui-accordion-header")
            header_count = await date_headers.count()

            if header_count == 0:
                logger.warning("No date accordion headers found")
                return appointments

            logger.debug(f"Found {header_count} date accordion headers")

            # Process each date section
            for i in range(header_count):
                header = date_headers.nth(i)

                # Extract the date text from the h3
                date_text = await header.text_content()
                if not date_text:
                    continue

                date_text = date_text.strip()
                logger.debug(f"Processing date section: {date_text}")

                # Parse the date from German format (e.g., "Dienstag, 18.11.2025")
                parsed_date = self._parse_german_date(date_text)

                if not parsed_date:
                    logger.warning(f"Could not parse date from: {date_text}")
                    continue

                # Find the corresponding accordion panel (div after the h3)
                # Use the aria-controls attribute to find the right panel
                panel_id = await header.get_attribute("aria-controls")

                if panel_id:
                    panel = page.locator(f"#{panel_id}")
                else:
                    # Fallback: next sibling div
                    panel = header.locator("+ div")

                # Find all time slot buttons within this panel
                # Look for buttons or table cells containing times
                time_buttons = panel.locator("button.suggest_btn, td button")
                button_count = await time_buttons.count()

                logger.debug(f"  Found {button_count} time slot buttons for {date_text}")

                # Extract each time slot
                for j in range(button_count):
                    button = time_buttons.nth(j)
                    time_text = await button.text_content()

                    if not time_text:
                        continue

                    time_text = time_text.strip()

                    # Parse time (should be in format like "14:00")
                    _, parsed_time = self._parse_datetime_from_text(time_text)

                    if parsed_time:
                        appointment = AppointmentSlot(
                            date=parsed_date,
                            time=parsed_time,
                            raw_text=f"{date_text} {time_text}"
                        )
                        appointments.append(appointment)

            if appointments:
                logger.info(f"Extracted {len(appointments)} appointment slots across {header_count} dates")
            else:
                logger.warning("No appointment slots extracted despite finding date headers")

            return appointments

        except Exception as e:
            logger.error(f"Error extracting appointments: {e}", exc_info=True)
            return appointments

    def _parse_datetime_from_text(self, text: str) -> tuple[Optional[str], Optional[str]]:
        """
        Parse date and time from German text

        Examples:
        - "Montag, 15.01.2025 um 14:30 Uhr"
        - "15.01.2025 14:30"
        - "14:30 Uhr"

        Args:
            text: Text containing date/time information

        Returns:
            Tuple of (date, time) or (None, None) if not found
        """
        if not text:
            return None, None

        date_match = None
        time_match = None

        # German date pattern: DD.MM.YYYY
        date_pattern = r'\b(\d{1,2}\.\d{1,2}\.\d{4})\b'
        date_result = re.search(date_pattern, text)
        if date_result:
            date_match = date_result.group(1)

        # Time pattern: HH:MM
        time_pattern = r'\b(\d{1,2}:\d{2})\b'
        time_result = re.search(time_pattern, text)
        if time_result:
            time_match = time_result.group(1)

        return date_match, time_match

    def _parse_german_date(self, text: str) -> Optional[str]:
        """
        Parse German date format to ISO format

        Handles formats like:
        - "Dienstag, 18.11.2025" -> "2025-11-18"
        - "Mittwoch, 19.11.2025" -> "2025-11-19"
        - "18.11.2025" -> "2025-11-18"

        Args:
            text: German date string

        Returns:
            ISO format date string (YYYY-MM-DD) or None
        """
        if not text:
            return None

        # Extract DD.MM.YYYY pattern
        date_pattern = r'\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b'
        match = re.search(date_pattern, text)

        if match:
            day = match.group(1).zfill(2)  # Pad with zero if needed
            month = match.group(2).zfill(2)
            year = match.group(3)

            # Convert to ISO format: YYYY-MM-DD
            iso_date = f"{year}-{month}-{day}"

            logger.debug(f"Parsed date '{text}' -> '{iso_date}'")
            return iso_date

        logger.warning(f"Could not parse date from: {text}")
        return None

    async def _save_screenshot(self, page: Page, status: str) -> str:
        """Save screenshot with timestamp and status"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{status}_{timestamp}.png"
        filepath = self.screenshot_dir / filename

        try:
            await page.screenshot(path=str(filepath), full_page=True)
            logger.info(f"Screenshot saved: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Failed to save screenshot: {e}")
            return ""

    async def _save_error_screenshot(self, page: Page, error_type: str) -> Optional[str]:
        """Save screenshot when error occurs"""
        try:
            return await self._save_screenshot(page, f"error_{error_type}")
        except:
            return None


# Convenience function for simple usage
async def check_appointments(
    category: str,
    service: str,
    quantity: int = 1,
    config: Optional[Dict[str, Any]] = None
) -> CheckResult:
    """
    Convenience function to check appointments

    Args:
        category: Service category
        service: Specific service
        quantity: Number of appointments (default: 1)
        config: Optional configuration dict

    Returns:
        CheckResult object
    """
    checker = AppointmentChecker(config)
    return await checker.check_appointments(category, service, quantity)


# Example usage
async def main():
    """Example usage"""
    # CATEGORY = "Umschreibung ausländische Fahrerlaubnis / Dienstfahrerlaubnis"
    # SERVICE = "Umschreibung ausländischer Führerschein (sonstige Staaten)"

    CATEGORY = "Abholung Führerschein / Rückfragen"
    SERVICE = "Abholung Führerschein"

    # Custom configuration
    config = {
        'headless': False,
        'slow_mo': 300,
        'screenshot_dir': 'screenshots',
        'debug': True
    }

    result = await check_appointments(CATEGORY, SERVICE, quantity=1, config=config)

    # Print result
    print("\n" + "="*60)
    print("APPOINTMENT CHECK RESULT")
    print("="*60)
    print(f"Status: {result.status}")
    print(f"Available: {result.available}")
    print(f"Service: {result.service_name}")
    print(f"Category: {result.category_name}")
    print(f"Checked at: {result.checked_at}")

    if result.error_message:
        print(f"Error: {result.error_message}")

    if result.appointments:
        print(f"\nFound {len(result.appointments)} appointments:")
        for i, apt in enumerate(result.appointments, 1):
            print(f"\n  {i}. Date: {apt.date}, Time: {apt.time}")
            print(f"     Raw: {apt.raw_text}")
    else:
        print("\nNo appointments available")

    if result.screenshot_path:
        print(f"\nScreenshot: {result.screenshot_path}")

    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
