# Scheduler Deduplication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate redundant TEVIS scrapes by checking each unique service once per scheduler run and fanning out the result to all subscribers, instead of scraping once per subscription.

**Architecture:** Split `CheckService.run_subscription_check` into two methods — `scrape_service` (one Playwright request per service) and `record_check` (one DB write per subscription). The scheduler groups due subscriptions by `(service_id, quantity)`, calls `scrape_service` once per group, then calls `record_check` for every subscriber. `run_subscription_check` stays intact as a thin wrapper used by manual checks from the bot handlers.

**Tech Stack:** APScheduler `AsyncIOScheduler`, SQLAlchemy + SQLite, Playwright via `AppointmentChecker`, `collections.defaultdict`.

---

## File Map

| File | What changes |
|------|-------------|
| `src/services/check_service.py` | Add `scrape_service()` and `record_check()`. Refactor `run_subscription_check()` to delegate to both. Import `Service` model. |
| `src/services/scheduler.py` | Replace sequential subscription loop with grouped loop. Import `defaultdict` and `datetime`. |
| `tests/test_scheduler_dedup.py` | New test file — unit tests for `scrape_service`, `record_check`, and scheduler grouping logic. |

---

### Task 1: `scrape_service` and `record_check` in CheckService

**Files:**
- Modify: `src/services/check_service.py`
- Create: `tests/test_scheduler_dedup.py`

Context: `check_service.py` currently has one public method `run_subscription_check(subscription_id)` that does everything: loads subscription from DB, calls Playwright, saves Check + Appointment records, updates `subscription.last_checked_at` and `service.total_checks`. We need to split this so the Playwright call can be shared across subscribers.

`CheckerResult` (imported as `CheckResult` from `..core.appointment_checker`) has: `.status: str`, `.available: bool`, `.appointments: List[AppointmentSlot]`, `.screenshot_path`, `.error_message`, `.checked_at`.

`AppointmentSlot` has: `.date`, `.time`, `.location`, `.raw_text`.

- [ ] **Step 1: Write failing tests**

Create `tests/test_scheduler_dedup.py`:

