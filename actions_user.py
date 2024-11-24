# actions_user.py

import logging

from telegram import Update

from globals import save_user_data_to_file, user_data_list
from states import State
from user_data import UserData

logger = logging.getLogger(__name__)


async def get_user_data(update: Update) -> UserData:
    message = update.effective_message
    user_id = message.from_user.id

    for user in user_data_list:
        if user.user_id == user_id:
            return user

    user = UserData(
        user_id=message.from_user.id,
        user_name=message.from_user.first_name,
    )
    user_data_list.append(user)

    await update.message.reply_text(f"Nice to meet you {user.user_name}!")
    return user
