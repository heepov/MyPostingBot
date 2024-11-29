import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from src.services.channel_service import get_user_channels, get_channel
from src.bot.keyboards.reply import get_main_keyboard
from src.bot.keyboards.inline import get_channels_keyboard
from src.bot.strings.messages import OPERATION_CANCELLED
from src.bot.handlers.add_channel import cmd_add_channel
from src.bot.dto import ChannelInfo

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "cancel")
async def process_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(OPERATION_CANCELLED, reply_markup=get_main_keyboard())
    await callback.message.delete()


@router.callback_query(F.data == "add_new_channel")
async def process_add_channel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await cmd_add_channel(callback.message, state)
    await callback.message.delete()


async def handle_channel_selection(
    callback: CallbackQuery,
    state: FSMContext,
    next_state,
    select_message: str,
    success_handler,
    action_type: str = "settings",
):
    """
    Общий обработчик выбора канала

    Args:
        callback: CallbackQuery
        state: FSMContext
        next_state: State - следующее состояние
        select_message: str - сообщение при выборе канала
        success_handler: Callable - функция обработки успешного выбора канала
        action_type: str - тип действия (settings/schedule/post)
    """
    action = callback.data
    user_id = callback.from_user.id
    await state.update_data(user_id=user_id)  # Сохраняем user_id в state

    if action == "cancel":
        await state.clear()
        await callback.message.answer(
            OPERATION_CANCELLED, reply_markup=get_main_keyboard()
        )
        await callback.message.delete()
    elif action == "add_new_channel":
        await state.clear()
        await cmd_add_channel(callback.message, state)
        await callback.message.delete()
    else:
        channel_id = int(action.split(":")[1])
        channel = await get_channel(channel_id)

        # Преобразуем модель в DTO
        channel_info = ChannelInfo(
            channel_id=channel.channel_id,
            channel_title=channel.channel_title,
            channel_username=channel.channel_username,
            channel_permission=channel.channel_permission,
            channel_caption=channel.channel_caption,
            chat_id=channel.chat_id,
            chat_title=channel.chat_title,
            chat_username=channel.chat_username,
            chat_permission=channel.chat_permission,
            chat_caption=channel.chat_caption,
        )

        await state.update_data(channel_id=channel_id)
        await state.set_state(next_state)
        await success_handler(callback, channel_info, state)


async def back_to_channels_handler(
    callback: CallbackQuery,
    state: FSMContext,
    next_state,
    select_message: str,
    action_type: str = "settings",
):
    """Общий обработчик возврата к списку каналов"""
    logger.info(f"User ID: {callback.from_user.id}")
    channels = await get_user_channels(callback.from_user.id)
    await state.set_state(next_state)
    logger.info(f"next_state: {next_state}")
    # Определяем тип действия из текущего состояния
    current_state = await state.get_state()
    if current_state and "settings" in current_state:
        action_type = "settings"
    elif current_state and "schedule" in current_state:
        action_type = "schedule"

    await callback.message.edit_text(
        select_message, reply_markup=get_channels_keyboard(channels, action_type)
    )
