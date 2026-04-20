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
