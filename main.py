# main.py

import logging

from telegram.ext import Application

from constants import BOT_TOKEN

from handlers import reg_all_handlers
from utils import setup_logging
from globals import user_data_list, posts_queue, load_user_data_from_file

setup_logging()
logger = logging.getLogger(__name__)


def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    reg_all_handlers(application)
    application.run_polling()


if __name__ == "__main__":
    main()
