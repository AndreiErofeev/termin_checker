# Termin Bot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the existing bot skeleton and services into a working Telegram bot that reads the S3 menu, lets users subscribe to appointment services, and sends Telegram notifications when slots open.

**Architecture:** Single EC2 t3.micro running a Python process with Telegram polling + APScheduler + Playwright (headless Chromium). Services menu loaded from S3 `termin/schema.json` at startup. SQLite for persistence.

**Tech Stack:** python-telegram-bot 21+, APScheduler, SQLAlchemy + SQLite, Playwright, boto3, systemd

---

## S3 Schema Format (reference for all tasks)

```json
{
  "departments": {
    "Einwohnerangelegenheiten": {
      "md": 4,
      "url": "https://termine.duesseldorf.de/select2?md=4",
      "categories": {
        "Meldeangelegenheiten": {
          "services": {
            "Anmeldung in Düsseldorf (pro Person)": { "max_quantity": 4 }
          }
        }
      }
    }
  }
}
```

Each `(category, service_name)` pair is one `Service` row. `base_url` = department `url`.

---

## Task 1: S3 Schema Loader

**Files:**
- Create: `src/core/schema_loader.py`
- Create: `tests/test_schema_loader.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_schema_loader.py
import json
from unittest.mock import MagicMock, patch
from src.core.schema_loader import load_schema_from_s3, upsert_services
from src.core.database import Database
from src.core.models import Service


SAMPLE_SCHEMA = {
    "departments": {
        "Dept A": {
            "url": "https://termine.duesseldorf.de/select2?md=4",
            "categories": {
                "Cat 1": {
                    "services": {
                        "Service X": {"max_quantity": 2},
                        "Service Y": {"max_quantity": 1},
                    }
                }
            },
        }
    }
}


def test_load_schema_from_s3():
    mock_s3 = MagicMock()
    mock_s3.get_object.return_value = {
        "Body": MagicMock(read=lambda: json.dumps(SAMPLE_SCHEMA).encode())
    }
    result = load_schema_from_s3(mock_s3, "my-bucket", "termin/schema.json")
    assert result["departments"]["Dept A"]["url"] == "https://termine.duesseldorf.de/select2?md=4"


def test_upsert_services_creates_rows():
    db = Database("sqlite:///:memory:")
    db.create_tables()
    upsert_services(db, SAMPLE_SCHEMA)
    with db.get_session() as session:
        services = session.query(Service).all()
    assert len(services) == 2
    names = {s.service_name for s in services}
    assert "Service X" in names
    assert "Service Y" in names


def test_upsert_services_sets_base_url():
    db = Database("sqlite:///:memory:")
    db.create_tables()
    upsert_services(db, SAMPLE_SCHEMA)
    with db.get_session() as session:
        svc = session.query(Service).filter_by(service_name="Service X").first()
    assert svc.base_url == "https://termine.duesseldorf.de/select2?md=4"
    assert svc.category == "Cat 1"


def test_upsert_services_idempotent():
    db = Database("sqlite:///:memory:")
    db.create_tables()
    upsert_services(db, SAMPLE_SCHEMA)
    upsert_services(db, SAMPLE_SCHEMA)  # second call must not duplicate
    with db.get_session() as session:
        count = session.query(Service).count()
    assert count == 2
```

- [ ] **Step 2: Run test to verify it fails**

```
pytest tests/test_schema_loader.py -v
```
Expected: `ModuleNotFoundError: No module named 'src.core.schema_loader'`

- [ ] **Step 3: Implement schema_loader**

