# actions_post.py

import logging
from collections import defaultdict
from datetime import datetime

from telegram import (
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
    Update,
)
from telegram.ext import CallbackContext, CommandHandler
from telegram.helpers import effective_message_type

from actions_chat import get_channel_string
from actions_user import get_user_data
from secret import DATE_TIME_FORMAT
from globals import DATE_TIME_FORMAT_PRINT, save_user_data_to_file
from message import Message
from post import Post
from states import State
from user_data import Channel
from utils import log_processing_info

logger = logging.getLogger(__name__)
tmp_post = Post()
tmp_chat = Channel()

MEDIA_GROUP_TYPES = {
    "photo": InputMediaPhoto,
    "video": InputMediaVideo,
    "document": InputMediaDocument,
    "audio": InputMediaAudio,
}


def reg_post_handlers(application) -> None:
    # application.add_handler(CommandHandler("posts", cmd_posts))
    application.add_handler(CommandHandler("add_post", cmd_add_post))
    application.add_handler(CommandHandler("add_post_chat", cmd_add_post_chat))
    application.add_handler(CommandHandler("time", cmd_post_time))
    application.add_handler(CommandHandler("set_channel", cmd_set_channel))


async def actions_post_handlers(update: Update, context: CallbackContext) -> None:
    user = await get_user_data(update)
    state = user.state

    if state == State.ADD_POST:
        await add_message(update, context, "channel")
    elif state == State.ADD_POST_CHAT:
        await add_message(update, context, "chat")
    elif state == State.SET_POST_TIME:
        await set_post_time(update, context)
    elif state == State.SET_CHANNEL:
        await set_channel(update, context)
    else:
        await update.message.reply_text("Shit happened! Use /cancel")


async def state_check(update: Update, context: CallbackContext, state_list) -> bool:
    user = await get_user_data(update)

    if user.state not in state_list and user.state != State.ERROR:
        await update.message.reply_text(f"Finish you current task {user.state}")
        return False

    elif user.state == State.ERROR or not user.user_has_channel_with_permission():
        await update.message.reply_text(
            "You dont have any channels or channel have not required permissions"
        )
        return False

    else:
        return True


async def cmd_add_post(update: Update, context: CallbackContext) -> None:
    global tmp_post
    user = await get_user_data(update)
    await log_processing_info(update, "command /add_post")

    if not await state_check(update, context, [State.IDLE, State.ADD_POST]):
        return
    if tmp_chat.channel_id == None:
        await cmd_set_channel(update, context)
        return

    tmp_post = Post(
        post_id=update.message.message_id,
        user_id=user.user_id,
        channel_id=tmp_chat.channel_id,
        chat_id=tmp_chat.chat_id,
        date_time=update.message.date,
    )
    user.state = State.ADD_POST
    try:
        info = await context.bot.get_chat(tmp_chat.channel_id)
        username = info.username
        await update.message.reply_text(
            f"You create post to @{username}.\nSend me your new Cannel Post. Or use /add_post_chat or /cancel"
        )
        return
    except Exception as e:
        logger.error({e})

    await update.message.reply_text("Shit happened! Use /cancel")


async def cmd_add_post_chat(update: Update, context: CallbackContext) -> None:
    user = await get_user_data(update)
    await log_processing_info(update, "command /add_post_chat")

    if not await state_check(update, context, [State.ADD_POST_CHAT, State.ADD_POST]):
        return
    if tmp_post.file_id == None:
        await update.message.reply_text(
            "You cant send chat messages to this post. Or use /time or /cancel"
        )
        user.state = State.SET_POST_TIME
        await cmd_post_time(update, context)
        return

    user.state = State.ADD_POST_CHAT
    await update.message.reply_text(
        "Send me your Chat messages. Or use /time or /cancel"
    )


async def cmd_post_time(update: Update, context: CallbackContext) -> None:
    user = await get_user_data(update)
    await log_processing_info(update, "command /time")

    if not await state_check(
        update, context, [State.ADD_POST_CHAT, State.SET_POST_TIME]
    ):
        return

    user.state = State.SET_POST_TIME
    await update.message.reply_text(
        f"Now send the date and time in this format: {DATE_TIME_FORMAT_PRINT}."
    )


async def cmd_set_channel(update: Update, context: CallbackContext):
    user = await get_user_data(update)
    await log_processing_info(update, "command /set_channel")
    if not await state_check(update, context, [State.IDLE, State.SET_CHANNEL]):
        return

    if user.channels == []:
        await update.message.reply_text(f"You dont have any channels")
        return
    await update.message.reply_text(
        f"Chose the channel:\n{await get_channel_string(update, context)}\n And send me number or /cancel"
    )
    user.state = State.SET_CHANNEL


