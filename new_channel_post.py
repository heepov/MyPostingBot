# new_channel_post.py

import os
import logging
from datetime import datetime
from apscheduler.triggers.date import DateTrigger
from telegram.ext import CallbackContext
import asyncio

from states import State
from file_service import load_file, save_file


# Настройка логирования
logger = logging.getLogger(__name__)

# Константы для идентификаторов канала и чата
CHANNEL_ID = -1002326941935
CHAT_ID = -1002355298602

# Словарь для хранения данных о постах
scheduled_channel_posts = load_file(os.getenv('CHANNEL_POSTS_FILE'))
current_channel_post = {}

# Добавляет новые данные к существующему ключу в файле.
# Если ключ отсутствует, создаёт его с новым списком.
def append_post_by_user_id(user_id, file_name):
    global scheduled_channel_posts, current_channel_post 
    if user_id in scheduled_channel_posts:
        if isinstance(scheduled_channel_posts[user_id], list):  # Убедимся, что значение ключа — это список
            scheduled_channel_posts[user_id].append(current_channel_post)
        else:
            logger.error(f"ValueError Значение для ключа {user_id} не является списком.")
    else:
        # Если ключа нет, создаём его с новым списком
        scheduled_channel_posts[user_id] = [current_channel_post]
    save_file(scheduled_channel_posts, file_name)

def delete_post_by_user_id(user_id, message_id, file_name):
    global scheduled_channel_posts
    if user_id in scheduled_channel_posts:
        scheduled_channel_posts[user_id] = [post for post in scheduled_channel_posts[user_id] if post['message_id'] != message_id]
        save_file(scheduled_channel_posts, file_name)

# Функция для обработки сообщений с изображением и текстом
async def handle_channel_message(update, context: CallbackContext) -> None:
    global current_channel_post
    message = update.message
    if message.photo:
        user_id = update.message.from_user.id
        photo_id = message.photo[-1].file_id
        current_channel_post = {
            'message_id': message.message_id,
            'photo_id': photo_id,
            'text': message.caption if message.caption else "",
            'scheduled_time': None,
            'channel_id' : CHANNEL_ID #TODO channel_id
        }
        user_data_manager = context.bot_data.get("user_data_manager")
        user_data_manager.set_state(user_id, State.WAITING_TIME_FOR_CHANNEL_POST)
        await update.message.reply_text("Теперь отправьте дату и время публикации (формат: YYYY-MM-DD HH:MM).")
    else:
        await update.message.reply_text("Пожалуйста, отправьте изображение с текстом.")

# Установка времени для публикации
async def set_time(update, context: CallbackContext) -> None:
    global current_channel_post
    try:
        user_id = update.message.from_user.id
        datetime_str = update.message.text.strip()

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

        scheduler = context.bot_data["scheduler"]
        
        if not scheduler.get_job(job_id):
            trigger = DateTrigger(run_date=post_time)
            
            scheduler.add_job(
                forward_post_async,
                trigger,
                args=[context.bot, current_channel_post['channel_id'], current_channel_post['text'], current_channel_post['photo_id'], user_id, current_channel_post['message_id'], update.message.chat_id],
                id=job_id
            )

        append_post_by_user_id(user_id, os.getenv('CHANNEL_POSTS_FILE'))
        
        user_data_manager = context.bot_data.get("user_data_manager")
        user_data_manager.reset_state(user_id)
        user_data_manager.set_current_channel_post(user_id, current_channel_post)
        
        await update.message.reply_text(f"Пост будет опубликован {post_time.strftime('%Y-%m-%d %H:%M')}.")
    except ValueError:
        await update.message.reply_text("Ошибка! Проверьте формат даты и времени (YYYY-MM-DD HH:MM).")
    except Exception as e:
        logger.error(f"Error in set_time: {e}")
        await update.message.reply_text("Произошла ошибка. Попробуйте снова.")

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
        delete_post_by_user_id(user_id, message_id, os.getenv('CHANNEL_POSTS_FILE'))
    except Exception as e:
        logger.error(f"Error forwarding post: {e}")

# Обертка для асинхронной функции пересылки
def forward_post_async(bot, chat_id, text, photo_id, user_id, message_id, user_chat_id):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(forward_post(bot, chat_id, text, photo_id, user_id, message_id, user_chat_id))