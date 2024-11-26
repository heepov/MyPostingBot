# handlers.py

import logging
from telegram import constants

from telegram import Update
from telegram.ext import (
    CallbackContext,
    ChatMemberHandler,
    CommandHandler,
    MessageHandler,
    filters,
)
from action_db import (
    db_create_user,
    db_get_user_state,
    db_get_all_channels_ids,
    db_get_all_chats_ids,
    db_set_channel_permission,
    db_set_chat_permission,
)
from service_db import State
from actions_chat import (
    handle_chat_messages,
    cmd_add_channel,
    cmd_show_channels,
    cmd_select_channel,
)
from actions_post import (
    handle_post_messages,
    cmd_add_post,
    cmd_add_post_chat,
    cmd_post_time,
    cmd_set_channel,
)
from send_post_logic import send_messages_at_comment
from telegram.helpers import effective_message_type
from action_db import db_set_user_state

logger = logging.getLogger(__name__)


def reg_all_handlers(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("schedule", cmd_schedule))

    application.add_handler(CommandHandler("my_channels", cmd_show_channels))
    application.add_handler(CommandHandler("add_channel", cmd_add_channel))
    application.add_handler(CommandHandler("settings_channel", cmd_select_channel))

    application.add_handler(CommandHandler("add_post", cmd_add_post))
    application.add_handler(CommandHandler("add_post_chat", cmd_add_post_chat))
    application.add_handler(CommandHandler("time", cmd_post_time))
    application.add_handler(CommandHandler("set_channel", cmd_set_channel))

    application.add_handler(ChatMemberHandler(on_chat_member_update))

    application.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE & ~filters.COMMAND, bot_private_massage_handlers
        )
    )
    application.add_handler(
        MessageHandler(~filters.COMMAND, bot_reply_messages_from_chat)
    )


async def bot_reply_messages_from_chat(
    update: Update, context: CallbackContext
) -> None:
    if update.effective_message.forward_origin:
        logger.info("Это пересланное сообщение")
        logger.info(f"{update.effective_message.forward_origin.chat.id}")
        logger.info(f"{update.effective_message.forward_origin.message_id}")
        # logger.info(f"{update.effective_message.chat_id}")
        # logger.info(f"{update.effective_message.message_id}")
        await send_messages_at_comment(update, context)
    else:
        logger.warning("Это сообщение не является пересланным.")


# Private message processing (from bot and not command)
async def bot_private_massage_handlers(
    update: Update, context: CallbackContext
) -> None:
    user = update.effective_user
    db_create_user(user)
    state = db_get_user_state(user.id)

    if state in [
        State.ADD_CHANNEL,
        State.CHANNEL_SELECT,
        State.CHANNEL_SETTINGS,
        State.ADD_CHAT,
    ]:
        if effective_message_type(update.effective_message) != "text":
            await update.message.reply_text("Wrong input. Try again")
            return
        await handle_chat_messages(update, context)
        return

    elif state in [
        State.ADD_POST,
        State.ADD_POST_CHAT,
        State.SET_POST_TIME,
        State.SET_CHANNEL,
    ]:
        if effective_message_type(update.effective_message) != "text" and state in [
            State.SET_POST_TIME,
            State.SET_CHANNEL,
        ]:
            await update.message.reply_text("Wrong input. Try again")
            return
        await handle_post_messages(update, context)
        return

    elif state == State.IDLE:
        await start(update, context)
    else:
        await update.message.reply_text("Shit happened! Use /cancel")


async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Hi! Use /help command!")


async def cancel(update: Update, context: CallbackContext) -> None:
    state = db_set_user_state(update.effective_user.id, State.IDLE)


async def help(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("This is help command!")


async def on_chat_member_update(update, context):

    chat_id = update.my_chat_member.chat.id
    member = update.my_chat_member.new_chat_member
    bot = await context.bot.get_me()
    if member.user.id != bot.id:
        return

    if member.status == constants.ChatMemberStatus.ADMINISTRATOR:
        can_post_messages = getattr(member, "can_post_messages", None)
        if can_post_messages is None:
            permission_change(chat_id, True)
        elif can_post_messages:
            permission_change(chat_id, True)
        else:
            permission_change(chat_id, False)
    else:
        permission_change(chat_id, False)


def permission_change(chat_id, permission):
    channel_ids = db_get_all_channels_ids()
    chat_ids = db_get_all_chats_ids()

    if chat_id in channel_ids:
        logger.info(
            f"PERMISSIONS in channel {chat_id} has been changed to {permission}"
        )
        db_set_channel_permission(chat_id, permission)

    if chat_id in chat_ids:
        logger.info(
            f"PERMISSIONS in channel {chat_id} has been changed to {permission}"
        )
        db_set_chat_permission(chat_id, permission)
