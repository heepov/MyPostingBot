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


# Загружаем переменные из .env файла
load_dotenv()
# Теперь вы можете использовать токен как переменную окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')

USER_STATE_WAITING_FOR_IMAGE = 'waiting_for_image'
USER_STATE_WAITING_FOR_CHANNEL = 'waiting_for_channel'
USER_STATE_WAITING_FOR_TIME = 'waiting_for_time'
USER_STATE_IDLE = 'idle'

# Константы для идентификаторов канала и чата
CHANNEL_ID = -1002326941935  # Замените на ID вашего канала
CHAT_ID = -1002355298602  # Замените на ID вашего чата

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Путь к файлу для хранения постов
POSTS_FILE = 'posts.json'

# Словарь для хранения данных о постах
scheduled_posts = {}
current_post={}

user_state = {}

# Загружаем существующие посты из файла
def load_posts():
    if os.path.exists(POSTS_FILE):
        with open(POSTS_FILE, 'r') as f:
            return json.load(f)
    return {}

# Сохраняем посты в файл
def save_posts():
    # Открываем файл для добавления данных, а не перезаписи
    with open(POSTS_FILE, 'w') as f:
        json.dump(scheduled_posts, f, indent=4)
        
# Функция для добавления нового поста
def add_new_post(user_id):
    global scheduled_posts, current_post

    if user_id not in scheduled_posts:
        scheduled_posts[user_id] = []
    
    scheduled_posts[user_id].append(current_post.copy())  # Добавляем новый пост в список
    save_posts()  # Сохраняем изменения
    
    
# Создаем объект планировщика
scheduler = BackgroundScheduler()

# Команда /start
async def start(update: Update, context: CallbackContext) -> None:
    if update.effective_chat.type != 'private':
        return  # Игнорируем команды, не из личных сообщений
    user_state[update.message.from_user.id] = USER_STATE_IDLE  # Устанавливаем состояние в 'idle' при старте
    await update.message.reply_text("Привет! Отправь команду /add_post для добавления поста.")

# Команда /add_post
async def add_post(update: Update, context: CallbackContext) -> None:
    user_state[update.message.from_user.id] = USER_STATE_WAITING_FOR_IMAGE  # Устанавливаем состояние в 'waiting_for_image'
    await update.message.reply_text("Пожалуйста, отправьте текст вашего поста и прикрепите картинку.")

# Функция для обработки сообщений с изображением и текстом
async def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_state.get(user_id) != USER_STATE_WAITING_FOR_IMAGE:
        return  # Игнорируем сообщения, если пользователь не в нужном состоянии
    
    if update.effective_chat.type != 'private':
        return  # Игнорируем сообщения не из личных чатов

    message = update.message
    global current_post
    
    if message.photo:
        current_post = {
            'message_id': message.message_id,
            'photo_id': message.photo[-1].file_id,
            'text': message.caption if message.caption else "",
            'scheduled_time': None,
            'channel_id' : None
        }
        user_state[user_id] = USER_STATE_WAITING_FOR_CHANNEL  # Переходим к состоянию выбора канала
        await update.message.reply_text("Теперь выберите, куда будет отправлен пост:", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("КАНАЛ", callback_data="set_channel"),
             InlineKeyboardButton("ЧАТ", callback_data="set_chat")]
        ]))
    else:
        await update.message.reply_text("Пожалуйста, отправьте изображение с текстом.")
        
# Обработчик для установки ID канала/чата
async def set_channel_id(update: Update, context: CallbackContext) -> None:
    if update.effective_chat.type != 'private':
        return  # Игнорируем сообщения не из личных чатов

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
    user_id = update.callback_query.from_user.id
    if user_state.get(user_id) != USER_STATE_WAITING_FOR_CHANNEL:
        return  # Игнорируем выбор, если пользователь не в нужном состоянии
    
    query = update.callback_query
    global current_post
    
    await query.answer()  # Подтверждение нажатия кнопки

    # Получаем ID канала/чата, куда нужно отправить посты
    new_channel_id = CHANNEL_ID if query.data == "set_channel" else CHAT_ID

    current_post['channel_id'] = new_channel_id
    
    # Ответ пользователю
    if query.data == "set_channel":
        await query.edit_message_text("Сообщения будут отправлены в КАНАЛ.")
    elif query.data == "set_chat":
        await query.edit_message_text("Сообщения будут отправлены в ЧАТ.")
    
    user_state[user_id] = USER_STATE_WAITING_FOR_TIME  # Переходим к состоянию ожидания времени публикации
    await query.message.reply_text("Теперь отправьте дату и время публикации (формат: YYYY-MM-DD HH:MM).")

# Установка времени для публикации
async def set_time(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_state.get(user_id) != USER_STATE_WAITING_FOR_TIME:
        return  # Игнорируем сообщения, если пользователь не в нужном состоянии
    
    if update.effective_chat.type != 'private':
        return  # Игнорируем сообщения, не из личных чатов
    
    global current_post
    try:
        user_id = update.message.from_user.id
        datetime_str = update.message.text.strip()

        logger.info(current_post)
        if not current_post:
            await update.message.reply_text("Сначала отправьте изображение с текстом.")
            return

        post_time = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
        if post_time < datetime.now():
            await update.message.reply_text("Дата и время должны быть позже текущего момента.")
            return

        if not current_post["channel_id"]:
            await update.message.reply_text("Сначала укажите ID канала.")
            return

        # Обновляем только scheduled_time
        current_post['scheduled_time'] = post_time.strftime("%Y-%m-%d %H:%M")
        job_id = f"{user_id}_{current_post['message_id']}_{current_post['scheduled_time']}"

        if not scheduler.get_job(job_id):
            trigger = DateTrigger(run_date=post_time)
            
            scheduler.add_job(
                forward_post_async,
                trigger,
                args=[context.bot, current_post['channel_id'], current_post['text'], current_post['photo_id'], user_id, current_post['message_id'], update.message.chat_id],
                id=job_id
            )

        add_new_post(user_id)
        user_state[user_id] = USER_STATE_IDLE  # Завершаем процесс и возвращаемся к состоянию 'idle'
        await update.message.reply_text(f"Посты будут опубликованы {post_time.strftime('%Y-%m-%d %H:%M')}.")
    except ValueError:
        await update.message.reply_text("Ошибка! Проверьте формат даты и времени (YYYY-MM-DD HH:MM).")
    except Exception as e:
        logger.error(f"Error in set_time: {e}")
        await update.message.reply_text("Произошла ошибка. Попробуйте снова.")
      
#   
def remove_post(user_id, message_id):
    global scheduled_posts
    if user_id in scheduled_posts:
        scheduled_posts[user_id] = [post for post in scheduled_posts[user_id] if post['message_id'] != message_id]
        save_posts()  # Сохраняем изменения после удаления
        
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

# Основная функция
def main() -> None:
    global scheduled_posts, current_post
    scheduled_posts = load_posts()
    current_post = {}

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add_post", add_post))
    application.add_handler(CommandHandler("set_channel", set_channel_id))  # Команда выбора канала/чата
    application.add_handler(CallbackQueryHandler(button_callback))  # Обработчик кнопок
    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE & ~filters.COMMAND, set_time))  # Обрабатываем время публикации
    application.add_handler(MessageHandler(filters.PHOTO & filters.ChatType.PRIVATE, handle_message))
    

    scheduler.start()
    application.run_polling()

if __name__ == '__main__':
    main()