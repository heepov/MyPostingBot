from peewee import DoesNotExist
import logging

from service_db import Channel, Chat, Message, Post, State, User, db


logger = logging.getLogger(__name__)


# Функция для получения состояния пользователя
def get_user_state(user_id: int) -> str:
    try:
        user = User.get(User.user_id == user_id)
        return user.state
    except DoesNotExist:
        return None


def get_selected_channel(user_id: int) -> str:
    try:
        channel = Channel.get(
            Channel.user_id == user_id and Channel.last_selected == True
        )
        return channel.channel_id
    except DoesNotExist:
        return None
    


# Выполняем обновление состояния пользователя
def set_user_state(user_id: int, new_state: str) -> bool:
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


def set_channel_selected(channel_id, user_id) -> bool:
    try:
        rows_updated = (
            Channel.update(last_selected=False)
            .where(Channel.user_id == user_id)
            .execute()
        )
        rows_updated = (
            Channel.update(last_selected=True)
            .where(Channel.channel_id == channel_id)
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


def is_channel_exists_for_user(user_id: int, channel_id: int):
    try:
        # Получаем канал для конкретного пользователя
        channel = (
            Channel.select()
            .where((Channel.user_id == user_id) & (Channel.channel_id == channel_id))
            .first()
        )

        # Если канал найден, возвращаем True, иначе False
        return channel is not None
    except Channel.DoesNotExist:
        return False


def get_all_user_channels(user_id: int):
    return Channel.select().where(Channel.user_id == user_id)


def get_channel_chat(channel_id: int):
    return Chat.select().where(Chat.channel_id == channel_id).first()


def del_channel(channel_id: int):
    channel = Channel.select().where(Channel.channel_id == channel_id).first()
    if channel:
        channel.delete_instance()

def del_chat(chat_id: int):
    channel = Chat.select().where(Chat.chat_id == chat_id).first()
    if channel:
        channel.delete_instance()


def create_user(data):
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


def create_channel(data, channel_id=None):
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
