"""Tests for window-based free-tier scheduling and premium 15-min scheduling."""

from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from src.services.subscription_service import (
    _current_free_window_start,
    SubscriptionService,
    BERLIN,
)
from src.core.database import init_database
from src.core.models import User, UserPlan, Service, Subscription


# ── Helpers ────────────────────────────────────────────────────────────────

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


def make_user(session, tid=1, plan=UserPlan.FREE):
    u = User(telegram_id=tid, plan=plan)
    session.add(u)
    session.flush()
    return u


def make_subscription(session, user, service, last_checked_at=None):
    sub = Subscription(
        user_id=user.id,
        service_id=service.id,
        interval_hours=6,
        quantity=1,
        active=True,
        last_checked_at=last_checked_at,
    )
    session.add(sub)
    session.flush()
    return sub


def berlin_dt(hour, minute, second=0):
    """Construct a Berlin-aware datetime for today."""
    now = datetime.now(BERLIN)
    return now.replace(hour=hour, minute=minute, second=second, microsecond=0)


# ── _current_free_window_start ─────────────────────────────────────────────

def test_window_start_inside_first_window():
    # 7:45 Berlin → should return window start at 7:30 Berlin
    dt = berlin_dt(7, 45)
    result = _current_free_window_start(dt)
    assert result is not None
    assert result.hour == 7
    assert result.minute == 30


def test_window_start_inside_last_window():
    # 15:50 Berlin → window start at 15:30
    dt = berlin_dt(15, 50)
    result = _current_free_window_start(dt)
    assert result is not None
    assert result.hour == 15
    assert result.minute == 30


def test_window_start_at_exact_window_start():
    # 9:30 exactly → inside window
    dt = berlin_dt(9, 30)
    result = _current_free_window_start(dt)
    assert result is not None
    assert result.hour == 9
    assert result.minute == 30


def test_window_start_at_exact_window_end_is_outside():
    # 10:00 exactly → outside (window is [9:30, 10:00))
    dt = berlin_dt(10, 0)
    result = _current_free_window_start(dt)
    assert result is None


def test_window_start_returns_none_outside_all_windows():
    # 11:00 Berlin → between windows, should return None
    dt = berlin_dt(11, 0)
    result = _current_free_window_start(dt)
    assert result is None


def test_window_start_returns_none_at_midnight():
    dt = berlin_dt(0, 0)
    result = _current_free_window_start(dt)
    assert result is None


# ── get_subscriptions_due_for_check ────────────────────────────────────────

def test_premium_sub_due_after_15min():
    db = make_db()
    with db.get_session() as session:
        svc = make_service(session)
        u = make_user(session, tid=1, plan=UserPlan.PREMIUM)
        # last checked 20 minutes ago (naive UTC)
        last = datetime.utcnow().replace(tzinfo=None)
        from datetime import timedelta
        last = last - timedelta(minutes=20)
        make_subscription(session, u, svc, last_checked_at=last)
        session.commit()

    svc_obj = SubscriptionService(db)
    due = svc_obj.get_subscriptions_due_for_check()
    assert len(due) == 1


def test_premium_sub_not_due_within_15min():
    db = make_db()
    with db.get_session() as session:
        svc = make_service(session)
        u = make_user(session, tid=2, plan=UserPlan.PREMIUM)
        from datetime import timedelta
        last = datetime.utcnow().replace(tzinfo=None) - timedelta(minutes=5)
        make_subscription(session, u, svc, last_checked_at=last)
        session.commit()

    svc_obj = SubscriptionService(db)
    due = svc_obj.get_subscriptions_due_for_check()
    assert len(due) == 0


def _patch_now(berlin_time):
    """Return a mock for datetime.now that returns berlin_time for tz=BERLIN, naive UTC otherwise."""
    fake_utc = datetime.utcnow().replace(tzinfo=None)

    def _now(tz=None):
        if tz == BERLIN:
            return berlin_time
        return fake_utc

    return _now


def test_free_sub_not_due_outside_window():
    db = make_db()
    with db.get_session() as session:
        svc = make_service(session)
        u = make_user(session, tid=3, plan=UserPlan.FREE)
        make_subscription(session, u, svc, last_checked_at=None)
        session.commit()

    svc_obj = SubscriptionService(db)

    outside_window = berlin_dt(11, 0)
    with patch("src.services.subscription_service.datetime") as mock_dt:
        mock_dt.now.side_effect = _patch_now(outside_window)
        due = svc_obj.get_subscriptions_due_for_check()

    assert len(due) == 0


def test_free_sub_due_inside_window_never_checked():
    db = make_db()
    with db.get_session() as session:
        svc = make_service(session)
        u = make_user(session, tid=4, plan=UserPlan.FREE)
        make_subscription(session, u, svc, last_checked_at=None)
        session.commit()

    svc_obj = SubscriptionService(db)

    inside_window = berlin_dt(7, 45)
    with patch("src.services.subscription_service.datetime") as mock_dt:
        mock_dt.now.side_effect = _patch_now(inside_window)
        due = svc_obj.get_subscriptions_due_for_check()

    assert len(due) == 1


def test_free_sub_not_due_already_checked_this_window():
    db = make_db()
    with db.get_session() as session:
        svc = make_service(session)
        u = make_user(session, tid=5, plan=UserPlan.FREE)
        # Compute window_start_utc for the 7:30 Berlin window
        from datetime import timedelta
        inside_window = berlin_dt(7, 45)
        window_start = inside_window.replace(hour=7, minute=30, second=0, microsecond=0)
        window_start_utc = window_start.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
        # Set last_checked_at to 5 minutes after window start (naive UTC) — already checked this window
        last_checked = window_start_utc + timedelta(minutes=5)
        make_subscription(session, u, svc, last_checked_at=last_checked)
        session.commit()

    svc_obj = SubscriptionService(db)

    inside_window = berlin_dt(7, 45)
    with patch("src.services.subscription_service.datetime") as mock_dt:
        mock_dt.now.side_effect = _patch_now(inside_window)
        due = svc_obj.get_subscriptions_due_for_check()

    assert len(due) == 0


def test_premium_returned_before_free():
    """Premium subs appear before free subs in the return value."""
    db = make_db()
    with db.get_session() as session:
        svc = make_service(session)
        # Free user — never checked
        u_free = make_user(session, tid=10, plan=UserPlan.FREE)
        make_subscription(session, u_free, svc, last_checked_at=None)
        # Premium user — never checked
        u_prem = make_user(session, tid=11, plan=UserPlan.PREMIUM)
        svc2 = make_service(session, name="Anmeldung")
        make_subscription(session, u_prem, svc2, last_checked_at=None)
        session.commit()

    svc_obj = SubscriptionService(db)

    # Inside a free window so free sub is also due
    inside_window = berlin_dt(7, 45)
    with patch("src.services.subscription_service.datetime") as mock_dt:
        mock_dt.now.side_effect = _patch_now(inside_window)
        due = svc_obj.get_subscriptions_due_for_check()

    assert len(due) == 2
    # Premium should come first
    assert due[0].user.plan == UserPlan.PREMIUM
    assert due[1].user.plan == UserPlan.FREE