```python
# src/core/schema_loader.py
import json
import logging
from typing import Any

import boto3

from .database import Database
from .models import Service

logger = logging.getLogger(__name__)


def load_schema_from_s3(s3_client: Any, bucket: str, key: str) -> dict:
    response = s3_client.get_object(Bucket=bucket, Key=key)
    return json.loads(response["Body"].read())


def upsert_services(db: Database, schema: dict) -> int:
    """Insert or update services from schema. Returns count of services processed."""
    count = 0
    departments = schema.get("departments", {})

    with db.get_session() as session:
        for dept_name, dept_data in departments.items():
            base_url = dept_data.get("url", "https://termine.duesseldorf.de/select2?md=3")
            for category, cat_data in dept_data.get("categories", {}).items():
                for service_name in cat_data.get("services", {}):
                    existing = session.query(Service).filter_by(
                        category=category, service_name=service_name
                    ).first()
                    if existing:
                        existing.base_url = base_url
                        existing.active = True
                    else:
                        session.add(Service(
                            category=category,
                            service_name=service_name,
                            base_url=base_url,
                            active=True,
                        ))
                    count += 1
        session.commit()

    logger.info("Upserted %d services from schema", count)
    return count


def load_and_sync(db: Database, bucket: str, key: str = "termin/schema.json") -> int:
    """Convenience: fetch from S3 and upsert into DB. Returns service count."""
    s3 = boto3.client("s3")
    schema = load_schema_from_s3(s3, bucket, key)
    return upsert_services(db, schema)
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/test_schema_loader.py -v
```
Expected: 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/core/schema_loader.py tests/test_schema_loader.py
git commit -m "feat: add S3 schema loader with upsert logic"
```

---

## Task 2: Fix AppointmentChecker for headless server

**Files:**
- Modify: `src/core/appointment_checker.py:77-84`

The current default is `headless: False` and no Chrome flags. On EC2 (no display) this crashes.

- [ ] **Step 1: Update DEFAULT_CONFIG and launch call**

In `src/core/appointment_checker.py`, replace the `DEFAULT_CONFIG` dict and the browser launch call:

```python
# Replace DEFAULT_CONFIG (lines ~77-84)
DEFAULT_CONFIG = {
    'base_url': 'https://termine.duesseldorf.de/select2?md=3',
    'headless': True,
    'slow_mo': 0,
    'timeout': 30000,
    'screenshot_dir': 'screenshots',
    'debug': False,
}
```

Replace the `p.chromium.launch(...)` call inside `check_appointments` (lines ~119-124):

```python
browser = await p.chromium.launch(
    headless=self.config['headless'],
    slow_mo=self.config['slow_mo'],
    args=[
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--single-process",
    ],
)
```

- [ ] **Step 2: Verify no syntax errors**

```
python -c "from src.core.appointment_checker import AppointmentChecker; print('ok')"
```
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add src/core/appointment_checker.py
git commit -m "fix: headless=True and no-sandbox flags for server operation"
```

---

## Task 3: Fix CheckService — pass base_url and fix eager loading

**Files:**
- Modify: `src/services/check_service.py`

Two bugs: (a) `AppointmentChecker()` uses hardcoded `md=3` ignoring service's `base_url`; (b) the returned `Check` doesn't have `subscription.service` loaded, causing `DetachedInstanceError` in `NotificationService`.

- [ ] **Step 1: Fix both issues**

In `src/services/check_service.py`, replace the checker init and the final re-fetch:

```python
# Replace lines ~70-78 (checker init + check_appointments call)
if not self.checker:
    self.checker = AppointmentChecker(config={
        'base_url': service.base_url,
        'headless': True,
    })
else:
    self.checker.config['base_url'] = service.base_url

result: CheckerResult = await self.checker.check_appointments(
    category=service.category,
    service=service.service_name,
    quantity=subscription.quantity
)
```

Replace the final re-fetch (lines ~116-119) to also load subscription+service:

```python
check = session.query(Check).options(
    joinedload(Check.appointments),
    joinedload(Check.subscription).joinedload(Subscription.service),
    joinedload(Check.subscription).joinedload(Subscription.user),
).filter(Check.id == check.id).first()
```

Also add `Subscription` to the import at the top if not already present (it already is).

- [ ] **Step 2: Verify import**

```
python -c "from src.services.check_service import CheckService; print('ok')"
```
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add src/services/check_service.py
git commit -m "fix: pass service base_url to AppointmentChecker, fix eager loading"
```

---

## Task 4: Wire bot main.py — schema load + scheduler start

**Files:**
- Modify: `src/bot/main.py`

Currently the bot starts polling but never loads the S3 schema and never starts the scheduler.

- [ ] **Step 1: Replace main.py**

```python
# src/bot/main.py
import logging
import os

from telegram.ext import Application, CommandHandler, CallbackQueryHandler, PreCheckoutQueryHandler, MessageHandler, filters
from dotenv import load_dotenv

