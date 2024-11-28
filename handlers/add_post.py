import logging

from peewee import *
from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
)
from handlers.select_channel import show_channel_select
from handlers.states import AddPost
from handlers.common import cmd_cancel
from keyboards.reply_keyboard import make_one_line_keyboard
from db.db import db_get_channel_by_channel_id, db_add_model, db_user_by_user_id
from utils.app_strings import MENU_ADD_POST_BTN, MENU_ADD_POST_WITH_CHAT_BTN
from db.models import Post, Message
from datetime import datetime
from zoneinfo import ZoneInfo
from utils.config_reader import config

router = Router()
logger = logging.getLogger(__name__)


add_channel_menu = ["Cancel", "Instruction"]
add_chat_menu = ["Dont add channel", "Instruction"]


@router.message(F.text == "Add post")
@router.message(Command("addpost"))
async def add_post_handler(message: Message, state: FSMContext, bot: Bot) -> None:
    await state.clear()
    await show_channel_select(
        message, state, next_state=AddPost.add_channel_message, bot=bot
    )


@router.message(F.text == "Add comment")
@router.message(Command("addcomment"))
async def cmd_add_chat_message_handler(message: Message, state: FSMContext) -> None:
    logger.info("Handler cmd_add_chat_message_handler called")
    user_state = await state.get_state()
    logger.info(f"Current state: {user_state}")
    if user_state != AddPost.add_channel_message.state:
        await message.answer("Wrong command. At first you need /addpost.")
        return

    data = await state.get_data()
    channel = db_get_channel_by_channel_id(data.get("channel_id"))
    channel_messages = data.get("channel_messages", [])

    if len(channel_messages) == 0:
        await message.answer(
            text="You dont add any messages. To add message send it here.",
        )
        return

    if channel.chat_id == None and len(channel_messages) > 0:
        await message.answer(
            text="You dont have any chats linked to this channel. To set time for post use /settime",
            reply_markup=make_one_line_keyboard(MENU_ADD_POST_BTN),
        )
        return

    await message.answer(
        text=f"Now send your comments. Or set time for post use /settime",
        reply_markup=make_one_line_keyboard(MENU_ADD_POST_BTN),
    )
    await state.set_state(AddPost.add_chat_message)


@router.message(F.text == "Set time")
@router.message(Command("settime"))
async def cmd_set_time_handler(message: Message, state: FSMContext) -> None:
    user_state = await state.get_state()
    if user_state not in [
        AddPost.add_channel_message.state,
        AddPost.add_chat_message.state,
    ]:
        await message.answer("Wrong command. At first you need /addpost.")
        return

    data = await state.get_data()
    channel = db_get_channel_by_channel_id(data.get("channel_id"))
    channel_messages = data.get("channel_messages", [])

    if len(channel_messages) == 0 and user_state == AddPost.add_channel_message.state:
        await message.answer(
            text="You dont add any messages. To add message send it here.",
        )
        return

    await message.answer(
        text=f"Now choose ate and time for post",
        reply_markup=make_one_line_keyboard(MENU_ADD_POST_BTN),
    )
    await state.set_state(AddPost.set_time)


@router.message(AddPost.add_channel_message)
async def add_channel_message_handler(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    channel = db_get_channel_by_channel_id(data.get("channel_id"))
    personal_caption = channel.channel_caption
    if personal_caption:
        personal_caption = f"\n\n{personal_caption}"
    else:
        personal_caption = ""
    await add_message_sate_data(message, state, True, personal_caption)


@router.message(AddPost.add_chat_message)
async def add_chat_message_handler(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    channel = db_get_channel_by_channel_id(data.get("channel_id"))
    personal_caption = channel.chat_caption
    if personal_caption:
        personal_caption = f"\n\n{personal_caption}"
    else:
        personal_caption = ""
    await add_message_sate_data(message, state, False, personal_caption)


@router.message(AddPost.set_time)
async def set_time_handler(message: Message, state: FSMContext, bot: Bot) -> None:
    user = db_user_by_user_id(message.from_user.id)
    user_tz = ZoneInfo(user.time_zone)  # Получаем часовой пояс пользователя
    user_input = message.text.strip()

    try:
        naive_dt = datetime.strptime(user_input, config.date_time_format)

        user_aware_dt = naive_dt.replace(tzinfo=user_tz)
        if user_aware_dt <= datetime.now(user_tz):
            await message.answer(
                f"Нельзя установить время в прошлом. Текущее время: "
                f"{datetime.now(user_tz).strftime(config.date_time_format)}"
            )
            return

        await message.answer(
            f"Время поста установлено на: {user_aware_dt.strftime(config.date_time_format)}"
        )
        await add_post_to_db(message, state, user_aware_dt)
        await cmd_cancel(message, state, bot)

    except ValueError:
        await message.answer(
            f"Неверный формат даты. Используйте формат: {config.date_time_format_print}\n"
            f"Например: 25.12.2023 15:30"
        )
        return


async def add_message_sate_data(
    message: Message, state: FSMContext, is_channel_message: bool, personal_caption: str
) -> None:
    file_id, media_type = get_message_type_file_id(message)
    data = await state.get_data()

    if is_channel_message:
        messages = data.get("channel_messages", [])
    else:
        messages = data.get("chat_messages", [])

    new_message = {
        "is_channel_message": is_channel_message,
    }

    if media_type == "text":
        new_message.update(
            {
                "text": f"{message.text or ''}{personal_caption}",
                "caption": None,
                "file_type": None,
                "file_id": None,
                "media_group_id": None,
            }
        )
    else:
        new_message.update(
            {
                "text": None,
                "caption": f"{message.caption or ''}{personal_caption}",
                "file_type": media_type,
                "file_id": file_id,
                "media_group_id": message.media_group_id,
            }
        )

    messages.append(new_message)

    if is_channel_message:
        await state.update_data(channel_messages=messages)
        logger.info(f"Added message {len(messages)} to channel messages")
    else:
        await state.update_data(chat_messages=messages)
        logger.info(f"Added message {len(messages)} to chat messages")


async def add_messages_to_db(post_id: int, messages: list[dict]) -> None:
    if len(messages) > 0:
        for message in messages:
            db_add_model(
                Message(
                    post_id=post_id,
                    is_channel_message=message.get("is_channel_message"),
                    text=message.get("text"),
                    caption=message.get("caption"),
                    file_type=message.get("file_type"),
                    file_id=message.get("file_id"),
                    media_group_id=message.get("media_group_id"),
                )
            )


async def add_post_to_db(
    message: Message, state: FSMContext, date_time: datetime
) -> None:
    data = await state.get_data()
    channel = db_get_channel_by_channel_id(data.get("channel_id"))
    chat_messages = data.get("chat_messages", [])
    channel_messages = data.get("channel_messages", [])

    post = db_add_model(
        Post(
            user_id=message.from_user.id,
            channel_id=channel.channel_id,
            date_time=date_time,
        )
    )
    await add_messages_to_db(post.post_id, channel_messages)
    await add_messages_to_db(post.post_id, chat_messages)


def get_message_type_file_id(message: Message):
    if message.photo:
        return message.photo[-1].file_id, "photo"
    elif message.document:
        return message.document.file_id, "document"
    elif message.video:
        return message.video.file_id, "video"
    elif message.audio:
        return message.audio.file_id, "audio"
    elif message.voice:
        return message.voice.file_id, "voice"
    elif message.animation:
        return message.animation.file_id, "animation"
    elif message.text:
        return None, "text"

    return None, None