```python
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from src.core.database import init_database
from src.core.models import (
    User, UserPlan, Service, Subscription, Check, CheckStatus
)
from src.services.check_service import CheckService


def make_db():
    db = init_database("sqlite:///:memory:")
    db.create_tables()
    db.apply_migrations()
    return db


def make_service(session, name="Führerschein"):
    svc = Service(
        category="Fahrerlaubnis",
        service_name=name,
        base_url="https://termine.duesseldorf.de/select2?md=3",
    )
    session.add(svc)
    session.flush()
    return svc


def make_user(session, tid=1):
    u = User(telegram_id=tid, plan=UserPlan.FREE)
    session.add(u)
    session.flush()
    return u


def make_subscription(session, user, service, quantity=1):
    sub = Subscription(
        user_id=user.id,
        service_id=service.id,
        interval_hours=12,
        quantity=quantity,
        active=True,
    )
    session.add(sub)
    session.flush()
    return sub


def fake_result(available=False, appointments=None):
    from src.core.appointment_checker import CheckResult, AppointmentSlot
    apts = appointments or []
    return CheckResult(
        status="appointments_found" if available else "no_appointments",
        available=available,
        appointments=apts,
        checked_at=datetime.now().isoformat(),
    )


# ── scrape_service ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_scrape_service_calls_checker_with_correct_args():
    db = make_db()
    with db.get_session() as session:
        svc = make_service(session, "Führerschein")
        service_id = svc.id
        session.commit()

    svc_obj = CheckService(db)
    mock_result = fake_result(available=False)
    with patch.object(svc_obj, "_get_checker") as mock_get_checker:
        mock_checker = AsyncMock()
        mock_checker.check_appointments = AsyncMock(return_value=mock_result)
        mock_get_checker.return_value = mock_checker

        result = await svc_obj.scrape_service(service_id, quantity=1)

    mock_checker.check_appointments.assert_called_once_with(
        category="Fahrerlaubnis",
        service="Führerschein",
        quantity=1,
    )
    assert result is mock_result


@pytest.mark.asyncio
async def test_scrape_service_returns_none_for_unknown_service():
    db = make_db()
    svc_obj = CheckService(db)
    result = await svc_obj.scrape_service(service_id=9999, quantity=1)
    assert result is None


@pytest.mark.asyncio
async def test_scrape_service_increments_total_checks():
    db = make_db()
    with db.get_session() as session:
        svc = make_service(session)
        service_id = svc.id
        session.commit()

    svc_obj = CheckService(db)
    mock_result = fake_result(available=False)
    with patch.object(svc_obj, "_get_checker") as mock_get_checker:
        mock_checker = AsyncMock()
        mock_checker.check_appointments = AsyncMock(return_value=mock_result)
        mock_get_checker.return_value = mock_checker
        await svc_obj.scrape_service(service_id, quantity=1)

    from src.core.models import Service as SvcModel
    with db.get_session() as session:
        svc = session.query(SvcModel).filter_by(id=service_id).first()
        assert svc.total_checks == 1


# ── record_check ───────────────────────────────────────────────────────────

def test_record_check_saves_check_record():
    db = make_db()
    with db.get_session() as session:
        svc = make_service(session)
        u = make_user(session, tid=10)
        sub = make_subscription(session, u, svc)
        sub_id = sub.id
        session.commit()

    svc_obj = CheckService(db)
    checked_at = datetime(2026, 4, 20, 12, 0, 0)
    result = fake_result(available=False)
    check = svc_obj.record_check(sub_id, result, checked_at)

    assert check is not None
    assert check.subscription_id == sub_id
    assert check.available is False
    assert check.status == CheckStatus.NO_APPOINTMENTS


def test_record_check_saves_appointments_when_available():
    from src.core.appointment_checker import AppointmentSlot
    db = make_db()
    with db.get_session() as session:
        svc = make_service(session)
        u = make_user(session, tid=11)
        sub = make_subscription(session, u, svc)
        sub_id = sub.id
        session.commit()

    apt = AppointmentSlot(date="2026-05-01", time="10:00", location="", raw_text="")
    result = fake_result(available=True, appointments=[apt])
    checked_at = datetime(2026, 4, 20, 12, 0, 0)

    svc_obj = CheckService(db)
    check = svc_obj.record_check(sub_id, result, checked_at)

    assert check is not None
    assert check.available is True
    assert len(check.appointments) == 1
    assert check.appointments[0].appointment_date == "2026-05-01"


def test_record_check_updates_subscription_last_checked_at():
    db = make_db()
    with db.get_session() as session:
        svc = make_service(session)
        u = make_user(session, tid=12)
        sub = make_subscription(session, u, svc)
        sub_id = sub.id
        session.commit()

    checked_at = datetime(2026, 4, 20, 9, 30, 0)
    svc_obj = CheckService(db)
    svc_obj.record_check(sub_id, fake_result(), checked_at)

    with db.get_session() as session:
        sub = session.query(Subscription).filter_by(id=sub_id).first()
        assert sub.last_checked_at == checked_at


def test_record_check_returns_none_for_inactive_subscription():
    db = make_db()
    with db.get_session() as session:
        svc = make_service(session)
        u = make_user(session, tid=13)
        sub = make_subscription(session, u, svc)
        sub.active = False
        session.commit()
        sub_id = sub.id

    svc_obj = CheckService(db)
    result = svc_obj.record_check(sub_id, fake_result(), datetime.now())
    assert result is None
```

- [ ] **Step 2: Run tests to confirm they fail**

```
pytest tests/test_scheduler_dedup.py -v
```
Expected: FAILED — `scrape_service`, `record_check`, `_get_checker` do not exist yet.

- [ ] **Step 3: Add `_get_checker`, `scrape_service`, and `record_check` to `check_service.py`**

Add `Service` to the models import line (line 17):
```python
from ..core.models import Check, Appointment, Subscription, CheckStatus, Service
```

Add these three methods to `CheckService`, **before** `run_subscription_check`:

```python
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
```

- [ ] **Step 4: Refactor `run_subscription_check` to use the new methods**

Replace the entire body of `run_subscription_check` with:

```python
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
```

- [ ] **Step 5: Run all tests**

```
pytest tests/ -v
```
Expected: all existing tests PASS, new tests PASS. No regressions.

- [ ] **Step 6: Commit**

```bash
git add src/services/check_service.py tests/test_scheduler_dedup.py
git commit -m "refactor: split CheckService into scrape_service + record_check"
```

