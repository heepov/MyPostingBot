# user_setup.py
import os
from file_service import load_file
from utils import check_if_bot_is_admin
from states import State

async def check_user_data(update, context):
    context.bot_data["user_id"] = update.message.from_user.id
    user_data_file = load_file(os.getenv("USER_CHANNELS_FILE"))

    # Проверка наличия всех необходимых данных в user_data_file
    if not all(
        [
            user_data_file.get("channel_id"),
            user_data_file.get("channel_username"),
            user_data_file.get("chat_id"),
            user_data_file.get("chat_username"),
        ]
    ):
        await update.message.reply_text(f"Вам необходимо добавить канал и чат")
        context.bot_data["user_state"] = State.WAITING_ADD_CHANNEL
        return False

    # Сохранение данных в контексте
    context.bot_data["user_channel"] = {
        "channel_id": user_data_file["channel_id"],
        "channel_username": user_data_file["channel_username"],
    }
    context.bot_data["user_chat"] = {
        "chat_id": user_data_file["chat_id"],
        "chat_username": user_data_file["chat_username"],
    }

    # Проверка прав бота в канале и чате
    if await check_if_bot_is_admin(
        context.bot, context.bot_data["user_channel"]["channel_id"]
    ):
        if await check_if_bot_is_admin(
            context.bot, context.bot_data["user_chat"]["chat_id"]
        ):
            context.bot_data["user_state"] = State.IDLE
            await update.message.reply_text(f"Проверка выполнена успешно")
            return True
        else:
            return await handle_permission_error(update, context, "chat")
    else:
        return await handle_permission_error(update, context, "channel")


# Обрабатывает ошибку, если бот не является администратором в канале или чате.
async def handle_permission_error(update, context, entity_type):
    channel_or_chat = (
        context.bot_data["user_channel"]
        if entity_type == "channel"
        else context.bot_data["user_chat"]
    )
    await update.message.reply_text(
        f"Бот не добавлен либо не имеет нужных прав в {entity_type} {channel_or_chat['channel_username'] if entity_type == 'channel' else channel_or_chat['chat_username']}"
    )
    context.bot_data["user_state"] = State.WAITING_ADD_CHANNEL
    return False
