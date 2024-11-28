import logging

from aiogram import Bot
from handlers.states import AddPost, AddChannel
from keyboards.reply_keyboard import make_one_line_keyboard
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from utils.app_strings import MENU_ADD_CHANNEL_BTN
from utils.strings import MSG_ADD_CHANNEL_INSTRUCTION
from db.db import db_get_channel_by_channel_id
from handlers.common import cmd_cancel
from utils.app_strings import MENU_ADD_POST_BTN, MENU_ADD_POST_WITH_CHAT_BTN

logger = logging.getLogger(__name__)


async def start_post_creation(message: Message, state: FSMContext, bot: Bot) -> None:
    selected_channel = db_get_channel_by_channel_id(
        (await state.get_data()).get("channel_id")
    )
    if selected_channel == None:
        await message.answer(text="You dont have any channels")
        await cmd_cancel(message, state, bot)

    menu = MENU_ADD_POST_BTN
    if selected_channel.chat_id != None and selected_channel.chat_permission == True:
        menu = MENU_ADD_POST_WITH_CHAT_BTN

    await message.answer(
        text=f"Add message for new Post in Channel @{selected_channel.channel_username} with Chat @{selected_channel.chat_username}",
        reply_markup=make_one_line_keyboard(menu),
    )
    await state.set_state(AddPost.add_channel_message)


async def start_channel_adding(message: Message, state: FSMContext, bot: Bot) -> None:
    await message.answer(
        text=MSG_ADD_CHANNEL_INSTRUCTION,
        reply_markup=make_one_line_keyboard(MENU_ADD_CHANNEL_BTN),
    )
    await state.set_state(AddChannel.adding_channel)


async def start_show_schedule(message: Message, state: FSMContext, bot: Bot) -> None:
    return None