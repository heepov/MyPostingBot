from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def make_two_rows_keyboard(items: list[str]) -> ReplyKeyboardMarkup:
    """
    Создаёт реплай-клавиатуру с кнопками в один ряд
    :param items: список текстов для кнопок
    :return: объект реплай-клавиатуры
    """
    mid = len(items) // 2
    row1 = [KeyboardButton(text=item) for item in items[:mid]]
    row2 = [KeyboardButton(text=item) for item in items[mid:]]
    return ReplyKeyboardMarkup(keyboard=[row1, row2], resize_keyboard=True)

def make_one_line_keyboard(items: list[str]) -> ReplyKeyboardMarkup:
    """
    Создаёт реплай-клавиатуру с кнопками в один ряд.
    """
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=item) for item in items]], resize_keyboard=True)
