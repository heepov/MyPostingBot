import logging
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

logger = logging.getLogger(__name__)


def make_inline_binary_keyboard(
    callback_data_yes: str, callback_data_no: str
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Yes", callback_data=callback_data_yes)],
            [InlineKeyboardButton(text="No", callback_data=callback_data_no)],
        ]
    )