from src.core.database import init_database
from src.core.schema_loader import load_and_sync
from src.bot.handlers import BotHandlers
from src.services.scheduler import SchedulerService

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    bot_token = os.environ["TELEGRAM_BOT_TOKEN"]
    s3_bucket = os.environ["S3_BUCKET"]
    db_path = os.environ.get("DB_PATH", "/var/app/termin.db")

    db = init_database(f"sqlite:///{db_path}")
    db.create_tables()

    logger.info("Syncing service menu from S3...")
    try:
        count = load_and_sync(db, s3_bucket)
        logger.info("Loaded %d services from S3", count)
    except Exception as e:
        logger.warning("Could not load S3 schema: %s — using existing DB data", e)

    handlers = BotHandlers(db)
    scheduler = SchedulerService(db, bot_token)

    app = Application.builder().token(bot_token).build()

    app.add_handler(CommandHandler("start", handlers.start_command))
    app.add_handler(CommandHandler("help", handlers.help_command))
    app.add_handler(CommandHandler("subscribe", handlers.subscribe_command))
    app.add_handler(CommandHandler("list", handlers.list_command))
    app.add_handler(CommandHandler("unsubscribe", handlers.unsubscribe_command))
    app.add_handler(CommandHandler("check", handlers.check_command))
    app.add_handler(CommandHandler("premium", handlers.premium_command))
    app.add_handler(CommandHandler("setschedule", handlers.setschedule_command))
    app.add_handler(PreCheckoutQueryHandler(handlers.precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, handlers.successful_payment_callback))
    app.add_handler(CallbackQueryHandler(handlers.button_callback))

    scheduler.start()
    logger.info("Scheduler started")

    try:
        app.run_polling(allowed_updates=["message", "callback_query"])
    finally:
        scheduler.stop()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify import**

```
python -c "import src.bot.main; print('ok')"
```
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add src/bot/main.py
git commit -m "feat: wire schema load and scheduler start in bot main"
```

---

## Task 5: Enforce free tier limits in subscribe handler

**Files:**
- Modify: `src/bot/handlers.py`

Free users: max 3 subscriptions, `interval_hours=12`. Premium users: unlimited, `interval_hours` from their setting (default 1).

- [ ] **Step 1: Update `_create_subscription` in handlers.py**

Replace the `_create_subscription` method (currently lines ~310-339):

```python
async def _create_subscription(self, query, service_id: int):
    user = query.from_user
    db_user = self.user_service.get_user_by_telegram_id(user.id)
    if not db_user:
        await query.edit_message_text("❌ User not found.")
        return

    from ..core.models import UserPlan
    is_free = db_user.plan == UserPlan.FREE

    if is_free:
        existing = self.subscription_service.get_user_subscriptions(db_user.id)
        if len(existing) >= 3:
            await query.edit_message_text(
                "❌ Free plan allows up to 3 subscriptions.\n\n"
                "Use /premium to upgrade and get unlimited subscriptions."
            )
            return
        interval_hours = 12
    else:
        interval_hours = 1  # premium default, can be changed with /setschedule

    subscription = self.subscription_service.create_subscription(
        user_id=db_user.id,
        service_id=service_id,
        interval_hours=interval_hours,
        quantity=1,
    )

    if subscription:
        service = subscription.service
        freq = "twice daily" if is_free else f"every {interval_hours}h"
        await query.edit_message_text(
            f"✅ *Subscribed!*\n\n"
            f"Service: {service.service_name}\n"
            f"Category: {service.category}\n"
            f"Checks: {freq}\n\n"
            f"You'll be notified when appointments open.",
            parse_mode="Markdown",
        )
    else:
        await query.edit_message_text("❌ Already subscribed to this service.")
```

- [ ] **Step 2: Verify import**

```
python -c "from src.bot.handlers import BotHandlers; print('ok')"
```
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add src/bot/handlers.py
git commit -m "feat: enforce free tier limit (3 subs, 12h interval) in subscribe"
```

---

## Task 6: Add premium handlers (Telegram Stars + /setschedule)

**Files:**
- Modify: `src/bot/handlers.py`

- [ ] **Step 1: Add LabeledPrice import at top of handlers.py**

Add to the existing imports block:

```python
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
```

(`UserPlan` is already imported locally inside `_create_subscription` from Task 5 — move it to module level here by adding `from ..core.models import Service, UserPlan` to the models import line.)

- [ ] **Step 2: Add premium_command, precheckout_callback, successful_payment_callback, setschedule_command to BotHandlers**

