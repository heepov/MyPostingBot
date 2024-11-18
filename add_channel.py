#add_channel.py

from utils import check_if_bot_is_admin
from file_service import load_file, save_file
import os
from telegram import Update
from telegram.ext import CallbackContext

import logging
from states import State


logger = logging.getLogger(__name__)

users_channels = load_file(os.getenv('USER_CHANNELS_FILE'))

def check_link(link):
    if link.startswith("https://t.me/"):
        return "@" + link.split("https://t.me/")[-1]  # Извлекаем имя канала
    elif link.startswith("@"):
        return link
    else:
        return None

async def add_channel_link(update: Update, context: CallbackContext) -> None:
    global users_channels
    user_id = update.message.from_user.id
    user_data_manager = context.bot_data.get("user_data_manager")
    
    channel_link = check_link(update.message.text.strip())
    # Извлекаем имя канала из полного URL, если оно было передано
    if not channel_link:
        await update.message.reply_text("Неверная ссылка на канал. Пожалуйста, отправьте правильную ссылку или @имя канала.")
        return
    
    try:
        # Получаем информацию о канале
        channel = await context.bot.get_chat(channel_link)

        # Проверяем, является ли бот администратором канала
        is_admin_channel = await check_if_bot_is_admin(context.bot, channel.id)
        if not is_admin_channel:
            await update.message.reply_text(f"Бот не добавлен в канал @{channel.username} или не имеет нужных прав.")
            return

        # Если канал найден, сохраняем информацию
        users_channels = {
            'channel_username': channel.username,
            'channel_id': channel.id,
            'chat_username': None,
            'chat_id': None,
        }
        user_data_manager.set_state(user_id, State.WAITING_ADD_CHAT)
        await update.message.reply_text(f"Канал @{channel.username} добавлен успешно.\n\nТеперь пожалуйста отправьте ссылку на ваш КАНАЛ.")

    except Exception as e:
        logging.error(f"Ошибка при добавлении канала: {e}")
        await update.message.reply_text(f"Произошла ошибка при добавлении канала {channel_link}. Ошибка: {str(e)}")
    
    
async def add_chat_link(update: Update, context: CallbackContext) -> None:
    global users_channels
    user_id = update.message.from_user.id
    user_data_manager = context.bot_data.get("user_data_manager")
    
    channel_link = check_link(update.message.text.strip())

    if not channel_link:
        await update.message.reply_text("Неверная ссылка на ЧАТ. Пожалуйста, отправьте правильную ссылку или @имя канала.")
        return
    
    try:
        chat = await context.bot.get_chat(channel_link)

        is_admin_channel = await check_if_bot_is_admin(context.bot, chat.id)
        if not is_admin_channel:
            await update.message.reply_text(f"Бот не добавлен в чат @{chat.username} или не имеет нужных прав.")
           
        users_channels['chat_username'] = chat.username
        users_channels['chat_id'] = chat.id

        user_data_manager.set_users_channels(user_id, users_channels)
        save_file(users_channels, os.getenv('USER_CHANNELS_FILE'))

        user_data_manager.set_state(user_id, State.IDLE)
        await update.message.reply_text(f"Теперь у вас подключен:\nКанал @{users_channels['channel_username']}\nЧат @{users_channels['chat_username']}")
    except Exception as e:
        logging.error(f"Ошибка при добавлении канала: {e}")
        await update.message.reply_text(f"Произошла ошибка при добавлении канала {channel_link}. Ошибка: {str(e)}")