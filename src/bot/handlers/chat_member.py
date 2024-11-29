from aiogram import Router, Bot, F
from aiogram.types import ChatMemberUpdated
from src.services.channel_service import (
    update_channel_permission,
    update_chat_permission,
)
from src.db.models import Channels

import logging

router = Router()
logger = logging.getLogger(__name__)


@router.my_chat_member()
async def on_chat_member_update(event: ChatMemberUpdated, bot: Bot):
    """Обработчик изменения прав бота в чате/канале"""
    chat_id = event.chat.id
    new_member = event.new_chat_member

    # Проверяем, что обновление касается нашего бота
    if new_member.user.id != bot.id:
        return

    chat = await bot.get_chat(chat_id)
    has_permission = False

    if new_member.status == "administrator":
        if chat.type == "channel":
            # Для каналов проверяем can_post_messages
            has_permission = getattr(new_member, "can_post_messages", False)
        else:
            # Для групп проверяем can_send_messages или can_manage_chat
            has_permission = getattr(new_member, "can_manage_chat", False)

    try:
        # Проверяем, является ли чат каналом или связанной группой
        channel = Channels.get_or_none(Channels.channel_id == chat_id)
        if channel:
            logger.info(f"Channel {chat_id} permissions changed to {has_permission}")
            await update_channel_permission(chat_id, has_permission)
            return

        channel = Channels.get_or_none(Channels.chat_id == chat_id)
        if channel:
            logger.info(f"Chat {chat_id} permissions changed to {has_permission}")
            await update_chat_permission(chat_id, has_permission)

    except Exception as e:
        logger.error(f"Error updating permissions: {e}")
