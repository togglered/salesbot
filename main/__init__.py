from aiogram import Bot, Dispatcher

from handlers.client import client_router
from handlers.admin import admin_router
from database.models import async_main
from app_config import CONFIG


async def main():
    await async_main()
    bot = Bot(token=CONFIG["BOT_TOKEN"])
    dp = Dispatcher()
    dp.include_router(client_router)
    dp.include_router(admin_router)
    await dp.start_polling(bot)

