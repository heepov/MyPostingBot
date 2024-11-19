# states.py

class State:    
    IDLE = "idle"

    WAITING_CHANNEL_POST = "waiting_channel_post"
    WAITING_TIME_FOR_CHANNEL_POST = "waiting_time_for_channel_post"

    WAITING_CHAT_POSTS = "waiting_chat_posts"

    WAITING_ADD_CHANNEL = "waiting_add_channel"
    WAITING_ADD_CHAT = "waiting_add_chat"


def get_user_state(context):
    return context.bot_data["user_state"]

def set_user_state(context, state):
    context.bot_data["user_state"] = state
    
def reset_user_state(context):
    context.bot_data["user_state"] = State.IDLE