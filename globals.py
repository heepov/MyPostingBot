# globals.py

import json
import logging

from file_service import load_file, save_file
from post import Post
from user_data import Channel, UserData

FILE_PATH_USER_DATA = "user_data.json"
FILE_PATH_POST_QUEUE = "post_queue.json"

MAX_MEDIA_IN_GROUP = 10
DATE_TIME_FORMAT = "%Y-%m-%d %H:%M"
DATE_TIME_FORMAT_PRINT = "YYYY-MM-DD HH:MM"


logger = logging.getLogger(__name__)


user_data_list = []
posts_queue = {}
tmp_chat = Channel()


def load_user_data_from_file() -> None:
    global user_data_list
    data = load_file("user_data.json")
    for user_id, user_data in data.items():
        try:
            user = UserData(
                user_id=user_id,
                user_name=user_data.get("user_name"),
                channels=[
                    Channel(**channel) for channel in user_data.get("channels", [])
                ],
                state=user_data.get("state"),  # Распаковка состояния
                scheduled_post=(
                    Post(**user_data["scheduled_post"])
                    if user_data.get("scheduled_post")
                    else None
                ),
            )
            user_data_list.append(user)
        except ValueError as e:
            print(f"Skipping user {user_id} due to error: {e}")

    logger.info(f"{user_data_list}")


def save_user_data_to_file(data) -> None:
    logger.info("HERE")
    logger.info(f"{data}")
    d = {user.user_id: user.to_dict() for user in data}
    logger.info(d)
    save_file(d, FILE_PATH_USER_DATA)


def load_post_queue_from_file() -> None:
    posts_queue = load_file(FILE_PATH_POST_QUEUE)


def save_post_queue_to_file() -> None:
    save_file(posts_queue, FILE_PATH_POST_QUEUE)
