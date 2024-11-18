import os
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from dotenv import load_dotenv
import logging
from state_manager import StateManager
from handlers import start, add_post, cancel, add_channel
from new_channel_post import handle_channel_message, set_channel_type, button_callback, set_time, scheduler
from states import State
import json

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Загрузка из файла
def load_channel_posts(file_name):
    if os.path.exists(file_name):
        with open(file_name, 'r') as f:
            return json.load(f)
    return {}

async def handle_text(update, context):
    state_manager = context.bot_data["state_manager"]
    user_id = update.message.from_user.id
    user_state_value = state_manager.get_state(user_id)

    logger.info(f"Обработка сообщения от {user_id}. Состояние: {user_state_value}")

    if user_state_value == State.WAITING_FOR_IMAGE:
        await handle_channel_message(update, context)
    elif user_state_value == State.WAITING_FOR_CHANNEL:
        await set_time(update, context)
    elif user_state_value == State.WAITING_FOR_TIME:
        await set_time(update, context)
    else:
        await update.message.reply_text("Я не понимаю это сообщение. Используйте команду /start для начала работы.")

async def check_channel_post(update, context):
    await update.message.reply_text(update.message)

# Основная функция
def main() -> None:
    global scheduled_channel_posts, current_channel_post
    scheduled_channel_posts = load_channel_posts(os.getenv('CHANNEL_POSTS_FILE'))  # Теперь загружаем посты из файла
    current_channel_post = {}

    # Инициализация приложения и планировщика
    application = Application.builder().token(os.getenv('BOT_TOKEN')).build()
    state_manager = StateManager()
    application.bot_data["state_manager"] = state_manager

    # Планировщик передается в обработчики
    application.bot_data["scheduler"] = scheduler

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add_post", add_post))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CommandHandler("add_channel", add_channel))
    application.add_handler(CommandHandler("set_channel", set_channel_type))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(~filters.COMMAND, check_channel_post))
    
    # Запуск планировщика
    scheduler.start()
    application.run_polling()

if __name__ == '__main__':
    main()