from aiogram.fsm.state import State, StatesGroup

class AddChannel(StatesGroup):
    waiting_for_link = State()

class AddPost(StatesGroup):
    waiting_for_channel = State()
    waiting_for_messages = State()
    waiting_for_chat_messages = State()
    waiting_for_date = State()
    waiting_for_time = State()
    waiting_for_repeat = State()

class ShowSchedule(StatesGroup):
    waiting_for_channel = State()
    waiting_for_post = State()

class ChannelSettings(StatesGroup):
    waiting_for_channel = State()
    waiting_for_action = State()
    waiting_for_caption = State()