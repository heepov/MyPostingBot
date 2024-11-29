import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from src.bot.states import ShowSchedule
from src.bot.keyboards.reply import get_main_keyboard
from src.bot.keyboards.inline import (
    get_channels_keyboard,
    get_posts_keyboard,
    get_yes_no_keyboard,
)
from src.bot.strings.messages import *
from src.services.channel_service import get_user_channels
from src.services.post_service import delete_post
from .add_channel import cmd_add_channel
from .common import handle_channel_selection, back_to_channels_handler
from src.bot.dto import ChannelInfo
from .common import router


logger = logging.getLogger(__name__)


async def schedule_success(
    callback: CallbackQuery, channel_info: ChannelInfo, state: FSMContext
):
    """Обработчик успешного выбора канала в расписании"""
    keyboard = await get_posts_keyboard(channel_info.channel_id)
    await callback.message.edit_text("Запланированные посты:", reply_markup=keyboard)


@router.message(F.text == "Show schedule")
@router.message(Command("schedule"))
async def cmd_show_schedule(message: Message, state: FSMContext):
    channels = await get_user_channels(message.from_user.id)

    if not channels:
        await message.answer(NO_CHANNELS)
        return

    await state.set_state(ShowSchedule.waiting_for_channel)
    await message.answer(
        SCHEDULE_SELECT_CHANNEL,
        reply_markup=get_channels_keyboard(channels, "schedule"),
    )


@router.callback_query(F.data.startswith("back_to_schedule_channels"))
async def back_to_channels(callback: CallbackQuery, state: FSMContext):
    await back_to_channels_handler(
        callback,
        state,
        ShowSchedule.waiting_for_channel,
        SCHEDULE_SELECT_CHANNEL,
        "schedule",
    )


@router.callback_query(F.data.startswith("schedule_channel:"))
async def process_channel_selection(callback: CallbackQuery, state: FSMContext):
    await handle_channel_selection(
        callback,
        state,
        ShowSchedule.waiting_for_post,
        SCHEDULE_SELECT_CHANNEL,
        schedule_success,
        "schedule",
    )


@router.callback_query(
    F.data.startswith("posts_offset:"), StateFilter(ShowSchedule.waiting_for_post)
)
async def process_posts_pagination(callback: CallbackQuery):
    _, channel_id, offset = callback.data.split(":")
    keyboard = await get_posts_keyboard(int(channel_id), int(offset))
    await callback.message.edit_reply_markup(reply_markup=keyboard)


@router.callback_query(
    F.data.startswith("select_post:"), StateFilter(ShowSchedule.waiting_for_post)
)
async def process_post_selection(callback: CallbackQuery):
    post_id = int(callback.data.split(":")[1])
    await callback.message.edit_text(
        CONFIRM_DELETE_POST, reply_markup=get_yes_no_keyboard(f"delete_post:{post_id}")
    )


@router.callback_query(F.data.startswith("yes_delete_post:"))
async def confirm_post_deletion(callback: CallbackQuery, state: FSMContext):
    post_id = int(callback.data.split(":")[1])
    scheduler = router.callback_data["scheduler"]
    scheduler.remove_job(post_id)

    await delete_post(post_id)
    data = await state.get_data()

    await callback.message.edit_text(
        SCHEDULE_SELECT_CHANNEL,
        reply_markup=await get_posts_keyboard(data["channel_id"]),
    )


@router.callback_query(F.data.startswith("no_delete_post:"))
async def cancel_post_deletion(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback.message.edit_text(
        "Запланированные посты:",
        reply_markup=await get_posts_keyboard(data["channel_id"]),
    )
