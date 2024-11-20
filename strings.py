# strings.py

ERROR = lambda error_message: f"Shit happened. {error_message}"
ERROR_ACCESS_DENY = "Your access deny!"
ERROR_DATA = "You don't have any connected channels. Please connect your channel use this command /setup"
ERROR_PERMISSIONS = "Bot doesn't have require permissions"
ERROR_WRONG_MESSAGE = "Wrong command or message. Use command /help or /cancel"
ERROR_CHANNEL_LINK = "This isn't channel or chat link or username"
ERROR_CHANNEL_ADD = "Can't get channel or chat info."

COMMAND_START = "All good! To show menu input /help"
COMMAND_HELP = f"Menu:\n/add - to add new post\n/setup - to connect channels\n/checkup - to check connection and permission\n/help - to show menu\n/cancel - to reset all action"
COMMAND_CANCEL = "All actions canceled"
COMMAND_END = "Success your post was planing"
COMMAND_CHECKUP = "Start checking your channels"
COMMAND_SETUP = "To add channel and chat, send me CHANNEL link or username"
SETUP_ALREADY = (
    "If you want to change channel send me CHANNEL LINK. If not send /cancel command."
)
COMMAND_ADD = "Send post (picture and text):"
SETTING_TIME = lambda format: (f"Now send date and time (format: {format}).")
DATE_TIME_MISTAKE_FORMAT = lambda format: f"Date and time error. Check format {format}"
DATE_TIME_MISTAKE_PAST = "Date and time must be later than the current moment."
SUCCESS_CHANNEL_POST = (
    lambda post_time: f"Post will send {post_time}. \nNow send file witch will be send in comment. When uploading finish send command /end"
)
PERMISSION_SUCCESS = "Success bot has all required permission"
CHANNELS_INFO_STRING = (
    lambda channel_username, chat_username: f"Now you have connected:\nChannel: @{channel_username}\nChat: @{chat_username}"
)
ERROR_PERMISSION_STRING = (
    lambda type, error_message: f"Bot doesn't have required permissions in your {type}. {error_message}"
)
CHANNEL_SETUP_STRING = (
    lambda type, channel_username: f"You added {type} @{channel_username}."
)


