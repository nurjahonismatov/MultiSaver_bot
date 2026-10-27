import json
from pathlib import Path
from typing import Any, Dict

LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"
SUPPORTED_LANGUAGES = ("uz", "en", "ru")
DEFAULT_LANGUAGE = "uz"

_translations: Dict[str, Dict[str, str]] = {}


def load_translations() -> None:
    """Load all locale JSON files into memory."""
    global _translations
    for lang in SUPPORTED_LANGUAGES:
        path = LOCALES_DIR / f"{lang}.json"
        if path.exists():
            with open(path, encoding="utf-8") as f:
                _translations[lang] = json.load(f)
        else:
            _translations[lang] = {}


def get_text(key: str, lang: str = DEFAULT_LANGUAGE, **kwargs: Any) -> str:
    """Return translated string for key, with optional format kwargs."""
    if not _translations:
        load_translations()

    lang = lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
    text = _translations.get(lang, {}).get(key)

    if text is None:
        # Fallback to English, then Uzbek, then key itself
        text = _translations.get("en", {}).get(key)
        if text is None:
            text = _translations.get("uz", {}).get(key, key)

    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text


def get_all_keys() -> set[str]:
    """Return union of all translation keys (for validation)."""
    if not _translations:
        load_translations()
    keys: set[str] = set()
    for data in _translations.values():
        keys.update(data.keys())
    return keys


def validate_locales() -> list[str]:
    """Return list of missing key reports."""
    if not _translations:
        load_translations()
    all_keys = get_all_keys()
    issues = []
    for lang in SUPPORTED_LANGUAGES:
        missing = all_keys - set(_translations.get(lang, {}).keys())
        if missing:
            issues.append(f"{lang}: missing {sorted(missing)}")
    return issues


# Load on import
load_translations()