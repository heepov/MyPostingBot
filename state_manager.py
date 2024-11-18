# state_manager.py

import logging
from states import State


logger = logging.getLogger(__name__)

class StateManager:
    def __init__(self):
        """Инициализация словаря для хранения состояний пользователей."""
        self.states = {}

    def set_state(self, user_id: int, state: str) -> None:
        """Устанавливает состояние пользователя."""
        self.states[user_id] = state

    def get_state(self, user_id: int) -> str:
        """Возвращает текущее состояние пользователя. Если состояние не установлено, возвращает 'idle'."""
        return self.states.get(user_id, State.IDLE)

    def reset_state(self, user_id: int) -> None:
        """Сбрасывает состояние пользователя в 'idle'."""
        self.states[user_id] = State.IDLE

    def delete_state(self, user_id: int) -> None:
        """Удаляет состояние пользователя (например, если нужно освободить память)."""
        if user_id in self.states:
            del self.states[user_id]