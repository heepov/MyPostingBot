from datetime import datetime, timedelta, timezone
from typing import List, Literal, Optional
from pydantic import BaseModel, field_validator
from message import Message


class Post(BaseModel):
    user_id: Optional[int] = None
    post_id: Optional[int] = None
    channel_id: Optional[int] = None
    chat_id: Optional[int] = None

    file_id: Optional[str] = None

    date_time: Optional[datetime] = None
    job_name: Optional[str] = None
    channel_message: List[Message] = []
    chat_message: List[Message] = []

    @staticmethod
    def parse_datetime_value(value) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value).astimezone(
                timezone(timedelta(hours=3))
            )
        if isinstance(value, int):
            return datetime.fromtimestamp(value, tz=timezone(timedelta(hours=3)))
        raise ValueError("Invalid date_time format")

    @field_validator("date_time", mode="before")
    def parse_date_time(cls, value) -> datetime:
        return cls.parse_datetime_value(value)

    def set_date_time(self, timestamp: int) -> None:
        self.date_time = self.parse_datetime_value(timestamp)
        self.update_job_name()

    def update_job_name(self) -> None:
        if self.date_time:
            self.job_name = (
                f"{self.user_id}_{self.post_id}_{int(self.date_time.timestamp())}"
            )

    def add_message(
        self, message: Message, channel_type: Literal["channel", "chat"]
    ) -> None:
        if channel_type == "channel":
            self.channel_message = self.channel_message or []
            self.channel_message.append(message)
        elif channel_type == "chat":
            self.chat_message = self.chat_message or []
            self.chat_message.append(message)

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "post_id": self.post_id,
            "channel_id": self.channel_id,
            "chat_id": self.chat_id,
            "date_time": self.date_time.isoformat() if self.date_time else None,
            "job_name": self.job_name,
            "channel_message": [
                message.to_dict() for message in (self.channel_message or [])
            ],
            "chat_message": [
                message.to_dict() for message in (self.chat_message or [])
            ],
        }

    def reset(self) -> None:
        self.user_id = None
        self.post_id = None
        self.channel_id = None
        self.chat_id = None
        self.date_time = None
        self.job_name = None
        self.channel_message = []
        self.chat_message = []
