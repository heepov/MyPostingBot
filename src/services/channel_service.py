import logging
from typing import Tuple

from aiogram import Bot
from aiogram.types import Chat

from src.db import db_add_or_get_model
from src.db.models import Channels
from src.bot.strings.messages import (
    CHAT_ADDED,
    CHAT_ALREADY_ADDED,
    NO_LINKED_CHAT,
    BOT_NEEDS_CHAT_RIGHTS,
)

logger = logging.getLogger(__name__)


def extract_username_from_link(link: str) -> str | None:

    if link.startswith("https://t.me/"):
        return "@" + link.split("https://t.me/")[-1].strip("/")
    elif link.startswith("@"):
        return link.strip()
    else:
        return None


async def check_channel_permissions(bot: Bot, chat_id: int) -> Tuple[bool, bool]:
    """
    Универсальная проверка прав бота для чатов и каналов.
    Returns: (is_admin, can_post/send_messages)
    """
    try:
        chat = await bot.get_chat(chat_id)
        bot_member = await bot.get_chat_member(chat_id, bot.id)

        is_admin = bot_member.status in ["administrator", "creator"]

        if chat.type == "channel":
            can_post = getattr(bot_member, "can_post_messages", False)
            return is_admin, can_post
        else:  # group or supergroup
            can_send_messages = getattr(bot_member, "can_manage_chat", False)
            return is_admin, can_send_messages
    except Exception as e:
        logger.error(f"Error checking permissions: {e}")
        return False, False


async def get_linked_chat(bot: Bot, channel: Chat) -> Chat | None:
    """Получает связанный с каналом чат"""
    try:
        if channel.linked_chat_id:
            return await bot.get_chat(channel.linked_chat_id)
    except Exception as e:
        logger.error(f"Error getting linked chat: {e}")
    return None


async def get_user_channels(user_id: int) -> list[Channels]:
    """Получает список каналов пользователя"""
    return list(Channels.select().where(Channels.user_id == user_id))


async def add_channel(
    user_id: int,
    channel: Chat,
    chat: Chat | None = None,
    channel_permission: bool = False,
    chat_permission: bool = False,
) -> Channels:
    """Добавляет канал в базу данных"""
    channel_model = Channels(
        channel_id=channel.id,
        channel_username=channel.username,
        channel_title=channel.title,
        channel_permission=channel_permission,
        chat_id=chat.id if chat else None,
        chat_username=chat.username if chat else None,
        chat_title=chat.title if chat else None,
        chat_permission=chat_permission if chat else None,
        user_id=user_id,
    )
    return db_add_or_get_model(channel_model)


async def delete_channel(channel_id: int) -> None:
    """Удаляет канал из БД"""
    channel = Channels.get(Channels.channel_id == channel_id)
    channel.delete_instance()


async def update_channel_info(bot: Bot, channel_id: int) -> Channels:
    """Обновляет информацию о канале и чате"""
    channel = Channels.get(Channels.channel_id == channel_id)

    # Обновляем информацию о канале
    chat = await bot.get_chat(channel_id)
    channel.channel_username = chat.username
    channel.channel_title = chat.title

    # Если есть чат, обновляем его информацию
    if channel.chat_id:
        chat = await bot.get_chat(channel.chat_id)
        channel.chat_username = chat.username
        channel.chat_title = chat.title

    channel.save()
    return channel


async def add_chat_to_channel(bot: Bot, channel_id: int) -> tuple[bool, str]:
    """Добавляет чат к каналу"""
    channel = Channels.get(Channels.channel_id == channel_id)

    if channel.chat_id:
        return False, CHAT_ALREADY_ADDED

    chat = await get_linked_chat(bot, await bot.get_chat(channel_id))
    if not chat:
        return False, NO_LINKED_CHAT

    chat_admin, chat_post = await check_channel_permissions(bot, chat.id)
    if not chat_admin or not chat_post:
        return False, BOT_NEEDS_CHAT_RIGHTS

    channel.chat_id = chat.id
    channel.chat_username = chat.username
    channel.chat_title = chat.title
    channel.chat_permission = True
    channel.save()

    return True, CHAT_ADDED


async def get_channel(channel_id: int) -> Channels:
    """Получает канал по ID"""
    try:
        return Channels.get(Channels.channel_id == channel_id)
    except Channels.DoesNotExist:
        return None


async def update_channel_permission(channel_id: int, permission: bool) -> None:
    """Обновляет права бота в канале"""
    channel = Channels.get(Channels.channel_id == channel_id)
    channel.channel_permission = permission
    channel.save()
 

async def update_chat_permission(chat_id: int, permission: bool) -> None:
    """Обновляет права бота в чате"""
    channel = Channels.get(Channels.chat_id == chat_id)
    channel.chat_permission = permission
    channel.save()
