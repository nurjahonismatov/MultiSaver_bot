
"""Onboarding translation keys exist."""

from utils.i18n import get_text


def test_q1_options_exist():
    for lang in ("uz", "en", "ru"):
        assert get_text("onboarding.q1", lang)
        for i in range(1, 7):
            assert get_text(f"onboarding.q1.opt{i}", lang)


def test_q2_options_exist():
    for lang in ("uz", "en", "ru"):
        assert get_text("onboarding.q2", lang)
        for i in range(1, 8):
            assert get_text(f"onboarding.q2.opt{i}", lang)
