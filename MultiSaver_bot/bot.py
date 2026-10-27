"""MultiSaver_bot — to'liq ishlaydigan kirish nuqtasi."""

import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message

from config import get_settings
from database.session import close_db, init_db
from handlers import setup_routers
from middlewares.throttling import ThrottlingMiddleware
from middlewares.user_context import UserContextMiddleware
from utils.logging_setup import setup_logging

logger = logging.getLogger(__name__)


async def main() -> None:
    setup_logging()
    settings = get_settings()

    if not settings.bot_token or settings.bot_token.startswith(("replace_", "TEST_", "YANGI_")):
        logger.error("BOT_TOKEN noto'g'ri. .env faylni tekshiring.")
        return

    await init_db()
    logger.info("Database initialized")

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Middleware
    dp.message.middleware(UserContextMiddleware())
    dp.callback_query.middleware(UserContextMiddleware())
    dp.message.middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware())

    # Barcha routerlar (buyruqlar ichida)
    dp.include_router(setup_routers())

    # MUHIM: hech qanday umumiy "havola yuboring" handler YO'Q

    logger.info("Starting MultiSaver_bot...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await close_db()
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass