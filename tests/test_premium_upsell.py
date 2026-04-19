from src.bot.i18n import t


def test_ad_premium_upsell_en():
    result = t("en", "ad_premium_upsell")
    assert "12h" in result
    assert "/premium" in result


def test_ad_premium_upsell_ru():
    result = t("ru", "ad_premium_upsell")
    assert "12" in result


def test_ad_premium_upsell_all_langs():
    for lang in ("en", "de", "ru", "uk", "tr"):
        result = t(lang, "ad_premium_upsell")
        assert result  # not empty, not the key itself


def test_btn_get_premium_all_langs():
    for lang in ("en", "de", "ru", "uk", "tr"):
        result = t(lang, "btn_get_premium")
        assert result
        assert "coming" in result.lower() or "скоро" in result or "demnächst" in result or "незабаром" in result or "yakında" in result


def test_premium_unavailable_has_coming_soon():
    for lang in ("en", "de", "ru", "uk", "tr"):
        result = t(lang, "premium_unavailable")
        assert any(s in result for s in ("coming soon", "demnächst", "скоро", "незабаром", "yakında"))


import sqlalchemy
from src.core.database import init_database
from src.core.models import UserPlan
from src.bot.handlers import BotHandlers


def _make_db():
    db = init_database("sqlite:///:memory:")
    db.create_tables()
    db.apply_migrations()
    return db


class _FreeUser:
    plan = UserPlan.FREE


class _PremiumUser:
    plan = UserPlan.PREMIUM


def test_ad_footer_free_returns_premium_upsell():
    db = _make_db()
    handlers = BotHandlers(db)
    result = handlers._ad_footer("en", _FreeUser())
    assert result is not None
    assert "12h" in result


def test_ad_footer_premium_returns_none():
    db = _make_db()
    handlers = BotHandlers(db)
    result = handlers._ad_footer("en", _PremiumUser())
    assert result is None


def test_ad_footer_custom_ad_overrides_upsell():
    db = _make_db()
    with db.engine.connect() as conn:
        conn.execute(sqlalchemy.text(
            "INSERT INTO bot_settings (key, value) VALUES ('current_ad', 'Sponsor message here')"
        ))
        conn.commit()
    handlers = BotHandlers(db)
    result = handlers._ad_footer("en", _FreeUser())
    assert result == "Sponsor message here"


def test_ad_footer_custom_ad_not_shown_to_premium():
    db = _make_db()
    with db.engine.connect() as conn:
        conn.execute(sqlalchemy.text(
            "INSERT INTO bot_settings (key, value) VALUES ('current_ad', 'Sponsor message here')"
        ))
        conn.commit()
    handlers = BotHandlers(db)
    result = handlers._ad_footer("en", _PremiumUser())
    assert result is None


def test_ad_footer_respects_language():
    db = _make_db()
    handlers = BotHandlers(db)
    result_ru = handlers._ad_footer("ru", _FreeUser())
    assert "12" in result_ru
    result_en = handlers._ad_footer("en", _FreeUser())
    assert result_en != result_ru
