from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from database.repository import UserRepository
from database.session import async_session_factory


class UserContextMiddleware(BaseMiddleware):
    """Load or create user and attach to data['user'] and data['lang']."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        tg_user = None
        if isinstance(event, Message) and event.from_user:
            tg_user = event.from_user
        elif isinstance(event, CallbackQuery) and event.from_user:
            tg_user = event.from_user

        if tg_user is None:
            return await handler(event, data)

        async with async_session_factory() as session:
            repo = UserRepository(session)
            user, _ = await repo.get_or_create(
                telegram_id=tg_user.id,
                first_name=tg_user.first_name,
                last_name=tg_user.last_name,
                username=tg_user.username,
            )
            await session.commit()
            data["db_user"] = user
            data["lang"] = user.language or "uz"

        return await handler(event, data)
