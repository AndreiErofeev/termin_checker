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
    u = User(telegram_id=tid, plan=UserPlan.PREMIUM)
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


# ── Scheduler grouping ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_scheduler_scrapes_once_per_unique_service():
    """3 subs on same service + 1 sub on different service = 2 scrapes, not 4."""
    from unittest.mock import AsyncMock, MagicMock, patch
    from src.services.scheduler import SchedulerService

    db = make_db()
    with db.get_session() as session:
        svc_a = make_service(session, "Führerschein")
        svc_b = make_service(session, "Anmeldung")
        u1 = make_user(session, tid=101)
        u2 = make_user(session, tid=102)
        u3 = make_user(session, tid=103)
        u4 = make_user(session, tid=104)
        make_subscription(session, u1, svc_a)
        make_subscription(session, u2, svc_a)
        make_subscription(session, u3, svc_a)
        make_subscription(session, u4, svc_b)
        session.commit()

    scheduler = SchedulerService(db, bot_token=None)

    # Fetch all subs to return as "due" — bypasses window logic so test is time-independent
    with db.get_session() as session:
        all_subs = scheduler.subscription_service.get_all_active_subscriptions()

    async def mock_scrape(service_id, quantity):
        return fake_result(available=False)

    with patch.object(scheduler.subscription_service, "get_subscriptions_due_for_check", return_value=all_subs), \
         patch.object(scheduler.check_service, "scrape_service", side_effect=mock_scrape) as mock_scrape_fn, \
         patch.object(scheduler.check_service, "record_check", return_value=MagicMock(available=False)) as mock_record:
        await scheduler._check_all_due_subscriptions()

    assert mock_scrape_fn.call_count == 2
    assert mock_record.call_count == 4


@pytest.mark.asyncio
async def test_scheduler_groups_same_service_different_quantity_separately():
    """qty=1 and qty=2 for the same service are different groups → 2 scrapes."""
    from unittest.mock import patch, MagicMock
    from src.services.scheduler import SchedulerService

    db = make_db()
    with db.get_session() as session:
        svc = make_service(session, "Führerschein")
        u1 = make_user(session, tid=201)
        u2 = make_user(session, tid=202)
        make_subscription(session, u1, svc, quantity=1)
        make_subscription(session, u2, svc, quantity=2)
        session.commit()

    scheduler = SchedulerService(db, bot_token=None)

    with db.get_session() as session:
        all_subs = scheduler.subscription_service.get_all_active_subscriptions()

    async def mock_scrape(service_id, quantity):
        return fake_result(available=False)

    with patch.object(scheduler.subscription_service, "get_subscriptions_due_for_check", return_value=all_subs), \
         patch.object(scheduler.check_service, "scrape_service", side_effect=mock_scrape) as mock_scrape_fn, \
         patch.object(scheduler.check_service, "record_check", return_value=MagicMock(available=False)):
        await scheduler._check_all_due_subscriptions()

    assert mock_scrape_fn.call_count == 2


@pytest.mark.asyncio
async def test_scheduler_sends_notification_when_slot_found():
    """When scrape returns available=True, notification sent to each subscriber."""
    from unittest.mock import patch, MagicMock, AsyncMock
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

    with db.get_session() as session:
        all_subs = scheduler.subscription_service.get_all_active_subscriptions()

    async def mock_scrape(service_id, quantity):
        return fake_result(available=True)

    with patch.object(scheduler.subscription_service, "get_subscriptions_due_for_check", return_value=all_subs), \
         patch.object(scheduler.check_service, "scrape_service", side_effect=mock_scrape), \
         patch.object(scheduler.check_service, "record_check", return_value=mock_check):
        await scheduler._check_all_due_subscriptions()

    assert scheduler.notification_service.send_appointment_notification.call_count == 2


@pytest.mark.asyncio
async def test_scheduler_skips_group_when_scrape_fails():
    """If scrape_service returns None, record_check is not called for that group."""
    from unittest.mock import patch
    from src.services.scheduler import SchedulerService

    db = make_db()
    with db.get_session() as session:
        svc = make_service(session)
        u = make_user(session, tid=401)
        make_subscription(session, u, svc)
        session.commit()

    scheduler = SchedulerService(db, bot_token=None)

    with db.get_session() as session:
        all_subs = scheduler.subscription_service.get_all_active_subscriptions()

    async def mock_scrape_fail(service_id, quantity):
        return None

    with patch.object(scheduler.subscription_service, "get_subscriptions_due_for_check", return_value=all_subs), \
         patch.object(scheduler.check_service, "scrape_service", side_effect=mock_scrape_fail), \
         patch.object(scheduler.check_service, "record_check") as mock_record:
        await scheduler._check_all_due_subscriptions()

    mock_record.assert_not_called()
