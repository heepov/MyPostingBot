from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
import logging


class Settings(BaseSettings):
    bot_token: SecretStr
    db_name: str
    db_user: str
    db_password: SecretStr
    db_host: str
    db_port: int

    date_time_format: str
    date_time_format_print: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


config = Settings()


def setup_logging(level=logging.INFO):
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),  # Вывод в консоль
            #     RotatingFileHandler(
            #         "bot.log", maxBytes=5_000_000, backupCount=5, encoding="utf-8"
            #     ),  # Ротация логов
        ],
    )

    # Настроим уровень логирования для httpx
    # logging.getLogger("httpx").setLevel(logging.WARNING)