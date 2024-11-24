# utils.py

import logging
from collections import defaultdict
from datetime import datetime
from logging.handlers import RotatingFileHandler

from telegram import Bot, Update
from telegram.ext import CallbackContext

from actions_user import get_user_data
from file_service import load_file, save_file
from globals import user_data_list
from old.planning_send_posts import set_post_in_scheduler
from old.strings import ERROR_PERMISSION_STRING
from old.user_data_manager import user_data_manager


def setup_logging(level=logging.INFO):
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),  # Вывод в консоль
            #     RotatingFileHandler(
            #         "bot.log", maxBytes=5_000_000, backupCount=5, encoding="utf-8"
            #     ),  # Ротация логов
        ],
    )

    # Настроим уровень логирования для httpx
    logging.getLogger("httpx").setLevel(logging.WARNING)


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


async def log_processing_info(update, type):
    user = await get_user_data(update)
    for i in user_data_list:
        if i.user_id == user.user_id:
            i = user
    logger.info(
        f"OPERATION: {type} from user_id {update.message.from_user.id} in user_data {user.user_id}. State: {user.state}. Hasn't error: {user.user_has_channel_with_permission()}"
    )
    logger.info(f"DATA: {user.to_dict()}")
    logger.info(f"DATA: {user_data_list}")


# def files_cleaner():
#     posts = load_file(FILE_PATH_POST_QUEUE)

#     updated_posts = {
#         key: value
#         for key, value in posts.items()
#         if datetime.strptime(
#             value["channel_post"].get("scheduled_time"), DATE_TIME_FORMAT
#         )
#         > datetime.now()
#     }

#     save_file(updated_posts, FILE_PATH_POST_QUEUE)


# async def check_scheduled_post(update: Update, context: CallbackContext) -> None:
#     files_cleaner()
#     posts = load_file(FILE_PATH_POST_QUEUE)
#     for key, value in posts.items():
#         await set_post_in_scheduler(update, context, value)


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
    logger.info(str(job_names))
    if not job_names:
        return "You have not any post. Try use /check_post command."
    # job_data = [job.data for job in context.job_queue.jobs()]
    # job = context.job_queue.jobs()
    # return group_by_date(f"{job_names}")
    # return f"{context.job_queue.get_jobs_by_name("5411_2024-11-30 00:00_error_tag")[0].data}"
