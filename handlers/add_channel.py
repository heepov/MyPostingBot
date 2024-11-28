import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from db.db import db_add_model
from handlers.common import cmd_cancel
from db.models import Channel
from handlers.states import AddChannel
from utils.chat_utils import check_bot_permission, extract_username_from_link
from aiogram.types import (
    Message,
    CallbackQuery,
)

from utils.app_strings import (
    STR_ADD_CHANNEL,
    CMD_ADD_CHANNEL,
)
from utils.strings import (
    MSG_CHANNEL_ADDED,
    MSG_CHANNEL_AND_CHAT_ADDED,
    MSG_ERROR,
    MSG_ERROR_CANT_GET_CHAT,
    MSG_ERROR_NO_PERMISSION,
    MSG_ERROR_WRONG_LINK,
)
from handlers.common_actions import start_channel_adding
from keyboards.inline_keyboard import make_inline_binary_keyboard

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == STR_ADD_CHANNEL)
@router.message(Command(CMD_ADD_CHANNEL))
async def add_channel_cmd_handler(message: Message, state: FSMContext) -> None:
    await start_channel_adding(message, state)


@router.message(AddChannel.adding_channel)
async def add_channel(message: Message, state: FSMContext, bot: Bot) -> None:
    link = extract_username_from_link(message.text.strip())
    await state.update_data(user_id=message.from_user.id)
    if not link:
        await message.answer(MSG_ERROR_WRONG_LINK)
        return

    channel = await check_get_channel(bot, link)

    if isinstance(channel, str):
        await message.answer(channel)
        return

    if channel["chat_id"]:
        chat = await check_get_chat(bot, channel["chat_id"])

        if isinstance(chat, str):
            await message.answer(chat)
            await state.update_data(channel=channel)
            await state.set_state(AddChannel.confirming_without_chat)

            await message.answer(
                text=f"Do you want to add Channel @{channel['channel_username']} without Chat? Chat error is {chat}.",
                reply_markup=make_inline_binary_keyboard(
                    "confirm_without_chat", "cancel_add_channel"
                ),
            )
            return
        else:
            await add_channel_to_db(message, state, bot, channel, chat)
            return

    await add_channel_to_db(message, state, bot, channel, None)


@router.callback_query(lambda c: c.data == "confirm_without_chat")
async def confirm_without_chat(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    channel = data.get("channel")
    await add_channel_to_db(callback.message, state, bot, channel, None)
    await callback.message.delete_reply_markup()


@router.callback_query(lambda c: c.data == "cancel_add_channel")
async def cancel_add_channel(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await callback.message.answer("Channel addition cancelled.")
    await callback.message.delete_reply_markup()
    await callback.message.delete()
    await cmd_cancel(callback.message, state, bot)


async def add_channel_to_db(
    message: Message, state: FSMContext, bot: Bot, channel: dict, chat: dict | None
):
    channel_db = Channel(
        channel_id=channel["channel_id"],
        channel_username=channel["channel_username"],
        channel_permission=channel["channel_permission"],
        user_id=(await state.get_data())["user_id"],
        chat_id=chat["chat_id"] if chat is not None else None,
        chat_username=chat["chat_username"] if chat is not None else None,
        chat_permission=chat["chat_permission"] if chat is not None else None,
    )

    if chat == None:
        await message.answer(
            text=f"You added Channel @{channel['channel_username']} without Chat.",
        )
    else:
        await message.answer(
            text=f"You added Channel @{channel['channel_username']} with Chat @{chat['chat_username']}",
        )

    db_add_model(channel_db)
    await cmd_cancel(message, state, bot)


async def check_get_channel(bot: Bot, link: str) -> dict | str:

    try:
        chat_info = await bot.get_chat(link)
    except Exception as e:
        return MSG_ERROR_CANT_GET_CHAT

    if chat_info.type != "channel":
        return "Wrong channel type"

    try:
        permission_check = await check_bot_permission(bot, chat_info.id)
        if permission_check is not True:
            return MSG_ERROR_NO_PERMISSION
    except Exception as e:
        return MSG_ERROR_NO_PERMISSION

    return {
        "channel_id": chat_info.id,
        "channel_username": chat_info.username,
        "channel_permission": True,
        "chat_id": chat_info.linked_chat_id,
    }


async def check_get_chat(bot: Bot, chat_id: int) -> dict | str:
    try:
        chat_info = await bot.get_chat(chat_id)
    except Exception as e:
        return MSG_ERROR_CANT_GET_CHAT

    if chat_info.type != "supergroup":
        return "Wrong chat type"

    try:
        permission_check = await check_bot_permission(bot, chat_info.id)
        if permission_check is not True:
            return MSG_ERROR_NO_PERMISSION
    except Exception as e:
        return MSG_ERROR_NO_PERMISSION

    return {
        "chat_id": chat_info.id,
        "chat_username": chat_info.username,
        "chat_permission": True,
    }
