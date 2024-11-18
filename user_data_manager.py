# user_data_manager.py

import os
from states import State
from file_service import load_file

class UserDataManager:
    def __init__(self):
        self.user_data = {}

    def get_user_data(self, user_id):
        if user_id not in self.user_data:
            self.user_data[user_id] = {
                'state': State.IDLE,
                'current_channel_post': {},
                'users_channels' : load_file(os.getenv('USER_CHANNELS_FILE'))
                }
        return self.user_data[user_id]

    def set_current_channel_post(self, user_id: int, current_channel_post) -> None:
        user_data = self.get_user_data(user_id)
        user_data["current_channel_post"] = current_channel_post
        
    def get_current_channel_post(self, user_id: int):
        user_data = self.get_user_data(user_id)
        if not user_data['current_channel_post']:
            return None
        else:
            return user_data['current_channel_post']
        
    def set_users_channels(self, user_id: int, users_channels) -> None:
        user_data = self.get_user_data(user_id)
        user_data['users_channels'] = [users_channels]

    def get_users_channels(self, user_id: int):
        user_data = self.get_user_data(user_id)
        if not user_data['users_channels']:
            return None
        else:
            return user_data['users_channels']


    def set_state(self, user_id: int, state: str) -> None:
        """Устанавливает состояние пользователя."""
        user_data = self.get_user_data(user_id)
        user_data["state"] = state

    def get_state(self, user_id: int) -> str:
        """Возвращает текущее состояние пользователя. Если состояние не установлено, возвращает 'idle'."""
        user_data = self.get_user_data(user_id)
        return user_data.get("state", State.IDLE)

    def reset_state(self, user_id: int) -> None:
        """Сбрасывает состояние пользователя в 'idle'."""
        user_data = self.get_user_data(user_id)
        user_data["state"] = State.IDLE

    def delete_state(self, user_id: int) -> None:
        """Удаляет состояние пользователя (например, если нужно освободить память)."""
        user_data = self.get_user_data(user_id)
        if "state" in user_data:
            del user_data["state"]