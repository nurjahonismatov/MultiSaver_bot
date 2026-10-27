from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.i18n import get_text


def onboarding_q1_kb(lang: str = "uz") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    options = [
        ("easy", "onboarding.q1.opt1"),
        ("multi", "onboarding.q1.opt2"),
        ("fast", "onboarding.q1.opt3"),
        ("recommended", "onboarding.q1.opt4"),
        ("other", "onboarding.q1.opt5"),
        ("later", "onboarding.q1.opt6"),
    ]
    for code, key in options:
        builder.row(
            InlineKeyboardButton(
                text=get_text(key, lang),
                callback_data=f"onb:q1:{code}",
            )
        )
    return builder.as_markup()


def onboarding_q2_kb(lang: str = "uz") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    options = [
        ("telegram", "onboarding.q2.opt1"),
        ("instagram", "onboarding.q2.opt2"),
        ("friends", "onboarding.q2.opt3"),
        ("tiktok", "onboarding.q2.opt4"),
        ("search", "onboarding.q2.opt5"),
        ("other", "onboarding.q2.opt6"),
        ("later", "onboarding.q2.opt7"),
    ]
    for code, key in options:
        builder.row(
            InlineKeyboardButton(
                text=get_text(key, lang),
                callback_data=f"onb:q2:{code}",
            )
        )
    return builder.as_markup()
