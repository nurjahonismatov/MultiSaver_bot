import asyncio
from aiogram import Bot
from MultiSaver_bot.config import get_settings

async def main():
    get_settings.cache_clear()
    settings = get_settings()
    bot = Bot(token=settings.bot_token)

    try:
        me = await bot.get_me()
        print(f"MUVAFFAQIYAT! Bot ishlayapti: @{me.username}")
    except Exception as e:
        print("Xato turi:", type(e).__name__)
        print("Xabar:", str(e))
    finally:
        await bot.session.close()

asyncio.run(main())
