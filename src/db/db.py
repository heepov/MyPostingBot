import logging
from peewee import *

from .models import Channels, Messages, Posts, Users, db_postgres, BaseModel


logger = logging.getLogger(__name__)


def connect_db() -> None:
    if db_postgres.is_closed():
        db_postgres.connect()


def close_db() -> None:
    if not db_postgres.is_closed():
        db_postgres.close()


# def delete_db() -> None:
#     if not db.is_closed():
#         db.drop_tables([Users, Channels, Posts, Messages])


def create_tables() -> None:
    db_postgres.create_tables([Users, Channels, Posts, Messages])


def db_add_or_get_model(model: BaseModel) -> BaseModel:
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


def db_get_user_channels(user_id: int) -> list[Channels] | None:
    try:
        return list(
            Channels.select().where(
                (Channels.user_id == user_id) & (Channels.channel_permission == True)
            )
        )
    except Channels.DoesNotExist:
        logger.warning(f"Channels by user {user_id} not found or no permission")
        return None


def db_get_channel(channel_id: int) -> Channels | None:
    try:
        return Channels.get(
            (Channels.channel_id == channel_id) & (Channels.channel_permission == True)
        )
    except Channels.DoesNotExist:
        logger.warning(f"Channel {channel_id} not found or no permission")
        return None


def db_get_user(user_id: int) -> Users | None:
    try:
        return Users.get(Users.user_id == user_id)
    except Users.DoesNotExist:
        logger.warning(f"User {user_id} not found")
        return None
