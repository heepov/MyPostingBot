# handlers.py

from telegram import Update
from telegram.ext import CallbackContext
import logging

from states import State


logger = logging.getLogger(__name__)


async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_data_manager = context.bot_data.get("user_data_manager")
    user_data_manager.reset_state(user_id)
    await update.message.reply_text(
        "Привет! Отправь команду /add_post для добавления поста."
    )


async def add_post(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_data_manager = context.bot_data.get("user_data_manager")
    user_data_manager.set_state(user_id, State.WAITING_CHANNEL_POST)
    await update.message.reply_text(
        "Пожалуйста, отправьте текст вашего поста и прикрепите картинку."
    )


async def add_channel(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_data_manager = context.bot_data.get("user_data_manager")
    user_data_manager.set_state(user_id, State.WAITING_ADD_CHANNEL)

    if not user_data_manager.get_users_channels(user_id):
        await update.message.reply_text("Пожалуйста, ссылку на ваш КАНАЛ.")
    else:
        await update.message.reply_text(
            f"Сейчас у вас подключен:\nКанал @{user_data_manager.get_users_channels(user_id)['channel_username']}\nЧат @{user_data_manager.get_users_channels(user_id)['chat_username']}\nЕсли хотите их поменять отправьте ссылку на ваш КАНАЛ."
        )


async def cancel(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_data_manager = context.bot_data.get("user_data_manager")
    user_data_manager.reset_state(user_id)
    await update.message.reply_text("Вы вышли в главное меню!")


async def end(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_data_manager = context.bot_data.get("user_data_manager")
    user_data_manager.reset_state(user_id)
    await update.message.reply_text("Ваш пост успешно запланирован")
