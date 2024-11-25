from collections import defaultdict
import logging
import pytz

from telegram import (
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
    Update,
)
from telegram.ext import CallbackContext
from service_db import Post
from action_db import (
    db_get_chat_by_channel,
    db_get_messages_by_post,
    db_post_by_id,
    db_set_sended_message_id,
    db_get_post_by_sended_message_id,
)
from actions_chat import get_channel_string

MOSCOW_TZ = pytz.timezone("Europe/Moscow")

logger = logging.getLogger(__name__)
current_posts = {}

MEDIA_GROUP_TYPES = {
    "photo": InputMediaPhoto,
    "video": InputMediaVideo,
    "document": InputMediaDocument,
    "audio": InputMediaAudio,
}


async def set_post_in_scheduler(
    update: Update, context: CallbackContext, post: Post
) -> None:
    my_job_queue = context.job_queue
    job_name = f"{post.post_id}_{post.user_id}_{post.channel_id}_{post.date_time}"

    if not my_job_queue.get_jobs_by_name(job_name):
        my_job_queue.run_once(
            send_post,
            when=post.date_time,
            data=post.post_id,
            name=job_name,
        )


async def send_post(context: CallbackContext) -> None:
    post_id = context.job.data

    post = db_post_by_id(post_id)
    if post == None:
        return

    grouped_media_channel = defaultdict(list)
    channel_messages = db_get_messages_by_post(post_id, is_channel_message=True)

    for msg in channel_messages:
        if msg.file_type is not None:
            media_type = MEDIA_GROUP_TYPES[msg.file_type]
            media_item = media_type(media=msg.file_id, caption=msg.caption)
            grouped_media_channel[msg.media_group_id].append(media_item)

    sended_message: int = None

    for channel_msg in channel_messages:
        if channel_msg.file_type == None:
            sended_message = await context.bot.send_message(
                chat_id=post.channel_id.channel_id, text=channel_msg.text
            )

    for media_group in grouped_media_channel.values():
        if media_group:
            sended_message = await context.bot.send_media_group(
                chat_id=post.channel_id.channel_id,
                media=media_group,
                read_timeout=20,
                write_timeout=35,
            )

    db_set_sended_message_id(post_id, sended_message[0].message_id)


async def send_messages_at_comment(update: Update, context: CallbackContext) -> None:
    post = db_get_post_by_sended_message_id(
        channel_id=update.effective_message.forward_origin.chat.id,
        sended_message_id=update.effective_message.forward_origin.message_id,
    )
    if post == None:
        return
    chat_id = db_get_chat_by_channel(post.channel_id).chat_id
    messages = db_get_messages_by_post(post_id=post.post_id, is_channel_message=False)
    reply_to_message_id = update.effective_message.message_id

    if len(messages) == 0:
        return

    grouped_media_chat = defaultdict(list)

    for channel_msg in messages:
        if channel_msg.file_type is None:
            await context.bot.send_message(
                chat_id=chat_id,
                text=channel_msg.text,
                reply_to_message_id=reply_to_message_id,
            )

    for msg in messages:
        if msg.file_type is not None:
            media_type = MEDIA_GROUP_TYPES[msg.file_type]
            media_item = media_type(media=msg.file_id, caption=msg.caption)
            grouped_media_chat[msg.media_group_id].append(media_item)

    for media_group in grouped_media_chat.values():
        if media_group:
            await context.bot.send_media_group(
                chat_id=chat_id,
                media=media_group,
                reply_to_message_id=reply_to_message_id,
                read_timeout=20,
                write_timeout=35,
            )
