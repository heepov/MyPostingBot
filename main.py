# main.py

import logging

from telegram.ext import Application

from constants import BOT_TOKEN
from handlers import register_all_handlers
from user_data_manager import user_data_manager
from utils import files_cleaner, setup_logging

setup_logging()
logger = logging.getLogger(__name__)

files_cleaner()


def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    user_data_manager.get_state()
    
    register_all_handlers(application)
    application.run_polling()


if __name__ == "__main__":
    main()
