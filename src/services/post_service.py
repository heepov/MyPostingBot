import logging
from datetime import datetime
from aiogram.types import Message
from src.db import db_add_or_get_model, Posts, Messages, Channels, Users
from src.bot.constants import POSTS_PER_PAGE
import pytz

logger = logging.getLogger(__name__)


async def create_post(channel_id: int, date_time: datetime | None = None) -> Posts:
    """Создает новый пост"""
    post = Posts(channel_id=channel_id, date_time=date_time)
    return db_add_or_get_model(post)


async def add_message_to_post(
    message: Message, post_id: int, is_channel_message: bool = True
) -> Messages:
    """Добавляет сообщение к посту"""

    # Определяем тип файла и его ID
    file_type = None
    file_id = None

    if message.photo:
        file_type = "photo"
        file_id = message.photo[-1].file_id
    elif message.video:
        file_type = "video"
        file_id = message.video.file_id
    elif message.document:
        file_type = "document"
        file_id = message.document.file_id

    msg = Messages(
        post_id=post_id,
        is_channel_message=is_channel_message,
        text=message.text,
        caption=message.caption,
        file_type=file_type,
        file_id=file_id,
        media_group_id=message.media_group_id,
    )

    return db_add_or_get_model(msg)


async def update_post_datetime(post_id: int, date_time: datetime) -> Posts:
    """Обновляет время публикации поста"""
    post = Posts.get(Posts.post_id == post_id)
    post.date_time = date_time
    post.save()
    return post


async def get_channel(channel_id: int) -> Channels:
    try:
        return Channels.get(Channels.channel_id == channel_id)
    except Channels.DoesNotExist:
        logger.error(f"Channel {channel_id} not found")
        return None


async def delete_post(post_id: int) -> None:
    """Удаляет пост по ID"""
    try:
        post = Posts.get(Posts.post_id == post_id)
        post.delete_instance(
            recursive=True
        )  # recursive=True удалит также все связанные сообщения
    except Posts.DoesNotExist:
        pass


async def get_channel_posts(
    channel_id: int, offset: int = 0
) -> tuple[list[Posts], int]:
    """Получает посты канала с пагинацией"""
    try:
        channel = await get_channel(channel_id)
        user = await get_user(channel.user_id)
        timezone = pytz.timezone(user.time_zone or "UTC")
        current_time = datetime.now(timezone)

        # Получаем только будущие посты
        query = (
            Posts.select()
            .where((Posts.channel_id == channel_id) & (Posts.date_time > current_time))
            .order_by(Posts.date_time.asc())  # Сортировка по возрастанию даты
            .offset(offset)
            .limit(POSTS_PER_PAGE)
        )

        posts = list(query)

        # Считаем общее количество будущих постов
        total = (
            Posts.select()
            .where((Posts.channel_id == channel_id) & (Posts.date_time > current_time))
            .count()
        )

        return posts, total
    except Exception as e:
        logger.error(f"Error getting channel posts: {e}")
        return [], 0


async def get_post_preview(post_id: int) -> tuple[str, int]:
    """Получает превью поста и количество сообщений в чате"""
    try:
        # Получаем первое сообщение поста
        first_message = Messages.get_or_none(
            (Messages.post_id == post_id) & (Messages.is_channel_message == True)
        )
        preview = (
            first_message.text or first_message.caption
            if first_message
            else "Нет текста"
        )
        preview = preview[:20] if len(preview) > 20 else preview

        # Считаем количество сообщений для чата
        chat_count = (
            Messages.select()
            .where(
                (Messages.post_id == post_id) & (Messages.is_channel_message == False)
            )
            .count()
        )

        return preview, chat_count
    except Exception as e:
        logger.error(f"Error getting post preview: {e}")
        return "Ошибка превью", 0


async def get_post(post_id: int) -> Posts:
    """Получает пост по ID"""
    try:
        return Posts.get(Posts.post_id == post_id)
    except Posts.DoesNotExist:
        return None


async def get_post_messages(
    post_id: int, is_channel_message: bool = True
) -> list[Messages]:
    """Получает сообщения поста для канала"""
    try:
        messages = list(
            Messages.select()
            .where(
                (Messages.post_id == post_id)
                & (Messages.is_channel_message == is_channel_message)
            )
            .order_by(Messages.message_id)
        )
        return messages
    except Exception as e:
        logger.error(f"Error getting post messages: {e}")
        return []


async def get_user(user_id: int) -> Users:
    """Получает пользователя по ID"""
    try:
        return Users.get(Users.user_id == user_id)
    except Users.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return None
