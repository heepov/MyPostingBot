# new_channel_post.py

import logging
from os import getenv
from datetime import datetime
from apscheduler.triggers.date import DateTrigger
from telegram import Update
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

logger = logging.getLogger(__name__)

FILE_PATH = getenv("CHANNEL_POSTS_FILE")
DATE_TIME_FORMAT = getenv("DATE_TIME_FORMAT")
DATE_TIME_FORMAT_PRINT = getenv("DATE_FOR_PRINT")

# Словарь для хранения данных о постах
scheduled_channel_posts = load_file(FILE_PATH)
current_channel_post = {}


def add_post_to_file():
    global scheduled_channel_posts, current_channel_post
    scheduled_channel_posts[current_channel_post["message_id"]] = current_channel_post
    save_file(scheduled_channel_posts, FILE_PATH)


def del_post_from_file(message_id):
    global scheduled_channel_posts
    if message_id in scheduled_channel_posts:
        del scheduled_channel_posts[message_id]
        save_file(scheduled_channel_posts, FILE_PATH)


# Функция для обработки сообщений с изображением и текстом
async def adding_channel_post(update: Update, context: CallbackContext) -> None:
    global current_channel_post
    message = update.message
    if message.photo:
        current_channel_post = {
            "channel_id": user_data_manager.get_channel_id(),
            "text": message.caption if message.caption else "",
            "photo_id": message.photo[-1].file_id,
            "message_id": message.message_id,
            "chat_id": update.message.chat_id,
            "scheduled_time": None,
        }

        user_data_manager.set_state(State.SETTING_TIMER_FOR_CHANNEL_POST)
        await update.message.reply_text(SETTING_TIME(DATE_TIME_FORMAT_PRINT))
    else:
        await update.message.reply_text(COMMAND_ADD)


# Установка времени для публикации
async def set_time(update, context: CallbackContext) -> None:
    global current_channel_post
    try:
        datetime_str = update.message.text.strip()

        if not current_channel_post:
            await update.message.reply_text(COMMAND_ADD)
            return
        logger.info(datetime_str)
        post_time = datetime.strptime(datetime_str, DATE_TIME_FORMAT)
        logger.info(post_time)
        if post_time < datetime.now():
            await update.message.reply_text(DATE_TIME_MISTAKE_PAST)
            return

        # Обновляем только scheduled_time
        current_channel_post["scheduled_time"] = post_time.strftime(DATE_TIME_FORMAT)
        job_id = f"{current_channel_post['message_id']}_{current_channel_post['scheduled_time']}"

        scheduler = context.bot_data["scheduler"]

        if not scheduler.get_job(job_id):
            trigger = DateTrigger(run_date=post_time)
            scheduler.add_job(
                forward_post_async,
                trigger,
                args=[
                    context.bot,
                    current_channel_post["channel_id"],
                    current_channel_post["text"],
                    current_channel_post["photo_id"],
                    current_channel_post["message_id"],
                    update.message.chat_id,
                ],
                id=job_id,
            )

        add_post_to_file()
        user_data_manager.set_state(State.ADDING_CHAT_POSTS)
        user_data_manager.set_photo_id(current_channel_post["photo_id"])

        await update.message.reply_text(
            SUCCESS_CHANNEL_POST(post_time.strftime(DATE_TIME_FORMAT))
        )

    except ValueError:
        await update.message.reply_text(
            DATE_TIME_MISTAKE_FORMAT(DATE_TIME_FORMAT_PRINT)
        )
    except Exception as e:
        logger.error(ERROR(e))
        await update.message.reply_text(ERROR(e))


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
        del_post_from_file(message_id)
    except Exception as e:
        logger.error(f"Error forwarding post: {e}")


# Обертка для асинхронной функции пересылки
def forward_post_async(bot, chat_id, text, photo_id, message_id, user_chat_id):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(
        forward_post(bot, chat_id, text, photo_id, message_id, user_chat_id)
    )
