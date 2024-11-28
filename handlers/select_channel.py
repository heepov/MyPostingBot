import logging
from aiogram import F, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from db.db import db_get_channels_by_user_id
from handlers.states import ChannelSelect, AddChannel, AddPost, BaseState
from utils.app_strings import STR_ADD_CHANNEL
from handlers.add_channel import add_channel_cmd_handler
from handlers.common_actions import start_post_creation

router = Router()
logger = logging.getLogger(__name__)


async def show_channel_select(
    message: Message, state: FSMContext, next_state: BaseState, bot: Bot
) -> None:
    user_channels = db_get_channels_by_user_id(message.from_user.id)

    buttons = []
    for channel in user_channels:
        chat = ""
        if channel.chat_id != None and channel.chat_permission == True:
            chat = f" with Chat @{channel.chat_username}"

        callback_data = f"select_channel|{channel.channel_id}|{next_state.state}"

        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"Channel @{channel.channel_username}{chat}",
                    callback_data=callback_data,
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text=STR_ADD_CHANNEL,
                callback_data=f"select_channel|add_channel|{AddChannel.adding_channel.state}",
            )
        ]
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer("Select a channel:", reply_markup=keyboard)
    await state.set_state(ChannelSelect.selecting_channel)


@router.callback_query(lambda c: c.data.startswith("select_channel"))
async def process_channel_selection(callback: CallbackQuery, state: FSMContext, bot: Bot):
    _, channel_id, next_state = callback.data.split("|")
    logger.info(callback.data)

    await state.update_data(channel_id=channel_id)
    await state.set_state(next_state)
    await callback.message.delete_reply_markup()

    if next_state == AddChannel.adding_channel.state:
        await add_channel_cmd_handler(callback.message, state)
    elif next_state == AddPost.add_channel_message.state:
        await start_post_creation(callback.message, state, bot)
