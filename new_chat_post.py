# new_chat_post.py

from os import getenv
import logging
import asyncio
import logging
from typing import TypedDict, Literal
from telegram.ext import ContextTypes
from telegram.helpers import effective_message_type
from telegram import (
    Update,
    InputMediaVideo,
    InputMediaPhoto,
    InputMediaDocument,
    InputMediaAudio,
)

from user_data_manager import user_data_manager
from file_service import load_file, save_file
from states import State

FILE_PATH = getenv("CHAT_POSTS_FILE")
MAX_MEDIA_IN_GROUP = 10
MEDIA_GROUP_TYPES = {
    "photo": InputMediaPhoto,
    "video": InputMediaVideo,
    "document": InputMediaDocument,
    "audio": InputMediaAudio,
}

logger = logging.getLogger(__name__)
scheduled_chat_posts = load_file(FILE_PATH)


def add_posts_to_file(photo_id, msg_dict):
    global scheduled_chat_posts
    if photo_id in scheduled_chat_posts:
        if isinstance(
            scheduled_chat_posts[photo_id], list
        ):  # Убедимся, что значение ключа — это список
            scheduled_chat_posts[photo_id].append(msg_dict)
        else:
            logger.error(
                f"ValueError Значение для ключа {photo_id} не является списком."
            )
    else:
        # Если ключа нет, создаём его с новым списком
        scheduled_chat_posts[photo_id] = [msg_dict]
    save_file(scheduled_chat_posts, FILE_PATH)


def del_posts_from_file(key_to_remove):
    global scheduled_chat_posts
    if key_to_remove in scheduled_chat_posts:
        del scheduled_chat_posts[key_to_remove]
    save_file(scheduled_chat_posts, FILE_PATH)


class MsgDict(TypedDict):
    media_type: Literal["video", "photo", "document", "audio"]
    media_id: str
    caption: str
    message_id: int
    media_group_id: str


async def media_group_sender(
    context: ContextTypes.DEFAULT_TYPE, chat_id, reply_to_message_id
):
    media = []
    for msg in context.job.data[0]:
        media_type = MEDIA_GROUP_TYPES[msg["media_type"]]
        media_item = media_type(media=msg["media_id"], caption=msg["caption"])
        media.append(media_item)

    if media:
        try:
            # Разбиваем медиафайлы на части по 10 элементов
            for i in range(0, len(media), MAX_MEDIA_IN_GROUP):
                media_chunk = media[i : i + MAX_MEDIA_IN_GROUP]
                await asyncio.sleep(1)
                await context.bot.send_media_group(
                    chat_id=chat_id,
                    media=media_chunk,
                    reply_to_message_id=reply_to_message_id,
                )
        except Exception as e:
            logger.error(f"Ошибка: {e}")
        finally:
            await asyncio.sleep(1)


async def send_chat_posts(update: Update, context: ContextTypes.DEFAULT_TYPE, file_id):
    reply_to_message_id = update.message.message_id
    chat_id = user_data_manager.get_chat_id()
    photo_id = user_data_manager.get_photo_id()

    if not photo_id in scheduled_chat_posts:
        return

    msg_dict = scheduled_chat_posts[photo_id]
    del_posts_from_file(photo_id)
    media_group_id = msg_dict[0]["media_group_id"]

    jobs = context.job_queue.get_jobs_by_name(media_group_id)

    if jobs:
        jobs[0].data.append(msg_dict)
    else:
        context.job_queue.run_once(
            callback=lambda job_context: media_group_sender(
                job_context, chat_id=chat_id, reply_to_message_id=reply_to_message_id
            ),
            when=2,
            data=[msg_dict],
            name=media_group_id,
        )


async def schedule_chat_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    media_type = effective_message_type(message)

    photo_id = user_data_manager.get_photo_id()

    media_id = (
        message.photo[-1].file_id
        if message.photo
        else message.effective_attachment.file_id
    )

    msg_dict = MsgDict(
        media_type=media_type,
        media_id=media_id,
        caption=message.caption_html or "",
        message_id=message.message_id,
        media_group_id=message.media_group_id,
    )

    add_posts_to_file(photo_id, msg_dict)
