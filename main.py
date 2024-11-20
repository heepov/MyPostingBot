# main.py
import logging

from constants import BOT_TOKEN
from telegram.ext import Application
from apscheduler.schedulers.background import BackgroundScheduler

from user_data_manager import user_data_manager
from utils import setup_logging, files_cleaner
from handlers import register_all_handlers

setup_logging()
logger = logging.getLogger(__name__)

files_cleaner()
scheduler = BackgroundScheduler()


def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    application.bot_data["scheduler"] = scheduler
    user_data_manager.get_state()
    register_all_handlers(application)

    scheduler.start()
    application.run_polling()


if __name__ == "__main__":
    main()
