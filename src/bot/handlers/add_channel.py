import logging

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from src.bot.states import AddChannel
from src.bot.keyboards.reply import get_main_keyboard, get_channel_add_keyboard
from src.bot.keyboards.inline import get_add_without_chat_keyboard
from src.bot.strings.messages import *
from src.services.channel_service import (
    extract_username_from_link,
    check_channel_permissions,
    get_linked_chat,
    add_channel,
)

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == "Add channel")
@router.message(Command("add_channel"))
async def cmd_add_channel(message: Message, state: FSMContext):
    await state.set_state(AddChannel.waiting_for_link)
    await state.update_data(user_id=message.from_user.id)

    await message.answer(
        CHANNEL_ADD_INSTRUCTION, reply_markup=get_channel_add_keyboard()
    )


@router.message(F.text == "Cancel")
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Операция отменена", reply_markup=get_main_keyboard())


@router.message(F.text == "Instruction", StateFilter(AddChannel.waiting_for_link))
async def cmd_instruction(message: Message):
    await message.answer(CHANNEL_ADD_INSTRUCTION)


@router.message(StateFilter(AddChannel.waiting_for_link))
async def process_channel_link(message: Message, state: FSMContext, bot: Bot):

    link = extract_username_from_link(message.text.strip())
    if not link:
        await message.answer(CHANNEL_LINK_INVALID + "1")
        return

    # Получаем информацию о канале
    try:
        channel = await bot.get_chat(link)
        if channel.type != "channel":
            raise ValueError("Not a channel")
    except Exception:
        await message.answer(CHANNEL_LINK_INVALID + "2")
        return

    # Проверяем права бота в канале
    is_admin, can_post = await check_channel_permissions(bot, channel.id)
    if not is_admin or not can_post:
        await message.answer(CHANNEL_BOT_NOT_ADMIN)
        return

    # Проверяем наличие связанного чата
    chat = await get_linked_chat(bot, channel)

    if chat:
        # Проверяем права в чате
        chat_admin, chat_post = await check_channel_permissions(bot, chat.id)
        if chat_admin and chat_post:
            # Добавляем канал и чат
            await add_channel(
                user_id=message.from_user.id,
                channel=channel,
                chat=chat,
                channel_permission=True,
                chat_permission=True,
            )
            await state.clear()
            await message.answer(
                CHANNEL_WITH_CHAT_SUCCESS, reply_markup=get_main_keyboard()
            )
        else:
            # Предлагаем добавить канал без чата
            await message.answer(
                CHANNEL_ADD_WITHOUT_CHAT, reply_markup=get_add_without_chat_keyboard()
            )
            await state.update_data(channel=channel)
    else:
        # Добавляем только канал
        await add_channel(
            user_id=message.from_user.id, channel=channel, channel_permission=True
        )
        await state.clear()
        await message.answer(CHANNEL_ADDED_SUCCESS, reply_markup=get_main_keyboard())


@router.callback_query(F.data == "add_channel_without_chat")
async def add_channel_without_chat(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    channel = data.get("channel")

    await add_channel(
        user_id=callback.from_user.id, channel=channel, channel_permission=True
    )

    await state.clear()
    await callback.message.answer(
        CHANNEL_ADDED_SUCCESS, reply_markup=get_main_keyboard()
    )
    await callback.message.delete()


@router.callback_query(F.data == "cancel_adding_channel")
async def cancel_adding_channel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Операция отменена", reply_markup=get_main_keyboard())
    await callback.message.delete()
