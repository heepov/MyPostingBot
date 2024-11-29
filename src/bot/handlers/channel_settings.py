import logging
from aiogram import F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup

from .common import handle_channel_selection, back_to_channels_handler
from src.bot.states import ChannelSettings
from src.bot.keyboards.reply import get_main_keyboard
from src.bot.keyboards.inline import (
    get_channels_keyboard,
    get_channel_settings_keyboard,
    get_caption_keyboard,
    get_yes_no_keyboard,
)
from src.bot.strings.messages import *
from src.services.channel_service import (
    get_user_channels,
    delete_channel,
    update_channel_info,
    add_chat_to_channel,
    get_channel,
)
from src.bot.dto import ChannelInfo
from .common import router
from src.services.post_service import get_channel_posts

logger = logging.getLogger(__name__)


async def edit_message_if_changed(
    message: Message, new_text: str, new_markup: InlineKeyboardMarkup
):
    """Редактирует сообщение только если текст или разметка изменились"""
    try:
        await message.edit_text(new_text, reply_markup=new_markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise e


async def settings_success(
    callback: CallbackQuery, channel_info: ChannelInfo, state: FSMContext
):
    """Обработчик успешного выбора канала в расписании"""
    keyboard = get_channel_settings_keyboard(channel_info)
    await callback.message.edit_text("Запланированные посты:", reply_markup=keyboard)


@router.message(F.text == "Channels settings")
@router.message(Command("settings"))
async def cmd_channel_settings(message: Message, state: FSMContext):
    channels = await get_user_channels(message.from_user.id)

    if not channels:
        await message.answer(NO_CHANNELS)
        return

    await state.set_state(ChannelSettings.waiting_for_channel)
    await message.answer(
        SETTINGS_SELECT_CHANNEL,
        reply_markup=get_channels_keyboard(channels, "settings"),
    )


@router.callback_query(F.data.startswith("back_to_settings_channels"))
async def back_to_channels(callback: CallbackQuery, state: FSMContext):
    await back_to_channels_handler(
        callback,
        state,
        ChannelSettings.waiting_for_channel,
        SETTINGS_SELECT_CHANNEL,
        "settings",
    )


@router.callback_query(F.data.startswith("settings_channel:"))
async def process_channel_selection(callback: CallbackQuery, state: FSMContext):
    await handle_channel_selection(
        callback,
        state,
        ChannelSettings.waiting_for_action,
        SCHEDULE_SELECT_CHANNEL,
        settings_success,
        "settings",
    )


@router.message(StateFilter(ChannelSettings.waiting_for_channel))
async def process_any_message(message: Message):
    await message.answer(SETTINGS_SELECT_CHANNEL)


@router.callback_query(F.data.startswith("channel_delete:"))
async def process_channel_delete(callback: CallbackQuery):
    channel_id = int(callback.data.split(":")[1])
    await callback.message.edit_text(
        CONFIRM_DELETE_CHANNEL,
        reply_markup=get_yes_no_keyboard(f"confirm_delete_channel:{channel_id}"),
    )


@router.callback_query(F.data.startswith("yes_confirm_delete_channel:"))
async def confirm_channel_delete(callback: CallbackQuery, state: FSMContext):
    channel_id = int(callback.data.split(":")[1])
    await delete_channel(channel_id)
    await state.clear()

    await callback.message.edit_text(CHANNEL_DELETED, reply_markup=get_main_keyboard())


@router.callback_query(F.data.startswith("no_confirm_delete_channel:"))
async def cancel_channel_delete(callback: CallbackQuery, state: FSMContext):
    channel_id = int(callback.data.split(":")[1])
    channel = await get_channel(channel_id)

    await callback.message.edit_text(
        CHANNEL_SETTINGS.format(
            channel_name=channel.channel_title or channel.channel_username
        ),
        reply_markup=get_channel_settings_keyboard(channel),
    )


@router.callback_query(F.data.startswith("channel_add_chat:"))
async def process_add_chat(callback: CallbackQuery, state: FSMContext, bot: Bot):
    channel_id = int(callback.data.split(":")[1])
    success, message = await add_chat_to_channel(bot, channel_id)
    channel = await get_channel(channel_id)
    if success:
        await callback.answer(CHAT_ADDED)
    else:
        await callback.answer(message)

    await edit_message_if_changed(
        CHANNEL_SETTINGS.format(
            channel_name=channel.channel_title or channel.channel_username
        ),
        reply_markup=get_channel_settings_keyboard(channel),
    )


@router.callback_query(F.data.startswith("channel_check_schedule:"))
async def process_check_schedule(callback: CallbackQuery, state: FSMContext):
    channel_id = int(callback.data.split(":")[1])
    channel = await get_channel(channel_id)

    # Получаем все посты канала
    posts, _ = await get_channel_posts(channel_id)
    scheduler = router.callback_data["scheduler"]

    # Добавляем каждый пост с датой в планировщик
    for post in posts:
        if post.date_time:
            await scheduler.schedule_post(post.post_id)

    await callback.answer(SCHEDULE_CHECKED)

    await edit_message_if_changed(
        callback.message,
        CHANNEL_SETTINGS.format(
            channel_name=channel.channel_title or channel.channel_username
        ),
        get_channel_settings_keyboard(channel),
    )


@router.callback_query(F.data.startswith("channel_update_info:"))
async def process_update_info(callback: CallbackQuery, state: FSMContext, bot: Bot):
    channel_id = int(callback.data.split(":")[1])
    channel = await update_channel_info(bot, channel_id)

    await callback.answer(INFO_UPDATED)

    await edit_message_if_changed(
        callback.message,
        CHANNEL_SETTINGS.format(
            channel_name=channel.channel_title or channel.channel_username
        ),
        get_channel_settings_keyboard(channel),
    )


@router.callback_query(F.data.startswith("channel_caption:"))
async def process_caption(callback: CallbackQuery, state: FSMContext):
    data = callback.data.split(":")
    channel_id = int(data[1])
    caption_type = data[2]  # "channel" или "chat"
    channel = await get_channel(channel_id)
    await state.update_data(channel_id=channel_id, caption_type=caption_type)
    await state.set_state(ChannelSettings.waiting_for_caption)

    caption_target = "канала" if caption_type == "channel" else "комментариев"
    caption = (
        channel.channel_caption if caption_type == "channel" else channel.chat_caption
    )
    await callback.message.edit_text(
        CAPTION_INSTRUCTION.format(target=caption_target, caption=caption),
        reply_markup=get_caption_keyboard(channel_id, caption_type),
    )


@router.message(StateFilter(ChannelSettings.waiting_for_caption))
async def process_caption_text(message: Message, state: FSMContext):
    data = await state.get_data()
    channel_id = data["channel_id"]
    caption_type = data["caption_type"]
    channel = await get_channel(channel_id)

    # Сохраняем подпись в БД
    if caption_type == "channel":
        channel.channel_caption = message.text
    else:
        channel.chat_caption = message.text
    channel.save()

    await message.answer(CAPTION_ADDED)
    await message.answer(
        CHANNEL_SETTINGS.format(
            channel_name=channel.channel_title or channel.channel_username
        ),
        reply_markup=get_channel_settings_keyboard(channel),
    )


@router.callback_query(F.data.startswith("delete_caption:"))
async def process_delete_caption(callback: CallbackQuery, state: FSMContext):
    data = callback.data.split(":")
    channel_id = int(data[1])
    caption_type = data[2]
    channel = await get_channel(channel_id)

    # Удаляем подпись из БД
    if caption_type == "channel":
        channel.channel_caption = None
    else:
        channel.chat_caption = None
    channel.save()

    await callback.answer(CAPTION_DELETED)
    await callback.message.edit_text(
        CHANNEL_SETTINGS.format(
            channel_name=channel.channel_title or channel.channel_username
        ),
        reply_markup=get_channel_settings_keyboard(channel),
    )


@router.callback_query(F.data.startswith("back_to_settings:"))
async def back_to_settings(callback: CallbackQuery, state: FSMContext):
    channel_id = int(callback.data.split(":")[1])
    channel = await get_channel(channel_id)

    await callback.message.edit_text(
        CHANNEL_SETTINGS.format(
            channel_name=channel.channel_title or channel.channel_username
        ),
        reply_markup=get_channel_settings_keyboard(channel),
    )
