# setup.py

from utils import check_bot_permission, check_link
from telegram import Update
from telegram.ext import CallbackContext
import logging

from user_data_manager import user_data_manager
from states import State
from strings import (
    ERROR_PERMISSION_STRING,
    CHAT_SETUP_STRING,
    ERROR_CHANNEL_LINK,
    ERROR_GET_CHANNEL_INFO,
    CHANNEL_SETUP_STRING,
)


logger = logging.getLogger(__name__)


async def process_setup(
    update: Update,
    context: CallbackContext,
    is_channel: bool,
) -> None:
    user_id = update.message.from_user.id
    channel_type = "channel" if is_channel else "chat"

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

    try:
        # Проверка прав бота в чате
        permission_check = await check_bot_permission(context.bot, channel_info.id)
        if permission_check != True:
            await update.message.reply_text(
                ERROR_PERMISSION_STRING(channel_type, permission_check)
            )
            user_data_manager.set_state(State.ERROR_PERMISSION)
            return
    except Exception as e:
        logger.error(f"Ошибка при обработке {channel_type}: {e}")
        await update.message.reply_text(ERROR_PERMISSION_STRING)
        return

    if is_channel:
        user_data_manager.set_channel_id(channel_info.id)
        await update.message.reply_text(
            f"{CHAT_SETUP_STRING(channel_type, channel_info.username)}\n{CHANNEL_SETUP_STRING}"
        )
    else:
        user_data_manager.set_chat_id(channel_info.id)
        await update.message.reply_text(
            CHAT_SETUP_STRING(channel_type, channel_info.username)
        )

    user_data_manager.set_state(State.IDLE if not is_channel else State.ADDING_CHAT)
    user_data_manager.save_data()
