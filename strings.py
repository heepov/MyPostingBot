# strings.py

from constants import DATE_TIME_FORMAT_PRINT


# ERROR = lambda error_message: f"An error occurred: {error_message}"
ERROR_ACCESS_DENIED = "Access denied!"
ERROR_EMPTY_DATA = (
    "No channels connected. Please connect channels using the /setup command."
)
ERROR_PERMISSIONS = "The bot lacks the required permissions."
ERROR_INVALID_COMMAND = (
    "Invalid command or message. Use /help or /cancel for assistance."
)
ERROR_CHANNEL_LINK = "This is not a valid channel or chat link/username."
ERROR_GET_CHANNEL_INFO = "Unable to retrieve channel or chat information."


COMMAND_START = "Welcome! Use /help to see the available commands."
COMMAND_HELP = (
    "Menu:\n"
    "/add - Add a new post\n"
    "/setup - Connect a channel\n"
    "/checkup - Check connection and permissions\n"
    "/help - Show this menu\n"
    "/cancel - Reset all actions\n"
    "/check_post - View scheduled posts\n"
    "/count - See how many posts are planned"
)
COMMAND_CANCEL = "All actions have been canceled."
COMMAND_SETUP = "To connect a channel, send me CHANNEL link or username."
COMMAND_ADD_POST = "Send the post (image and text):"
COMMAND_COUNT = lambda count: f"You have planned {count}"

ADD_POST_MEDIA_FILES = "Now upload the file that will be included as a comment. Once uploaded, send the /time command."

EXTRA_SETUP_ALREADY = "If you want to change the channel, send me the CHANNEL LINK. Otherwise, use /cancel."
COMMAND_TIME = f"Now send the date and time in this format: {DATE_TIME_FORMAT_PRINT}."
ERROR_DATE_TIME_FORMAT = (
    f"Invalid date and time format. Please use this format: {DATE_TIME_FORMAT_PRINT}."
)
ERROR_ADD_POST_NEED_PHOTO = "Пожалуйста, отправьте изображение для поста."
ERROR_DATE_TIME_PAST = "The date and time must be in the future."
ERROR_NEED_CANCEL = "This command work only after use /cancel command."
SUCCESS_PERMISSION = "The bot has all the required permissions."
SUCCESS_POST_SCHEDULED = "Success! Your post has been scheduled."
SUCCESS_POSTS_CHECKED = lambda count_posts: f"Success! You have : {count_posts} posts."
CHANNELS_INFO_STRING = lambda channel_username, chat_username: (
    f"Connected channels:\n"
    f"Channel: @{channel_username}\n"
    f"Chat: @{chat_username}\n"
)
ERROR_PERMISSION_STRING = lambda type, error_message: (
    f"The bot lacks the required permissions in your {type}. {error_message}"
)
CHAT_SETUP_STRING = (
    lambda type, channel_username: f"You have added the {type}: @{channel_username}."
)
CHANNEL_SETUP_STRING = "Now please send CHAT link or username:"
