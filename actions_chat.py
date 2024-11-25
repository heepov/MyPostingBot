# setup.py

import logging

from telegram import Update
from telegram.ext import CallbackContext

from action_db import (
    create_channel,
    create_user,
    del_channel,
    del_chat,
    get_all_user_channels,
    get_channel_chat,
    get_selected_channel,
    get_user_state,
    is_channel_exists_for_user,
    set_channel_selected,
    set_user_state,
)
from service_db import State
from utils import check_bot_permission, check_link

logger = logging.getLogger(__name__)
required_states = [State.IDLE, State.ERROR]


async def actions_chat_handlers(update: Update, context: CallbackContext) -> None:
    global channel_id
    user = update.effective_user
    create_user(user)
    state = get_user_state(user.id)
    logger.info(f"STATE {state}")
    if not state:
        await update.message.reply_text("Shit happened! Use /cancel")
        return

    if state == State.ADD_CHANNEL:
        await add_channel(update, context, True)
    elif state == State.CHANNEL_SETTINGS:
        await set_channel(update, context)
    elif state == State.CHOOSE_ACTION:
        await choose_action(update, context)
    elif state == State.ADD_CHAT:
        await add_channel(update, context, False)
    else:
        await update.message.reply_text("Shit happened! Use /cancel")


def get_channel_string(channels) -> str:
    if len(channels) == 0:
        return f"You dont have any channels"

    str = "Your channels:\n"
    i = 1
    for channel in channels:
        if channel.permission:
            str += f"{i} @{channel.username}"
            i += 1
            chat = get_channel_chat(channel.channel_id)
            if chat != None:
                if chat.permission:
                    str += f" connected with chat: @{chat.username}"
        str += f"\n"
    return str


async def cmd_channels(update: Update, context: CallbackContext):
    user = update.effective_user
    create_user(user)
    state = get_user_state(user.id)

    if not state:
        await update.message.reply_text("Shit happened! Use /cancel")
        return

    channels = get_all_user_channels(user.id)

    await update.message.reply_text(get_channel_string(channels))


async def cmd_add_channel(update: Update, context: CallbackContext):
    user = update.effective_user
    create_user(user)
    state = get_user_state(user.id)

    if not state:
        await update.message.reply_text("Shit happened! Use /cancel")
        return
    if state not in required_states:
        await update.message.reply_text("Finish your current task first!")
        return

    await update.message.reply_text(
        "Send me your CHANNEL link or username. Or use /cancel"
    )
    set_user_state(user.id, State.ADD_CHANNEL)


async def cmd_set_channel(update: Update, context: CallbackContext):
    user = update.effective_user
    create_user(user)
    state = get_user_state(user.id)

    if not state:
        await update.message.reply_text("Shit happened! Use /cancel")
        return
    if state not in required_states:
        await update.message.reply_text("Finish your current task first!")
        return

    channel = get_all_user_channels(user.id)

    if len(channel) == 0:
        await update.message.reply_text(
            "You dont have any channels. Use /add_channel first!"
        )
        return

    set_user_state(user.id, State.CHANNEL_SETTINGS)
    await update.message.reply_text(f"Chose channel:\n {get_channel_string(channel)}")


async def set_channel(update: Update, context: CallbackContext):
    user = update.effective_user
    create_user(user)
    user_id = update.effective_user.id
    input = update.effective_message.text

    if not input.isdigit():
        await update.message.reply_text(f"Error send normal number or /cancel")
        return

    channels = get_all_user_channels(user_id)

    if int(input) > len(channels) or int(input) < 1:
        await update.message.reply_text(f"Error send normal number or /cancel")
        return
    await update.message.reply_text(
        f"You choose channel: @{channels[int(input) - 1].username}"
    )
    set_channel_selected(channels[int(input) - 1].channel_id, user_id)

    await update.message.reply_text(
        f"Choose you action:\n1. To add chat\n2. To delete channel"
    )
    set_user_state(user.id, State.CHOOSE_ACTION)


async def choose_action(update: Update, context: CallbackContext):
    user = update.effective_user
    create_user(user)
    user_id = update.effective_user.id
    input = update.effective_message.text

    if not input.isdigit():
        await update.message.reply_text(f"Error send normal number or /cancel")
        return
    if input not in ["1", "2"]:
        await update.message.reply_text(f"Error send normal number or /cancel")
        return

    if input == "1":
        set_user_state(user.id, State.ADD_CHAT)
        await update.message.reply_text(
            f"Send me your CHAT link or username. Or use /cancel"
        )
    else:
        del_channel(get_selected_channel(user_id))
        await update.message.reply_text(f"Noice DELETING CHANNEL")
        set_user_state(user_id, State.IDLE)


async def add_channel(
    update: Update,
    context: CallbackContext,
    is_channel: bool = True,
) -> None:
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

    if is_channel_exists_for_user(user_id, chat_id):
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
        create_channel(data, None)
    else:
        del_chat(get_channel_chat(get_selected_channel(user_id)))
        create_channel(data, get_selected_channel(user_id))

    await update.message.reply_text("COOL!")
    set_user_state(user_id, State.IDLE)
