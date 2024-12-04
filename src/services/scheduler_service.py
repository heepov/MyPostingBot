from datetime import datetime
import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from aiogram.types import InputMediaPhoto, InputMediaVideo, InputMediaDocument
from aiogram import Bot
from src.services.post_service import get_post_messages, get_user, get_channel, get_post
from src.db.models import Posts

logger = logging.getLogger(__name__)


class PostScheduler:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler(
            jobstores={"default": MemoryJobStore()}, timezone="UTC"
        )

    async def send_media_group(self, chat_id: int, media_group: list):
        """Отправка медиа группы"""
        try:
            await self.bot.send_media_group(chat_id=chat_id, media=media_group)
        except Exception as e:
            logger.error(f"Error sending media group: {e}")

    async def send_single_message(
        self, chat_id: int, message_data: dict, channel_caption: str = None, first_message_sent: bool = False
    ):
        """Отправка одиночного сообщения"""
        try:
            sent_message = None

            if message_data.get("text"):
                text = message_data["text"]
                if channel_caption:
                    text = f"{text}\n\n{channel_caption}"
                sent_message = await self.bot.send_message(
                    chat_id=chat_id, text=text, request_timeout=20.0
                )
            else:
                caption = message_data.get("caption", "")
                if channel_caption:
                    caption = (
                        f"{caption}\n\n{channel_caption}"
                        if caption
                        else channel_caption
                    )

                if message_data["file_type"] == "photo":
                    sent_message = await self.bot.send_photo(
                        chat_id=chat_id,
                        photo=message_data["file_id"],
                        caption=caption,
                        request_timeout=20.0,
                    )
                elif message_data["file_type"] == "video":
                    sent_message = await self.bot.send_video(
                        chat_id=chat_id,
                        video=message_data["file_id"],
                        caption=caption,
                        request_timeout=20.0,
                    )
                elif message_data["file_type"] == "document":
                    sent_message = await self.bot.send_document(
                        chat_id=chat_id,
                        document=message_data["file_id"],
                        caption=caption,
                        request_timeout=20.0,
                    )

            # Сохраняем message_id первого отправленного сообщения
            if (
                sent_message
                and not first_message_sent
                and message_data.get("post_id")
            ):
                await self._save_message_id(
                    message_data["post_id"], sent_message.message_id
                )
                return True  # Возвращаем флаг, что сообщение сохранено

            return first_message_sent  # Возвращаем текущее состояние флага

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return first_message_sent

    async def _save_message_id(self, post_id: int, message_id: int):
        """Сохраняет ID сообщения в БД"""
        try:
            logger.info(f"Saving message ID {message_id} for post {post_id}")
            post = Posts.get(Posts.post_id == post_id)
            post.sended_message_id = message_id
            post.save()
            logger.info(f"Successfully saved message ID {message_id} for post {post_id}")
        except Exception as e:
            logger.error(f"Error saving message ID for post {post_id}: {e}")

    async def send_post(self, post_id: int):
        logger.info(f"Starting to send post {post_id}")
        try:
            post = await get_post(post_id)
            if not post:
                logger.error(f"Post {post_id} not found")
                return

            channel = await get_channel(post.channel_id)
            if not channel:
                logger.error(f"Channel {post.channel_id} not found")
                return

            messages = await get_post_messages(post_id, True)
            if not messages:
                logger.warning(f"No messages found for post {post_id}")
                return

            await self._process_messages(
                messages, channel.channel_caption, channel.channel_id
            )
            
            # Проверяем, сохранился ли ID сообщения
            updated_post = await get_post(post_id)
            if not updated_post.sended_message_id:
                logger.error(f"sended_message_id was not saved for post {post_id}")

        except Exception as e:
            logger.error(f"Error sending post {post_id}: {e}")

    async def _process_messages(
        self, messages: list, channel_caption: str = None, channel_id: int = None
    ):
        """Обработка списка сообщений"""
        if not messages:
            return

        post_id = messages[0].post_id if messages else None
        first_message_sent = False

        # Обрабатываем текстовые сообщения первыми
        text_messages = [msg for msg in messages if msg.text and not msg.file_type]
        for msg in text_messages:
            message_data = {
                "text": msg.text,
                "post_id": post_id,
            }
            first_message_sent = await self.send_single_message(
                channel_id, message_data, channel_caption, first_message_sent
            )

        # Затем обрабатываем медиа сообщения
        media_messages = [msg for msg in messages if msg.file_type]
        media_groups = {}

        # Сначала отправляем одиночные медиа
        for msg in media_messages:
            if not msg.media_group_id:
                message_data = {
                    "caption": msg.caption,
                    "file_type": msg.file_type,
                    "file_id": msg.file_id,
                    "post_id": post_id,
                }
                first_message_sent = await self.send_single_message(
                    channel_id, message_data, channel_caption, first_message_sent
                )

            else:
                if msg.media_group_id not in media_groups:
                    media_groups[msg.media_group_id] = []
                media_groups[msg.media_group_id].append(msg)

        # Отправляем медиа группы
        for media_group in media_groups.values():
            media = []
            last_msg = media_group[-1]

            for msg in media_group:
                caption = msg.caption or ""
                if msg == last_msg and channel_caption:
                    caption = (
                        f"{caption}\n\n{channel_caption}"
                        if caption
                        else channel_caption
                    )

                if msg.file_type == "photo":
                    media.append(InputMediaPhoto(media=msg.file_id, caption=caption))
                elif msg.file_type == "video":
                    media.append(InputMediaVideo(media=msg.file_id, caption=caption))
                elif msg.file_type == "document":
                    media.append(InputMediaDocument(media=msg.file_id, caption=caption))

            if media:
                try:
                    sent_messages = await self.bot.send_media_group(
                        chat_id=channel_id, media=media, request_timeout=35.0
                    )
                    # Сохраняем ID первого сообщения из медиа-группы
                    if not first_message_sent and sent_messages:
                        await self._save_message_id(
                            post_id, sent_messages[0].message_id
                        )
                except Exception as e:
                    logger.error(f"Error sending media group: {e}")

    async def schedule_post(self, post_id: int):
        """
        Добавление поста в планировщик
        Args:
            post_id: ID поста
            date_time: время публикации (опционально, если не указано - берется из БД)
        """
        try:
            # Получаем пост из БД
            post = await get_post(post_id)
            if not post:
                logger.error(f"Post {post_id} not found")
                return

            channel = await get_channel(post.channel_id)
            user = await get_user(channel.user_id)  # Нужно создать эту функцию
            timezone = (
                user.time_zone or "Europe/Moscow"
            )  # Используем часовой пояс пользователя

            schedule_time = post.date_time

            if not schedule_time:
                logger.error(f"No schedule time for post {post_id}")
                return

            job_id = f"post_{post_id}"
            self.scheduler.add_job(
                self.send_post,
                "date",
                run_date=schedule_time,
                args=[post_id],
                id=job_id,
                replace_existing=True,
                timezone=timezone,
            )
            logger.info(f"Scheduled post {post_id} for {schedule_time}")
        except Exception as e:
            logger.error(f"Error scheduling post {post_id}: {e}")

    def start(self):
        """Запуск планировщика"""
        self.scheduler.start()
        asyncio.create_task(self.restore_scheduled_posts())
        logger.info("Scheduler started")

    def shutdown(self):
        """Остановка планировщика"""
        self.scheduler.shutdown()
        logger.info("Scheduler shutdown")

    def remove_job(self, post_id: int):
        """Удаление задачи из планировщика"""
        job_id = f"post_{post_id}"
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed job {job_id} from scheduler")
        except Exception as e:
            logger.error(f"Error removing job {job_id}: {e}")

    async def restore_scheduled_posts(self):
        """Восстанавливает все запланированные посты при перезапуске бота"""
        logger.info("Restoring scheduled posts...")
        try:
            # Получаем все будущие посты из всех каналов
            current_time = datetime.now()
            future_posts = Posts.select().where(Posts.date_time > current_time)
            
            count = 0
            for post in future_posts:
                try:
                    await self.schedule_post(post.post_id)
                    count += 1
                except Exception as e:
                    logger.error(f"Error restoring post {post.post_id}: {e}")
                    
            logger.info(f"Successfully restored {count} scheduled posts")
            
        except Exception as e:
            logger.error(f"Error restoring scheduled posts: {e}")
