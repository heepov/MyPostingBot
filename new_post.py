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


from post import Post
from message import Message

import json


# await update.message.reply_text(json.dumps(scheduled_post.to_dict(), indent=4))
async def add_message(
    update: Update, context: CallbackContext, scheduled_post, channel_type
) -> None:

    if effective_message_type(message) == "text":
        message = Message(
            text=message.text,
            date_time=message.date,
            message_id=message.message_id,
            user_id=message.from_user.id,
        )

    scheduled_post.add_message(message, channel_type)


# async def set_post_time(
#     update: Update,
#     context: CallbackContext,
#     scheduled_post) -> None:

#      post = user_data_manager.get_post()
#     try:
#         message = update.message.text.strip()
#         post_time = datetime.strptime(message, DATE_TIME_FORMAT)

#         if post_time < datetime.now():
#             await update.message.reply_text(ERROR_DATE_TIME_PAST)
#             return

#         post["channel_post"]["scheduled_time"] = post_time.strftime(DATE_TIME_FORMAT)

#     scheduled_post.set_date_time()
