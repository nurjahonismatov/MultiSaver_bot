"""Settings menu keyboard."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.i18n import get_text


def settings_kb(lang: str = "uz") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=get_text("settings.language", lang),
            callback_data="menu:languages",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=get_text("settings.platforms", lang),
            callback_data="menu:platforms",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=get_text("settings.privacy", lang),
            callback_data="settings:privacy",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=get_text("settings.complete_survey", lang),
            callback_data="settings:survey",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=get_text("settings.back", lang),
            callback_data="menu:main",
        )
    )
    return builder.as_markup()


def history_kb(lang: str = "uz") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=get_text("history.clear", lang),
            callback_data="history:clear",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=get_text("common.back", lang),
            callback_data="menu:main",
        )
    )
    return builder.as_markup()
