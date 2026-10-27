from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from database.models import User
from database.repository import UserRepository
from database.session import async_session_factory
from keyboards.language import language_kb
from keyboards.main_menu import main_menu_kb
from utils.i18n import get_text

router = Router(name="language")


@router.message(Command("language"))
async def cmd_language(message: Message, lang: str) -> None:
    await message.answer(get_text("language.choose", lang), reply_markup=language_kb(lang))


@router.callback_query(F.data == "menu:languages")
async def cb_language(callback: CallbackQuery, lang: str) -> None:
    await callback.answer()
    await callback.message.answer(get_text("language.choose", lang), reply_markup=language_kb(lang))


@router.callback_query(F.data.startswith("lang:"))
async def set_lang(callback: CallbackQuery, db_user: User, lang: str) -> None:
    await callback.answer()
    new_lang = callback.data.split(":", 1)[1]
    if new_lang not in ("uz", "en", "ru"):
        return
    async with async_session_factory() as session:
        repo = UserRepository(session)
        await repo.set_language(db_user.telegram_id, new_lang)
        await session.commit()
    await callback.message.answer(get_text("language.changed", new_lang))
    await callback.message.answer(get_text("start.main_menu", new_lang), reply_markup=main_menu_kb(new_lang))