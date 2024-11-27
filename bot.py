import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from db.db import create_tables, connect_db, delete_db
from handlers import add_channel, common
from utils.config_reader import config
from utils.utils import setup_logging

logger = logging.getLogger(__name__)

setup_logging()

connect_db()
delete_db()
create_tables()


async def main():
    setup_logging()

    dp = Dispatcher(storage=MemoryStorage())
    bot = Bot(config.bot_token.get_secret_value())

    dp.include_router(common.router)
    dp.include_router(add_channel.router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
