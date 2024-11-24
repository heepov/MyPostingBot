from enum import Enum


class State(str, Enum):
    ERROR = "error"
    IDLE = "idle"
    SET_CHANNEL = "set_channel"
    ADD_POST = "add_post"
    ADD_POST_CHAT = "add_post_chat"
    SET_POST_TIME = "set_post_time"
    ADD_CHANNEL = "add_channel"
    ADD_CHAT = "add_chat"
    DELETE_CHANNEL = "delete_channel"
