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

    chat_data = await check_and_get_chat(message, bot, message.text)
    if not chat_data:
        return

    channel = Channel(
        channel_id=chat_data["id"],
        username=chat_data["username"],
        permission=chat_data["permission"],
        user_id=message.from_user.id,
    )

    db_add_channel(channel)

    await state.update_data(
        channel_id=chat_data["id"], channel_username=chat_data["username"]
    )
    await message.answer(
        text=f"You added Channel @{chat_data["username"]}.\n\nIf you want to add chat, send here link or username.",
        reply_markup=make_one_line_keyboard(add_chat_menu),
    )
    await state.set_state(AddChannel.adding_chat)


@router.message(AddChannel.adding_chat)
async def add_chat(message: Message, state: FSMContext, bot: Bot) -> None:

    chat_data = await check_and_get_chat(message, bot, message.text)
    if not chat_data:
        return

    data = await state.get_data()

    chat = Chat(
        chat_id=chat_data["id"],
        username=chat_data["username"],
        permission=chat_data["permission"],
        channel_id=data.get("channel_id"),
    )

    db_add_chat(chat)

    await message.answer(
        f"Channel @{data.get("channel_username")} with linked Chat @{chat_data["username"]} successfully added!"
    )

    await state.update_data(
        chat_id=chat_data["id"], chat_username=chat_data["username"]
    )

    await cmd_cancel(message, state)


async def check_and_get_chat(message: Message, bot: Bot, string: str) -> dict | None:
    link = extract_username_from_link(string.strip())
    if not link:
        await message.answer("Wrong link. Try again.")
        return None
    try:
        chat_info = await bot.get_chat(link)
        chat_id = chat_info.id
    except Exception as e:
        await message.answer(f"Can't get chat info: {e}")
        return None

    try:
        permission_check = await check_bot_permission(bot, chat_id)
        if permission_check is not True:
            await message.answer("Bot doesn't have permission in this channel.")
            return None
    except Exception as e:
        await message.answer(f"Some error: {e}")
        return None

    return {
        "id": chat_id,
        "username": chat_info.username,
        "permission": permission_check,
    }
