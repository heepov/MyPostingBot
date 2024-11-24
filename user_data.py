# user_data_manager.py

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Literal, Optional

from pydantic import BaseModel, field_validator

from post import Post
from states import State

logger = logging.getLogger(__name__)


class Channel(BaseModel):
    channel_id: Optional[int] = None
    channel_permission: bool = False
    chat_id: Optional[int] = None
    chat_permission: bool = False

    def to_dict(self):
        return {
            "channel_id": self.channel_id,
            "channel_permission": self.channel_permission,
            "chat_id": self.chat_id,
            "chat_permission": self.chat_permission,
        }

    def reset(self):
        self.channel_id = None
        self.channel_permission = False
        self.chat_id = None
        self.chat_permission = False


class UserData(BaseModel):
    user_id: int
    user_name: Optional[str] = ""
    channels: List[Channel] = []
    state: State = State.ERROR
    post: Optional[Post] = None

    @field_validator("state", mode="before")
    def validate_state(cls, value):
        if value in vars(State).values():
            return value
        raise ValueError(f"Invalid state: {value}")

    def add_new_channel(
        self,
        channel_id: int,
        channel_permission=False,
        chat_id: int = None,
        chat_permission=False,
    ) -> None:
        self.channels.append(
            Channel(
                channel_id=channel_id,
                channel_permission=channel_permission,
                chat_id=chat_id,
                chat_permission=chat_permission,
            )
        )

    def user_has_channel_with_permission(self) -> bool:
        for channel in self.channels:
            if channel.channel_id != None and channel.channel_permission != False:
                return True

        return False

    def chanel_already_added(self, channel_id) -> bool:
        for channel in self.channels:
            if channel.channel_id == channel_id:
                return True

        return False

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "channels": [channels.to_dict() for channels in (self.channels or [])],
            "state": self.state,
            "post": self.post,
        }
