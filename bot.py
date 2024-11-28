import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from db.db import create_tables, connect_db
from handlers import add_channel, common, add_post, select_channel
from utils.config_reader import config
from utils.utils import setup_logging
from middlewares.bot_middleware import BotMiddleware

logger = logging.getLogger(__name__)

setup_logging()

connect_db()
create_tables()


async def main():
    dp = Dispatcher(storage=MemoryStorage())
    bot = Bot(config.bot_token.get_secret_value())

    dp.message.middleware.register(BotMiddleware(bot))


    dp.include_router(add_channel.router)
    dp.include_router(add_post.router)
    dp.include_router(select_channel.router)
    dp.include_router(common.router)
    
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
