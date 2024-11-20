# handlers.py

import logging
from os import getenv
from telegram import Update
from telegram.ext import CallbackContext

from user_data_manager import user_data_manager
from new_channel_post import adding_channel_post, set_time
from new_chat_post import schedule_chat_message, send_chat_posts
from setup import process_setup
from utils import check_all_permission
from states import State
from strings import (
    CHANNELS_INFO_STRING,
    ERROR,
    ERROR_ACCESS_DENY,
    ERROR_DATA,
    ERROR_WRONG_MESSAGE,
    ERROR_PERMISSIONS,
    COMMAND_HELP,
    COMMAND_START,
    COMMAND_CANCEL,
    COMMAND_END,
    COMMAND_CHECKUP,
    COMMAND_SETUP,
    COMMAND_ADD,
    PERMISSION_SUCCESS,
    SETUP_ALREADY,
)

logger = logging.getLogger(__name__)


def check_access(user_id):
    return user_id == int(getenv("ADMIN_ID"))


def check_data():
    if (
        user_data_manager.get_state() != State.ERROR_DATA
        and user_data_manager.get_channel_id()
        and user_data_manager.get_chat_id()
    ):
        return True
    else:
        return False


# Private message processing (from bot and not command)
async def private_messages(update: Update, context: CallbackContext) -> None:
    if not check_access(update.message.from_user.id):
        await update.message.reply_text(ERROR_ACCESS_DENY)
        return

    user_id = update.message.from_user.id
    state = user_data_manager.get_state()

    logger.info(
        f"Обработка сообщения от {user_id}. Состояние: {state}. Check data: {check_data()}"
    )

    if check_data():
        if state == State.ADDING_CHANNEL_POST:
            await adding_channel_post(update, context)
            return
        elif state == State.SETTING_TIMER_FOR_CHANNEL_POST:
            await set_time(update, context)
            return
        # TODO тут надо обрабатывать не только медиа групп но и одиночные сообщения
        elif update.message.media_group_id and state == State.ADDING_CHAT_POSTS:
            await schedule_chat_message(update, context)
            return

    if state == State.ERROR_DATA:
        await update.message.reply_text(ERROR_DATA)
        return
    elif state == State.ERROR_PERMISSION:
        await update.message.reply_text(ERROR_PERMISSIONS)
        return
    elif state == State.ADDING_CHANNEL:
        await process_setup(update, context, True)
        return
    elif state == State.ADDING_CHAT:
        await process_setup(update, context, False)
        return
    else:
        await update.message.reply_text(ERROR_WRONG_MESSAGE)
        return


# Sending post to new channel message's comment
async def reply_post(update: Update, context: CallbackContext) -> None:
    try:
        if (
            not update.message
            or user_data_manager.get_state() == State.ERROR_DATA
            or update.message.reply_to_message
            or update.message.from_user.first_name != "Telegram"
        ):
            return
    except Exception as e:
        logger.error(e)
        return
    if update.message.photo and len(update.message.photo) > 0:
        channel_post_photo_id = update.message.photo[-1].file_id
        await send_chat_posts(update, context, channel_post_photo_id)


# Command /start
async def start(update: Update, context: CallbackContext) -> None:
    if not check_access(update.message.from_user.id):
        await update.message.reply_text(ERROR_ACCESS_DENY)
        return

    await update.message.reply_text(COMMAND_START)


# Command /help
async def help(update: Update, context: CallbackContext) -> None:
    if not check_access(update.message.from_user.id):
        await update.message.reply_text(ERROR_ACCESS_DENY)
        return

    await update.message.reply_text(COMMAND_HELP)


# Command /cancel
async def cancel(update: Update, context: CallbackContext) -> None:
    if not check_access(update.message.from_user.id):
        await update.message.reply_text(ERROR_ACCESS_DENY)
        return

    if check_data():
        user_data_manager.reset_state()
    else:
        user_data_manager.set_state(State.ERROR_DATA)
    await update.message.reply_text(COMMAND_CANCEL)


# Command /end
async def end(update: Update, context: CallbackContext) -> None:
    if not check_access(update.message.from_user.id):
        await update.message.reply_text(ERROR_ACCESS_DENY)
        return

    if user_data_manager.get_state() != State.ADDING_CHAT_POSTS:
        await update.message.reply_text(ERROR_WRONG_MESSAGE)
        return

    await update.message.reply_text(COMMAND_END)
    user_data_manager.reset_state()


# Command /checkup
async def checkup(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(COMMAND_CHECKUP)
    check = await check_all_permission(update, context)
    if check == True:
        await update.message.reply_text(PERMISSION_SUCCESS)
    else:
        await update.message.reply_text(check)
        user_data_manager.set_state(State.ERROR_PERMISSION)


# Command /setup
async def setup(update: Update, context: CallbackContext) -> None:

    if not check_access(update.message.from_user.id):
        await update.message.reply_text(ERROR_ACCESS_DENY)
        return

    user_data_manager.set_state(State.ADDING_CHANNEL)

    if check_data():
        channel_username = user_data_manager.get_channel_id()
        chat_username = user_data_manager.get_chat_id()

        try:
            info = await context.bot.get_chat(channel_username)
            channel_username = info.username
            info = await context.bot.get_chat(chat_username)
            chat_username = info.username
        except Exception as e:
            logger.error({e})

        await update.message.reply_text(
            f"{CHANNELS_INFO_STRING(channel_username, chat_username)}\n{SETUP_ALREADY}"
        )
    else:
        chat_id = update.effective_chat.id
        await context.bot.send_message(chat_id=chat_id, text=COMMAND_SETUP)


# Command /add
async def add(update: Update, context: CallbackContext) -> None:
    if not check_access(update.message.from_user.id):
        await update.message.reply_text(ERROR_ACCESS_DENY)
        return

    if check_data():
        await checkup(update, context)
        if user_data_manager.get_state() != State.ERROR_PERMISSION:
            user_data_manager.set_state(State.ADDING_CHANNEL_POST)
            await update.message.reply_text(COMMAND_ADD)
