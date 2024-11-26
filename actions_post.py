# actions_post.py

from collections import defaultdict
import logging
from datetime import datetime
import pytz
import uuid

from utils import command_checker, get_channel_string

from telegram import (
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
    Update,
)
from telegram.ext import CallbackContext, CommandHandler
from telegram.helpers import effective_message_type
from globals import DATE_TIME_FORMAT_PRINT, DATE_TIME_FORMAT
from send_post_logic import set_post_in_scheduler
from service_db import State, Post, Message
from action_db import (
    db_get_user_state,
    db_create_user,
    db_get_selected_channel,
    db_get_chat_by_channel,
    db_set_user_state,
    db_get_user_channels_with_permission,
    db_set_selected_channel,
    db_create_post,
    db_get_channel,
)

MOSCOW_TZ = pytz.timezone("Europe/Moscow")

logger = logging.getLogger(__name__)
current_posts = {}

MEDIA_GROUP_TYPES = {
    "photo": InputMediaPhoto,
    "video": InputMediaVideo,
    "document": InputMediaDocument,
    "audio": InputMediaAudio,
}


async def handle_post_messages(update: Update, context: CallbackContext) -> None:

    if not await command_checker(
        update,
        context,
        [
            State.SET_CHANNEL,
            State.ADD_POST,
            State.ADD_POST_CHAT,
            State.SET_POST_TIME,
        ],
    ):
        return

    user = update.effective_user
    state = db_get_user_state(user.id)

    if state == State.ADD_POST:
        await handle_add_message(update, context, "channel")
    elif state == State.ADD_POST_CHAT:
        await handle_add_message(update, context, "chat")
    elif state == State.SET_POST_TIME:
        await handle_set_post_time(update, context)
    elif state == State.SET_CHANNEL:
        await handle_set_channel(update, context)
    else:
        await update.message.reply_text("Shit happened! Use /cancel")


async def cmd_add_post(update: Update, context: CallbackContext) -> None:
    if not await command_checker(update, context, [State.IDLE]):
        return

    user = update.effective_user
    if user.id in current_posts:
        del current_posts[user.id]

    channel = db_get_selected_channel(user.id)

    if channel == None:
        db_set_user_state(user.id, State.SET_CHANNEL)
        await cmd_set_channel(update, context)
        return

    if channel.permission == False:
        await update.message.reply_text("Your channel doesn't have permissions")
        return

    str = f"Your choose channel @{channel.username}"

    chat = db_get_chat_by_channel(channel.channel_id)
    if chat != None:
        if chat.permission:
            str += f" with chat @{chat.username}"

    await update.message.reply_text(f"{str}\nSend me your new Cannel Posts.")
    db_set_user_state(user.id, State.ADD_POST)


async def cmd_add_post_chat(update: Update, context: CallbackContext) -> None:
    if not await command_checker(
        update, context, [State.ADD_POST, State.ADD_POST_CHAT]
    ):
        return

    user = update.effective_user
    if user.id not in current_posts:
        await update.message.reply_text("First of all you need start adding new post")
        return

    post = current_posts[user.id]["post"]

    chat = db_get_chat_by_channel(post.channel_id)

    if chat == None:
        await update.message.reply_text("Your channel doesn't have connected chat")
        return
    if not chat.permission:
        await update.message.reply_text("Your chat doesn't have permissions")
    channel = db_get_channel(post.user_id, post.channel_id)
    str = f"Your are posting to channel @{channel.username} with chat @{chat.username}"

    await update.message.reply_text(f"{str}\nSend me your new Chat Posts.")
    db_set_user_state(user.id, State.ADD_POST_CHAT)


async def cmd_post_time(update: Update, context: CallbackContext) -> None:
    if not await command_checker(
        update, context, [State.ADD_POST_CHAT, State.SET_POST_TIME, State.ADD_POST]
    ):
        return
    user = update.effective_user
    if user.id not in current_posts:
        await update.message.reply_text("First of all you need start adding new post")
        return

    await update.message.reply_text(
        f"Now send the date and time in this format: {DATE_TIME_FORMAT_PRINT}."
    )
    db_set_user_state(user.id, State.SET_POST_TIME)


