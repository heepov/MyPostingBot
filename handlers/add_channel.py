import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from db.db import db_add_channel, db_add_chat
from handlers.common import cmd_cancel
from keyboards.simple_row import make_one_line_keyboard
from db.models import Channel, Chat
from handlers.states import AddChannel
from utils.chat_utils import check_bot_permission, extract_username_from_link

router = Router()
logger = logging.getLogger(__name__)


add_channel_menu = ["Cancel", "Instruction"]
add_chat_menu = ["Dont add channel", "Instruction"]


@router.message(F.text == "Add channel")
@router.message(Command("addchannel"))
async def add_channel_handler(message: Message, state: FSMContext) -> None:
    await message.answer(
        text="Add bot to CHANNEL admins and send here link or username",
        reply_markup=make_one_line_keyboard(add_channel_menu),
    )
    await state.set_state(AddChannel.adding_channel)


@router.message(AddChannel.adding_channel)
async def add_channel(message: Message, state: FSMContext, bot: Bot) -> None:
    user_id = message.from_user.id
    link = extract_username_from_link(message.text.strip())

    if not link:
        await message.answer("Wrong link. Try again.")
        return
    try:
        chat_info = await bot.get_chat(link)
        chat_id = chat_info.id
    except Exception as e:
        await message.answer(f"Can't get chat info: {e}")
        return

    try:
        permission_check = await check_bot_permission(bot, chat_id)
        if permission_check is not True:
            await message.answer("Bot doesn't have permission in this channel.")
            return
    except Exception as e:
        await message.answer(f"Some error: {e}")
        return

    channel = Channel(
        channel_id=chat_id,
        username=chat_info.username,
        permission=permission_check,
        user_id=user_id,
    )

    db_add_channel(channel)

    await message.answer(
        text=f"You added Channel @{chat_info.username}.\n\nIf you want to add chat, send here link or username.",
        reply_markup=make_one_line_keyboard(add_chat_menu),
    )
    await state.update_data(channel_id=chat_id, channel_username=chat_info.username)
    await state.set_state(AddChannel.adding_chat)


@router.message(AddChannel.adding_chat)
async def add_chat(message: Message, state: FSMContext, bot: Bot) -> None:
    link = extract_username_from_link(message.text.strip())
    data = await state.get_data()
    channel_id = data.get("channel_id")

    if not link:
        await message.answer("Wrong link. Try again.")
        return
    try:
        chat_info = await bot.get_chat(link)
        chat_id = chat_info.id
    except Exception as e:
        await message.answer(f"Can't get chat info: {e}")
        return

    try:
        permission_check = await check_bot_permission(bot, chat_id)
        if permission_check is not True:
            await message.answer("Bot doesn't have permission in this channel.")
            return
    except Exception as e:
        await message.answer(f"Some error: {e}")
        return

    chat = Chat(
        chat_id=chat_id,
        username=chat_info.username,
        permission=permission_check,
        channel_id=channel_id,
    )
    db_add_chat(chat)
    await message.answer(
        f"Channel @{data.get("channel_username")} with linked Chat @{data.get("chat_username")} successfully added!"
    )
    await state.update_data(chat_id=chat_id, chat_username=chat_info.username)
    await cmd_cancel(message, state)
