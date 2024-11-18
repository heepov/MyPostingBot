#add_channel.py

async def add_channel_link(update: Update, context: CallbackContext) -> None:
    user_message = update.message.text.strip()
    
    # if user_message.startswith("https://t.me/") or user_message.startswith("@"):
    #     channel_info = user_message
    #     try:
    #         # Получаем информацию о канале
    #         channel = await context.bot.get_chat(channel_info)

    #         # Проверяем, является ли бот администратором канала
    #         is_admin_channel = await check_if_bot_is_admin(context.bot, channel.id)
    #         if not is_admin_channel:
    #             await update.message.reply_text(f"Бот не добавлен в канал {channel.username} или не имеет нужных прав.")
                
    #     except Exception as e:
    #         logging.error(f"Ошибка при добавлении канала: {e}")
    #         await update.message.reply_text(f"Произошла ошибка при добавлении канала {channel.username}. Ошибка: {str(e)}")
    # else:
    #     await update.message.reply_text("Я не могу найти ссылку или @имя канала в вашем сообщении. Пожалуйста, отправьте правильную ссылку или @имя канала.")
    
    
    # user_state[update.message.from_user.id] = USER_STATE_WAITING_ADD_CHANNEL 
    # await update.message.reply_text("Пожалуйста, ссылку на ваш КАНАЛ.")
    
    # user_state[update.message.from_user.id] = USER_STATE_WAITING_ADD_CHAT
    
async def add_chat(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Пожалуйста, ссылку на ЧАТ прикрепленный к вашему КАНАЛУ.")
    
    user_state[update.message.from_user.id] = State.IDLE