async def cmd_set_channel(update: Update, context: CallbackContext):
    if not await command_checker(update, context, [State.IDLE, State.SET_CHANNEL]):
        return
    user = update.effective_user
    if user.id in current_posts:
        del current_posts[user.id]
    channels = db_get_user_channels_with_permission(user.id)

    if channels == []:
        await update.message.reply_text(f"You dont have any channels")
        return

    await update.message.reply_text(
        f"Chose the channel:\n{await get_channel_string(channels)}\n And send me number or /cancel"
    )
    db_set_user_state(user.id, State.SET_CHANNEL)


async def handle_set_channel(update: Update, context: CallbackContext):
    if not await command_checker(update, context, [State.SET_CHANNEL]):
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

    await update.message.reply_text(
        f"You choose channel: @{channels[int(input) - 1].username}"
    )

    db_set_selected_channel(channels[int(input) - 1].channel_id, user.id)
    db_set_user_state(user.id, State.ADD_POST)
    await cmd_add_post(update, context)


# Получение основного поста
async def handle_add_message(update: Update, context: CallbackContext, type) -> None:
    global current_posts
    if not await command_checker(
        update, context, [State.ADD_POST, State.ADD_POST_CHAT]
    ):
        return
    user = update.effective_user
    input = update.effective_message
    media_type = effective_message_type(input)

    if type == "channel":
        if user.id not in current_posts:
            current_posts[user.id] = {}
        current_posts[user.id]["post"] = Post(
            post_id=uuid.uuid4(),
            user_id=user.id,
            channel_id=db_get_selected_channel(user.id).channel_id,
        )
        logger.info(f"{current_posts}")
    else:
        if current_posts[user.id] == None:
            await update.message.reply_text(
                "First of all you need start adding new post"
            )
            return
    data: Message
    if media_type == "text":
        data = Message(
            message_id=input.message_id,
            post_id=current_posts[user.id]["post"].post_id,
            text=input.text if input.text else "",
            is_channel_message=True if type == "channel" else False,
        )
        logger.info(f"{data.to_dict()}")
    else:
        file_id = (
            input.photo[-1].file_id
            if input.photo
            else input.effective_attachment.file_id
        )
        data = Message(
            post_id=current_posts[user.id]["post"].post_id,
            caption=input.caption if input.caption else "",
            is_channel_message=True if type == "channel" else False,
            file_type=media_type,
            file_id=file_id,
            media_group_id=input.media_group_id if input.media_group_id else None,
        )

    if "messages" not in current_posts[user.id]:
        current_posts[user.id]["messages"] = [data]
    else:
        current_posts[user.id]["messages"].append(data)


async def handle_set_post_time(update: Update, context: CallbackContext) -> None:
    if not await command_checker(update, context, [State.SET_POST_TIME]):
        return
    user = update.effective_user
    input = update.effective_message.text

    if current_posts[user.id] == None:
        await update.message.reply_text("First of all you need start adding new post")
        return

    try:
        input = input.strip()
        post_time = MOSCOW_TZ.localize(datetime.strptime(input, DATE_TIME_FORMAT))
        if post_time < datetime.now(MOSCOW_TZ):
            await update.message.reply_text("We cant back to past. Try again")
            return
        current_posts[user.id]["post"].date_time = post_time
    except ValueError:
        logger.info(f"{input}")
        await update.message.reply_text("Wrong date format. Try again")
        return
    post_db = db_create_post(
        current_posts[user.id]["post"], current_posts[user.id]["messages"]
    )
    del current_posts[user.id]

    await set_post_in_scheduler(update, context, post_db)
    db_set_user_state(user.id, State.IDLE)
