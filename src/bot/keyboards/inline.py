import logging
from datetime import datetime, timedelta
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from src.db.models import Channels
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from src.services.post_service import get_channel_posts, get_post_preview
from src.bot.constants import POSTS_PER_PAGE, POSTS_PER_ROW
from src.bot.dto import ChannelInfo

logger = logging.getLogger(__name__)


def get_add_without_chat_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="Да", callback_data="add_channel_without_chat"),
            InlineKeyboardButton(text="Нет", callback_data="cancel_adding_channel"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_channels_keyboard(
    channels: list[Channels], action: str = "select"
) -> InlineKeyboardMarkup:
    """
    Args:
        channels: список каналов
        action: тип действия ('settings', 'schedule', 'post')
    """
    logger.info(f"Creating keyboard for action: {action}")
    builder = InlineKeyboardBuilder()
    for channel in channels:
        builder.button(
            text=channel.channel_title or channel.channel_username,
            callback_data=f"{action}_channel:{channel.channel_id}",
        )
    builder.button(text="Добавить канал", callback_data="add_new_channel")
    builder.button(text="Отмена", callback_data="cancel")
    builder.adjust(1)
    return builder.as_markup()


async def get_calendar_keyboard() -> InlineKeyboardMarkup:
    return await SimpleCalendar().start_calendar()


def get_time_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # Добавляем кнопки времени с интервалом в 1 час
    for hour in range(24):
        builder.button(
            text=f"{hour:02d}:00", callback_data=f"select_time:{hour:02d}:00"
        )

    builder.adjust(4)
    return builder.as_markup()


def get_yes_no_keyboard(callback_data: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Да", callback_data=f"yes_{callback_data}")
    builder.button(text="Нет", callback_data=f"no_{callback_data}")
    builder.adjust(2)
    return builder.as_markup()


async def get_posts_keyboard(channel_id: int, offset: int = 0) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    posts, total = await get_channel_posts(channel_id, offset)

    # Добавляем посты в две колонки
    for i in range(0, len(posts), POSTS_PER_ROW):
        row_buttons = []
        for post in posts[i : i + POSTS_PER_ROW]:
            preview, chat_count = await get_post_preview(post.post_id)
            # Сокращаем превью до 15 символов вместо 20
            preview = preview[:15] + "..." if len(preview) > 15 else preview
            # Форматируем дату более компактно
            date_str = post.date_time.strftime("%d.%m")
            time_str = post.date_time.strftime("%H:%M")

            # Формируем текст кнопки в более компактном виде
            text = f"{date_str} {time_str}"
            if chat_count > 0:
                text = f"{text} [{chat_count}]"
            text = f"{text} | {preview}"

            row_buttons.append(
                InlineKeyboardButton(
                    text=text, callback_data=f"select_post:{post.post_id}"
                )
            )
        if len(row_buttons) == 1:
            row_buttons.append(InlineKeyboardButton(text=" ", callback_data="none"))
        builder.row(*row_buttons)

    # Навигационные кнопки
    nav_buttons = [
        InlineKeyboardButton(
            text="⬅️" if offset > 0 else " ",
            callback_data=(
                f"posts_offset:{channel_id}:{offset-POSTS_PER_PAGE}"
                if offset > 0
                else "none"
            ),
        ),
        InlineKeyboardButton(
            text="Назад к каналам", callback_data="back_to_schedule_channels"
        ),
        InlineKeyboardButton(
            text="➡️" if total > offset + POSTS_PER_PAGE else " ",
            callback_data=(
                f"posts_offset:{channel_id}:{offset+POSTS_PER_PAGE}"
                if total > offset + POSTS_PER_PAGE
                else "none"
            ),
        ),
    ]

    builder.row(*nav_buttons)
    return builder.as_markup()


def get_channel_settings_keyboard(channel: ChannelInfo) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(
        text="❌ Удалить", callback_data=f"channel_delete:{channel.channel_id}"
    )

    if not channel.chat_id:
        builder.button(
            text="➕ Добавить чат",
            callback_data=f"channel_add_chat:{channel.channel_id}",
        )

    builder.button(
        text="📅 Проверить расписание",
        callback_data=f"channel_check_schedule:{channel.channel_id}",
    )

    builder.button(
        text="ℹ️ Обновить информацию",
        callback_data=f"channel_update_info:{channel.channel_id}",
    )

    builder.button(
        text="✏️ Подпись канала",
        callback_data=f"channel_caption:{channel.channel_id}:channel",
    )

    if channel.chat_id:
        builder.button(
            text="✏️ Подпись комментариев",
            callback_data=f"channel_caption:{channel.channel_id}:chat",
        )

    builder.button(text="◀️ Назад", callback_data="back_to_settings_channels")

    builder.adjust(1)
    return builder.as_markup()


def get_caption_keyboard(channel_id: int, caption_type: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="❌ Удалить подпись",
        callback_data=f"delete_caption:{channel_id}:{caption_type}",
    )
    builder.button(text="◀️ Назад", callback_data=f"back_to_settings:{channel_id}")
    builder.adjust(1)
    return builder.as_markup()
