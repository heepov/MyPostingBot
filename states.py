# states.py


class State:
    ERROR_DATA = "error_data"
    ERROR_PERMISSION = "error_permission"
    IDLE = "idle"

    ADDING_CHANNEL_POST = "waiting_channel_post"
    SETTING_TIMER_FOR_CHANNEL_POST = "waiting_time_for_channel_post"

    ADDING_CHAT_POSTS = "waiting_chat_posts"

    ADDING_CHANNEL = "waiting_add_channel"
    ADDING_CHAT = "waiting_add_chat"