import asyncio
import os

import dotenv
from aiogram import Bot, Dispatcher

from handlers import (handlers_router, instagram_router, pinterest_router,
                      soundcloud_router, tiktok_router, youtube_router)
from handlers.handler import set_commands

dotenv.load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.include_router(handlers_router)
dp.include_router(soundcloud_router)
dp.include_router(pinterest_router)
dp.include_router(tiktok_router)
dp.include_router(instagram_router)
dp.include_router(youtube_router)


async def main():
    await set_commands(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
