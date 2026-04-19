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