---

### Task 2: Group subscriptions by service in the scheduler

**Files:**
- Modify: `src/services/scheduler.py`
- Modify: `tests/test_scheduler_dedup.py` (append new tests)

Context: `scheduler.py` runs `_check_all_due_subscriptions` every hour via APScheduler. Currently it loops over every due subscription and calls `check_service.run_subscription_check(sub.id)` sequentially. We replace this with a grouped loop: group by `(service_id, quantity)`, call `check_service.scrape_service` once per group, then `check_service.record_check` for each subscriber.

`Subscription` has `.service_id: int`, `.quantity: int`, `.user`, `.notify_telegram: bool`, `.notify_on_found: bool`.

`notification_service.send_appointment_notification(user, check, appointments)` sends the Telegram notification.

- [ ] **Step 1: Write failing tests for scheduler grouping**

Append to `tests/test_scheduler_dedup.py`:

```python
# ── Scheduler grouping ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_scheduler_scrapes_once_per_unique_service():
    """3 subs on same service + 1 sub on different service = 2 scrapes, not 4."""
    from unittest.mock import AsyncMock, MagicMock, patch, call
    from src.services.scheduler import SchedulerService

    db = make_db()
    with db.get_session() as session:
        svc_a = make_service(session, "Führerschein")
        svc_b = make_service(session, "Anmeldung")
        u1 = make_user(session, tid=101)
        u2 = make_user(session, tid=102)
        u3 = make_user(session, tid=103)
        u4 = make_user(session, tid=104)
        sub1 = make_subscription(session, u1, svc_a)
        sub2 = make_subscription(session, u2, svc_a)
        sub3 = make_subscription(session, u3, svc_a)
        sub4 = make_subscription(session, u4, svc_b)
        session.commit()

    scheduler = SchedulerService(db, bot_token=None)

    scrape_results = {
        svc_a.id: fake_result(available=False),
        svc_b.id: fake_result(available=False),
    }

    async def mock_scrape(service_id, quantity):
        return scrape_results[service_id]

    with patch.object(scheduler.check_service, "scrape_service", side_effect=mock_scrape) as mock_scrape_fn, \
         patch.object(scheduler.check_service, "record_check", return_value=MagicMock(available=False)) as mock_record:
        await scheduler._check_all_due_subscriptions()

    assert mock_scrape_fn.call_count == 2
    assert mock_record.call_count == 4


@pytest.mark.asyncio
async def test_scheduler_groups_same_service_different_quantity_separately():
    """qty=1 and qty=2 for the same service are different groups → 2 scrapes."""
    from src.services.scheduler import SchedulerService

    db = make_db()
    with db.get_session() as session:
        svc = make_service(session, "Führerschein")
        u1 = make_user(session, tid=201)
        u2 = make_user(session, tid=202)
        sub1 = make_subscription(session, u1, svc, quantity=1)
        sub2 = make_subscription(session, u2, svc, quantity=2)
        session.commit()

    scheduler = SchedulerService(db, bot_token=None)

    async def mock_scrape(service_id, quantity):
        return fake_result(available=False)

    with patch.object(scheduler.check_service, "scrape_service", side_effect=mock_scrape) as mock_scrape_fn, \
         patch.object(scheduler.check_service, "record_check", return_value=MagicMock(available=False)):
        await scheduler._check_all_due_subscriptions()

    assert mock_scrape_fn.call_count == 2


@pytest.mark.asyncio
async def test_scheduler_sends_notification_when_slot_found():
    """When scrape returns available=True, notification is sent to each subscriber."""
    from src.services.scheduler import SchedulerService

    db = make_db()
    with db.get_session() as session:
        svc = make_service(session)
        u1 = make_user(session, tid=301)
        u2 = make_user(session, tid=302)
        make_subscription(session, u1, svc)
        make_subscription(session, u2, svc)
        session.commit()

    scheduler = SchedulerService(db, bot_token=None)
    scheduler.notification_service = AsyncMock()
    scheduler.notification_service.send_appointment_notification = AsyncMock(return_value=True)

    mock_check = MagicMock()
    mock_check.available = True
    mock_check.appointments = []

    async def mock_scrape(service_id, quantity):
        return fake_result(available=True)

    with patch.object(scheduler.check_service, "scrape_service", side_effect=mock_scrape), \
         patch.object(scheduler.check_service, "record_check", return_value=mock_check):
        await scheduler._check_all_due_subscriptions()

    assert scheduler.notification_service.send_appointment_notification.call_count == 2


@pytest.mark.asyncio
async def test_scheduler_skips_group_when_scrape_fails():
    """If scrape_service returns None, record_check is not called for that group."""
    from src.services.scheduler import SchedulerService

    db = make_db()
    with db.get_session() as session:
        svc = make_service(session)
        u = make_user(session, tid=401)
        make_subscription(session, u, svc)
        session.commit()

    scheduler = SchedulerService(db, bot_token=None)

    async def mock_scrape_fail(service_id, quantity):
        return None

    with patch.object(scheduler.check_service, "scrape_service", side_effect=mock_scrape_fail), \
         patch.object(scheduler.check_service, "record_check") as mock_record:
        await scheduler._check_all_due_subscriptions()

    mock_record.assert_not_called()
```

