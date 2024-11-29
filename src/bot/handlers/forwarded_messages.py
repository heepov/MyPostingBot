from aiogram import Router, Bot, F
from aiogram.types import Message, InputMediaPhoto, InputMediaVideo, InputMediaDocument
from src.db.models import Channels, Posts, Messages
from src.services.post_service import get_post_messages
import logging
from itertools import groupby
from operator import attrgetter

router = Router()
logger = logging.getLogger(__name__)


async def send_media_group(
    bot: Bot,
    chat_id: int,
    messages: list[Messages],
    reply_to_message_id: int,
    chat_caption: str = None,
):
    """Отправка медиа-группы"""
    media = []
    for i, msg in enumerate(messages):
        caption = msg.caption if msg.caption else ""
        if (
            chat_caption and i == len(messages) - 1
        ):  # Добавляем подпись только к последнему элементу группы
            caption = f"{caption}\n\n{chat_caption}" if caption else chat_caption

        if msg.file_type == "photo":
            media.append(InputMediaPhoto(media=msg.file_id, caption=caption))
        elif msg.file_type == "video":
            media.append(InputMediaVideo(media=msg.file_id, caption=caption))
        elif msg.file_type == "document":
            media.append(InputMediaDocument(media=msg.file_id, caption=caption))

    try:
        await bot.send_media_group(
            chat_id=chat_id,
            media=media,
            reply_to_message_id=reply_to_message_id,
            request_timeout=35.0,
        )
    except Exception as e:
        logger.error(f"Error sending media group: {e}")


@router.message(F.forward_from_chat)
async def handle_forwarded_post(message: Message, bot: Bot):
    """Обработчик для пересланных постов в связанный чат"""
    if message.forward_from_chat.type != "channel":
        return

    channel_id = message.forward_from_chat.id
    chat_id = message.chat.id
    message_id = message.forward_from_message_id

    try:
        channel = Channels.get_or_none(
            (Channels.channel_id == channel_id) & (Channels.chat_id == chat_id)
        )
        if not channel:
            return

        post = Posts.get_or_none(
            (Posts.channel_id == channel_id) & (Posts.sended_message_id == message_id)
        )
        if not post:
            return

        chat_messages = await get_post_messages(post.post_id, False)

        # Разделяем сообщения на медиа и текстовые
        media_messages = [msg for msg in chat_messages if msg.file_type]
        text_messages = [msg for msg in chat_messages if msg.text and not msg.file_type]

        # Обрабатываем текстовые сообщения
        for msg in text_messages:
            text = msg.text
            if channel.chat_caption:
                text = f"{text}\n\n{channel.chat_caption}"
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_to_message_id=message.message_id,
                request_timeout=20.0,
            )

        # Обрабатываем медиа сообщения
        if media_messages:
            sorted_media = sorted(
                media_messages, key=lambda x: (x.media_group_id or "")
            )
            for media_group_id, group in groupby(
                sorted_media, key=lambda x: x.media_group_id
            ):
                group_messages = list(group)

                if media_group_id:
                    await send_media_group(
                        bot,
                        chat_id,
                        group_messages,
                        message.message_id,
                        channel.chat_caption,
                    )
                else:
                    # Одиночные медиа сообщения
                    msg = group_messages[0]
                    caption = msg.caption if msg.caption else ""
                    if channel.chat_caption:
                        caption = (
                            f"{caption}\n\n{channel.chat_caption}"
                            if caption
                            else channel.chat_caption
                        )

                    if msg.file_type == "photo":
                        await bot.send_photo(
                            chat_id=chat_id,
                            photo=msg.file_id,
                            caption=caption,
                            reply_to_message_id=message.message_id,
                            request_timeout=20.0,
                        )
                    elif msg.file_type == "video":
                        await bot.send_video(
                            chat_id=chat_id,
                            video=msg.file_id,
                            caption=caption,
                            reply_to_message_id=message.message_id,
                            request_timeout=20.0,
                        )
                    elif msg.file_type == "document":
                        await bot.send_document(
                            chat_id=chat_id,
                            document=msg.file_id,
                            caption=caption,
                            reply_to_message_id=message.message_id,
                            request_timeout=20.0,
                        )

    except Exception as e:
        logger.error(f"Error handling forwarded post: {e}")
