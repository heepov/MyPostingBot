# main.py

import logging

from telegram.ext import Application

from secret import BOT_TOKEN

# from globals import load_user_data_from_file, posts_queue, user_data_list
# from handlers import reg_all_handlers
# from utils import setup_logging
from service_db import User, Channel, Chat, Post, Message, db
from telegram import Update
from telegram.ext import (
    CallbackContext,
    ChatMemberHandler,
    CommandHandler,
    MessageHandler,
    filters,
)



logger = logging.getLogger(__name__)


async def start(update: Update, context: CallbackContext) -> None:
    message = update.effective_message

    # Проверка, существует ли уже пользователь в базе
    user, created = User.get_or_create(
        user_id=message.from_user.id,
        defaults={
            "first_name": message.from_user.first_name,
            "last_name": message.from_user.last_name,
            "username": message.from_user.username,
            "language_code": message.from_user.language_code,
        },
    )

    if created:
        print(f"User {user.first_name} created successfully.")
    else:
        print(f"User {user.first_name} already exists.")


def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    setup_logging()
    db.connect()
    db.create_tables([User, Channel, Chat, Post, Message])

    application.add_handler(CommandHandler("start", start))

    application.run_polling()


if __name__ == "__main__":
    main()
