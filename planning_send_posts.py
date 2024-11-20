# planning_send_posts.py

import asyncio
import logging
from apscheduler.triggers.date import DateTrigger
from datetime import datetime
from telegram.ext import ContextTypes
from telegram.ext import CallbackContext
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


async def set_post_in_scheduler(update: Update, context: CallbackContext, post) -> None:
    post_time = datetime.strptime(
        post["channel_post"].get("scheduled_time"), DATE_TIME_FORMAT
    )
    # Планирование задачи
    job_id = f"{post['channel_post'].get('message_id')}_{post['channel_post'].get('scheduled_time')}"

    scheduler = context.bot_data["scheduler"]

    if not scheduler.get_job(job_id):
        trigger = DateTrigger(run_date=post_time)
        scheduler.add_job(
            forward_post_async,
            trigger,
            args=[
                context.bot,
                post["channel_post"].get("channel_id"),
                post["channel_post"].get("text"),
                post["channel_post"].get("photo_id"),
                post["channel_post"].get("message_id"),
                update.message.chat_id,
            ],
            id=job_id,
        )
    else:
        logger.info("Post already planning")


# Пересылка сообщения и удаление сообщения из чата с ботом
async def forward_post(bot, chat_id, text, photo_id, message_id, user_chat_id):
    try:
        # Пересылаем сообщение в канал или чат
        await bot.send_photo(chat_id=chat_id, photo=photo_id, caption=text)
        logger.info(f"Post forwarded to chat_id={chat_id}")

        # Удаляем сообщение из чата с ботом после пересылки
        # await bot.delete_message(chat_id=user_chat_id, message_id=message_id)
        # logger.info(f"Message {message_id} deleted from chat with bot.")

    except Exception as e:
        logger.error(f"Error forwarding post: {e}")


# Обертка для асинхронной функции пересылки
def forward_post_async(bot, chat_id, text, photo_id, message_id, user_chat_id):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(
        forward_post(bot, chat_id, text, photo_id, message_id, user_chat_id)
    )


async def media_group_sender(
    context: ContextTypes.DEFAULT_TYPE, chat_id, reply_to_message_id, post_id
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
            del_posts_from_file(post_id)
        except Exception as e:
            logger.error(f"Ошибка: {e}")
        finally:
            await asyncio.sleep(1)


async def send_chat_posts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    posts = load_file(FILE_PATH_POSTS)
    reply_to_message_id = update.message.message_id
    chat_id = user_data_manager.get_chat_id()
    photo_id = update.message.photo[-1].file_id

    if not photo_id in posts:
        return
    else:
        msg_dict = posts[photo_id]["chat_posts"]

    media_group_id = msg_dict[0]["media_group_id"]

    jobs = context.job_queue.get_jobs_by_name(media_group_id)

    if jobs:
        jobs[0].data.append(msg_dict)
    else:
        context.job_queue.run_once(
            callback=lambda job_context: media_group_sender(
                job_context,
                chat_id=chat_id,
                reply_to_message_id=reply_to_message_id,
                post_id=photo_id,
            ),
            when=2,
            data=[msg_dict],
            name=media_group_id,
        )
