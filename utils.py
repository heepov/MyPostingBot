# utils.py

from datetime import datetime
import logging
from collections import defaultdict
import pytz
from telegram import Update
from telegram.ext import CallbackContext
from globals import DATE_TIME_FORMAT
from service_db import State
from telegram import Bot
from action_db import (
    db_get_user_state,
    db_set_user_state,
    db_create_user,
    db_get_user_channels_with_permission,
    db_get_chat_by_channel,
    db_get_all_post_by_channel_id,
    db_get_messages_by_post,
    db_schedule_posts,
)

MOSCOW_TZ = pytz.timezone("Europe/Moscow")


def setup_logging(level=logging.INFO):
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),  # Вывод в консоль
            #     RotatingFileHandler(
            #         "bot.log", maxBytes=5_000_000, backupCount=5, encoding="utf-8"
            #     ),  # Ротация логов
        ],
    )

    # Настроим уровень логирования для httpx
    logging.getLogger("httpx").setLevel(logging.WARNING)


logger = logging.getLogger(__name__)


async def check_bot_permission(bot: Bot, chat_id: int):
    """Проверка, является ли бот администратором канала или чата."""
    try:
        # Получаем список администраторов для чата
        admins = await bot.get_chat_administrators(chat_id)
        bot_id = (await bot.get_me()).id
        for admin in admins:
            if admin.user.id == bot_id:
                return True  # Бот является администратором
        return "Bot isn't an admin."  # Бот не администратор
    except Exception as e:
        logging.error(f"Ошибка при проверке прав бота в чате {chat_id}: {e}")
        return e


def check_link(link):
    if link.startswith("https://t.me/"):
        return "@" + link.split("https://t.me/")[-1]
    elif link.startswith("@"):
        return link
    else:
        return None


async def command_checker(
    update: Update, context: CallbackContext, required_states
) -> bool:
    user = update.effective_user
    db_create_user(user)
    state = db_get_user_state(user.id)
    logger.info(f"STATE {state}")
    if state == None:
        await update.message.reply_text("Shit happened! Use /cancel")
        return False

    if state not in required_states:
        await update.message.reply_text("Finish your current task first!")
        return False
    else:
        return True


def get_channel_string(channels) -> str:
    if len(channels) == 0:
        return f"You dont have any channels"

    str = ""
    i = 1
    for channel in channels:
        str += f"{i} @{channel.username}"
        i += 1
        chat = db_get_chat_by_channel(channel.channel_id)
        if chat != None:
            if chat.permission:
                str += f" connected with chat: @{chat.username}"
            else:
                str += f" cat @{chat.username} error permission!"
        str += f"\n"
    return str


async def cmd_schedule(update: Update, context: CallbackContext):
    if not await command_checker(update, context, [State.IDLE]):
        return

    user = update.effective_user
    channels = db_get_user_channels_with_permission(user.id)

    if len(channels) == 0:
        await update.message.reply_text(
            "You don't have any channels. Use /add_channel first!"
        )
        return

    db_set_user_state(user.id, State.SCHEDULE)

    await update.message.reply_text(
        f"Choose a channel:\n{get_channel_string(channels)}"
    )


def schedule_string(channel_id) -> str:
    posts = db_get_all_post_by_channel_id(channel_id)
    grouped_by_day = {}
    today = datetime.today().date()

    for post in posts:
        post_date = post.date_time.date()

        if post_date < today:
            continue

        post_str = ""
        if post_date not in grouped_by_day:
            grouped_by_day[post_date] = []

        for msg in db_get_messages_by_post(post.post_id):
            if msg.text is not None:
                post_str += msg.text.split()[0]
                break
            if msg.caption is not None:
                post_str += msg.caption.split()[0]
                break
            post_str += "#error_tag"

        grouped_by_day[post_date].append(post_str)

    result = ""
    for date, post_ids in grouped_by_day.items():
        result += f"{date} | {' | '.join(post_ids)}\n"

    return result


async def handle_schedule(update: Update, context: CallbackContext):

    if not await command_checker(update, context, [State.SCHEDULE]):
        return

    user = update.effective_user
    input = update.effective_message.text

    if not input.isdigit():
        await update.message.reply_text(f"Error send normal number or /cancel")
        return

    channels = db_get_user_channels_with_permission(user.id)

    if int(input) > len(channels) or int(input) < 1:
        await update.message.reply_text(f"Error send normal number or /cancel")
        return
    channel = channels[int(input) - 1]
    chat = db_get_chat_by_channel(channel)

    str = f"Channel: @{channel.username} with chat @{chat.username}\n"
    str += schedule_string(channel.channel_id)
    await update.message.reply_text(str)
    db_set_user_state(user.id, State.IDLE)
