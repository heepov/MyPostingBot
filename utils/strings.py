# Common messages
MSG_ERROR = lambda error: f"Some error: {error}"
EXTRA_STR_CANCEL = "To return to main menu send /cancel"

# Start messages
MSG_START = "/help - to know more about bot\n/cancel – to return to main menu"

# Add channel messages
MSG_ERROR_WRONG_LINK = "Wrong link. Try again."
MSG_ERROR_CANT_GET_CHAT = "Can't get chat info"
MSG_ERROR_NO_PERMISSION = "Bot doesn't have permission in this chat"
MSG_ADD_CHANNEL_INSTRUCTION = (
    f"Add bot to CHANNEL admins and send here link or username. {EXTRA_STR_CANCEL}"
)
MSG_CHANNEL_ADDED = (
    lambda channel_username: f"You added CHANNEL @{channel_username}.\n\nIf you want to add CHAT, send here link or username. {EXTRA_STR_CANCEL}"
)
MSG_CHANNEL_AND_CHAT_ADDED = (
    lambda channel_username, chat_username: f"Channel @{channel_username} with linked Chat @{chat_username} successfully added!"
)

# Add post messages