async def set_channel(update: Update, context: CallbackContext):
    global tmp_chat
    user = await get_user_data(update)
    input = update.message.text.strip()
    if not input.isdigit():
        await update.message.reply_text(f"Error send normal number or /cancel")
        return

    if int(input) > len(user.channels) or int(input) < 1:
        await update.message.reply_text(f"Error send normal number or /cancel")
        return

    tmp_chat = user.channels[int(input) - 1]
    await update.message.reply_text(f"Noice CHOOSE CHANNEL")
    user.state = State.ADD_POST
    await cmd_add_post(update, context)


# Получение основного поста
async def add_message(update: Update, context: CallbackContext, type) -> None:
    user = await get_user_data(update)
    input = update.effective_message
    media_type = effective_message_type(input)

    if media_type == "text":
        message = Message(
            text=input.text,
            date_time=input.date,
            message_id=input.message_id,
            user_id=input.from_user.id,
        )
    else:
        file_id = (
            input.photo[-1].file_id
            if input.photo
            else input.effective_attachment.file_id
        )
        message = Message(
            caption=input.caption if input.caption else "",  # TODO
            date_time=input.date,
            message_id=input.message_id,
            user_id=input.from_user.id,
            file_type=media_type,
            file_id=file_id,
            media_group_id=(input.media_group_id if input.media_group_id else None),
        )

        if type == "channel":
            tmp_post.file_id = file_id

    tmp_post.add_message(message=message, channel_type=type)


# Получение основного поста
async def set_post_time(update: Update, context: CallbackContext) -> None:
    user = await get_user_data(update)
    try:
        input = update.message.text.strip()
        post_time = datetime.strptime(input, DATE_TIME_FORMAT)

        if post_time < datetime.now():
            await update.message.reply_text("We cant back to past. Try again")
            return
        tmp_post.date_time = post_time

        tmp_post.update_job_name()
        user.post = tmp_post

    except ValueError:
        logger.info(f"{input}")
        await update.message.reply_text("Wrong date format. Try again")
    await set_post_in_scheduler(update, context, tmp_post)
    user.state = State.IDLE


async def set_post_in_scheduler(
    update: Update, context: CallbackContext, post: Post
) -> None:
    my_job_queue = context.job_queue
    i = 0
    dict = {}
    for p in post.channel_message:
        dict[i] = p.to_dict()
        i += 1

    if not my_job_queue.get_jobs_by_name(post.job_name):
        my_job_queue.run_once(
            send_post,
            when=post.date_time,
            data=dict,
            name=post.job_name,
        )

    logger.info(f"{my_job_queue.get_jobs_by_name(post.job_name)[0].data}")


async def send_post(update: Update, context: CallbackContext):
    data = context.job.data
    logger.info(f"JOB DATA {data}")
    # grouped_media_channel = defaultdict(list)
    # grouped_media_chat = defaultdict(list)

    # for msg in tmp_post.channel_message:
    #     if msg.file_type is not None:
    #         media_type = MEDIA_GROUP_TYPES[msg.file_type]
    #         media_item = media_type(media=msg.file_id, caption=msg.caption)
    #         grouped_media_channel[msg.media_group_id].append(media_item)

    # # Группируем медиа для чатов
    # for msg in tmp_post.chat_message:
    #     if msg.file_type is not None:
    #         media_type = MEDIA_GROUP_TYPES[msg.file_type]
    #         media_item = media_type(media=msg.file_id, caption=msg.caption)
    #         grouped_media_chat[msg.media_group_id].append(media_item)

    # logger.info(f"{grouped_media_channel}")

    # for channel_msg in tmp_post.channel_message:
    #     if channel_msg.file_type == None:
    #         await context.bot.send_message(
    #             chat_id=tmp_chat.channel_id, text=channel_msg.text
    #         )
    # for chat_msg in tmp_post.chat_message:
    #     if chat_msg.file_type == None:
    #         await context.bot.send_message(chat_id=tmp_chat.chat_id, text=chat_msg.text)
    # # Отправляем группы медиа для каналов
    # for media_group in grouped_media_channel.values():
    #     await context.bot.send_media_group(
    #         chat_id=tmp_chat.channel_id,
    #         media=media_group,  # Передаём список объектов InputMedia
    #         read_timeout=20,
    #         write_timeout=35,
    #     )

    # # Отправляем группы медиа для чатов
    # for media_group in grouped_media_chat.values():
    #     await context.bot.send_media_group(
    #         chat_id=tmp_chat.chat_id,
    #         media=media_group,  # Передаём список объектов InputMedia
    #         read_timeout=20,
    #         write_timeout=35,
    #     )
