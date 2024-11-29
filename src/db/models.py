from peewee import *
from config import config

db_postgres = PostgresqlDatabase(
    config.db_name,
    user=config.db_user,
    password=config.db_password.get_secret_value(),
    host=config.db_host,
    port=config.db_port,
)


# Базовая модель
class BaseModel(Model):
    class Meta:
        database = db_postgres


# Таблица User
class Users(BaseModel):
    user_id = BigIntegerField(primary_key=True)
    first_name = CharField(max_length=255, null=True)
    last_name = CharField(max_length=255, null=True)
    username = CharField(max_length=255, null=True)
    language_code = CharField(max_length=10, null=True)

    time_zone = CharField(max_length=50, null=True, default="Europe/Moscow")


# Таблица Channel
class Channels(BaseModel):
    channel_id = BigIntegerField(primary_key=True)
    channel_username = CharField(max_length=255, null=True)
    channel_title = CharField(max_length=255, null=True)
    channel_permission = BooleanField(default=False)
    channel_caption = CharField(max_length=255, null=True)

    chat_id = BigIntegerField(null=True)
    chat_username = CharField(max_length=255, null=True)
    chat_title = CharField(max_length=255, null=True)
    chat_permission = BooleanField(null=True)
    chat_caption = CharField(max_length=255, null=True)

    user_id = ForeignKeyField(Users, backref="channels", on_delete="CASCADE")


# Таблица Post
class Posts(BaseModel):
    post_id = AutoField()
    date_time = DateTimeField(null=True)
    sended_message_id = BigIntegerField(null=True)

    channel_id = ForeignKeyField(Channels, backref="posts", on_delete="CASCADE")


# Таблица Message
class Messages(BaseModel):
    message_id = AutoField()
    is_channel_message = BooleanField(default=True)

    text = TextField(null=True)
    caption = TextField(null=True)
    file_type = CharField(max_length=20, null=True)
    file_id = CharField(max_length=255, null=True)
    media_group_id = CharField(max_length=255, null=True)

    post_id = ForeignKeyField(Posts, backref="messages", on_delete="CASCADE")
