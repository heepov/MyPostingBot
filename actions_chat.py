# setup.py

from utils import check_bot_permission, check_link, log_processing_info
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler
import logging
from user_data import Channel
from states import State
from strings import (
    ERROR_PERMISSION_STRING,
    CHAT_SETUP_STRING,
    ERROR_CHANNEL_LINK,
    ERROR_GET_CHANNEL_INFO,
    CHANNEL_SETUP_STRING,
)

tmp_chat = Channel()

from actions_user import get_user_data

logger = logging.getLogger(__name__)

def reg_chat_handlers(application)->None:
    application.add_handler(CommandHandler("channels", cmd_channels))
    application.add_handler(CommandHandler("add_channel", cmd_add_channel))
    application.add_handler(CommandHandler("delete_channel", cmd_delete_channel))

async def actions_chat_handlers(update: Update, context: CallbackContext) -> None:
    user = await get_user_data(update)
    state = user.state

    if state == State.ADD_CHANNEL:
        await add_channel(update, context, tmp_chat)
    elif state == State.ADD_CHAT:
        await add_channel(update, context, tmp_chat)
    elif state == State.DELETE_CHANNEL:
        await delete_channel(update, context)
    else:
        await update.message.reply_text("Shit happened! Use /cancel")


async def get_channel_string(update: Update, context: CallbackContext) -> str:
    user = await get_user_data(update)
    str = ""
    i = 1
    for channel in user.channels:
        try:
            if channel.channel_id and channel.channel_permission:
                info = await context.bot.get_chat(channel.channel_id)
                username = info.username

                str += f"{i}. @{username}"
                if channel.chat_id and channel.chat_permission:
                    info = await context.bot.get_chat(channel.chat_id)
                    username = info.username

                    str += f" with chat: @{username}\n"
                else:
                    str += "\n"
        except Exception as e:
            logger.error({e})
            return "ERROR"
        i += 1
    return str


async def cmd_channels(update: Update, context: CallbackContext):
    user = await get_user_data(update)
    await log_processing_info(update, "command /my_channels")

    if not user.user_has_channel_with_permission():
        await update.message.reply_text(f"You dont have any channels")
        return
    else:
        await update.message.reply_text(
            f"Your channels:\n{await get_channel_string(update, context)}"
        )


async def cmd_add_channel(update: Update, context: CallbackContext):
    global tmp_chat
    tmp_chat = Channel()
    user = await get_user_data(update)
    await log_processing_info(update, "command /add_channel")

    await update.message.reply_text(
        "Send me your CHANNEL link or username. Or use /cancel"
    )
    user.state = State.ADD_CHANNEL


async def cmd_delete_channel(update: Update, context: CallbackContext):
    user = await get_user_data(update)
    await log_processing_info(update, "command /delete_channel")

    if user.channels == []:
        await update.message.reply_text(f"You dont have any channels")
        return
    await update.message.reply_text(
        f"Chose the channel:\n{await get_channel_string(update, context)}\n And send me number or /cancel"
    )
    user.state = State.DELETE_CHANNEL


async def add_channel(
    update: Update,
    context: CallbackContext,
    channel_type: Channel,
) -> None:
    user = await get_user_data(update)

    # Проверка ссылки
    link = check_link(update.message.text.strip())
    if not link:
        await update.message.reply_text(ERROR_CHANNEL_LINK)
        return

    try:
        # Получение информации о чате
        channel_info = await context.bot.get_chat(link)
    except Exception as e:
        await update.message.reply_text(f"{ERROR_GET_CHANNEL_INFO} {e}")
        return

    if user.chanel_already_added(channel_info.id):
        await update.message.reply_text(
            "Channel already added. If you want add chat for this channel send CHANNEL link or username. Or use /cancel"
        )
        return

    try:
        # Проверка прав бота в чате
        permission_check = await check_bot_permission(context.bot, channel_info.id)
        if permission_check != True:
            await update.message.reply_text(
                "Bot doesn't have permission in this channel"
            )
            return
    except Exception as e:
        await update.message.reply_text(f"Some error: {e}")
        return

    if channel_type.channel_id == None:
        channel_type.channel_id = channel_info.id
        channel_type.channel_permission = True
        user.channels.append(channel_type)
        await update.message.reply_text(
            f"If you want add chat for this channel send CHAT link or username. Or use /cancel"
        )
        user.state = State.ADD_CHAT

    elif channel_type.chat_id == None:
        channel_type.chat_id = channel_info.id
        channel_type.chat_permission = True
        await update.message.reply_text(f"Successfully add channel and chat!")
        user.state = State.IDLE


async def delete_channel(update: Update, context: CallbackContext):
    user = await get_user_data(update)
    input = update.message.text.strip()
    if not input.isdigit():
        await update.message.reply_text(f"Error send normal number or /cancel")
        return

    if int(input) > len(user.channels) or int(input) < 1:
        await update.message.reply_text(f"Error send normal number or /cancel")
        return

    del user.channels[int(input) - 1]
    await update.message.reply_text(f"Noice DELETING CHANNEL")
    user.state = State.IDLE
