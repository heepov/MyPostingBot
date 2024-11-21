# creating_new_post.py

import logging
from datetime import datetime
from telegram.ext import CallbackContext
from telegram import Update
from typing import TypedDict, Literal
from telegram.helpers import effective_message_type

from states import State
from file_service import load_file, save_file
from planning_send_posts import set_post_in_scheduler
from user_data_manager import user_data_manager
from constants import FILE_PATH_POSTS, DATE_TIME_FORMAT

from strings import (
    ERROR_DATE_TIME_PAST,
    ERROR_DATE_TIME_FORMAT,
    SUCCESS_POST_SCHEDULED,
    ADD_POST_MEDIA_FILES,
    ERROR_ADD_POST_NEED_PHOTO,
)

logger = logging.getLogger(__name__)
scheduled_posts = load_file(FILE_PATH_POSTS)


class MsgDict(TypedDict):
    media_type: Literal["video", "photo", "document", "audio"]
    media_id: str
    caption: str
    message_id: int
    media_group_id: str


# Получение основного поста
async def adding_channel_post(update: Update, context: CallbackContext) -> None:

    if update.message.photo:
        info = await context.bot.get_chat(user_data_manager.get_channel_id())
        channel_username = info.username
        post = {
            "channel_post": {
                "channel_id": user_data_manager.get_channel_id(),
                "text": f"{update.message.caption if update.message.caption else 'error_tag'}\n\nmore in comments\n@{channel_username}",
                "photo_id": update.message.photo[-1].file_id,
                "message_id": update.message.message_id,
                "chat_id": update.message.chat_id,
                "scheduled_time": None,
            },
            "chat_posts": [],
        }
        user_data_manager.set_post(post)
        user_data_manager.set_state(State.ADDING_MEDIA)
        await update.message.reply_text(ADD_POST_MEDIA_FILES)
    else:
        await update.message.reply_text(ERROR_ADD_POST_NEED_PHOTO)


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


# Установка времени
async def set_time(update: Update, context: CallbackContext) -> None:
    post = user_data_manager.get_post()
    try:
        message = update.message.text.strip()
        post_time = datetime.strptime(message, DATE_TIME_FORMAT)

        if post_time < datetime.now():
            await update.message.reply_text(ERROR_DATE_TIME_PAST)
            return

        post["channel_post"]["scheduled_time"] = post_time.strftime(DATE_TIME_FORMAT)
        scheduled_posts[post["channel_post"].get("photo_id")] = post

        save_file(scheduled_posts, FILE_PATH_POSTS)
        await set_post_in_scheduler(update, context, post)
        await update.message.reply_text(SUCCESS_POST_SCHEDULED)
        user_data_manager.set_state(State.IDLE)

    except ValueError:
        logger.info(f"{message}  {post_time}")
        await update.message.reply_text(ERROR_DATE_TIME_FORMAT)
