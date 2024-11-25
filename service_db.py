from peewee import *
from datetime import datetime
from enum import Enum

from secret import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

# Подключение к базе данных
db = PostgresqlDatabase(
    DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
)


# Базовая модель
class BaseModel(Model):
    class Meta:
        database = db


# Enum для состояния пользователя
class State(str, Enum):
    IDLE = "idle"

    SET_CHANNEL = "set_channel"
    ADD_POST = "add_post"
    ADD_POST_CHAT = "add_post_chat"
    SET_POST_TIME = "set_post_time"

    ADD_CHANNEL = "add_channel"
    CHANNEL_SETTINGS = "channel_settings"
    CHANNEL_SELECT = "channel_select"
    ADD_CHAT = "add_chat"


# Таблица User
class User(BaseModel):
    user_id = BigIntegerField(primary_key=True)
    first_name = CharField(max_length=255, null=True)
    last_name = CharField(max_length=255, null=True)
    username = CharField(max_length=255, null=True)
    language_code = CharField(max_length=10, null=True)
    state = CharField(
        max_length=50,
        choices=[(state.value, state.name) for state in State],
        default=State.IDLE,
    )


# Таблица Channel
class Channel(BaseModel):
    channel_id = BigIntegerField(primary_key=True)
    username = CharField(max_length=255, null=True)
    permission = BooleanField(default=False)
    user_id = ForeignKeyField(User, backref="channels", on_delete="CASCADE")
    last_selected = BooleanField(default=False)


# Таблица Chat (только один для одного канала)
class Chat(BaseModel):
    chat_id = BigIntegerField(primary_key=True)
    username = CharField(max_length=255, null=True)
    permission = BooleanField(default=False)
    channel_id = ForeignKeyField(
        Channel, backref="chat", unique=True, on_delete="CASCADE"
    )


# Таблица Post
class Post(BaseModel):
    post_id = AutoField()
    user_id = ForeignKeyField(User, backref="posts", on_delete="CASCADE")
    channel_id = ForeignKeyField(Channel, backref="posts", on_delete="CASCADE")
    date_time = DateTimeField(null=True)
    sended_message_id = BigIntegerField(null=True)

    def to_dict(self):
        return {
            "post_id": self.post_id,
            "user_id": self.user_id,
            "channel_id": self.channel_id,
            "date_time": self.date_time,
        }

    def __repr__(self):
        return f"Post(post_id={self.post_id}, user_id={self.user_id}, channel_id={self.channel_id}, date_time = {self.date_time})"


# Таблица Message
class Message(BaseModel):
    message_id = AutoField()
    post_id = ForeignKeyField(Post, backref="messages", on_delete="CASCADE")
    is_channel_message = BooleanField(default=True)

    text = TextField(null=True)
    caption = TextField(null=True)
    file_type = CharField(max_length=20, null=True)
    file_id = CharField(max_length=255, null=True)
    media_group_id = CharField(max_length=255, null=True)


    def to_dict(self):
        return {
            "message_id": self.message_id,
            "is_channel_message": self.is_channel_message,
            "text": self.text,
            "caption": self.caption,
            "file_type": self.file_type,
            "file_id": self.file_id,
            "media_group_id": self.media_group_id,
        }