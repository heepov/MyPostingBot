import logging

from aiogram import Bot
from aiogram.types import ChatMemberAdministrator, ChatMemberOwner

logger = logging.getLogger(__name__)


async def check_bot_permission(bot: Bot, chat_id: int) -> str|bool:
    try:
        admins = await bot.get_chat_administrators(chat_id)
        bot_id = (await bot.get_me()).id

        for admin in admins:
            if admin.user.id == bot_id and isinstance(
                admin, (ChatMemberAdministrator, ChatMemberOwner)
            ):
                return True
        return "Bot isn't an admin."
    except Exception as e:
        logging.error(f"Ошибка при проверке прав бота в чате {chat_id}: {e}")
        return str(e)


def extract_username_from_link(link: str) -> str | None:

    if link.startswith("https://t.me/"):
        return "@" + link.split("https://t.me/")[-1].strip("/")
    elif link.startswith("@"):
        return link.strip()
    else:
        return None
