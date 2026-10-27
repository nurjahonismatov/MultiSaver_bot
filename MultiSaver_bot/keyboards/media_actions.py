from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.i18n import get_text


def media_actions_kb(
    job_id: str,
    lang: str = "uz",
    media_type: str = "video",
    can_extract_audio: bool = False,
) -> InlineKeyboardMarkup:
    """
    Build action keyboard for a completed download.
    job_id is a short opaque identifier stored temporarily.
    """
    builder = InlineKeyboardBuilder()

    if media_type == "video" and can_extract_audio:
        builder.row(
            InlineKeyboardButton(
                text=get_text("media.audio", lang),
                callback_data=f"act:audio:{job_id}",
            )
        )

    builder.row(
        InlineKeyboardButton(
            text=get_text("media.save", lang),
            callback_data=f"act:save:{job_id}",
        ),
        InlineKeyboardButton(
            text=get_text("media.share", lang),
            callback_data=f"act:share:{job_id}",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=get_text("media.again", lang),
            callback_data=f"act:again:{job_id}",
        ),
        InlineKeyboardButton(
            text=get_text("media.main_menu", lang),
            callback_data="menu:main",
        ),
    )
    return builder.as_markup()
