from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.i18n import get_text


def main_menu_kb(lang: str = "uz") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=get_text("menu.download", lang),
            callback_data="menu:download",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=get_text("menu.languages", lang),
            callback_data="menu:languages",
        ),
        InlineKeyboardButton(
            text=get_text("menu.history", lang),
            callback_data="menu:history",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=get_text("menu.platforms", lang),
            callback_data="menu:platforms",
        ),
        InlineKeyboardButton(
            text=get_text("menu.settings", lang),
            callback_data="menu:settings",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=get_text("menu.help", lang),
            callback_data="menu:help",
        )
    )
    return builder.as_markup()
