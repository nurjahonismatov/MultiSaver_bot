
from utils.i18n import load_translations, validate_locales, get_all_keys, SUPPORTED_LANGUAGES


def test_locales_loaded():
    load_translations()
    keys = get_all_keys()
    assert len(keys) > 20


def test_no_missing_keys():
    issues = validate_locales()
    assert issues == [], f"Locale mismatches: {issues}"


def test_required_keys_present():
    load_translations()
    required = [
        "start.welcome",
        "menu.download",
        "onboarding.q1",
        "onboarding.q2",
        "download.processing",
        "media.audio",
        "media.save",
        "media.share",
        "admin.stats",
    ]
    from utils.i18n import _translations
    for lang in SUPPORTED_LANGUAGES:
        for key in required:
            assert key in _translations[lang], f"{lang} missing {key}"
