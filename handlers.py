# handlers.py

import logging
from os import getenv
from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import Application, CommandHandler, MessageHandler, filters


from user_data_manager import user_data_manager
from creating_new_post import adding_channel_post, adding_media, set_time
from planning_send_posts import send_chat_posts
from setup import process_setup
from utils import check_all_permission, check_scheduled_post, count_scheduled_post
from states import State
from strings import (
    SETTING_TIME,
    CHANNELS_INFO_STRING,
    ERROR,
    ERROR_ACCESS_DENY,
    ERROR_DATA,
    ERROR_WRONG_MESSAGE,
    ERROR_PERMISSIONS,
    COMMAND_HELP,
    COMMAND_START,
    COMMAND_CANCEL,
    COMMAND_CHECKUP,
    COMMAND_SETUP,
    COMMAND_ADD,
    PERMISSION_SUCCESS,
    SETUP_ALREADY,
)

logger = logging.getLogger(__name__)


def register_all_handlers(application):
    # Регистрация команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CommandHandler("checkup", checkup))
    application.add_handler(CommandHandler("setup", setup))
    application.add_handler(CommandHandler("count", count))
    application.add_handler(CommandHandler("check_post", check_post))

    application.add_handler(CommandHandler("add", add))
    application.add_handler(CommandHandler("time", time))

    # Регистрация обработки сообщений
    application.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE & ~filters.COMMAND, bot_private_massage_handlers
        )
    )
    application.add_handler(
        MessageHandler(~filters.COMMAND, bot_reply_messages_from_chat)
    )


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
        user_data_manager.set_state(State.ERROR_DATA)
        return False


# Private message processing (from bot and not command)
async def bot_private_massage_handlers(
    update: Update, context: CallbackContext
) -> None:

    if not check_access(update.message.from_user.id):
        await update.message.reply_text(ERROR_ACCESS_DENY)
        return

    user_id = update.message.from_user.id
    state = user_data_manager.get_state()

    log_processing_info(update, "message")

    if check_data():
        if state == State.CREATING_POST:
            await adding_channel_post(update, context)
            return
        elif state == State.ADDING_MEDIA:
            await adding_media(update, context)
            return
        elif state == State.SETTING_TIMER:
            await set_time(update, context)
            return

    if state == State.ERROR_DATA:
        await update.message.reply_text(ERROR_DATA)
    elif state == State.ERROR_PERMISSION:
        await update.message.reply_text(ERROR_PERMISSIONS)
    elif state == State.ADDING_CHANNEL:
        await process_setup(update, context, True)
    elif state == State.ADDING_CHAT:
        await process_setup(update, context, False)
    else:
        await update.message.reply_text(ERROR_WRONG_MESSAGE)


# Command /start
async def start(update: Update, context: CallbackContext) -> None:
    log_processing_info(update, "/start")
    if not check_access(update.message.from_user.id):
        await update.message.reply_text(ERROR_ACCESS_DENY)
        return

    await update.message.reply_text(COMMAND_START)


# Command /help
async def help(update: Update, context: CallbackContext) -> None:
    log_processing_info(update, "/help")
    if not check_access(update.message.from_user.id):
        await update.message.reply_text(ERROR_ACCESS_DENY)
        return

    await update.message.reply_text(COMMAND_HELP)


# Command /cancel
async def cancel(update: Update, context: CallbackContext) -> None:
    log_processing_info(update, "/cancel")
    if not check_access(update.message.from_user.id):
        await update.message.reply_text(ERROR_ACCESS_DENY)
        return
    logger.info(f"HERE {check_data()}")
    if check_data():
        user_data_manager.reset_state()
    else:
        user_data_manager.set_state(State.ERROR_DATA)
    await update.message.reply_text(COMMAND_CANCEL)


# Command /checkup
async def checkup(update: Update, context: CallbackContext) -> None:
    log_processing_info(update, "/checkup")
    await update.message.reply_text(COMMAND_CHECKUP)
    check = await check_all_permission(update, context)
    if check == True:
        await update.message.reply_text(PERMISSION_SUCCESS)
    else:
        await update.message.reply_text(check)
        user_data_manager.set_state(State.ERROR_PERMISSION)


# Command /setup
async def setup(update: Update, context: CallbackContext) -> None:
    log_processing_info(update, "/setup")
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
    log_processing_info(update, "/add")
    if not check_access(update.message.from_user.id):
        await update.message.reply_text(ERROR_ACCESS_DENY)
        return

    if check_data():
        await checkup(update, context)
        if user_data_manager.get_state() != State.ERROR_PERMISSION:
            user_data_manager.set_state(State.CREATING_POST)
            await update.message.reply_text(COMMAND_ADD)


# Command /time
async def time(update: Update, context: CallbackContext) -> None:
    log_processing_info(update, "/time")
    if not check_access(update.message.from_user.id):
        await update.message.reply_text(ERROR_ACCESS_DENY)
        return

    if user_data_manager.get_state() != State.ADDING_MEDIA:
        await update.message.reply_text(ERROR_WRONG_MESSAGE)
        return

    user_data_manager.set_state(State.SETTING_TIMER)
    await update.message.reply_text(SETTING_TIME(getenv("DATE_FOR_PRINT")))


# Command /check_post
async def check_post(update: Update, context: CallbackContext) -> None:
    log_processing_info(update, "/check_post")
    if not check_access(update.message.from_user.id):
        await update.message.reply_text(ERROR_ACCESS_DENY)
        return

    if check_data():
        if user_data_manager.get_state() == State.IDLE:
            await check_scheduled_post(update, context)
            await update.message.reply_text(
                f"All updated! You have : {count_scheduled_post(context)} posts."
            )
        else:
            await update.message.reply_text(
                "This command work only after use /cancel command."
            )
    else:
        await update.message.reply_text(ERROR_DATA)


# Command /count
async def count(update: Update, context: CallbackContext) -> None:
    log_processing_info(update, "/count")
    if not check_access(update.message.from_user.id):
        await update.message.reply_text(ERROR_ACCESS_DENY)
        return

    if check_data():
        await update.message.reply_text(
            f"You have planned {count_scheduled_post(context)}"
        )

    else:
        await update.message.reply_text(ERROR_DATA)


# Sending post to new channel message's comment
async def bot_reply_messages_from_chat(
    update: Update, context: CallbackContext
) -> None:
    logger.info(f"Were getting new message from chat or channel")
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
        logger.info(f"Were getting new message from chat. Start replying messages")
        await send_chat_posts(update, context)


def log_processing_info(update: Update, type):
    user_id = update.message.from_user.id
    state = user_data_manager.get_state()
    logger.info(
        f"Processing {type} from user_id {user_id}. State: {state}. Check data: {check_data()}"
    )
