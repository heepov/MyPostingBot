import logging
from peewee import *

from db.models import Channel, Message, Post, User, db, BaseModel

logger = logging.getLogger(__name__)


def connect_db() -> None:
    if db.is_closed():
        db.connect()


def close_db() -> None:
    if not db.is_closed():
        db.close()


def delete_db() -> None:
    if not db.is_closed():
        db.drop_tables([User, Channel, Post, Message])


def create_tables() -> None:
    db.create_tables([User, Channel, Post, Message])


def db_add_model(model: BaseModel) -> BaseModel:
    """Generic function to save or update any model instance"""
    try:
        unique_key = None

        # Определяем уникальное поле (например, user_id или channel_id)
        for key in model._meta.sorted_field_names:
            if "id" in key and key != "id":  # Находим уникальный идентификатор
                unique_key = key
                break

        if not unique_key:
            raise ValueError(
                f"Cannot determine unique key for {model.__class__.__name__}"
            )

        # Получаем или создаем объект
        instance, created = type(model).get_or_create(
            **{unique_key: getattr(model, unique_key)},
            defaults={
                field: getattr(model, field)
                for field in model._meta.sorted_field_names
                if field != unique_key
            },
        )

        # Если объект уже существует, обновляем его поля
        if not created:
            for field in model._meta.sorted_field_names:
                if field != unique_key:
                    setattr(instance, field, getattr(model, field))
            instance.save()

        logger.info(f"{'Created' if created else 'Updated'} {model.__class__.__name__}")

        return instance

    except Exception as e:
        logger.error(f"Error in db_add_model: {e}")
        raise


def db_get_channels_by_user_id(user_id: int) -> list[Channel]:
    return list(
        Channel.select().where(
            (Channel.user_id == user_id) & (Channel.channel_permission == True)
        )
    )


def db_get_channel_by_channel_id(channel_id: int) -> Channel | None:
    try:
        return Channel.get(
            (Channel.channel_id == channel_id) & (Channel.channel_permission == True)
        )
    except Channel.DoesNotExist:
        logger.warning(f"Channel {channel_id} not found or no permission")
        return None


def db_user_by_user_id(user_id: int) -> User | None:
    try:
        return User.get(User.user_id == user_id)
    except User.DoesNotExist:
        logger.warning(f"User {user_id} not found")
        return None
