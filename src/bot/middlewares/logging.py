from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message
from typing import Any, Awaitable, Callable, Dict
import logging
import inspect

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any],
    ) -> Any:
        # Получаем информацию о пользователе
        user = None
        if isinstance(event, CallbackQuery):
            user = event.from_user
            log_msg = f"Callback from {user.id} (@{user.username}): {event.data}"

            # Получаем информацию о handler'е
            handler_info = ""
            for frame in inspect.stack():
                if "handlers" in frame.filename and frame.function != "__call__":
                    relative_path = frame.filename.split("PostingBot/")[
                        -1
                    ]  # Используйте имя вашего проекта
                    handler_info = (
                        f"Handler: {relative_path}:{frame.lineno} in {frame.function}"
                    )
                    break

            log_msg = f"{log_msg}\n{handler_info}"

        elif isinstance(event, Message):
            user = event.from_user
            log_msg = (
                f"Message from {user.id} (@{user.username}): "
                f"{event.text if event.text else '[no text]'}"
            )

        if user:
            logger.info(
                f"[{user.id}] {log_msg} "
                f"(first_name: {user.first_name}, last_name: {user.last_name})"
            )

        return await handler(event, data)
