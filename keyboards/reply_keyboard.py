from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import logging

logger = logging.getLogger(__name__)


def make_two_rows_keyboard(items: list[str]) -> ReplyKeyboardMarkup:
    mid = len(items) // 2
    row1 = [KeyboardButton(text=item) for item in items[:mid]]
    row2 = [KeyboardButton(text=item) for item in items[mid:]]
    return ReplyKeyboardMarkup(keyboard=[row1, row2], resize_keyboard=True)


def make_one_line_keyboard(items: list[str]) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=item) for item in items]], resize_keyboard=True
    )
