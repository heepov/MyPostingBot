from dataclasses import dataclass
from typing import Optional


@dataclass
class ChannelInfo:
    """DTO для информации о канале"""

    channel_id: int
    channel_title: Optional[str]
    channel_username: Optional[str]
    channel_permission: Optional[bool]
    channel_caption: Optional[str]

    chat_id: Optional[int]
    chat_title: Optional[str]
    chat_username: Optional[str]
    chat_permission: Optional[bool]
    chat_caption: Optional[str]
