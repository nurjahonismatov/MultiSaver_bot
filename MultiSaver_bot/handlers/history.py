from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from database.models import User
from database.repository import HistoryRepository
from database.session import async_session_factory
from keyboards.settings import history_kb
from utils.i18n import get_text

router = Router(name="history")


@router.message(Command("history"))
@router.callback_query(F.data == "menu:history")
async def show_history(event: Message | CallbackQuery, db_user: User, lang: str) -> None:
    async with async_session_factory() as session:
        repo = HistoryRepository(session)
        records = await repo.get_user_history(db_user.telegram_id, limit=15)

    if not records:
        text = get_text("history.empty", lang)
    else:
        lines = [get_text("history.title", lang)]
        for r in records:
            date_str = r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "-"
            lines.append(
                get_text(
                    "history.item",
                    lang,
                    platform=r.platform,
                    media_type=r.media_type or "-",
                    status=r.status,
                    date=date_str,
                )
            )
        text = "\n".join(lines)

    kb = history_kb(lang)
    if isinstance(event, Message):
        await event.answer(text, reply_markup=kb)
    else:
        await event.answer()
        await event.message.answer(text, reply_markup=kb)


@router.callback_query(F.data == "history:clear")
async def clear_history(callback: CallbackQuery, db_user: User, lang: str) -> None:
    async with async_session_factory() as session:
        repo = HistoryRepository(session)
        await repo.clear_user_history(db_user.telegram_id)
        await session.commit()

    await callback.answer()
    await callback.message.answer(get_text("history.cleared", lang))
