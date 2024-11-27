from aiogram.fsm.state import State, StatesGroup


class AddChannel(StatesGroup):
    adding_channel = State()
    adding_chat = State()
