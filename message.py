from datetime import datetime, timedelta, timezone
from typing import List, Literal, Optional

from pydantic import BaseModel, field_validator


class Message(BaseModel):
    text: Optional[str] = None
    caption: Optional[str] = None
    date_time: datetime
    message_id: int
    user_id: int
    file_type: Optional[Literal["video", "photo", "document", "audio"]] = None
    file_id: Optional[str] = None
    media_group_id: Optional[str] = None

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

    def to_dict(self):
        return {
            "text": self.text,
            "caption": self.caption,
            "date_time": self.date_time.isoformat(),
            "message_id": self.message_id,
            "user_id": self.user_id,
            "file_type": self.file_type,
            "file_id": self.file_id,
            "media_group_id": self.media_group_id,
        }
