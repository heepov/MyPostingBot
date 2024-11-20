# creating_new_post.py

import logging
from os import getenv
from datetime import datetime
from apscheduler.triggers.date import DateTrigger
from telegram.ext import CallbackContext
import asyncio
from user_data_manager import user_data_manager
from states import State
from file_service import load_file, save_file
from strings import (
    ERROR,
    COMMAND_ADD,
    SETTING_TIME,
    DATE_TIME_MISTAKE_PAST,
    DATE_TIME_MISTAKE_FORMAT,
    SUCCESS_CHANNEL_POST,
)
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


class MsgDict(TypedDict):
    media_type: Literal["video", "photo", "document", "audio"]
    media_id: str
    caption: str
    message_id: int
    media_group_id: str


MAX_MEDIA_IN_GROUP = 10
MEDIA_GROUP_TYPES = {
    "photo": InputMediaPhoto,
    "video": InputMediaVideo,
    "document": InputMediaDocument,
    "audio": InputMediaAudio,
}

logger = logging.getLogger(__name__)


FILE_PATH = getenv("POSTS_FILE")
DATE_TIME_FORMAT = "%Y-%m-%d %H:%M"
DATE_TIME_FORMAT_PRINT = getenv("DATE_FOR_PRINT")

scheduled_posts = load_file(FILE_PATH)


def del_posts_from_file(post_id):
    logger.info(f"DELETE {post_id}")
    posts = load_file(FILE_PATH)
    if post_id in posts:
        del posts[post_id]
    save_file(posts, FILE_PATH)


# Получение основного поста
async def adding_channel_post(update: Update, context: CallbackContext) -> None:

    if update.message.photo:
        post = {
            "channel_post": {
                "channel_id": user_data_manager.get_channel_id(),
                "text": update.message.caption if update.message.caption else "",
                "photo_id": update.message.photo[-1].file_id,
                "message_id": update.message.message_id,
                "chat_id": update.message.chat_id,
                "scheduled_time": None,
            },
            "chat_posts": [],
        }
        user_data_manager.set_post(post)
        user_data_manager.set_state(State.ADDING_MEDIA)
        await update.message.reply_text("Теперь отправьте медиафайлы для комментариев.")
    else:
        await update.message.reply_text("Пожалуйста, отправьте изображение для поста.")


# Добавление медиафайлов для комментариев
async def adding_media(update: Update, context: CallbackContext) -> None:
    message = update.effective_message
    media_type = effective_message_type(message)
    post = user_data_manager.get_post()

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

    post["chat_posts"].append(msg_dict)
    user_data_manager.set_post(post)

    await update.message.reply_text(
        "Медиа добавлено. Можете отправить еще или установить время с помощью команды /time."
    )


# Установка времени
async def set_time(update: Update, context: CallbackContext) -> None:
    post = user_data_manager.get_post()
    try:
        message = update.message.text.strip()
        post_time = datetime.strptime(message, DATE_TIME_FORMAT)

        if post_time < datetime.now():
            await update.message.reply_text(DATE_TIME_MISTAKE_PAST)
            return

        post["channel_post"]["scheduled_time"] = post_time.strftime(DATE_TIME_FORMAT)
        scheduled_posts[post["channel_post"].get("photo_id")] = post

        save_file(scheduled_posts, FILE_PATH)

        await set_post_in_scheduler(update, context, post)

    except ValueError:
        logger.info(f"{message}  {post_time}")
        await update.message.reply_text(
            DATE_TIME_MISTAKE_FORMAT(DATE_TIME_FORMAT_PRINT)
        )


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
        await bot.delete_message(chat_id=user_chat_id, message_id=message_id)
        logger.info(f"Message {message_id} deleted from chat with bot.")

        # Удаляем пост из файла
        # del_post_from_file(message_id)
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
    posts = load_file(FILE_PATH)
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
