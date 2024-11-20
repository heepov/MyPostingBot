# main.py
import logging

from os import getenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

from user_data_manager import user_data_manager
from utils import setup_logging, files_cleaner
from handlers import register_all_handlers

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

    register_all_handlers(application)

    # Запуск планировщика
    scheduler.start()

    application.run_polling()


if __name__ == "__main__":
    main()
