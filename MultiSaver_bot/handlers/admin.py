"""Admin panel (restricted)."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import get_settings
from database.repository import HistoryRepository, UserRepository
from database.session import async_session_factory
from utils.i18n import get_text

router = Router(name="admin")


def is_admin(user_id: int) -> bool:
    return user_id in get_settings().admin_id_list


@router.message(Command("admin"))
async def admin_stats(message: Message, lang: str) -> None:
    if not is_admin(message.from_user.id):
        await message.answer(get_text("admin.denied", lang))
        return

    async with async_session_factory() as session:
        user_repo = UserRepository(session)
        hist_repo = HistoryRepository(session)
        users = await user_repo.count_users()
        total = await hist_repo.count_total()
        success = await hist_repo.count_by_status("success")
        failed = await hist_repo.count_by_status("failed")

    text = get_text(
        "admin.stats",
        lang,
        users=users,
        total=total,
        success=success,
        failed=failed,
    )
    await message.answer(text)
