# main.py

import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv
import logging
from states import State
from apscheduler.schedulers.background import BackgroundScheduler

from user_data_manager import UserDataManager
from handlers import start, add_post, cancel
from new_channel_post import handle_channel_message, set_time
from file_service import load_file


# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Создаем объект планировщика
# scheduler = BackgroundScheduler()

async def handle_text(update, context):
    user_id = update.message.from_user.id
    user_data_manager = context.bot_data.get("user_data_manager")
    user_state_value = user_data_manager.get_state(user_id)

    logger.info(f"Обработка сообщения от {user_id}. Состояние: {user_state_value}")

    if user_state_value == State.WAITING_CHANNEL_POST:
        await handle_channel_message(update, context)
    elif user_state_value == State.WAITING_TIME_FOR_CHANNEL_POST:
        await set_time(update, context)
    else:
        await update.message.reply_text("Я не понимаю это сообщение. Используйте команду /start для начала работы.")


# async def check_channel_post(update, context):
#     logger.info(context.bot_data["current_channel_post"])
#     if update.message.photo[-1].file_id == context.bot_data["current_channel_post"]['photo_id']:
#         await update.message.reply_text("ЕБАШЬ ПОРНО!")
#     else:
#         await update.message.reply_text(context.bot_data["current_channel_post"])

# Основная функция
def main() -> None:
    # Инициализация приложения и планировщика
    application = Application.builder().token(os.getenv('BOT_TOKEN')).build()
    
    # Планировщик передается в обработчики
    scheduler = BackgroundScheduler()
    application.bot_data["scheduler"] = scheduler
    application.bot_data["user_data_manager"] = UserDataManager()
    
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add_post", add_post))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, handle_text))
    
 
        
    # Запуск планировщика
    scheduler.start()
    
    application.run_polling()

if __name__ == '__main__':
    main()