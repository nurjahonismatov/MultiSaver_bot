from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from keyboards.main_menu import main_menu_kb
from utils.i18n import get_text

router = Router(name="help")


@router.message(Command("help"))
async def cmd_help(message: Message, lang: str) -> None:
    await message.answer(get_text("help.text", lang))
    await message.answer(get_text("start.main_menu", lang), reply_markup=main_menu_kb(lang))


@router.message(Command("supported"))
async def cmd_supported(message: Message, lang: str) -> None:
    await message.answer(get_text("platforms.title", lang))


@router.callback_query(F.data == "menu:help")
async def cb_help(callback: CallbackQuery, lang: str) -> None:
    await callback.answer()
    await callback.message.answer(get_text("help.text", lang))


@router.callback_query(F.data == "menu:platforms")
async def cb_platforms(callback: CallbackQuery, lang: str) -> None:
    await callback.answer()
    await callback.message.answer(get_text("platforms.title", lang))