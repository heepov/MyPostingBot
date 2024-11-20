# states.py


class State:
    ERROR_DATA = "error_data"
    ERROR_PERMISSION = "error_permission"
    IDLE = "idle"

    CREATING_POST = "create_post"
    ADDING_MEDIA = "adding_media"
    SETTING_TIMER = "setting_timer"
    FINISH_CREATING_POST = "finish_creating_post"

    ADDING_CHANNEL = "waiting_add_channel"
    ADDING_CHAT = "waiting_add_chat"
