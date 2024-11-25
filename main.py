# main.py

import logging
from telegram.ext import Application
from db_conf import BOT_TOKEN
from utils import setup_logging
from service_db import db, User, Channel, Chat, Post, Message
from handlers import reg_all_handlers

logger = logging.getLogger(__name__)
setup_logging()
db.connect()
db.create_tables([User, Channel, Chat, Post, Message])


def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    setup_logging()

    reg_all_handlers(application)

    application.run_polling()


if __name__ == "__main__":
    main()
