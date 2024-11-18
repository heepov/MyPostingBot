import os
import logging
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler
from dotenv import load_dotenv
from utils import check_if_bot_is_admin 
from state_manager import StateManager
from handlers import start, add_post, cancel, add_channel
from states import State

load_dotenv()

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Константы для идентификаторов канала и чата
CHANNEL_ID = -1002326941935
CHAT_ID = -1002355298602

# Словарь для хранения данных о постах
scheduled_channel_posts = {}
current_channel_post={}

# Создаем объект планировщика
scheduler = BackgroundScheduler()

# Загружаем существующие посты из файла
def load_channel_posts():
    if os.path.exists(os.getenv('CHANNEL_POSTS_FILE')):
        with open(os.getenv('CHANNEL_POSTS_FILE'), 'r') as f:
            return json.load(f)
    return {}

# Сохраняем посты в файл
def save_channel_posts():
    # Открываем файл для добавления данных, а не перезаписи
    with open(os.getenv('CHANNEL_POSTS_FILE'), 'w') as f:
        json.dump(scheduled_channel_posts, f, indent=4)
        
# Функция для добавления нового поста
def add_new_channel_post(user_id):
    global scheduled_channel_posts, current_channel_post

    if user_id not in scheduled_channel_posts:
        scheduled_channel_posts[user_id] = []
    
    scheduled_channel_posts[user_id].append(current_channel_post.copy())
    save_channel_posts()


# Функция для обработки сообщений с изображением и текстом
async def handle_channel_message(update: Update, context: CallbackContext) -> None:
    global current_channel_post

    message = update.message
    if message.photo:
        user_id = update.message.from_user.id        
        current_channel_post = {
            'message_id': message.message_id,
            'photo_id': message.photo[-1].file_id,
            'text': message.caption if message.caption else "",
            'scheduled_time': None,
            'channel_id' : None
        }
        
        state_manager = context.bot_data["state_manager"]
        state_manager.set_state(user_id, State.WAITING_ADD_CHANNEL)
        await update.message.reply_text("Теперь выберите, куда будет отправлен пост:", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("КАНАЛ", callback_data="set_channel"),
             InlineKeyboardButton("ЧАТ", callback_data="set_chat")]
        ]))
    else:
        await update.message.reply_text("Пожалуйста, отправьте изображение с текстом.")
        
