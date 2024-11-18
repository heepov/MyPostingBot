# new_chat_post.py

import os
import logging
from states import State
import asyncio
import logging
from typing import TypedDict, Literal
from file_service import load_file, save_file

from telegram import (
    Update,
    InputMediaVideo,
    InputMediaPhoto,
    InputMediaDocument,
    InputMediaAudio,
)
from telegram.ext import ContextTypes

from telegram.helpers import effective_message_type

logger = logging.getLogger(__name__)

scheduled_chat_posts = load_file(os.getenv('CHAT_POSTS_FILE'))


# Константы
MEDIA_GROUP_TYPES = {
    "photo": InputMediaPhoto,
    "video": InputMediaVideo,
    "document": InputMediaDocument,
    "audio": InputMediaAudio,
}
MAX_MEDIA_IN_GROUP = 10


def append_post_by_photo_id(photo_id, msg_dict, file_name):
    global scheduled_chat_posts
    if photo_id in scheduled_chat_posts:
        if isinstance(scheduled_chat_posts[photo_id], list):  # Убедимся, что значение ключа — это список
            scheduled_chat_posts[photo_id].append(msg_dict)
        else:
            logger.error(f"ValueError Значение для ключа {photo_id} не является списком.")
    else:
        # Если ключа нет, создаём его с новым списком
        scheduled_chat_posts[photo_id] = [msg_dict]
    save_file(scheduled_chat_posts, file_name)


class MsgDict(TypedDict):
    media_type: Literal["video", "photo", "document", "audio"]
    media_id: str
    caption: str
    message_id: int
    media_group_id: str

async def media_group_sender(context: ContextTypes.DEFAULT_TYPE, chat_id, reply_to_message_id):
    """Отправляет медиагруппу после ожидания"""    
    media = []
    for msg in context.job.data[0]:
        media_type = MEDIA_GROUP_TYPES[msg["media_type"]]
        media_item = media_type(media=msg["media_id"], caption=msg["caption"])
        media.append(media_item)
        
    if media:
        try:
            # Разбиваем медиафайлы на части по 10 элементов
            for i in range(0, len(media), MAX_MEDIA_IN_GROUP):
                media_chunk = media[i:i + MAX_MEDIA_IN_GROUP]
                await asyncio.sleep(1)
                await context.bot.send_media_group(chat_id=chat_id, media=media_chunk, reply_to_message_id=reply_to_message_id)
        except Exception as e:
            logger.error(f"Ошибка: {e}")
        finally:
            await asyncio.sleep(1)
            

async def media_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает новые сообщения и отправляет их в медиагруппу или одиночные"""
    message = update.effective_message
    media_type = effective_message_type(message)
    
    user_id = update.message.from_user.id
    user_data_manager = context.bot_data.get("user_data_manager")
    chat_id = user_data_manager.get_users_channels(user_id)['chat_id']
    photo_id = user_data_manager.get_current_channel_post(user_id)['photo_id']
    
    media_id = (
        message.photo[-1].file_id
        if message.photo
        else message.effective_attachment.file_id
    )
    msg_dict = MsgDict(media_type=media_type, media_id=media_id, caption=message.caption_html or "", message_id=message.message_id, media_group_id=message.media_group_id)
    append_post_by_photo_id(photo_id, msg_dict, os.getenv('CHAT_POSTS_FILE'))
    await update.message.reply_text("Дождитесь пока загрузятся все файлы и после этого введите команду /end")
    
async def send_chat_posts(update: Update, context: ContextTypes.DEFAULT_TYPE, photo_id):
    reply_to_message_id = update.message.message_id
    chat_id = load_file(os.getenv('USER_CHANNELS_FILE'))['chat_id']
    
    msg_dict = load_file(os.getenv('CHAT_POSTS_FILE'))[photo_id]
    media_group_id = msg_dict[0]['media_group_id']
        
    jobs = context.job_queue.get_jobs_by_name(media_group_id)
        
    if jobs:
        jobs[0].data.append(msg_dict)
    else:    
        context.job_queue.run_once(
            callback=lambda job_context: media_group_sender(job_context, chat_id=chat_id, reply_to_message_id=reply_to_message_id),
            when=2,
            data=[msg_dict],
            name=media_group_id,
        )
