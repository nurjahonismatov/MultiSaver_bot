from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from services.rate_limiter import get_rate_limiter
from utils.errors import RateLimitError
from utils.i18n import get_text


class ThrottlingMiddleware(BaseMiddleware):
    """Apply rate limiting to messages that look like download requests."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id = None
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
            # Only throttle text that looks like a URL
            text = (event.text or "").strip()
            if not (text.startswith("http") or "instagram" in text or "pinterest" in text):
                return await handler(event, data)
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id
            # Light throttle on callbacks
        else:
            return await handler(event, data)

        if user_id is None:
            return await handler(event, data)

        limiter = get_rate_limiter()
        try:
            limiter.check(user_id)
        except RateLimitError as exc:
            lang = data.get("lang", "uz")
            text = get_text("download.rate_limit", lang, seconds=exc.seconds)
            if isinstance(event, Message):
                await event.answer(text)
            elif isinstance(event, CallbackQuery):
                await event.answer(text, show_alert=True)
            return None

        return await handler(event, data)