# Обработчик для установки ID канала/чата
async def set_channel_type(update: Update, context: CallbackContext) -> None:

    # Создаем кнопки
    buttons = [
        [
            InlineKeyboardButton("КАНАЛ", callback_data="set_channel"),
            InlineKeyboardButton("ЧАТ", callback_data="set_chat")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("Выберите, куда будет отправлен пост:", reply_markup=reply_markup)

# Обработчик нажатий кнопок
async def button_callback(update: Update, context: CallbackContext) -> None:
    global current_channel_post
    
    user_id = update.callback_query.from_user.id
    state_manager = context.bot_data["state_manager"]
    state_manager.set_state(user_id, State.WAITING_ADD_CHANNEL)
    
    query = update.callback_query
    
    
    await query.answer()  # Подтверждение нажатия кнопки

    # Получаем ID канала/чата, куда нужно отправить посты
    new_channel_id = CHANNEL_ID if query.data == "set_channel" else CHAT_ID

    current_channel_post['channel_id'] = new_channel_id
    
    # Ответ пользователю
    if query.data == "set_channel":
        await query.edit_message_text("Сообщения будут отправлены в КАНАЛ.")
    elif query.data == "set_chat":
        await query.edit_message_text("Сообщения будут отправлены в ЧАТ.")
    
    state_manager = context.bot_data["state_manager"]
    state_manager.set_state(user_id, State.WAITING_FOR_TIME)
    await query.message.reply_text("Теперь отправьте дату и время публикации (формат: YYYY-MM-DD HH:MM).")

# Установка времени для публикации
async def set_time(update: Update, context: CallbackContext) -> None:
    global current_channel_post
    try:
        user_id = update.message.from_user.id
        datetime_str = update.message.text.strip()

        logger.info(current_channel_post)
        if not current_channel_post:
            await update.message.reply_text("Сначала отправьте изображение с текстом.")
            return

        post_time = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
        if post_time < datetime.now():
            await update.message.reply_text("Дата и время должны быть позже текущего момента.")
            return

        if not current_channel_post["channel_id"]:
            await update.message.reply_text("Сначала укажите ID канала.")
            return

        # Обновляем только scheduled_time
        current_channel_post['scheduled_time'] = post_time.strftime("%Y-%m-%d %H:%M")
        job_id = f"{user_id}_{current_channel_post['message_id']}_{current_channel_post['scheduled_time']}"

        if not scheduler.get_job(job_id):
            trigger = DateTrigger(run_date=post_time)
            
            scheduler.add_job(
                forward_post_async,
                trigger,
                args=[context.bot, current_channel_post['channel_id'], current_channel_post['text'], current_channel_post['photo_id'], user_id, current_channel_post['message_id'], update.message.chat_id],
                id=job_id
            )

        add_new_channel_post(user_id)
        state_manager = context.bot_data["state_manager"]
        state_manager.reset_state(user_id)
        await update.message.reply_text(f"Посты будут опубликованы {post_time.strftime('%Y-%m-%d %H:%M')}.")
    except ValueError:
        await update.message.reply_text("Ошибка! Проверьте формат даты и времени (YYYY-MM-DD HH:MM).")
    except Exception as e:
        logger.error(f"Error in set_time: {e}")
        await update.message.reply_text("Произошла ошибка. Попробуйте снова.")
      
# Сохраняем изменения после удаления
def remove_post(user_id, message_id):
    global scheduled_channel_posts
    if user_id in scheduled_channel_posts:
        scheduled_channel_posts[user_id] = [post for post in scheduled_channel_posts[user_id] if post['message_id'] != message_id]
        save_channel_posts() 
        
# Пересылка сообщения и удаление сообщения из чата с ботом
async def forward_post(bot, chat_id, text, photo_id, user_id, message_id, user_chat_id):
    try:
        # Пересылаем сообщение в канал или чат
        await bot.send_photo(chat_id=chat_id, photo=photo_id, caption=text)
        logger.info(f"Post forwarded to chat_id={chat_id}")
        
        # Удаляем сообщение из чата с ботом после пересылки
        await bot.delete_message(chat_id=user_chat_id, message_id=message_id)
        logger.info(f"Message {message_id} deleted from chat with bot.")

        # Удаляем пост из файла
        remove_post(user_id, message_id)
    except Exception as e:
        logger.error(f"Error forwarding post: {e}")
        
# Обертка для асинхронной функции пересылки
def forward_post_async(bot, chat_id, text, photo_id, user_id, message_id, user_chat_id):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(forward_post(bot, chat_id, text, photo_id, user_id, message_id, user_chat_id))

async def handle_text(update: Update, context: CallbackContext) -> None:
    state_manager = context.bot_data["state_manager"]  # Извлекаем state_manager
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

# Основная функция
def main() -> None:
    global scheduled_channel_posts, current_channel_post
    scheduled_channel_posts = load_channel_posts()
    current_channel_post = {}

    application = Application.builder().token(os.getenv('BOT_TOKEN')).build()
    state_manager = StateManager()
    application.bot_data["state_manager"] = state_manager


    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add_post", add_post))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CommandHandler("set_channel", set_channel_type))  # Команда выбора канала/чата
    application.add_handler(CommandHandler("add_channel", add_channel))
    application.add_handler(CallbackQueryHandler(button_callback))  # Обработчик кнопок
    
    
    application.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, handle_text))

    scheduler.start()
    application.run_polling()

if __name__ == '__main__':
    main()