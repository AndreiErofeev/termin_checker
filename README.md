# Düsseldorf Appointment Checker

Automated appointment availability checker for Düsseldorf city services (termine.duesseldorf.de).

## Features

- ✅ **Automated checking** of appointment availability
- ✅ **Smart detection** of available vs. unavailable appointments
- ✅ **Appointment extraction** with dates, times, and details
- ✅ **Screenshot capture** for verification
- ✅ **Structured logging** with detailed execution traces
- ✅ **Configurable services** via YAML configuration
- 🔄 **Multi-user support** (coming soon)
- 🤖 **Telegram bot integration** (coming soon)
- ⏰ **Scheduled checks** (coming soon)

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Poetry (recommended) or pip

### Installation

#### Option 1: Using Poetry (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd termin_checker

# Install dependencies
poetry install

# Install Playwright browsers
poetry run playwright install chromium
```

#### Option 2: Using pip

```bash
# Clone the repository
git clone <repository-url>
cd termin_checker

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Basic Usage

#### Run the checker directly

```bash
# Using Poetry
poetry run python appointment_checker.py

# Or with activated venv
python appointment_checker.py
```

#### Use as a module

```python
import asyncio
from appointment_checker import check_appointments

async def main():
    result = await check_appointments(
        category="Umschreibung ausländische Fahrerlaubnis / Dienstfahrerlaubnis",
        service="Umschreibung ausländischer Führerschein (sonstige Staaten)",
        quantity=1
    )

    print(f"Status: {result.status}")
    print(f"Available: {result.available}")
    print(f"Appointments found: {len(result.appointments)}")

asyncio.run(main())
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

Key variables:
- `HEADLESS`: Run browser in headless mode (default: false)
- `SLOW_MO`: Delay between actions in milliseconds (default: 300)
- `DEBUG`: Enable debug mode (default: true)
- `SCREENSHOT_DIR`: Directory for screenshots (default: screenshots)

### YAML Configuration

Edit `config.yaml` to customize:

```yaml
browser:
  headless: false
  slow_mo: 300
  timeout: 30000

services:
  - category: "Your Category"
    service: "Your Service"
    quantity: 1
    enabled: true
```

## Project Structure

```
termin_checker/
├── appointment_checker.py          # Main refactored checker module
├── dusseldorf_termin_checker_test_copy.py  # Original working version
├── config.yaml                     # Configuration file
├── .env.example                    # Environment variables template
├── requirements.txt                # Python dependencies
├── pyproject.toml                  # Poetry configuration
├── screenshots/                    # Screenshot output directory
└── README.md                       # This file
```

## How It Works

### Navigation Flow

1. **Load initial page** - Navigate to termine.duesseldorf.de
2. **Handle cookies** - Accept cookie consent if present
3. **Expand category** - Click on the service category accordion
4. **Select service** - Choose specific service from list
5. **Set quantity** - Enter number of appointments needed
6. **Navigate forward** - Click through "Weiter" buttons
7. **Handle popups** - Accept any confirmation dialogs
8. **Detect & Extract** - Analyze final page for appointment slots

### Detection Logic

The checker uses multiple strategies to determine appointment availability:

**No Appointments Detection:**
- Searches for German text patterns like:
  - "Zurzeit sind keine Termine frei"
  - "Keine Zeiten verfügbar"
  - "Aktuell sind keine Termine buchbar"

**Appointment Extraction:**
- Strategy 1: Calendar date cells (`td.buchbar`, `td.available`)
- Strategy 2: Time slot elements containing "Uhr"
- Strategy 3: Structured list items

### Result Structure

```python
{
    "status": "appointments_found" | "no_appointments" | "error" | "unknown",
    "available": bool,
    "appointments": [
        {
            "date": "15.01.2025",
            "time": "14:30",
            "location": "Optional location",
            "raw_text": "Original text from page"
        }
    ],
    "screenshot_path": "screenshots/appointments_found_20250109_143022.png",
    "error_message": null,
    "checked_at": "2025-01-09T14:30:22.123456",
    "service_name": "Service name",
    "category_name": "Category name"
}
```

## API Reference

### `AppointmentChecker` Class

Main class for checking appointments.

```python
from appointment_checker import AppointmentChecker

checker = AppointmentChecker(config={
    'headless': True,
    'slow_mo': 0,
    'screenshot_dir': 'my_screenshots'
})

result = await checker.check_appointments(
    category="Category name",
    service="Service name",
    quantity=1
)
```

### `check_appointments()` Function

Convenience function for simple usage.

```python
from appointment_checker import check_appointments

result = await check_appointments(
    category="Category name",
    service="Service name",
    quantity=1,
    config={'headless': True}
)
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `headless` | bool | `false` | Run browser without UI |
| `slow_mo` | int | `300` | Delay between actions (ms) |
| `timeout` | int | `30000` | Default timeout (ms) |
| `screenshot_dir` | str | `"screenshots"` | Screenshot directory |
| `debug` | bool | `true` | Enable debug logging |

## Testing

### Manual Test

Run the checker and observe the browser:

```bash
python appointment_checker.py
```

Check the output:
- Console logs showing each step
- Screenshot saved in `screenshots/` directory
- Result printed to console

### Automated Tests (Coming Soon)

```bash
# Run tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=appointment_checker
```

## Troubleshooting

### Common Issues

**Issue: "Timeout waiting for element"**
- Solution: Increase timeout in config.yaml
- Check if website structure has changed

**Issue: "Cookie banner not dismissed"**
- Solution: The checker tries multiple button texts automatically
- Check browser console for errors

**Issue: "No appointments detected but page shows availability"**
- Solution: The HTML selectors may need adjustment
- Run in headful mode (`headless: false`) and inspect the page
- Check `screenshots/` for captured state

**Issue: "Browser not found"**
- Solution: Install Playwright browsers:
  ```bash
  playwright install chromium
  ```

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or set in `.env`:
```
LOG_LEVEL=DEBUG
```

## Roadmap

### Phase 1: Core Functionality ✅
- [x] Refactored appointment checker
- [x] Detection and extraction logic
- [x] Configuration system
- [x] Structured logging
- [x] Error handling

### Phase 2: Multi-User System (In Progress)
- [ ] PostgreSQL/SQLite database
- [ ] User management
- [ ] Subscription system
- [ ] FastAPI service layer

### Phase 3: Telegram Bot
- [ ] Bot commands (`/start`, `/subscribe`, `/check`)
- [ ] Notification system
- [ ] Multi-user support
- [ ] Conversation flows

### Phase 4: Production Deployment
- [ ] Docker containerization
- [ ] CI/CD pipeline
- [ ] Monitoring and alerting
- [ ] Rate limiting
- [ ] Anti-bot evasion

### Phase 5: Scaling & Commercialization
- [ ] Payment integration (Stripe)
- [ ] Tiered plans (free/premium)
- [ ] Admin dashboard
- [ ] Analytics and reporting

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Add your license here]

## Disclaimer

This tool is for personal use only. Please respect the website's terms of service and avoid excessive requests that could overload the server. Use reasonable check intervals (recommended: minimum 15 minutes between checks).

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review the troubleshooting section above

## Acknowledgments

- Built with [Playwright](https://playwright.dev/) for reliable browser automation
- Designed for the Düsseldorf city appointment system