Add these four methods to the `BotHandlers` class:

```python
async def premium_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = self.user_service.get_user_by_telegram_id(user.id)
    if not db_user:
        await update.message.reply_text("❌ Please use /start first.")
        return

    if db_user.plan != UserPlan.FREE:
        await update.message.reply_text("✅ You already have Premium!")
        return

    await context.bot.send_invoice(
        chat_id=user.id,
        title="Termin Checker Premium",
        description="Unlimited subscriptions + custom check schedule",
        payload="premium_upgrade",
        currency="XTR",
        prices=[LabeledPrice("Premium", 50)],
    )

async def precheckout_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)

async def successful_payment_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = self.user_service.get_user_by_telegram_id(user.id)
    if db_user:
        self.user_service.update_plan(db_user.id, UserPlan.PREMIUM)
    await update.message.reply_text(
        "🎉 *Premium activated!*\n\n"
        "You now have unlimited subscriptions.\n"
        "Use /setschedule <hours> to customize check frequency.",
        parse_mode="Markdown",
    )

async def setschedule_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = self.user_service.get_user_by_telegram_id(user.id)
    if not db_user:
        await update.message.reply_text("❌ Please use /start first.")
        return

    if db_user.plan == UserPlan.FREE:
        await update.message.reply_text(
            "⚠️ Custom schedules are a Premium feature.\nUse /premium to upgrade."
        )
        return

    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /setschedule <hours>\nExample: /setschedule 2")
        return

    hours = int(context.args[0])
    if hours < 1 or hours > 24:
        await update.message.reply_text("❌ Hours must be between 1 and 24.")
        return

    subscriptions = self.subscription_service.get_user_subscriptions(db_user.id)
    for sub in subscriptions:
        self.subscription_service.update_subscription(sub.id, interval_hours=hours)

    await update.message.reply_text(
        f"✅ All your subscriptions will now check every {hours}h."
    )
```

- [ ] **Step 3: Add `update_plan` to UserService**

In `src/services/user_service.py`, add this method to the `UserService` class:

```python
def update_plan(self, user_id: int, plan) -> bool:
    try:
        with self.db.get_session() as session:
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                return False
            user.plan = plan
            session.commit()
            return True
    except Exception as e:
        logger.error("Error updating plan for user %d: %s", user_id, e)
        return False
```

Also add `User` to the import in `user_service.py` if not already present (check — it already imports `User` from models).

- [ ] **Step 4: Verify imports**

```
python -c "from src.bot.handlers import BotHandlers; from src.services.user_service import UserService; print('ok')"
```
Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add src/bot/handlers.py src/services/user_service.py
git commit -m "feat: add Telegram Stars premium flow and /setschedule command"
```

---

## Task 7: Fix scheduler poll interval

**Files:**
- Modify: `src/services/scheduler.py:54-61`

The scheduler fires every 5 minutes checking `get_subscriptions_due_for_check()`. That logic is correct (it respects `interval_hours`), but firing every 5 minutes wastes resources — hourly is enough given the minimum check interval is 1h.

- [ ] **Step 1: Change IntervalTrigger from minutes=5 to hours=1**

In `src/services/scheduler.py`, replace:

```python
# OLD
self.scheduler.add_job(
    self._check_all_due_subscriptions,
    trigger=IntervalTrigger(minutes=5),
    id='check_subscriptions',
    name='Check due subscriptions',
    replace_existing=True
)
```

With:

```python
# NEW
self.scheduler.add_job(
    self._check_all_due_subscriptions,
    trigger=IntervalTrigger(hours=1),
    id='check_subscriptions',
    name='Check due subscriptions',
    replace_existing=True,
)
```

- [ ] **Step 2: Verify**

```
python -c "from src.services.scheduler import SchedulerService; print('ok')"
```
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add src/services/scheduler.py
git commit -m "fix: reduce scheduler poll from every 5min to every 1h"
```

---

## Task 8: EC2 deployment files

**Files:**
- Create: `infra/ec2/install.sh`
- Create: `infra/ec2/termin-bot.service`
- Create: `.env.example`

- [ ] **Step 1: Create install.sh**

