from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from database.models import User
from keyboards.main_menu import main_menu_kb
from keyboards.onboarding import onboarding_q1_kb
from utils.i18n import get_text

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, db_user: User, lang: str) -> None:
    name = (message.from_user.first_name if message.from_user else None) or "User"
    await message.answer(get_text("start.welcome", lang, first_name=name))
    if not getattr(db_user, "onboarding_completed", True) and not getattr(db_user, "onboarding_skipped", False):
        await message.answer(get_text("onboarding.q1", lang), reply_markup=onboarding_q1_kb(lang))
    else:
        await message.answer(get_text("start.main_menu", lang), reply_markup=main_menu_kb(lang))


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, lang: str) -> None:
    await message.answer(get_text("cancel.ok", lang))


@router.callback_query(F.data == "menu:main")
async def cb_main(callback: CallbackQuery, lang: str) -> None:
    await callback.answer()
    await callback.message.answer(get_text("start.main_menu", lang), reply_markup=main_menu_kb(lang))