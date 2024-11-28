from aiogram.fsm.state import State, StatesGroup


class BaseState(StatesGroup):
    @classmethod
    def get_state_names(cls):
        return [state.state for state in cls.states]


class AddChannel(BaseState):
    adding_channel = State()
    confirming_without_chat = State()
    adding_chat = State()


class ChannelSelect(BaseState):
    selecting_channel = State()
    selected_channel = State()


class AddPost(BaseState):
    add_channel_message = State()
    add_chat_message = State()
    set_time = State()


class ChannelSettings(BaseState):
    editing = State()


class ShowSchedule(BaseState):
    show_schedule = State()
