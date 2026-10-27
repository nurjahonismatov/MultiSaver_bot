"""Settings handlers."""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from database.models import User
from database.repository import UserRepository
from database.session import async_session_factory
from keyboards.main_menu import main_menu_kb
from keyboards.onboarding import onboarding_q1_kb
from keyboards.settings import settings_kb
from utils.i18n import get_text

router = Router(name="settings")


@router.message(Command("settings"))
@router.callback_query(F.data == "menu:settings")
async def show_settings(event: Message | CallbackQuery, lang: str) -> None:
    text = get_text("settings.title", lang)
    kb = settings_kb(lang)
    if isinstance(event, Message):
        await event.answer(text, reply_markup=kb)
    else:
        await event.answer()
        await event.message.answer(text, reply_markup=kb)


@router.callback_query(F.data == "settings:privacy")
async def show_privacy(callback: CallbackQuery, lang: str) -> None:
    await callback.answer()
    await callback.message.answer(get_text("privacy.text", lang))


@router.callback_query(F.data == "settings:survey")
async def restart_survey(callback: CallbackQuery, db_user: User, lang: str) -> None:
    await callback.answer()
    async with async_session_factory() as session:
        repo = UserRepository(session)
        await repo.reset_onboarding(db_user.telegram_id)
        await session.commit()

    await callback.message.answer(
        get_text("onboarding.q1", lang),
        reply_markup=onboarding_q1_kb(lang),
    )
