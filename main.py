# main.py

import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv
import logging
from states import State, get_user_state
from telegram import User
from apscheduler.schedulers.background import BackgroundScheduler
from telegram.ext import ContextTypes

from user_data_manager import UserDataManager
from handlers import start, add, setup, cancel, end, checkup, menu
from new_channel_post import handle_channel_message, set_time
from add_channel import add_channel_link, add_chat_link
from new_chat_post import media_group_message, send_chat_posts
from file_service import load_file

import logging


# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()


async def handle_text(update, context):
    user_id = update.message.from_user.id
    # user_data_manager = context.bot_data.get("user_data_manager")
    # user_state_value = user_data_manager.get_state(user_id)
    user_state_value = get_user_state(context)

    logger.info(f"Обработка сообщения от {user_id}. Состояние: {user_state_value}")

    if user_state_value == State.WAITING_CHANNEL_POST:
        await handle_channel_message(update, context)
    elif user_state_value == State.WAITING_TIME_FOR_CHANNEL_POST:
        await set_time(update, context)
    elif update.message.media_group_id and user_state_value == State.WAITING_CHAT_POSTS:
        await media_group_message(update, context)
    elif user_state_value == State.WAITING_ADD_CHANNEL:
        await add_channel_link(update, context)
    elif user_state_value == State.WAITING_ADD_CHAT:
        await add_chat_link(update, context)
    else:
        await update.message.reply_text(
            "Я не понимаю это сообщение. Используйте команду /start для начала работы."
        )


# async def handle_reply_to_chat(update, context):
#     logger.info("!!!handle_reply_to_chat!!!")
#     if (
#         not update.message.reply_to_message
#         and update.message.from_user.first_name == "Telegram"
#         and update.message.chat.id == context.bot_data["user_chat"].get("chat_id")
#     ):
#         logger.info(str(update.message))
#         this_photo_id = update.message.photo[-1].file_id
#         if this_photo_id in load_file(os.getenv("CHAT_POSTS_FILE")):
#             # await send_chat_posts(update, context, this_photo_id)
#             await send_chat_posts(update, context)
async def handle_reply_to_chat(update, context):
    logger.info("!!!handle_reply_to_chat!!!")

    # Проверяем, что `update.message` не равно `None`
    if not update.message:
        logger.warning("Сообщение отсутствует в обновлении.")
        return

    # Проверяем, что `reply_to_message` отсутствует
    if (
        not update.message.reply_to_message
        and update.message.from_user.first_name == "Telegram"
        and update.message.chat.id
        == context.bot_data.get("user_chat", {}).get("chat_id")
    ):
        logger.info(str(update.message))

        # Проверяем, что `photo` существует и не пустой
        if update.message.photo and len(update.message.photo) > 0:
            this_photo_id = update.message.photo[-1].file_id

            # Проверяем наличие `this_photo_id` в файле
            if this_photo_id in load_file(os.getenv("CHAT_POSTS_FILE")):
                await send_chat_posts(update, context)
        else:
            logger.warning("Фото в сообщении отсутствует.")


# Основная функция
def main() -> None:
    # Инициализация приложения и планировщика
    application = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    scheduler = BackgroundScheduler()
    application.bot_data["scheduler"] = scheduler
    application.bot_data["user_data_manager"] = UserDataManager()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add))
    application.add_handler(CommandHandler("setup", setup))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CommandHandler("end", end))
    application.add_handler(CommandHandler("checkup", checkup))
    application.add_handler(CommandHandler("menu", menu))

    # try:
    #     application.add_handler(
    #         MessageHandler(
    #             filters.Chat(application.bot_data["user_chat"].get("chat_id"))
    #             & ~filters.COMMAND,
    #             handle_reply_to_chat,
    #         )
    #     )
    # except Exception as e:
    #     logger.error(f"Error: {e}")
    application.add_handler(
        MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, handle_text)
    )
    application.add_handler(MessageHandler(~filters.COMMAND, handle_reply_to_chat))
    # Запуск планировщика
    scheduler.start()

    application.run_polling()


if __name__ == "__main__":
    main()
