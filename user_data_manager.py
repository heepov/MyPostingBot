# user_data_manager.py

from os import getenv
import logging
from states import State
from file_service import load_file, save_file

logger = logging.getLogger(__name__)
FILE_PATH = getenv("USER_DATA_FILE")


class UserDataManager:
    def __init__(self):
        self.channel_id = None
        self.chat_id = None

        self.photo_id = None
        self.state: State = State.ERROR_DATA
        self.load_data()

    def load_data(self):
        required_keys = {"channel_id", "chat_id"}
        user_data = load_file(FILE_PATH)
        if not all(key in user_data and user_data[key] for key in required_keys):
            logger.warning("Not all user data has")
            return
        else:
            self.channel_id = user_data["channel_id"]
            self.chat_id = user_data["chat_id"]
            self.state = State.IDLE

    def save_data(self):
        data = {
            "channel_id": self.channel_id,
            "chat_id": self.chat_id,
        }
        save_file(data, FILE_PATH)

    def get_channel_id(self):
        return self.channel_id

    def set_channel_id(self, channel_id):
        self.channel_id = channel_id

    def get_chat_id(self):
        return self.chat_id

    def set_chat_id(self, chat_id):
        self.chat_id = chat_id

    def get_photo_id(self):
        return self.photo_id

    def set_photo_id(self, photo_id):
        self.photo_id = photo_id

    def get_state(self):
        return self.state

    def set_state(self, state):
        self.state = state

    def reset_state(self):
        self.state = State.IDLE


user_data_manager = UserDataManager()
