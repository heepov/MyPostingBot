# planning_send_post.py

import logging
from datetime import datetime
from telegram.ext import CallbackContext, ContextTypes, JobQueue, Updater
from telegram import (
    Update,
    InputMediaVideo,
    InputMediaPhoto,
    InputMediaDocument,
    InputMediaAudio,
)
from file_service import load_file, save_file
from user_data_manager import user_data_manager
from constants import FILE_PATH_POSTS, DATE_TIME_FORMAT, MAX_MEDIA_IN_GROUP
from itertools import groupby
from operator import itemgetter
from collections import defaultdict
import pytz

logger = logging.getLogger(__name__)

MEDIA_GROUP_TYPES = {
    "photo": InputMediaPhoto,
    "video": InputMediaVideo,
    "document": InputMediaDocument,
    "audio": InputMediaAudio,
}


def del_posts_from_file(post_id):
    posts = load_file(FILE_PATH_POSTS)
    if post_id in posts:
        del posts[post_id]
    save_file(posts, FILE_PATH_POSTS)


async def send_media_group_with_timeout(
    context, chat_id, reply_to_message_id, media_group
):
    try:
        # Отправка медиагруппы с увеличенным таймаутом
        await context.bot.send_media_group(
            chat_id=chat_id,
            media=media_group,
            reply_to_message_id=reply_to_message_id,
            read_timeout=20,
            write_timeout=35,
        )
        # Удаляем пост после успешной отправки
    except Exception as e:
        logger.error(f"Ошибка при отправке медиа группы: {e}")


async def send_chat_posts(update: Update, context: CallbackContext):
    posts = load_file(FILE_PATH_POSTS)
    reply_to_message_id = update.message.message_id
    chat_id = user_data_manager.get_chat_id()
    photo_id = update.message.photo[-1].file_id

    if photo_id not in posts:
        return

    msg_dict = posts[photo_id]["chat_posts"]
    grouped_media = defaultdict(list)

    for msg in msg_dict:
        media_type = MEDIA_GROUP_TYPES[msg["media_type"]]
        media_item = media_type(media=msg["media_id"], caption=msg["caption"])
        grouped_media[msg["media_group_id"]].append(media_item)

    for media_group_id, media_group in grouped_media.items():
        for i in range(0, len(media_group), 10):
            sub_group = media_group[i : i + 10]
            await send_media_group_with_timeout(
                context, chat_id, reply_to_message_id, sub_group
            )
    del_posts_from_file(photo_id)


# Функция для планирования задачи
async def set_post_in_scheduler(update: Update, context: CallbackContext, post) -> None:
    post_time = datetime.strptime(
        post["channel_post"].get("scheduled_time"), DATE_TIME_FORMAT
    )
    moscow_tz = pytz.timezone("Europe/Moscow")
    post_time = moscow_tz.localize(post_time)

    job_id = f"{post['channel_post'].get('message_id')}_{post['channel_post'].get('scheduled_time')}"

    my_job_queue = context.job_queue

    if not my_job_queue.get_jobs_by_name(job_id):
        my_job_queue.run_once(
            callback_forward_post,
            when=post_time,
            data={
                "chat_id": post["channel_post"].get("channel_id"),
                "text": post["channel_post"].get("text"),
                "photo_id": post["channel_post"].get("photo_id"),
                "message_id": post["channel_post"].get("message_id"),
                "user_chat_id": update.message.chat_id,
            },
            name=job_id,
        )
        logger.info(str(my_job_queue.get_jobs_by_name(job_id)))
    else:
        logger.info(f"Post with job_id={job_id} is already planned.")

async def callback_forward_post(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = context.job.data.get("chat_id")
    text = context.job.data.get("text")
    photo_id = context.job.data.get("photo_id")
    # message_id = context.job.data.get("message_id")
    # user_chat_id = context.job.data.get("user_chat_id")

    await context.bot.send_photo(chat_id=chat_id, photo=photo_id, caption=text)