- [ ] **Step 2: Run tests to confirm they fail**

```
pytest tests/test_scheduler_dedup.py::test_scheduler_scrapes_once_per_unique_service -v
```
Expected: FAIL — scheduler still calls `run_subscription_check`, not `scrape_service`.

- [ ] **Step 3: Rewrite `_check_all_due_subscriptions` in `scheduler.py`**

Add to imports at top of `scheduler.py`:
```python
from collections import defaultdict
from datetime import datetime
```

Replace the entire `_check_all_due_subscriptions` method:

```python
async def _check_all_due_subscriptions(self):
    """Check all due subscriptions, scraping each unique service only once."""
    try:
        due_subscriptions = self.subscription_service.get_subscriptions_due_for_check()
        if not due_subscriptions:
            logger.info("No subscriptions due for checking")
            return

        # Group by (service_id, quantity) — same service with different qty needs separate scrapes
        groups: dict = defaultdict(list)
        for sub in due_subscriptions:
            groups[(sub.service_id, sub.quantity)].append(sub)

        logger.info(
            f"Found {len(due_subscriptions)} due subscription(s) "
            f"across {len(groups)} unique service/quantity group(s)"
        )

        for (service_id, quantity), subs in groups.items():
            checked_at = datetime.now()
            logger.info(f"Scraping service {service_id} qty={quantity} for {len(subs)} subscriber(s)...")

            result = await self.check_service.scrape_service(service_id, quantity)

            if result is None:
                logger.error(
                    f"Scrape failed for service {service_id} qty={quantity}, "
                    f"skipping {len(subs)} subscription(s)"
                )
                await asyncio.sleep(2)
                continue

            for sub in subs:
                try:
                    check = self.check_service.record_check(sub.id, result, checked_at)
                    if check and check.available and self.notification_service:
                        if sub.notify_telegram and sub.notify_on_found:
                            try:
                                await self.notification_service.send_appointment_notification(
                                    user=sub.user,
                                    check=check,
                                    appointments=check.appointments,
                                )
                            except Exception as notif_error:
                                logger.error(f"Failed to send notification for sub {sub.id}: {notif_error}")
                except Exception as e:
                    logger.error(f"Error processing subscription {sub.id}: {e}", exc_info=True)

            await asyncio.sleep(2)

        logger.info("Scheduled check completed")

    except Exception as e:
        logger.error(f"Error in scheduled check: {e}", exc_info=True)
```

- [ ] **Step 4: Run all tests**

```
pytest tests/ -v
```
Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/services/scheduler.py tests/test_scheduler_dedup.py
git commit -m "feat: deduplicate TEVIS scrapes by grouping subscriptions by service"
```

---

### Task 3: Deploy to EC2

- [ ] **Step 1: Push to GitHub**

```bash
git push origin main
```

- [ ] **Step 2: SSH and deploy**

```bash
EC2_IP=$(aws ec2 describe-instances \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text --region eu-west-1)
ssh -i ~/.ssh/termin-bot.pem ec2-user@$EC2_IP \
  "cd /var/app && git pull && sudo systemctl restart termin-bot && sleep 2 && sudo systemctl status termin-bot --no-pager"
```

Expected: `active (running)` with a fresh start timestamp and no errors in the last 10 log lines.
