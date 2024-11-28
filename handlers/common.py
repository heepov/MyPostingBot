from aiogram import F, Router, Bot
from aiogram.filters import Command, StateFilter
from aiogram.filters.logic import or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup, default_state
from aiogram.types import Message, ReplyKeyboardRemove
import logging

from db.db import db_add_model
from db.models import User
from keyboards.reply_keyboard import make_two_rows_keyboard
from utils.app_strings import MAIN_MENU_BTN, CMD_START, CMD_CANCEL, STR_CANCEL
from utils.strings import MSG_START

logger = logging.getLogger(__name__)
router = Router()


async def add_new_user(message: Message, state: FSMContext, bot: Bot) -> None:
    user = message.from_user
    if user.id == bot.id:
        return

    user_db = User(
        user_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
        language_code=user.language_code,
    )
    db_add_model(user_db)


@router.message(Command(commands=[CMD_START]))
async def cmd_start(message: Message, state: FSMContext, bot: Bot) -> None:
    await state.clear()
    await message.answer(
        text=MSG_START,
        reply_markup=make_two_rows_keyboard(MAIN_MENU_BTN),
    )
    await add_new_user(message, state, bot)


@router.message(or_f(*[F.text == text for text in STR_CANCEL]))
@router.message(Command(CMD_CANCEL))
async def cmd_cancel(message: Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    user_state = await state.get_state()
    # state.set_state(None)
    logger.info(f"STATE BEFORE CLEAR: {user_state} DATA: {data}")
    await state.clear()
    logger.info(
        f"STATE AFTER CLEAR: {await state.get_data()} DATA: {await state.get_state()}"
    )
    await cmd_start(message, state, bot)
