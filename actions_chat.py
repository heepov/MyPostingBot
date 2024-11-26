# setup.py

import logging

from telegram import Update
from telegram.ext import CallbackContext

from action_db import (
    db_create_channel_or_chat,
    db_delete_channel,
    db_delete_chat,
    db_get_user_channels_with_permission,
    db_get_chat_by_channel,
    db_get_selected_channel,
    db_get_user_state,
    db_get_channel,
    db_set_selected_channel,
    db_set_user_state,
)
from service_db import State
from utils import check_bot_permission, check_link, command_checker, get_channel_string

logger = logging.getLogger(__name__)


async def handle_chat_messages(update: Update, context: CallbackContext) -> None:

    if not await command_checker(
        update,
        context,
        [
            State.ADD_CHANNEL,
            State.CHANNEL_SELECT,
            State.CHANNEL_SETTINGS,
            State.ADD_CHAT,
        ],
    ):
        return

    user = update.effective_user
    state = db_get_user_state(user.id)

    if state == State.ADD_CHANNEL:
        await handle_add_channel(update, context, True)
    elif state == State.CHANNEL_SELECT:
        await handle_select_channel(update, context)
    elif state == State.CHANNEL_SETTINGS:
        await handle_channel_settings(update, context)
    elif state == State.ADD_CHAT:
        await handle_add_channel(update, context, False)
    else:
        await update.message.reply_text("Shit happened! Use /cancel")


async def cmd_show_channels(update: Update, context: CallbackContext):
    if not await command_checker(update, context, [State.IDLE]):
        return

    user = update.effective_user

    channels = db_get_user_channels_with_permission(user.id)
    await update.message.reply_text(f"Your channels:\n{get_channel_string(channels)}")


async def cmd_add_channel(update: Update, context: CallbackContext):
    if not await command_checker(update, context, [State.IDLE]):
        return

    user = update.effective_user

    await update.message.reply_text(
        "Send me your CHANNEL link or username. Or use /cancel"
    )
    db_set_user_state(user.id, State.ADD_CHANNEL)


async def cmd_select_channel(update: Update, context: CallbackContext, action: str):
    if not await command_checker(update, context, [State.IDLE]):
        return

    user = update.effective_user
    channels = db_get_user_channels_with_permission(user.id)

    if len(channels) == 0:
        await update.message.reply_text(
            "You don't have any channels. Use /add_channel first!"
        )
        return

    db_set_user_state(user.id, State.CHANNEL_SELECT)

    await update.message.reply_text(
        f"Choose a channel:\n{get_channel_string(channels)}"
    )


async def handle_select_channel(update: Update, context: CallbackContext):

    if not await command_checker(update, context, [State.CHANNEL_SELECT]):
        return

    user = update.effective_user
    input = update.effective_message.text

    if not input.isdigit():
        await update.message.reply_text(f"Error send normal number or /cancel")
        return

    channels = db_get_user_channels_with_permission(user.id)

    if int(input) > len(channels) or int(input) < 1:
        await update.message.reply_text(f"Error send normal number or /cancel")
        return

    await update.message.reply_text(
        f"You choose channel: @{channels[int(input) - 1].username}"
    )

    db_set_selected_channel(channels[int(input) - 1].channel_id, user.id)

    await update.message.reply_text(
        f"Choose you action:\n1. To add chat\n2. To delete channel"
    )
    db_set_user_state(user.id, State.CHANNEL_SETTINGS)


async def handle_channel_settings(update: Update, context: CallbackContext):
    if not await command_checker(update, context, [State.CHANNEL_SETTINGS]):
        return

    user = update.effective_user
    input = update.effective_message.text

    if not input.isdigit():
        await update.message.reply_text(f"Error send normal number or /cancel")
        return
    if input not in ["1", "2"]:
        await update.message.reply_text(f"Error send normal number or /cancel")
        return

    if input == "1":
        db_set_user_state(user.id, State.ADD_CHAT)
        await update.message.reply_text(
            f"Send me your CHAT link or username. Or use /cancel"
        )
    else:
        db_delete_channel(db_get_selected_channel(user.id).channel_id)
        await update.message.reply_text(f"You delete channel!")
        db_set_user_state(user.id, State.IDLE)


async def handle_add_channel(
    update: Update,
    context: CallbackContext,
    is_channel: bool = True,
) -> None:
    if not await command_checker(update, context, [State.ADD_CHANNEL, State.ADD_CHAT]):
        return

    input = update.effective_message.text
    user_id = update.effective_user.id

    link = check_link(input.strip())

    if not link:
        await update.message.reply_text("Wrong link. Try again")
        return

    try:
        chat_info = await context.bot.get_chat(link)
    except Exception as e:
        await update.message.reply_text(f"Cant get chat info: {e}")
        return
    chat_id = chat_info.id

    if is_channel:
        if db_get_channel(user_id, chat_id) != None:
            await update.message.reply_text("Channel already added.")
            return

    try:
        permission_check = await check_bot_permission(context.bot, chat_info.id)
        if permission_check != True:
            await update.message.reply_text(
                "Bot doesn't have permission in this channel"
            )
            return
    except Exception as e:
        await update.message.reply_text(f"Some error: {e}")
        return

    data = {
        "channel_id": chat_id,
        "username": chat_info.username,
        "permission": permission_check,
        "user_id": user_id,
    }

    if is_channel:
        db_create_channel_or_chat(data, None)
    else:
        channel = db_get_selected_channel(user_id)
        if channel == None:
            await update.message.reply_text("You dont have selected channel")
            return
        chat = db_get_chat_by_channel(channel.chanel_id)
        if chat != None:
            db_delete_chat(chat.chat_id)
        db_create_channel_or_chat(data, channel.channel_id)

    await update.message.reply_text("COOL!")
    db_set_user_state(user_id, State.IDLE)
