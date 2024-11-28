from typing import Any, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import Message

class BotMiddleware(BaseMiddleware):
    def __init__(self, bot):
        self.bot = bot
        
    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any]
    ) -> Any:
        data["bot"] = self.bot
        return await handler(event, data)
