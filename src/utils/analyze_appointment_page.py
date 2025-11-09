"""
Analyze the appointment page HTML structure to improve date extraction

This script navigates to a service with known appointments and
analyzes the HTML/DOM structure to understand how to extract dates properly.
"""

import asyncio
import json
import logging
from pathlib import Path
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def analyze_appointment_page():
    """Analyze the structure of an appointment page"""

    # Use a service known to have appointments
    CATEGORY = "Abholung Führerschein / Rückfragen"
    SERVICE = "Abholung Führerschein"

    logger.info(f"Analyzing: {SERVICE}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        page = await browser.new_page()

        # Navigate to service
        await page.goto("https://termine.duesseldorf.de/select2?md=3")

        # Handle cookies
        try:
            await page.get_by_role("button", name="Akzeptieren").click(timeout=3000)
        except:
            pass

        # Navigate to service
        await page.get_by_text(CATEGORY, exact=True).click()
        await page.wait_for_timeout(500)

        row = page.locator("li").filter(has_text=SERVICE).first
        await row.click()
        await page.wait_for_timeout(300)

        spin = row.locator("input[type=number]")
        await spin.fill("")
        await spin.type("1")
        await spin.press("Tab")

        weiter = page.get_by_role("button", name="Weiter", exact=True)
        await weiter.click()
        await page.wait_for_load_state("domcontentloaded")

        try:
            popup = page.locator("button:has-text('OK')")
            if await popup.count() > 0:
                await popup.first.click()
                await page.wait_for_timeout(500)
        except:
            pass

        await page.get_by_role("button", name="Weiter", exact=True).click()
        await page.wait_for_load_state("networkidle", timeout=15000)

        logger.info("Reached appointment page. Analyzing structure...")

        # Save full HTML
        html = await page.content()
        output_dir = Path("analysis")
        output_dir.mkdir(exist_ok=True)

        with open(output_dir / "appointment_page.html", 'w', encoding='utf-8') as f:
            f.write(html)

        logger.info(f"✓ Saved HTML to: {output_dir}/appointment_page.html")

        # Take screenshot
        await page.screenshot(path=str(output_dir / "appointment_page.png"), full_page=True)

        # Analyze calendar structure
        logger.info("\nAnalyzing calendar structure...")

        # Look for calendar container
        calendar_selectors = [
            ".calendar",
            ".datepicker",
            "#calendar",
            "[class*='calendar']",
            "[id*='calendar']",
            "table.table",  # Bootstrap table
            ".fc-calendar"  # FullCalendar
        ]

        for selector in calendar_selectors:
            elem = page.locator(selector)
            count = await elem.count()
            if count > 0:
                logger.info(f"  ✓ Found calendar container: {selector} ({count} elements)")

                # Get outer HTML of first match
                if count > 0:
                    html_snippet = await elem.first.evaluate("el => el.outerHTML")
                    snippet_path = output_dir / f"calendar_{selector.replace('.', '').replace('#', '').replace('[', '').replace(']', '')}.html"
                    with open(snippet_path, 'w', encoding='utf-8') as f:
                        f.write(html_snippet)
                    logger.info(f"    Saved snippet to: {snippet_path}")

        # Look for date headers
        logger.info("\nLooking for date headers...")
        date_selectors = [
            "th",  # Table headers
            ".calendar-header",
            ".date-header",
            "[class*='date']",
            "h3", "h4", "h5"
        ]

        dates_found = {}

        for selector in date_selectors:
            elems = page.locator(selector)
            count = await elems.count()

            if count > 0:
                for i in range(min(count, 10)):
                    text = await elems.nth(i).text_content()
                    if text and text.strip():
                        # Check if contains date pattern
                        import re
                        if re.search(r'\d{1,2}\.\d{1,2}\.|\w+,\s*\d{1,2}\.\d{1,2}\.', text):
                            if selector not in dates_found:
                                dates_found[selector] = []
                            dates_found[selector].append(text.strip())

        if dates_found:
            logger.info("  ✓ Found date headers:")
            for selector, dates in dates_found.items():
                logger.info(f"    {selector}: {dates[:3]}")  # Show first 3

        # Look for time slots
        logger.info("\nLooking for time slots...")

        # Get all table cells
        cells = page.locator("td")
        cell_count = await cells.count()
        logger.info(f"  Found {cell_count} table cells")

        # Analyze first 20 cells
        cell_data = []
        for i in range(min(cell_count, 20)):
            cell = cells.nth(i)
            text = await cell.text_content()
            classes = await cell.get_attribute("class")
            data_date = await cell.get_attribute("data-date")
            data_time = await cell.get_attribute("data-time")

            cell_info = {
                'index': i,
                'text': text.strip() if text else "",
                'classes': classes,
                'data-date': data_date,
                'data-time': data_time,
            }

            cell_data.append(cell_info)

        with open(output_dir / "cell_analysis.json", 'w', encoding='utf-8') as f:
            json.dump(cell_data, f, indent=2, ensure_ascii=False)

        logger.info(f"  ✓ Saved cell analysis to: {output_dir}/cell_analysis.json")

        # Show some sample cells
        logger.info("\n  Sample cells:")
        for cell in cell_data[:5]:
            logger.info(f"    Cell {cell['index']}: '{cell['text']}' | classes: {cell['classes']}")

        # Look for calendar navigation (next/prev month)
        logger.info("\nLooking for calendar navigation...")
        nav_selectors = [
            "button:has-text('›')",
            "button:has-text('‹')",
            "a:has-text('›')",
            "a:has-text('‹')",
            ".next",
            ".prev",
            ".calendar-next",
            ".calendar-prev"
        ]

        for selector in nav_selectors:
            elem = page.locator(selector)
            count = await elem.count()
            if count > 0:
                logger.info(f"  ✓ Found navigation: {selector} ({count} elements)")

        # Analyze page structure
        logger.info("\nPage structure overview:")

        # Get main container
        main = page.locator("main, #main, .main, .content, #content")
        if await main.count() > 0:
            structure = await main.first.evaluate("""
                el => {
                    const getStructure = (elem, depth = 0) => {
                        if (depth > 3) return null;  // Limit depth

                        const tag = elem.tagName.toLowerCase();
                        const id = elem.id ? `#${elem.id}` : '';
                        const classes = elem.className ? `.${elem.className.split(' ').join('.')}` : '';
                        const children = Array.from(elem.children).slice(0, 5).map(child => getStructure(child, depth + 1)).filter(Boolean);

                        return {
                            tag: tag + id + classes,
                            children: children
                        };
                    };

                    return getStructure(el);
                }
            """)

            with open(output_dir / "page_structure.json", 'w', encoding='utf-8') as f:
                json.dump(structure, f, indent=2)

            logger.info(f"  ✓ Saved page structure to: {output_dir}/page_structure.json")

        logger.info("\n" + "="*60)
        logger.info("Analysis complete!")
        logger.info(f"All files saved to: {output_dir}/")
        logger.info("="*60)

        # Keep browser open for manual inspection
        logger.info("\nBrowser will stay open for manual inspection.")
        logger.info("Press Enter to close...")
        await asyncio.to_thread(input)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(analyze_appointment_page())
