from peewee import DoesNotExist

import logging

from service_db import Channel, Chat, Message, Post, State, User, db


logger = logging.getLogger(__name__)


def db_get_user_state(user_id: int) -> str:
    try:
        user = User.get(User.user_id == user_id)
        return user.state
    except DoesNotExist:
        return None


def db_set_user_state(user_id: int, new_state: str) -> bool:
    try:
        rows_updated = (
            User.update(state=new_state).where(User.user_id == user_id).execute()
        )
        if rows_updated > 0:
            logger.info("запись была обновлена")
            return True
        else:
            logger.info("не было обновлено ни одной записи")
            return False
    except Exception as e:
        logger.info(f"Error updating user state: {e}")
        return False


def db_get_selected_channel(user_id: int) -> str:
    try:
        channel = Channel.get(
            Channel.user_id == user_id and Channel.last_selected == True
        )
        return channel
    except DoesNotExist:
        return None


def db_set_selected_channel(post_id, sended_message_id) -> bool:
    try:
        rows_updated = (
            Post.update(sended_message_id=sended_message_id)
            .where(Post.post_id == post_id)
            .execute()
        )
        if rows_updated > 0:
            logger.info("запись была обновлена")
            return True
        else:
            logger.info("не было обновлено ни одной записи")
            return False
    except Exception as e:
        logger.info(f"Error updating user state: {e}")
        return False


def db_reset_selected_channel(user_id: int) -> bool:
    try:
        rows_updated = (
            Channel.update(last_selected=False)
            .where(Channel.user_id == user_id)
            .execute()
        )
        if rows_updated > 0:
            logger.info("запись была обновлена")
            return True
        else:
            logger.info("не было обновлено ни одной записи")
            return False
    except Exception as e:
        logger.info(f"Error updating user state: {e}")
        return False


def db_get_selected_channel(user_id: int) -> str:
    try:
        channel = Channel.get(
            Channel.user_id == user_id and Channel.last_selected == True
        )
        return channel
    except DoesNotExist:
        return None


def db_get_channel(user_id: int, channel_id: int):
    try:
        channel = Channel.get(
            Channel.channel_id == channel_id and Channel.user_id == user_id
        )
        return channel
    except DoesNotExist:
        return None


def db_get_chat_by_channel(channel_id: int):
    try:
        return Chat.get(Chat.channel_id == channel_id)
    except DoesNotExist:
        return None


def db_get_all_user_channels(user_id: int):
    return Channel.select().where(Channel.user_id == user_id)


def db_delete_channel(channel_id: int):
    channel = Channel.select().where(Channel.channel_id == channel_id).first()
    if channel:
        channel.delete_instance()


def db_delete_chat(chat_id: int):
    channel = Chat.select().where(Chat.chat_id == chat_id).first()
    if channel:
        channel.delete_instance()


def db_get_messages_by_post(post_id: int, is_channel_message=True):
    return Message.select().where(
        (Message.post_id == post_id)
        & (Message.is_channel_message == is_channel_message)
    )


def db_post_by_id(post_id: int):
    try:
        return Post.get(Post.post_id == post_id)
    except DoesNotExist:
        return None


def db_get_post_by_sended_message_id(channel_id: int, sended_message_id: int):
    try:
        return Post.get(
            (Post.sended_message_id == sended_message_id)
            & (Post.channel_id == channel_id)
        )
    except DoesNotExist:
        return None


def db_set_sended_message_id(post_id, sended_message_id) -> bool:
    try:
        rows_updated = (
            Post.update(sended_message_id=sended_message_id)
            .where(Post.post_id == post_id)
            .execute()
        )
        if rows_updated > 0:
            logger.info("запись была обновлена")
            return True
        else:
            logger.info("не было обновлено ни одной записи")
            return False
    except Exception as e:
        logger.info(f"Error updating user state: {e}")
        return False


def db_create_user(data):
    # Проверка, существует ли уже пользователь в базе
    User.get_or_create(
        user_id=data.id,
        defaults={
            "first_name": data.first_name,
            "last_name": data.last_name,
            "username": data.username,
            "language_code": data.language_code,
        },
    )


def db_create_post(post: Post, messages: list = None) -> Post:
    try:
        post_db = Post.create(
            user_id=post.user_id, channel_id=post.channel_id, date_time=post.date_time
        )
        if messages != None:
            for message in messages:
                message.post_id = post_db.post_id
                logger.info(f"Message: {str(message)}")
                db_create_message(message)
    except Exception as e:
        logger.error(f"Error creating post: {e}")
        return None
    return post_db


def db_create_message(data):
    Message.create(
        post_id=data.post_id,
        is_channel_message=data.is_channel_message,
        text=data.text,
        caption=data.caption,
        file_type=data.file_type,
        file_id=data.file_id,
        media_group_id=data.media_group_id,
    )


def db_create_channel_or_chat(data, channel_id=None):
    if channel_id == None:
        Channel.get_or_create(
            channel_id=data["channel_id"],
            username=data["username"],
            permission=data["permission"],
            user_id=data["user_id"],
        )
    else:
        Chat.get_or_create(
            chat_id=data["channel_id"],
            username=data["username"],
            permission=data["permission"],
            channel_id=channel_id,
        )
