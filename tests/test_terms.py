# tests/test_terms.py
import pytest
from src.bot.terms import TERMS

FORBIDDEN_WORDS = ["AI", "Claude", "artificial intelligence", "LLM"]


def test_terms_en_exists_and_nonempty():
    assert "en" in TERMS
    assert isinstance(TERMS["en"], str)
    assert len(TERMS["en"]) > 0


def test_terms_de_exists_and_nonempty():
    assert "de" in TERMS
    assert isinstance(TERMS["de"], str)
    assert len(TERMS["de"]) > 0


@pytest.mark.parametrize("lang", ["en", "de"])
@pytest.mark.parametrize("word", FORBIDDEN_WORDS)
def test_terms_no_forbidden_words(lang, word):
    assert word not in TERMS[lang], f"TERMS['{lang}'] contains forbidden word: '{word}'"
