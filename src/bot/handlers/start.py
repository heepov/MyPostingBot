from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.bot.keyboards import get_main_keyboard
from src.bot.strings import WELCOME_MESSAGE
from src.services import add_or_update_user

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    user = await add_or_update_user(
        user_id=message.from_user.id,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        username=message.from_user.username,
        language_code=message.from_user.language_code,
    )

    await message.answer(text=WELCOME_MESSAGE, reply_markup=get_main_keyboard())
