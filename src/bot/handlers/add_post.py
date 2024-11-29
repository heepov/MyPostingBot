from datetime import datetime
import logging
from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback

from .common import handle_channel_selection
from src.bot.dto import ChannelInfo
from src.bot.states import AddPost
from src.bot.keyboards.reply import get_main_keyboard, get_post_add_keyboard
from src.bot.keyboards.inline import (
    get_channels_keyboard,
    get_calendar_keyboard,
    get_time_keyboard,
    get_yes_no_keyboard,
)
from src.bot.strings.messages import *
from src.services.channel_service import get_user_channels
from src.services.post_service import (
    create_post,
    add_message_to_post,
    update_post_datetime,
    delete_post,
)
from .common import router

logger = logging.getLogger(__name__)


async def post_success(
    callback: CallbackQuery, channel_info: ChannelInfo, state: FSMContext
):
    """Обработчик успешного выбора канала в расписании"""
    channel_id = channel_info.channel_id
    post = await create_post(channel_id=channel_id)
    await state.update_data(post_id=post.post_id, channel_id=channel_id)
    await state.set_state(AddPost.waiting_for_messages)

    await callback.message.answer(
        SEND_POST_MESSAGES,
        reply_markup=get_post_add_keyboard(True, True),  # TODO get_post_add_keyboard
    )
    await callback.message.delete()


@router.message(F.text == "Add post")
@router.message(Command("add_post"))
async def cmd_add_post(message: Message, state: FSMContext):
    channels = await get_user_channels(message.from_user.id)

    if not channels:
        await message.answer(NO_CHANNELS)
        return

    await state.set_state(AddPost.waiting_for_channel)
    await message.answer(
        SELECT_CHANNEL, reply_markup=get_channels_keyboard(channels, "post")
    )


@router.callback_query(F.data.startswith("post_channel:"))
async def process_channel_selection(callback: CallbackQuery, state: FSMContext):
    await handle_channel_selection(
        callback,
        state,
        AddPost.waiting_for_channel,
        SCHEDULE_SELECT_CHANNEL,
        post_success,
        "post",
    )


@router.message(F.text == "Cancel", StateFilter(AddPost))
async def cancel_post(message: Message, state: FSMContext):
    data = await state.get_data()
    if post_id := data.get("post_id"):
        await delete_post(post_id)
    await state.clear()
    await message.answer("Операция отменена", reply_markup=get_main_keyboard())


@router.message(
    F.text == "Set time",
    StateFilter(AddPost.waiting_for_messages, AddPost.waiting_for_chat_messages),
)
async def set_post_time(message: Message, state: FSMContext):
    if (await state.get_data()).get("msg_channel_count", 0) > 0:
        await state.set_state(AddPost.waiting_for_date)
        await message.answer(SELECT_DATE, reply_markup=await get_calendar_keyboard())
    else:
        await message.answer(
            "Нет сообщений для публикации",
            reply_markup=get_post_add_keyboard(
                True, True
            ),  # TODO get_post_add_keyboard
        )


@router.message(F.text == "Add chat message", StateFilter(AddPost.waiting_for_messages))
async def request_chat_messages(message: Message, state: FSMContext):
    if (await state.get_data()).get("msg_channel_count", 0) > 0:
        await state.set_state(AddPost.waiting_for_chat_messages)
        await message.answer(
            SEND_CHAT_MESSAGES,
            reply_markup=get_post_add_keyboard(
                True, True
            ),  # TODO get_post_add_keyboard
        )
    else:
        await message.answer(
            "Нет сообщений для публикации",
            reply_markup=get_post_add_keyboard(
                True, True
            ),  # TODO get_post_add_keyboard
        )


@router.message(StateFilter(AddPost.waiting_for_messages))
async def process_channel_message(message: Message, state: FSMContext):
    data = await state.get_data()
    post_id = data.get("post_id")
    await state.update_data(msg_channel_count=data.get("msg_channel_count", 0) + 1)

    await add_message_to_post(message=message, post_id=post_id, is_channel_message=True)


@router.message(StateFilter(AddPost.waiting_for_chat_messages))
async def process_chat_message(message: Message, state: FSMContext):
    data = await state.get_data()
    post_id = data.get("post_id")
    await add_message_to_post(
        message=message, post_id=post_id, is_channel_message=False
    )


@router.callback_query(
    SimpleCalendarCallback.filter(), StateFilter(AddPost.waiting_for_date)
)
async def process_calendar(
    callback: CallbackQuery, callback_data: SimpleCalendarCallback, state: FSMContext
):
    selected, date = await SimpleCalendar().process_selection(callback, callback_data)
    if selected:
        await state.update_data(selected_date=date.strftime("%Y-%m-%d"))
        await state.set_state(AddPost.waiting_for_time)
        await callback.message.edit_text(SELECT_TIME, reply_markup=get_time_keyboard())


@router.callback_query(StateFilter(AddPost.waiting_for_time))
async def process_time_selection(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    date_str = data["selected_date"]
    time_str = callback.data.split(":")
    time_str = f"{time_str[1]}:{time_str[2]}"

    date_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

    # Проверяем, что выбранное время не в прошлом
    if date_time <= datetime.now():
        await callback.message.edit_text(
            "Нельзя запланировать пост на прошедшее время. Пожалуйста, выберите будущую дату и время.",
            reply_markup=await get_calendar_keyboard(),
        )
        await state.set_state(AddPost.waiting_for_date)
        return

    post = await update_post_datetime(data["post_id"], date_time)
    scheduler = router.callback_data["scheduler"]
    await scheduler.schedule_post(post.post_id)

    await callback.message.edit_text(POST_SCHEDULED)
    await state.set_state(AddPost.waiting_for_repeat)
    await callback.message.edit_text(
        "Хотите добавить еще один пост в этот канал?",
        reply_markup=get_yes_no_keyboard("add_another_post"),
    )


@router.message(StateFilter(AddPost.waiting_for_time))
async def process_manual_time_selection(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        date_str = data["selected_date"]
        time_str = message.text

        # Пробуем распарсить введенное время
        datetime.strptime(time_str, "%H:%M")  # Проверка формата
        date_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

        # Проверяем, что выбранное время не в прошлом
        if date_time <= datetime.now():
            await message.answer(
                "Нельзя запланировать пост на прошедшее время. Пожалуйста, выберите будущую дату и время.",
                reply_markup=await get_calendar_keyboard(),
            )
            await state.set_state(AddPost.waiting_for_date)
            return

        post = await update_post_datetime(data["post_id"], date_time)
        scheduler = router.callback_data["scheduler"]
        await scheduler.schedule_post(post.post_id)

        await message.answer(POST_SCHEDULED)
        await state.set_state(AddPost.waiting_for_repeat)
        await message.answer(
            "Хотите добавить еще один пост в этот канал?",
            reply_markup=get_yes_no_keyboard("add_another_post"),
        )
    except ValueError:
        await message.answer(
            "Неверный формат времени. Используйте формат ЧЧ:ММ, например: 15:30"
        )


@router.callback_query(F.data == "yes_add_another_post")
async def add_another_post(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    channel_info = ChannelInfo(
        channel_id=data["channel_id"],
        channel_title=None,
        channel_username=None,
        channel_permission=True,
        channel_caption=None,
        chat_id=None,
        chat_title=None,
        chat_username=None,
        chat_permission=True,
        chat_caption=None,
    )
    # Вызываем напрямую функцию успешного создания поста
    await post_success(callback, channel_info, state)


@router.callback_query(F.data == "no_add_another_post")
async def finish_adding_posts(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(WELCOME_MESSAGE, reply_markup=get_main_keyboard())
