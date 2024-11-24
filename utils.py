# utils.py

import logging
from telegram import Bot
from telegram import Update
from telegram.ext import CallbackContext
from datetime import datetime
from collections import defaultdict
from logging.handlers import RotatingFileHandler

from user_data_manager import user_data_manager
from strings import ERROR_PERMISSION_STRING
from file_service import load_file, save_file
from planning_send_posts import set_post_in_scheduler
from constants import DATE_TIME_FORMAT, FILE_PATH_POSTS


def setup_logging(level=logging.INFO):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("bot.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    handler = RotatingFileHandler("bot.log", maxBytes=5_000_000, backupCount=5)


logger = logging.getLogger(__name__)


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
    posts = load_file(FILE_PATH_POSTS)

    updated_posts = {
        key: value
        for key, value in posts.items()
        if datetime.strptime(
            value["channel_post"].get("scheduled_time"), DATE_TIME_FORMAT
        )
        > datetime.now()
    }

    save_file(updated_posts, FILE_PATH_POSTS)


async def check_scheduled_post(update: Update, context: CallbackContext) -> None:
    files_cleaner()
    posts = load_file(FILE_PATH_POSTS)
    for key, value in posts.items():
        await set_post_in_scheduler(update, context, value)


def group_by_date(posts):
    grouped = defaultdict(list)

    for post in posts:
        _, date_time, name = post.split("_", 2)
        date = date_time.split(" ")[0]
        grouped[date].append("#" + name)

    result = []
    for date, names in grouped.items():
        result.append(f"{date} |{len(names)}| {' | '.join(names)}")

    return "\n".join(result)


def count_scheduled_post(context: CallbackContext):
    job_names = [job.name for job in context.job_queue.jobs()]
    if not job_names:
        return "You have not any post. Try use /check_post command."
    return group_by_date(job_names)
