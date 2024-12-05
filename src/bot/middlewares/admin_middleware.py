from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from config import config

class AdminMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id if isinstance(event, Message) else event.from_user.id

        if user_id not in config.admin_user_ids:
            if isinstance(event, Message):
                await event.answer("⛔️ Доступ запрещен. Бот доступен только для администратора.")
            else:
                await event.answer("⛔️ Доступ запрещен", show_alert=True)
            return
        
        return await handler(event, data)