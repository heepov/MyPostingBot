from src.db import db_add_or_get_model, Users


async def add_or_update_user(
    user_id: int,
    first_name: str | None,
    last_name: str | None,
    username: str | None,
    language_code: str | None,
) -> Users:
    user = Users(
        user_id=user_id,
        first_name=first_name,
        last_name=last_name,
        username=username,
        language_code=language_code,
    )
    return db_add_or_get_model(user)
