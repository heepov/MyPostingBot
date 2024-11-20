# main.py
import logging

from os import getenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

from user_data_manager import user_data_manager
from utils import setup_logging, files_cleaner
from handlers import (
    start,
    help,
    cancel,
    end,
    checkup,
    setup,
    add,
    private_messages,
    reply_post,
)

# Настройка логирования
setup_logging()
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()


# Основная функция
def main() -> None:
    # Инициализация приложения и планировщика
    application = Application.builder().token(getenv("BOT_TOKEN")).build()
    scheduler = BackgroundScheduler()
    application.bot_data["scheduler"] = scheduler
    files_cleaner()
    user_data_manager.get_state()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CommandHandler("end", end))
    application.add_handler(CommandHandler("checkup", checkup))
    application.add_handler(CommandHandler("setup", setup))
    application.add_handler(CommandHandler("add", add))

    application.add_handler(
        MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, private_messages)
    )
    application.add_handler(MessageHandler(~filters.COMMAND, reply_post))

    # Запуск планировщика
    scheduler.start()

    application.run_polling()


if __name__ == "__main__":
    main()
