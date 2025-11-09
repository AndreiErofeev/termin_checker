"""
Comprehensive Test Script - Test ALL services on termine.duesseldorf.de

This script will:
1. Scrape all available categories and services from the website
2. Test appointment checking for each service
3. Generate a report of results
4. Save HTML snapshots for services with appointments
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from playwright.async_api import async_playwright, Page

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ServiceDiscovery:
    """Discover all available services on the website"""

    def __init__(self, base_url: str = "https://termine.duesseldorf.de/select2?md=3"):
        self.base_url = base_url
        self.services = []

    async def discover_all_services(self) -> List[Dict[str, Any]]:
        """
        Scrape the website to find all available categories and services

        Returns:
            List of dicts with category and service information
        """
        logger.info("Starting service discovery...")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=200)
            page = await browser.new_page()

            try:
                # Navigate to the page
                await page.goto(self.base_url)
                await page.wait_for_load_state("networkidle")

                # Handle cookie consent
                await self._handle_cookies(page)

                # Find all categories (accordion sections)
                categories = await self._find_categories(page)

                logger.info(f"Found {len(categories)} categories")

                # For each category, find all services
                for i, category in enumerate(categories, 1):
                    logger.info(f"Processing category {i}/{len(categories)}: {category['name']}")

                    # Expand the category
                    try:
                        await category['element'].click()
                        await page.wait_for_timeout(1000)  # Wait for accordion animation

                        # Find services in this category
                        services = await self._find_services_in_category(page, category['name'])

                        logger.info(f"  Found {len(services)} services in this category")

                        self.services.extend(services)

                        # Collapse the category (optional, for cleaner screenshots)
                        # await category['element'].click()
                        # await page.wait_for_timeout(500)

                    except Exception as e:
                        logger.error(f"  Error processing category '{category['name']}': {e}")
                        continue

                # Save screenshot of all categories
                screenshot_dir = Path("test_results")
                screenshot_dir.mkdir(exist_ok=True)
                await page.screenshot(path=str(screenshot_dir / "all_categories.png"), full_page=True)

            finally:
                await browser.close()

        logger.info(f"Discovery complete. Found {len(self.services)} total services")
        return self.services

    async def _handle_cookies(self, page: Page):
        """Handle cookie consent banner"""
        cookie_buttons = ["Akzeptieren", "Alle akzeptieren", "Zustimmen", "OK"]

        for button_text in cookie_buttons:
            try:
                accept_button = page.get_by_role("button", name=button_text)
                await accept_button.click(timeout=3000)
                logger.info(f"Cookie consent accepted via '{button_text}'")
                await page.wait_for_timeout(500)
                return
            except:
                continue

    async def _find_categories(self, page: Page) -> List[Dict[str, Any]]:
        """Find all category accordion headers"""
        categories = []

        # Look for accordion headers - adjust selector based on actual HTML
        # Common patterns: h3, h4, button with aria-expanded, etc.
        selectors = [
            "h3:has-text('/')",  # Headers containing '/' (like "Category / Subcategory")
            "h4:has-text('/')",
            "button[aria-expanded]",
            ".accordion-header",
            ".category-header",
            "h3.panel-title",
            "button.panel-title"
        ]

        for selector in selectors:
            try:
                elements = page.locator(selector)
                count = await elements.count()

                if count > 0:
                    logger.debug(f"Found {count} category elements with selector: {selector}")

                    for i in range(count):
                        element = elements.nth(i)
                        text = await element.text_content()

                        if text and text.strip():
                            categories.append({
                                'name': text.strip(),
                                'element': element,
                                'selector': selector
                            })

                    if categories:
                        logger.info(f"Successfully found categories using selector: {selector}")
                        return categories

            except Exception as e:
                logger.debug(f"Selector '{selector}' failed: {e}")
                continue

        # Fallback: Look for any clickable elements that might be categories
        logger.warning("Could not find categories with known selectors. Trying fallback...")

        # Try to find list items or divs that look like categories
        fallback_selector = "li:has(ul), div:has(ul)"
        elements = page.locator(fallback_selector)
        count = await elements.count()

        for i in range(min(count, 20)):  # Limit to 20 to avoid too many false positives
            element = elements.nth(i)
            text = await element.text_content()

            if text and len(text.strip()) > 5 and '/' in text:
                categories.append({
                    'name': text.strip().split('\n')[0],  # Get first line
                    'element': element,
                    'selector': fallback_selector
                })

        return categories

    async def _find_services_in_category(self, page: Page, category_name: str) -> List[Dict[str, Any]]:
        """Find all services within an expanded category"""
        services = []

        # Services are typically in <li> elements within the expanded accordion
        # Look for list items that are now visible
        service_selectors = [
            "li:visible:has(input[type=number])",  # Li with quantity input
            "ul.in li, ul.show li",  # Li in expanded accordion (Bootstrap classes)
            "li.service-item",
            "li.appointment-service"
        ]

        for selector in service_selectors:
            try:
                elements = page.locator(selector)
                count = await elements.count()

                if count > 0:
                    logger.debug(f"  Found {count} service elements with selector: {selector}")

                    for i in range(count):
                        element = elements.nth(i)

                        # Get the service name (usually in a label or span)
                        text = await element.text_content()

                        # Clean up the text (remove quantity controls, etc.)
                        service_name = self._clean_service_name(text)

                        if service_name and len(service_name) > 3:
                            services.append({
                                'category': category_name,
                                'service': service_name,
                                'selector': selector
                            })

                    if services:
                        return services

            except Exception as e:
                logger.debug(f"  Service selector '{selector}' failed: {e}")
                continue

        return services

    def _clean_service_name(self, text: str) -> str:
        """Clean up service name by removing quantity controls and extra whitespace"""
        if not text:
            return ""

        # Remove newlines and extra whitespace
        cleaned = ' '.join(text.split())

        # Remove common artifacts (adjust based on actual HTML)
        artifacts = [
            '- +',  # Quantity controls
            'Anzahl:',
            'Menge:',
            '0 1 2 3 4 5',  # Number artifacts
        ]

        for artifact in artifacts:
            cleaned = cleaned.replace(artifact, '')

        return cleaned.strip()


class ServiceTester:
    """Test appointment availability for discovered services"""

    def __init__(self, base_url: str = "https://termine.duesseldorf.de/select2?md=3"):
        self.base_url = base_url
        self.results = []

    async def test_service(self, category: str, service: str) -> Dict[str, Any]:
        """
        Test a single service for appointment availability

        Returns:
            Dict with test results
        """
        logger.info(f"Testing: {category} > {service}")

        result = {
            'category': category,
            'service': service,
            'timestamp': datetime.now().isoformat(),
            'status': 'unknown',
            'appointments_found': False,
            'appointment_count': 0,
            'error': None,
            'screenshot': None
        }

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, slow_mo=100)
            page = await browser.new_page()
            page.set_default_timeout(30000)

            try:
                # Navigate
                await page.goto(self.base_url)

                # Handle cookies
                await self._handle_cookies(page)

                # Expand category and select service
                await self._navigate_to_service(page, category, service)

                # Wait for result page
                await page.wait_for_load_state("networkidle", timeout=15000)

                # Analyze the page
                html = await page.content()

                # Check for "no appointments"
                no_appt_patterns = [
                    "Zurzeit sind keine Termine",
                    "keine freien Termine",
                    "Keine Zeiten verfügbar",
                    "derzeit keine Termine",
                    "Aktuell sind keine Termine"
                ]

                has_no_appointments = any(pattern.lower() in html.lower() for pattern in no_appt_patterns)

                if has_no_appointments:
                    result['status'] = 'no_appointments'
                    result['appointments_found'] = False
                else:
                    # Try to count appointment slots
                    appointment_selectors = [
                        "td:not(.disabled):not(.unavailable)",
                        "button.time-slot",
                        "a.appointment-time"
                    ]

                    for selector in appointment_selectors:
                        slots = page.locator(selector)
                        count = await slots.count()

                        if count > 0:
                            result['status'] = 'appointments_found'
                            result['appointments_found'] = True
                            result['appointment_count'] = count
                            break

                    if not result['appointments_found']:
                        result['status'] = 'unknown'

                # Save screenshot
                screenshot_dir = Path("test_results/screenshots")
                screenshot_dir.mkdir(parents=True, exist_ok=True)

                safe_filename = f"{self._sanitize_filename(service)}_{result['status']}.png"
                screenshot_path = screenshot_dir / safe_filename

                await page.screenshot(path=str(screenshot_path), full_page=True)
                result['screenshot'] = str(screenshot_path)

                # Save HTML if appointments found
                if result['appointments_found']:
                    html_dir = Path("test_results/html")
                    html_dir.mkdir(parents=True, exist_ok=True)

                    html_filename = f"{self._sanitize_filename(service)}.html"
                    html_path = html_dir / html_filename

                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(html)

                    logger.info(f"  ✓ Found {result['appointment_count']} appointments! HTML saved.")

            except Exception as e:
                logger.error(f"  ✗ Error: {e}")
                result['status'] = 'error'
                result['error'] = str(e)

            finally:
                await browser.close()

        self.results.append(result)
        return result

    async def _handle_cookies(self, page: Page):
        """Handle cookie consent"""
        try:
            accept = page.get_by_role("button", name="Akzeptieren")
            await accept.click(timeout=3000)
        except:
            pass

    async def _navigate_to_service(self, page: Page, category: str, service: str):
        """Navigate to a specific service"""
        # Expand category
        await page.get_by_text(category, exact=True).click()
        await page.wait_for_timeout(500)

        # Select service
        row = page.locator("li").filter(has_text=service).first
        await row.click()
        await page.wait_for_timeout(300)

        # Set quantity
        spin = row.locator("input[type=number]")
        await spin.fill("")
        await spin.type("1")
        await spin.press("Tab")

        # Click Weiter
        weiter = page.get_by_role("button", name="Weiter")
        await weiter.click()
        await page.wait_for_load_state("domcontentloaded")

        # Handle popup
        try:
            popup = page.locator("button:has-text('OK')")
            if await popup.count() > 0:
                await popup.first.click()
        except:
            pass

        # Click second Weiter
        await page.get_by_role("button", name="Weiter").click()

    def _sanitize_filename(self, name: str) -> str:
        """Create safe filename from service name"""
        import re
        # Remove special characters
        safe = re.sub(r'[^a-zA-Z0-9_\-]', '_', name)
        # Limit length
        return safe[:100]


async def main():
    """Main test execution"""
    logger.info("=" * 80)
    logger.info("COMPREHENSIVE SERVICE TEST - Düsseldorf Termine")
    logger.info("=" * 80)

    # Step 1: Discover all services
    logger.info("\n[STEP 1] Discovering all available services...")
    discovery = ServiceDiscovery()
    services = await discovery.discover_all_services()

    # Save discovered services
    results_dir = Path("test_results")
    results_dir.mkdir(exist_ok=True)

    with open(results_dir / "discovered_services.json", 'w', encoding='utf-8') as f:
        json.dump(services, f, indent=2, ensure_ascii=False)

    logger.info(f"\nDiscovered {len(services)} services. Saved to discovered_services.json")

    # Step 2: Test each service
    logger.info(f"\n[STEP 2] Testing {len(services)} services for appointment availability...")
    logger.info("This may take a while...\n")

    tester = ServiceTester()

    for i, svc in enumerate(services, 1):
        logger.info(f"[{i}/{len(services)}] Testing: {svc['service']}")
        await tester.test_service(svc['category'], svc['service'])

        # Small delay to avoid rate limiting
        await asyncio.sleep(2)

    # Step 3: Generate report
    logger.info("\n[STEP 3] Generating test report...")

    # Save detailed results
    with open(results_dir / "test_results.json", 'w', encoding='utf-8') as f:
        json.dump(tester.results, f, indent=2, ensure_ascii=False)

    # Generate summary
    total = len(tester.results)
    with_appointments = sum(1 for r in tester.results if r['appointments_found'])
    no_appointments = sum(1 for r in tester.results if r['status'] == 'no_appointments')
    errors = sum(1 for r in tester.results if r['status'] == 'error')
    unknown = sum(1 for r in tester.results if r['status'] == 'unknown')

    summary = {
        'total_services': total,
        'with_appointments': with_appointments,
        'no_appointments': no_appointments,
        'errors': errors,
        'unknown': unknown,
        'timestamp': datetime.now().isoformat()
    }

    with open(results_dir / "summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total services tested: {total}")
    logger.info(f"✓ With appointments:   {with_appointments} ({with_appointments/total*100:.1f}%)")
    logger.info(f"✗ No appointments:     {no_appointments} ({no_appointments/total*100:.1f}%)")
    logger.info(f"! Errors:              {errors} ({errors/total*100:.1f}%)")
    logger.info(f"? Unknown:             {unknown} ({unknown/total*100:.1f}%)")
    logger.info("=" * 80)

    # List services with appointments
    if with_appointments > 0:
        logger.info("\n📅 SERVICES WITH APPOINTMENTS AVAILABLE:")
        for r in tester.results:
            if r['appointments_found']:
                logger.info(f"  • {r['service']} ({r['appointment_count']} slots)")
                logger.info(f"    Category: {r['category']}")
                logger.info(f"    Screenshot: {r['screenshot']}")

    logger.info(f"\n✓ Full results saved to: {results_dir}/test_results.json")
    logger.info(f"✓ Summary saved to: {results_dir}/summary.json")
    logger.info(f"✓ Screenshots saved to: {results_dir}/screenshots/")


if __name__ == "__main__":
    asyncio.run(main())
