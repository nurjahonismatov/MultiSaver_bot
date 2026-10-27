from urllib.parse import quote


def build_share_text(url: str, lang: str = "en") -> str:
    """Build a shareable text message."""
    from utils.i18n import get_text

    return get_text("media.share_text", lang, url=url)


def build_telegram_share_url(text: str) -> str:
    """Create a t.me/share URL for the given text."""
    return f"https://t.me/share/url?url=&text={quote(text)}"
