from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="Add channel"), KeyboardButton(text="Add post")],
        [KeyboardButton(text="Channels settings"), KeyboardButton(text="Show schedule")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_channel_add_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="Cancel"), KeyboardButton(text="Instruction")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_post_add_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="Cancel"), KeyboardButton(text="Set time")],
        [KeyboardButton(text="Add chat message")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_post_add_keyboard(has_chat: bool = False, show_chat_button: bool = True) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="Cancel")], 
        [KeyboardButton(text="Set time")]
    ]
    if has_chat and show_chat_button:
        buttons.append([KeyboardButton(text="Add chat message")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