```bash
# infra/ec2/install.sh
#!/bin/bash
set -e

# Install system deps (Amazon Linux 2023 — same as Lambda base image)
dnf install -y \
    python3.12 python3.12-pip git \
    atk at-spi2-atk cups-libs \
    libXcomposite libXdamage libXfixes libXrandr \
    libgbm libxkbcommon nss pango alsa-lib \
    xorg-x11-fonts-Type1

# App directory
mkdir -p /var/app
cd /var/app

# Clone or pull repo (assumes SSH key already on instance)
if [ -d ".git" ]; then
    git pull
else
    git clone git@github.com:AndreiErofeev/termin_checker.git .
fi

# Python deps
python3.12 -m pip install -r requirements.txt boto3

# Install Chromium for Playwright
export PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
playwright install chromium

# Copy and enable systemd service
cp infra/ec2/termin-bot.service /etc/systemd/system/
systemd-reload
systemctl enable termin-bot
systemctl restart termin-bot

echo "Done. Check status: systemctl status termin-bot"
```

- [ ] **Step 2: Create systemd service**

```ini
# infra/ec2/termin-bot.service
[Unit]
Description=Termin Checker Telegram Bot
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/var/app
EnvironmentFile=/var/app/.env
Environment=PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ExecStart=/usr/bin/python3.12 -m src.bot.main
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

- [ ] **Step 3: Create .env.example**

```bash
# .env.example
TELEGRAM_BOT_TOKEN=your_bot_token_here
S3_BUCKET=termin-checker-data
AWS_DEFAULT_REGION=eu-west-1
DB_PATH=/var/app/termin.db
# Optional: ADMIN_TELEGRAM_ID=123456789
```

- [ ] **Step 4: Commit**

```bash
git add infra/ec2/install.sh infra/ec2/termin-bot.service .env.example
git commit -m "feat: add EC2 install script and systemd service"
```

---

## Task 9: Smoke test end-to-end locally

Before deploying to EC2, verify the bot starts without errors on your machine.

- [ ] **Step 1: Create a local .env**

```bash
cp .env.example .env
# Edit .env: fill in TELEGRAM_BOT_TOKEN, S3_BUCKET, set DB_PATH=./termin.db
```

- [ ] **Step 2: Run the bot**

```bash
python -m src.bot.main
```
Expected output (first run):
```
INFO ... Syncing service menu from S3...
INFO ... Loaded 118 services from S3
INFO ... Scheduler started
INFO ... Application started
```

- [ ] **Step 3: Test /start in Telegram**

Send `/start` to the bot. Expected: welcome message with plan = FREE.

- [ ] **Step 4: Test /subscribe**

Send `/subscribe`. Expected: inline keyboard with department names from the S3 menu (e.g., "Einwohnerangelegenheiten", "Führerschein", etc.).

- [ ] **Step 5: Complete subscribe flow**

Pick a department → pick a service. Expected: "✅ Subscribed! ... Checks: twice daily"

- [ ] **Step 6: Test /check**

Send `/check` and select the subscription. Expected: bot replies "🔍 Checking..." then either shows slots or "❌ No appointments available."

- [ ] **Step 7: Commit any fixes found during smoke test**

```bash
git add -p
git commit -m "fix: smoke test corrections"
```

---

## Task 10: Deploy to EC2

- [ ] **Step 1: Launch EC2 instance**

Via AWS Console: EC2 → Launch Instance
- AMI: Amazon Linux 2023
- Instance type: t3.micro
- IAM instance profile: attach role with `s3:GetObject` on `termin-checker-data/termin/*` (same policy as Lambda role)
- Security group: allow outbound HTTPS (443), no inbound needed

- [ ] **Step 2: SSH and run install script**

```bash
ssh ec2-user@<instance-ip>
curl -O https://raw.githubusercontent.com/AndreiErofeev/termin_checker/main/infra/ec2/install.sh
chmod +x install.sh
./install.sh
```

- [ ] **Step 3: Create .env on instance**

```bash
nano /var/app/.env
# Fill in TELEGRAM_BOT_TOKEN, S3_BUCKET=termin-checker-data, AWS_DEFAULT_REGION=eu-west-1
```

- [ ] **Step 4: Start service**

```bash
systemctl start termin-bot
systemctl status termin-bot
```
Expected: `Active: active (running)`

- [ ] **Step 5: Verify logs**

```bash
journalctl -u termin-bot -f
```
Expected: schema loads, scheduler starts, bot begins polling.

- [ ] **Step 6: Send /start in Telegram and confirm bot responds**
