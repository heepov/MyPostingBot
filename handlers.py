# handlers.py

from telegram import Update
from telegram.ext import CallbackContext
import logging
from states import State

logger = logging.getLogger(__name__)


async def start(update: Update, context: CallbackContext) -> None:
    state_manager = context.bot_data["state_manager"]
    state_manager.set_state(update.message.from_user.id, State.IDLE)
    await update.message.reply_text("Привет! Отправь команду /add_post для добавления поста.")

async def add_post(update: Update, context: CallbackContext) -> None:
    state_manager = context.bot_data["state_manager"]
    state_manager.set_state(update.message.from_user.id, State.WAITING_CHANNEL_POST)
    await update.message.reply_text("Пожалуйста, отправьте текст вашего поста и прикрепите картинку.")

async def cancel(update: Update, context: CallbackContext) -> None:
    state_manager = context.bot_data["state_manager"]
    state_manager.reset_state(update.message.from_user.id)
    await update.message.reply_text("Вы вышли в главное меню!")

# async def add_channel(update: Update, context: CallbackContext) -> None:
#     state_manager = context.bot_data["state_manager"]
#     state_manager.set_state(update.message.from_user.id, State.WAITING_ADD_CHANNEL)
#     await update.message.reply_text("Пожалуйста, ссылку на ваш КАНАЛ.")