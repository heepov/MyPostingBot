# handlers.py

import logging

from telegram import Update
from telegram.ext import (
    CallbackContext,
    ChatMemberHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

# from actions_chat import actions_chat_handlers, reg_chat_handlers
# from actions_post import actions_post_handlers, reg_post_handlers
# from actions_user import get_user_data
# from file_service import load_file, save_file
# from globals import (
#     load_user_data_from_file,
#     posts_queue,
#     save_user_data_to_file,
#     user_data_list,
# )
# from states import State
# from utils import log_processing_info

logger = logging.getLogger(__name__)

from service_db import User, Channel, Chat, Post, Message, db


def reg_all_handlers(application):


    # reg_post_handlers(application)
    # reg_chat_handlers(application)

    application.add_handler(CommandHandler("start", start))

    # application.add_handler(CommandHandler("cancel", cancel))
    # application.add_handler(CommandHandler("save", save))
    # application.add_handler(CommandHandler("load", load))

    # application.add_handler(
    #     MessageHandler(
    #         filters.ChatType.PRIVATE & ~filters.COMMAND, bot_private_massage_handlers
    #     )
    # )


# Private message processing (from bot and not command)
# async def bot_private_massage_handlers(
#     update: Update, context: CallbackContext
# ) -> None:
#     user = await get_user_data(update)
#     await log_processing_info(update, "message")

#     state = user.state

#     if state in [State.ADD_CHANNEL, State.ADD_CHAT, State.DELETE_CHANNEL]:
#         await actions_chat_handlers(update, context)
#         return
#     if state in [
#         State.ADD_POST,
#         State.ADD_POST_CHAT,
#         State.SET_POST_TIME,
#         State.SET_CHANNEL,
#     ]:
#         await actions_post_handlers(update, context)
#         return

#     if state == State.IDLE:
#         await start(update, context)
#     elif state == State.ERROR:
#         await update.message.reply_text(
#             "You dont have any channels or channel have not required permissions"
#         )
#     else:
#         await update.message.reply_text("Shit happened! Use /cancel")


async def start(update: Update, context: CallbackContext) -> None:
    message = update.effective_message

    # Проверка, существует ли уже пользователь в базе
    user, created = User.get_or_create(
        user_id=message.from_user.id,
        defaults={
            'first_name': message.from_user.first_name,
            'last_name': message.from_user.last_name,
            'username': message.from_user.username,
            'language_code': message.from_user.language_code,
        }
    )

    if created:
        print(f"User {user.first_name} created successfully.")
    else:
        print(f"User {user.first_name} already exists.")

    # user = await get_user_data(update)
    # await log_processing_info(update, "command /start")
    # # save_post_queue_to_file()
    # # save_user_data_to_file()
    # await update.message.reply_text(f"What's up {user.user_name}?")


# async def cancel(update: Update, context: CallbackContext) -> None:
#     user = await get_user_data(update)
#     if user.user_has_channel_with_permission():
#         user.state = State.IDLE
#     else:
#         user.state = State.ERROR

#     await log_processing_info(update, "command /cancel")
#     await update.message.reply_text("Your last action has been canceled")


# async def save(update: Update, context: CallbackContext) -> None:
#     await update.message.reply_text(f"DATA SAVE")
#     save_user_data_to_file(user_data_list)


# async def load(update: Update, context: CallbackContext) -> None:
#     await update.message.reply_text(f"DATA LOAD")
#     load_user_data_from_file()
