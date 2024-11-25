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
from action_db import create_user, get_user_state
from service_db import State
from actions_chat import (
    actions_chat_handlers,
    cmd_add_channel,
    cmd_channels,
    cmd_set_channel
)
from telegram.helpers import effective_message_type
from action_db import set_user_state

logger = logging.getLogger(__name__)


def reg_all_handlers(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cancel", cancel))

    application.add_handler(CommandHandler("channels", cmd_channels))
    application.add_handler(CommandHandler("add_channel", cmd_add_channel))
    application.add_handler(CommandHandler("set_channel", cmd_set_channel))

    # application.add_handler(CommandHandler("delete_channel", cmd_delete_channel))

    application.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE & ~filters.COMMAND, bot_private_massage_handlers
        )
    )


# Private message processing (from bot and not command)
async def bot_private_massage_handlers(
    update: Update, context: CallbackContext
) -> None:
    user = update.effective_user
    create_user(user)
    state = get_user_state(user.id)

    if effective_message_type(update.effective_message) != "text":
        await update.message.reply_text("Wrong input. Try again")
        return

    if state in [State.ADD_CHANNEL, State.ADD_CHAT, State.DELETE_CHANNEL, State.CHANNEL_SETTINGS, State.CHOOSE_ACTION]:
        await actions_chat_handlers(update, context)
        return


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

    # user = await get_user_data(update)
    # await log_processing_info(update, "command /start")
    # # save_post_queue_to_file()
    # # save_user_data_to_file()
    # await update.message.reply_text(f"What's up {user.user_name}?")


async def cancel(update: Update, context: CallbackContext) -> None:
    state = set_user_state(update.effective_user.id, State.IDLE)


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
