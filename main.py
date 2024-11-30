import asyncio
import logging

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import setup_logging
from src.db import connect_db, create_tables
from src.bot.handlers import routers
from src.bot.middlewares import LoggingMiddleware
from src.services.scheduler_service import PostScheduler
from src.bot.bot_instance import bot


async def main():
    setup_logging()
    connect_db()
    create_tables()

    dp = Dispatcher(storage=MemoryStorage())

    # Создаем планировщик
    scheduler = PostScheduler(bot)
    scheduler.start()

    try:
        dp.callback_query.middleware(LoggingMiddleware())
        dp.message.middleware(LoggingMiddleware())

        for router in routers:
            router.callback_data = {"scheduler": scheduler}
            dp.include_router(router)

        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
