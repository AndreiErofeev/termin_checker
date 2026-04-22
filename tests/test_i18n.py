import pytest
from src.bot.i18n import t


def test_english_key():
    assert t("en", "cancelled") == "❌ Cancelled."


def test_russian_key():
    assert t("ru", "cancelled") == "❌ Отменено."


def test_ukrainian_key():
    assert t("uk", "cancelled") == "❌ Скасовано."


def test_german_key():
    assert t("de", "cancelled") == "❌ Abgebrochen."


def test_turkish_key():
    assert t("tr", "cancelled") == "❌ İptal edildi."


def test_unknown_lang_falls_back_to_english():
    assert t("xx", "cancelled") == "❌ Cancelled."


def test_missing_key_falls_back_to_english():
    # Key that doesn't exist in any language falls back to the key itself
    assert t("ru", "nonexistent_key_xyz") == "nonexistent_key_xyz"


def test_kwargs_interpolation():
    result = t("en", "freq_every_nh", n=3)
    assert result == "every 3h"


def test_kwargs_interpolation_russian():
    result = t("ru", "freq_every_nh", n=6)
    assert result == "каждые 6ч"


def test_confirm_sub_prompt_all_langs():
    for lang in ("en", "de", "ru", "uk", "tr"):
        result = t(lang, "confirm_sub_prompt", name="Führerschein")
        assert "Führerschein" in result
        assert result != "confirm_sub_prompt"


def test_confirm_unsub_prompt_all_langs():
    for lang in ("en", "de", "ru", "uk", "tr"):
        result = t(lang, "confirm_unsub_prompt", name="Führerschein")
        assert "Führerschein" in result
        assert result != "confirm_unsub_prompt"


def test_btn_yes_subscribe_all_langs():
    for lang in ("en", "de", "ru", "uk", "tr"):
        result = t(lang, "btn_yes_subscribe")
        assert result and result != "btn_yes_subscribe"


def test_btn_yes_unsubscribe_all_langs():
    for lang in ("en", "de", "ru", "uk", "tr"):
        result = t(lang, "btn_yes_unsubscribe")
        assert result and result != "btn_yes_unsubscribe"
