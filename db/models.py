from peewee import *
from utils.config_reader import config

db = PostgresqlDatabase(
    config.db_name,
    user=config.db_user,
    password=config.db_password.get_secret_value(),
    host=config.db_host,
    port=config.db_port,
)


# Базовая модель
class BaseModel(Model):
    class Meta:
        database = db

# Таблица User
class User(BaseModel):
    user_id = BigIntegerField(primary_key=True)
    first_name = CharField(max_length=255, null=True)
    last_name = CharField(max_length=255, null=True)
    username = CharField(max_length=255, null=True)
    language_code = CharField(max_length=10, null=True)
    time_zone = CharField(max_length=50, null=True, default="Europe/Moscow")


# Таблица Channel
class Channel(BaseModel):
    channel_id = BigIntegerField(primary_key=True)
    channel_username = CharField(max_length=255, null=True)
    channel_permission = BooleanField(default=False)
    channel_caption = CharField(max_length=255, null=True)

    chat_id = BigIntegerField(null=True)
    chat_username = CharField(max_length=255, null=True)
    chat_permission = BooleanField(null=True)
    chat_caption = CharField(max_length=255, null=True)
    
    user_id = ForeignKeyField(User, backref="channels", on_delete="CASCADE")


# Таблица Post
class Post(BaseModel):
    post_id = AutoField()
    user_id = ForeignKeyField(User, backref="posts", on_delete="CASCADE")
    channel_id = ForeignKeyField(Channel, backref="posts", on_delete="CASCADE")
    date_time = DateTimeField(null=True)
    sended_message_id = BigIntegerField(null=True)


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
