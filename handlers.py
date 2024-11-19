# handlers.py

from telegram import Update
from telegram.ext import CallbackContext
import logging

from states import State, set_user_state, reset_user_state
from user_setup import check_user_data

logger = logging.getLogger(__name__)


async def start(update: Update, context: CallbackContext) -> None:
    if await check_user_data(update, context):
        await update.message.reply_text(
            "Привет! Отправь команду /menu для просмотра всех команд."
        )
        reset_user_state(context)
    else:
        await setup(update, context)


async def add(update: Update, context: CallbackContext) -> None:
    set_user_state(context, State.WAITING_CHANNEL_POST)
    await update.message.reply_text(
        "Пожалуйста, отправьте текст вашего поста и прикрепите картинку."
    )


async def setup(update: Update, context: CallbackContext) -> None:
    set_user_state(context, State.WAITING_ADD_CHANNEL)
    if not all(
        [
            context.bot_data["user_channel"].get("channel_id"),
            context.bot_data["user_channel"].get("channel_username"),
            context.bot_data["user_chat"].get("chat_id"),
            context.bot_data["user_chat"].get("chat_username"),
        ]
    ):
        await update.message.reply_text("Пожалуйста, ссылку на ваш КАНАЛ.")
    else:
        await update.message.reply_text(
            f"""
Сейчас у вас подключены:
Канал..@{context.bot_data["user_channel"].get("channel_username")}
Чат....@{context.bot_data["user_chat"].get("chat_username")}\n
Если хотите их поменять отправьте ссылку на ваш КАНАЛ иначе используйте команду /cancel"""
        )


async def cancel(update: Update, context: CallbackContext) -> None:
    reset_user_state(context)
    await update.message.reply_text("Все операции прерваны!")


async def end(update: Update, context: CallbackContext) -> None:
    reset_user_state(context)
    await update.message.reply_text("Ваш пост успешно запланирован!")


async def checkup(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(f"Проверка каналов пользователя...")
    await check_user_data(update, context)


async def menu(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        f"""
Меню:
/add - добавить новый пост
/setup - подключить каналы
/checkup - проверить подключенные каналы
/menu - посмотреть все доступные команды
/cancel - сброс любой операции
        """
    )
