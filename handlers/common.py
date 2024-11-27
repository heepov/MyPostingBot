from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup, default_state
from aiogram.types import Message, ReplyKeyboardRemove
import logging

from db.db import db_add_user
from db.models import User
from keyboards.simple_row import make_two_rows_keyboard

logger = logging.getLogger(__name__)
router = Router()

menu_buttons = ["Add post", "Channel settings", "Show posts", "Add channel"]


async def add_new_user(message: Message, state: FSMContext) -> None:
    user = message.from_user
    user_db = User(
        user_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
        language_code=user.language_code,
    )

    db_add_user(user_db)


@router.message(Command(commands=["start"]))
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        text=f"/help – полезная информация и техподдержка\n/cancel – отменить действие",
        reply_markup=make_two_rows_keyboard(menu_buttons),
    )
    await add_new_user(message, state)


@router.message(Command(commands=["menu"]))
async def cmd_main_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        text=f"Lest's do some JOB!",
        reply_markup=make_two_rows_keyboard(menu_buttons),
    )


@router.message(F.text == "Cancel")
@router.message(F.text == "Dont add channel")
@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    user_state = await state.get_state()

    await message.answer(f"STATE {user_state}")

    await state.clear()
    await cmd_main_menu(message, state)
