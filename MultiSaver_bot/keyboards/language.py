from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.i18n import get_text


def language_kb(lang: str = "uz") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=get_text("language.uz", lang),
            callback_data="lang:uz",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=get_text("language.en", lang),
            callback_data="lang:en",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=get_text("language.ru", lang),
            callback_data="lang:ru",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=get_text("common.back", lang),
            callback_data="menu:main",
        )
    )
    return builder.as_markup()
