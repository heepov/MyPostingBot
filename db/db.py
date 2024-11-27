import logging
from peewee import *

from db.models import Channel, Chat, Message, Post, User, db

logger = logging.getLogger(__name__)


def connect_db() -> None:
    if db.is_closed():
        db.connect()


def close_db() -> None:
    if not db.is_closed():
        db.close()


def delete_db() -> None:
    if not db.is_closed():
        db.drop_tables([User, Channel, Chat, Post, Message])


def create_tables() -> None:
    db.create_tables([User, Channel, Chat, Post, Message])


def db_add_user(user: User) -> None:
    User.get_or_create(
        user_id=user.user_id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
        language_code=user.language_code,
    )
    print(f"New User Added")


def db_add_channel(channel: Channel) -> None:
    Channel.get_or_create(
        channel_id=channel.channel_id,
        username=channel.username,
        permission=channel.permission,
        user_id=channel.user_id,
    )
    print(f"New Channel Added")


def db_add_chat(chat: Chat) -> None:
    Chat.get_or_create(
        chat_id=chat.chat_id,
        username=chat.username,
        permission=chat.permission,
        channel_id=chat.channel_id,
    )
    print(f"New Chat Added")


def db_add_post(post: Post) -> Post:
    post_db = Post.get_or_create(
        user_id=post.user_id,
        channel_id=post.channel_id,
        date_time=post.date_time,
        sended_message_id=post.sended_message_id,
    )
    print(f"New Post Added")
    return post_db


def db_add_message(message: Message) -> Message:
    message_db = Message.get_or_create(
        post_id=message.post_id,
        is_channel_message=message.is_channel_message,
        text=message.text,
        caption=message.caption,
        file_type=message.file_type,
        file_type=message.file_type,
        media_group_id=message.media_group_id,
    )
    print(f"New Message Added")
    return message_db
