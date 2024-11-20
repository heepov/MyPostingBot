# utils.py

import logging
from os import getenv
from telegram import Bot
from user_data_manager import user_data_manager
from strings import ERROR_PERMISSION_STRING
from file_service import load_file, save_file
from datetime import datetime


def setup_logging(level=logging.INFO):
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=level,
    )


logger = logging.getLogger(__name__)
date_time_format = getenv("DATE_TIME_FORMAT")


async def check_bot_permission(bot: Bot, chat_id: int):
    """Проверка, является ли бот администратором канала или чата."""
    try:
        # Получаем список администраторов для чата
        admins = await bot.get_chat_administrators(chat_id)
        bot_id = (await bot.get_me()).id
        for admin in admins:
            if admin.user.id == bot_id:
                return True  # Бот является администратором
        return "Bot isn't an admin."  # Бот не администратор
    except Exception as e:
        logging.error(f"Ошибка при проверке прав бота в чате {chat_id}: {e}")
        return e


def check_link(link):
    if link.startswith("https://t.me/"):
        return "@" + link.split("https://t.me/")[-1]
    elif link.startswith("@"):
        return link
    else:
        return None


# Проверка прав бота в канале и чате
async def check_all_permission(update, context):
    permission = await check_bot_permission(
        context.bot, user_data_manager.get_channel_id()
    )

    if permission == True:
        permission = await check_bot_permission(
            context.bot, user_data_manager.get_chat_id()
        )

        if permission == True:
            return True
        else:
            return ERROR_PERMISSION_STRING("chat", permission)
    else:
        return ERROR_PERMISSION_STRING("channel", permission)


def files_cleaner():
    channel_posts = load_file(getenv("CHANNEL_POSTS_FILE"))
    chat_posts = load_file(getenv("CHAT_POSTS_FILE"))

    updated_channel_posts = {
        key: value
        for key, value in channel_posts.items()
        if datetime.strptime(value["scheduled_time"], getenv("DATE_TIME_FORMAT"))
        > datetime.now()
    }

    updated_chat_posts = {
        key: value
        for key, value in chat_posts.items()
        if key in [value["photo_id"] for value in updated_channel_posts.values()]
    }

    save_file(updated_channel_posts, getenv("CHANNEL_POSTS_FILE"))
    save_file(updated_chat_posts, getenv("CHAT_POSTS_FILE"))
